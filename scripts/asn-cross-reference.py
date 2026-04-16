#!/usr/bin/env python3
"""
ASN Cross-Reference Tool

Scrapes the Aviation Safety Network database for Bomber Command aircraft types
and cross-references the records against our memorial database.

Usage:
    python3 scripts/asn-cross-reference.py [--dry-run] [--type LANC]

Supported types: LANC, HALI, WELL, STIR, MOSQ

The script is incremental — URLs already present in scrape_log are skipped.
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ─── Configuration ────────────────────────────────────────────────────────────

DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"
DB_PASS = "BmrResearch2026xHeritage"

RATE_LIMIT_SECONDS = 3.0

UA = "Mozilla/5.0 (compatible; BomberMemorialRegister/1.0)"

ASN_TYPES = {
    "LANC": ("Lancaster",  "https://aviation-safety.net/asndb/type/LANC"),
    "HALI": ("Halifax",    "https://aviation-safety.net/asndb/type/HALI"),
    "WELL": ("Wellington", "https://aviation-safety.net/asndb/type/WELL"),
    "STIR": ("Stirling",   "https://aviation-safety.net/asndb/type/STIR"),
    "MOSQ": ("Mosquito",   "https://aviation-safety.net/asndb/type/MOSQ"),
}

ASN_BASE = "https://aviation-safety.net"


# ─── Database helpers ─────────────────────────────────────────────────────────

def db_query(sql: str) -> str:
    """Run a SELECT and return raw psql output (pipe-separated)."""
    result = subprocess.run(
        [
            "docker", "exec", DB_CONTAINER,
            "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql,
        ],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip()


def db_exec(sql: str, dry_run: bool = False) -> bool:
    """Execute a write statement. Returns True on success."""
    if dry_run:
        print(f"  [DRY-RUN] {sql[:120]}")
        return True
    result = subprocess.run(
        [
            "docker", "exec", DB_CONTAINER,
            "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql,
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  [DB ERROR] {result.stderr.strip()[:200]}", file=sys.stderr)
    return result.returncode == 0


def escape_sql(value: str) -> str:
    """Escape a string value for SQL insertion."""
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 20) -> tuple[str | None, str | None]:
    """
    Fetch a URL and return (html, error). Returns (None, error_str) on failure.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:
        return None, str(exc)


def clean_html(raw: str) -> str:
    """Strip HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", raw)
    for entity, char in [
        ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
        ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'"),
    ]:
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


# ─── Scrape-log helpers ───────────────────────────────────────────────────────

def already_scraped(url: str) -> bool:
    """Return True if this URL has a successful scrape_log entry."""
    result = db_query(
        f"SELECT id FROM scrape_log WHERE url = {escape_sql(url)} AND status = 'completed' LIMIT 1;"
    )
    return bool(result)


def log_scrape(url: str, html: str, extracted: dict, dry_run: bool) -> int | None:
    """Insert a completed scrape_log row and return its id."""
    extracted_json = escape_sql(json.dumps(extracted))
    html_escaped = escape_sql(html[:500_000])  # cap at ~500 KB
    now = datetime.now(timezone.utc).isoformat()

    sql = (
        "INSERT INTO scrape_log (url, status, scraped_at, raw_content, extracted_data) "
        f"VALUES ({escape_sql(url)}, 'completed', {escape_sql(now)}, {html_escaped}, {extracted_json}::jsonb) "
        "RETURNING id;"
    )
    if dry_run:
        print(f"  [DRY-RUN] scrape_log INSERT for {url}")
        return -1

    result = subprocess.run(
        [
            "docker", "exec", DB_CONTAINER,
            "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql,
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip())
    return None


def log_scrape_error(url: str, error: str, dry_run: bool) -> None:
    """Insert a failed scrape_log row."""
    now = datetime.now(timezone.utc).isoformat()
    sql = (
        "INSERT INTO scrape_log (url, status, scraped_at, error_message) "
        f"VALUES ({escape_sql(url)}, 'failed', {escape_sql(now)}, {escape_sql(error)}) "
        "ON CONFLICT DO NOTHING;"
    )
    db_exec(sql, dry_run=dry_run)


# ─── ASN list-page scraping ───────────────────────────────────────────────────

def parse_asn_list_page(html: str) -> list[dict]:
    """
    Parse the ASN type index page and return a list of incident dicts.

    Each dict has: wikibase_id, detail_url, date_raw, registration, location
    """
    incidents = []

    # ASN list pages have a table with class="hp". Each row is one accident.
    # Typical columns (vary): Date, Type, Registration, MSN, Operator, Fatalities, Location, #
    table_match = re.search(
        r'<table[^>]*class="[^"]*hp[^"]*"[^>]*>(.*?)</table>',
        html, re.DOTALL | re.IGNORECASE,
    )
    if not table_match:
        # Fallback: look for any table with accident rows
        table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not table_match:
        return incidents

    table_html = table_match.group(1)

    # Extract header row to map column positions
    header_match = re.search(r'<thead[^>]*>(.*?)</thead>', table_html, re.DOTALL | re.IGNORECASE)
    col_names = []
    if header_match:
        th_cells = re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL | re.IGNORECASE)
        col_names = [clean_html(c).strip().lower() for c in th_cells]

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)

    for row_html in rows:
        # Skip header rows
        if "<th" in row_html.lower():
            continue

        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL | re.IGNORECASE)
        if len(cells) < 3:
            continue

        # Extract the wikibase link from any cell
        wikibase_match = re.search(
            r'href="(/asndb/[^"]*?(\d{6,})[^"]*?)"', row_html, re.IGNORECASE
        )
        if not wikibase_match:
            continue

        detail_path = wikibase_match.group(1)
        detail_url = ASN_BASE + detail_path

        # Try to pull wikibase_id from path
        wikibase_id_match = re.search(r'(\d{6,})', detail_path)
        wikibase_id = wikibase_id_match.group(1) if wikibase_id_match else detail_path

        # Map cells to columns if we have header info
        def cell_text(idx):
            if idx < len(cells):
                return clean_html(cells[idx]).strip()
            return ""

        def find_col(name):
            for i, h in enumerate(col_names):
                if name in h:
                    return cell_text(i)
            return ""

        date_raw = find_col("date") or cell_text(0)
        registration = find_col("registr") or find_col("serial") or cell_text(2)
        location = find_col("locat") or cell_text(5) if len(cells) > 5 else ""
        fatalities_raw = find_col("fatal") or find_col("fat") or ""

        incidents.append({
            "wikibase_id": wikibase_id,
            "detail_url": detail_url,
            "date_raw": date_raw,
            "registration": registration.upper().strip(),
            "location": location,
            "fatalities_raw": fatalities_raw,
        })

    return incidents


def parse_asn_detail_page(html: str, wikibase_id: str, detail_url: str) -> dict:
    """
    Parse an ASN detail/wikibase page and extract structured fields.

    Returns a dict with: date, location, serial, crew_count, fatality_count,
    wikibase_id, narrative, registration
    """
    data: dict = {
        "wikibase_id": wikibase_id,
        "detail_url": detail_url,
        "date": None,
        "location": None,
        "serial": None,
        "registration": None,
        "crew_count": None,
        "fatality_count": None,
        "narrative": None,
    }

    def _extract_field(label_pattern: str) -> str | None:
        m = re.search(
            label_pattern + r'[^<]*</[^>]+>\s*<[^>]+>([^<]+)<',
            html, re.IGNORECASE | re.DOTALL,
        )
        if m:
            return clean_html(m.group(1)).strip()
        return None

    # Date — look for labelled row
    date_match = re.search(
        r'(?:date|occurred)[^<]*</[^>]+>\s*<[^>]+>([^<]+)<',
        html, re.IGNORECASE,
    )
    if date_match:
        data["date"] = clean_html(date_match.group(1)).strip()

    # Also try meta / structured data
    date_meta = re.search(r'<meta[^>]*name="date"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if date_meta:
        data["date"] = date_meta.group(1).strip()

    # Location
    loc_match = re.search(
        r'(?:location|place)[^<]*</[^>]+>\s*<[^>]+>([^<]+)<',
        html, re.IGNORECASE,
    )
    if loc_match:
        data["location"] = clean_html(loc_match.group(1)).strip()

    # Registration / serial
    reg_match = re.search(
        r'(?:registr|serial)[^<]*</[^>]+>\s*<[^>]+>([A-Z0-9\-/ ]+)<',
        html, re.IGNORECASE,
    )
    if reg_match:
        val = reg_match.group(1).strip().upper()
        data["registration"] = val
        data["serial"] = val

    # Crew count
    crew_match = re.search(
        r'(?:crew|aboard|on board|occupants)[^<]*</[^>]+>\s*<[^>]+>(\d+)<',
        html, re.IGNORECASE,
    )
    if crew_match:
        data["crew_count"] = int(crew_match.group(1))

    # Fatalities
    fat_match = re.search(
        r'(?:fatalities|killed|fatal|dead)[^<]*</[^>]+>\s*<[^>]+>(\d+)<',
        html, re.IGNORECASE,
    )
    if fat_match:
        data["fatality_count"] = int(fat_match.group(1))

    # Narrative — find the largest <p> block outside navigation
    # Remove scripts, nav, headers
    clean = re.sub(r'<(script|style|nav|header|footer)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', clean, re.DOTALL | re.IGNORECASE)
    narrative_parts = []
    for p in paragraphs:
        text = clean_html(p).strip()
        if len(text) > 40:
            narrative_parts.append(text)
    if narrative_parts:
        data["narrative"] = " ".join(narrative_parts[:5])[:2000]

    # Normalise date to YYYY-MM-DD
    if data["date"]:
        data["date"] = _normalise_date(data["date"])

    return data


def _normalise_date(raw: str) -> str | None:
    """Convert various date formats to YYYY-MM-DD."""
    raw = raw.strip()

    # Already ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', raw):
        return raw

    # DD-MMM-YYYY or DD MMM YYYY
    m = re.match(
        r'(\d{1,2})[-\s/](\w+)[-\s/](\d{4})', raw, re.IGNORECASE
    )
    if m:
        months = {
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "may": "05", "jun": "06", "jul": "07", "aug": "08",
            "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        }
        day = m.group(1).zfill(2)
        mon = months.get(m.group(2).lower()[:3])
        year = m.group(3)
        if mon:
            return f"{year}-{mon}-{day}"

    # YYYY/MM/DD or MM/DD/YYYY
    m2 = re.match(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', raw)
    if m2:
        return f"{m2.group(1)}-{m2.group(2).zfill(2)}-{m2.group(3).zfill(2)}"

    # Keep raw if we can't parse it
    return raw if raw else None


# ─── Memorial matching ────────────────────────────────────────────────────────

def find_memorial_by_serial(serial: str) -> dict | None:
    """Look up a memorial by aircraft serial number."""
    if not serial:
        return None
    rows = db_query(
        f"SELECT id, slug, serial_number, crash_date, crew_count, asn_wikibase_id "
        f"FROM memorials "
        f"WHERE serial_number ILIKE {escape_sql(serial)} "
        f"AND status = 'production' LIMIT 1;"
    )
    if not rows:
        return None
    parts = rows.split("|")
    if len(parts) < 6:
        return None
    return {
        "id": parts[0],
        "slug": parts[1],
        "serial_number": parts[2],
        "crash_date": parts[3],
        "crew_count": parts[4],
        "asn_wikibase_id": parts[5],
    }


def find_memorial_by_date_location(date: str, location: str) -> dict | None:
    """Secondary match by crash date and approximate location."""
    if not date or not location:
        return None

    # Normalise location to first significant word for a fuzzy search
    loc_words = [w for w in location.split() if len(w) > 3]
    if not loc_words:
        return None
    loc_fragment = loc_words[0]

    rows = db_query(
        f"SELECT id, slug, serial_number, crash_date, crew_count, asn_wikibase_id "
        f"FROM memorials "
        f"WHERE crash_date = {escape_sql(date)} "
        f"AND (county ILIKE {escape_sql('%' + loc_fragment + '%')} "
        f"  OR country ILIKE {escape_sql('%' + loc_fragment + '%')} "
        f"  OR title ILIKE {escape_sql('%' + loc_fragment + '%')}) "
        f"AND status = 'production' LIMIT 1;"
    )
    if not rows:
        return None
    parts = rows.split("|")
    if len(parts) < 6:
        return None
    return {
        "id": parts[0],
        "slug": parts[1],
        "serial_number": parts[2],
        "crash_date": parts[3],
        "crew_count": parts[4],
        "asn_wikibase_id": parts[5],
    }


# ─── DB write operations ──────────────────────────────────────────────────────

def update_memorial_asn(memorial_id: str, wikibase_id: str, dry_run: bool) -> bool:
    """Set asn_wikibase_id on a memorial row."""
    sql = (
        f"UPDATE memorials SET asn_wikibase_id = {escape_sql(wikibase_id)} "
        f"WHERE id = {memorial_id} AND (asn_wikibase_id IS NULL OR asn_wikibase_id = '');"
    )
    return db_exec(sql, dry_run=dry_run)


def upsert_incident(asn_data: dict, dry_run: bool) -> bool:
    """
    Insert or update a row in the incident table for this ASN record.

    The incident table PK is 'id' (text), keyed by slug-style identifier.
    The unique constraint is on asn_wikibase_id.
    """
    wid = asn_data["wikibase_id"]
    incident_id = f"asn-{wid}"
    date_val = escape_sql(asn_data.get("date")) if asn_data.get("date") else "NULL"
    location_val = escape_sql(asn_data.get("location")) if asn_data.get("location") else "NULL"
    crew_val = str(asn_data["crew_count"]) if asn_data.get("crew_count") is not None else "NULL"
    url_val = escape_sql(asn_data.get("detail_url")) if asn_data.get("detail_url") else "NULL"
    now = escape_sql(datetime.now(timezone.utc).isoformat())

    sql = (
        f"INSERT INTO incident (id, date, location_name, asn_wikibase_id, asn_url, crew_count_asn) "
        f"VALUES ({escape_sql(incident_id)}, {date_val}, {location_val}, "
        f"{escape_sql(wid)}, {url_val}, {crew_val}) "
        f"ON CONFLICT (asn_wikibase_id) DO UPDATE SET "
        f"  date = EXCLUDED.date, "
        f"  location_name = EXCLUDED.location_name, "
        f"  asn_url = EXCLUDED.asn_url, "
        f"  crew_count_asn = EXCLUDED.crew_count_asn, "
        f"  updated_at = {now};"
    )
    return db_exec(sql, dry_run=dry_run)


def log_mismatch(memorial: dict, asn_data: dict, field_name: str, dry_run: bool) -> bool:
    """Write a verification row for a data mismatch."""
    our_val = str(memorial.get(field_name, ""))
    asn_val_map = {
        "crew_count": str(asn_data.get("crew_count", "")),
        "crash_date": str(asn_data.get("date", "")),
    }
    src_val = asn_val_map.get(field_name, "")

    sql = (
        f"INSERT INTO verification (entity_type, entity_id, field_name, our_value, source_value, source_name, match_status) "
        f"VALUES ('memorial', {escape_sql(str(memorial['id']))}, {escape_sql(field_name)}, "
        f"{escape_sql(our_val)}, {escape_sql(src_val)}, 'asn', 'mismatch') "
        f"ON CONFLICT DO NOTHING;"
    )
    return db_exec(sql, dry_run=dry_run)


# ─── Main processing logic ────────────────────────────────────────────────────

def process_type(type_code: str, dry_run: bool) -> dict:
    """
    Scrape one aircraft type from ASN and cross-reference against memorials.

    Returns a stats dict.
    """
    type_name, list_url = ASN_TYPES[type_code]
    stats = {
        "type": type_code,
        "type_name": type_name,
        "list_pages_fetched": 0,
        "asn_records_found": 0,
        "detail_pages_fetched": 0,
        "matched_by_serial": 0,
        "matched_by_date_location": 0,
        "unmatched": 0,
        "mismatches": 0,
        "errors": 0,
    }

    print(f"\n{'=' * 60}")
    print(f"Processing {type_name} ({type_code})")
    print(f"List URL: {list_url}")
    print(f"{'=' * 60}")

    # ── Step 1: Fetch the list page ──────────────────────────────────
    print(f"\nFetching list page...")
    html, err = fetch_url(list_url)
    if err or not html:
        print(f"  ERROR fetching list page: {err}", file=sys.stderr)
        stats["errors"] += 1
        return stats

    stats["list_pages_fetched"] += 1
    time.sleep(RATE_LIMIT_SECONDS)

    # ── Step 2: Parse incident rows from list ────────────────────────
    incidents = parse_asn_list_page(html)
    print(f"  Found {len(incidents)} incident rows on list page")
    stats["asn_records_found"] += len(incidents)

    if not incidents:
        print("  No incidents parsed — check ASN page structure")
        return stats

    # ── Step 3: Process each incident ───────────────────────────────
    for idx, inc in enumerate(incidents, start=1):
        wikibase_id = inc["wikibase_id"]
        detail_url = inc["detail_url"]

        print(f"\n  [{idx}/{len(incidents)}] Wikibase {wikibase_id} | {inc.get('date_raw', '')} | {inc.get('registration', '')}")

        # Check if we already have this detail page
        if already_scraped(detail_url):
            print(f"    Skipping — already scraped")
            # Still need to attempt matching if we have it in the log
            detail_html_row = db_query(
                f"SELECT raw_content FROM scrape_log WHERE url = {escape_sql(detail_url)} LIMIT 1;"
            )
            if detail_html_row:
                asn_data = parse_asn_detail_page(detail_html_row, wikibase_id, detail_url)
            else:
                continue
        else:
            # Fetch detail page
            print(f"    Fetching detail: {detail_url}")
            detail_html, detail_err = fetch_url(detail_url)
            time.sleep(RATE_LIMIT_SECONDS)

            if detail_err or not detail_html:
                print(f"    ERROR: {detail_err}", file=sys.stderr)
                log_scrape_error(detail_url, detail_err or "empty response", dry_run)
                stats["errors"] += 1
                continue

            stats["detail_pages_fetched"] += 1

            # Parse structured data
            asn_data = parse_asn_detail_page(detail_html, wikibase_id, detail_url)

            # Merge list-page fallback values where detail parse is empty
            if not asn_data.get("date") and inc.get("date_raw"):
                asn_data["date"] = _normalise_date(inc["date_raw"])
            if not asn_data.get("registration") and inc.get("registration"):
                asn_data["registration"] = inc["registration"]
                asn_data["serial"] = inc["registration"]
            if not asn_data.get("location") and inc.get("location"):
                asn_data["location"] = inc["location"]

            # Store in scrape_log
            log_scrape(detail_url, detail_html, asn_data, dry_run)

        # ── Step 4: Upsert incident record ───────────────────────────
        upsert_incident(asn_data, dry_run)

        # ── Step 5: Match against memorial ──────────────────────────
        serial = (asn_data.get("serial") or inc.get("registration") or "").strip().upper()
        match_date = asn_data.get("date")
        match_location = asn_data.get("location") or inc.get("location", "")

        memorial = None
        match_method = None

        if serial:
            memorial = find_memorial_by_serial(serial)
            if memorial:
                match_method = "serial"

        if not memorial:
            memorial = find_memorial_by_date_location(match_date, match_location)
            if memorial:
                match_method = "date_location"

        if not memorial:
            print(f"    No match (serial={serial!r}, date={match_date!r})")
            stats["unmatched"] += 1
            continue

        print(f"    Matched memorial {memorial['slug']} via {match_method}")

        if match_method == "serial":
            stats["matched_by_serial"] += 1
        else:
            stats["matched_by_date_location"] += 1

        # ── Step 6: Check for mismatches ────────────────────────────
        mismatch_found = False

        # Crew count mismatch
        asn_crew = asn_data.get("crew_count")
        our_crew = int(memorial["crew_count"]) if memorial["crew_count"] else None
        if asn_crew is not None and our_crew is not None and asn_crew != our_crew:
            print(f"    MISMATCH crew_count: ours={our_crew}, ASN={asn_crew}")
            log_mismatch(memorial, asn_data, "crew_count", dry_run)
            mismatch_found = True

        # Date mismatch (only when matched by serial, since date_location match already agrees on date)
        if match_method == "serial" and match_date and memorial["crash_date"]:
            our_date = memorial["crash_date"]
            if our_date != match_date:
                print(f"    MISMATCH crash_date: ours={our_date!r}, ASN={match_date!r}")
                log_mismatch(memorial, asn_data, "crash_date", dry_run)
                mismatch_found = True

        if mismatch_found:
            stats["mismatches"] += 1

        # ── Step 7: Update memorial with asn_wikibase_id ────────────
        if not memorial.get("asn_wikibase_id"):
            update_memorial_asn(memorial["id"], wikibase_id, dry_run)
            print(f"    Set asn_wikibase_id = {wikibase_id} on memorial {memorial['id']}")

    return stats


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cross-reference ASN database against BMR memorial records."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and match but do not write to the database.",
    )
    parser.add_argument(
        "--type",
        metavar="CODE",
        help=f"Process only this aircraft type. One of: {', '.join(ASN_TYPES)}",
    )
    args = parser.parse_args()

    if args.type:
        args.type = args.type.upper()
        if args.type not in ASN_TYPES:
            parser.error(f"Unknown type {args.type!r}. Valid: {', '.join(ASN_TYPES)}")
        types_to_run = [args.type]
    else:
        types_to_run = list(ASN_TYPES)

    if args.dry_run:
        print("[DRY-RUN MODE — no database writes will be made]")

    all_stats = []

    for type_code in types_to_run:
        stats = process_type(type_code, dry_run=args.dry_run)
        all_stats.append(stats)

    # ── Final summary ─────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Type':<8} {'Found':>6} {'Serial':>8} {'Date/Loc':>9} {'Unmatched':>10} {'Mismatches':>11} {'Errors':>7}")
    print(f"{'-' * 60}")

    total_found = total_serial = total_dateloc = total_unmatched = total_mismatch = total_err = 0

    for s in all_stats:
        print(
            f"{s['type']:<8} {s['asn_records_found']:>6} "
            f"{s['matched_by_serial']:>8} {s['matched_by_date_location']:>9} "
            f"{s['unmatched']:>10} {s['mismatches']:>11} {s['errors']:>7}"
        )
        total_found += s["asn_records_found"]
        total_serial += s["matched_by_serial"]
        total_dateloc += s["matched_by_date_location"]
        total_unmatched += s["unmatched"]
        total_mismatch += s["mismatches"]
        total_err += s["errors"]

    if len(all_stats) > 1:
        print(f"{'-' * 60}")
        print(
            f"{'TOTAL':<8} {total_found:>6} {total_serial:>8} {total_dateloc:>9} "
            f"{total_unmatched:>10} {total_mismatch:>11} {total_err:>7}"
        )

    print(f"\nTotal ASN records found:   {total_found}")
    print(f"Matched by serial:         {total_serial}")
    print(f"Matched by date+location:  {total_dateloc}")
    print(f"Unmatched:                 {total_unmatched}")
    print(f"Mismatches logged:         {total_mismatch}")
    print(f"Fetch errors:              {total_err}")


if __name__ == "__main__":
    main()
