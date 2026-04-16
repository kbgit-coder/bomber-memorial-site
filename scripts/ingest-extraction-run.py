#!/usr/bin/env python3
"""
Phase 0 — Ingest an extraction run JSON into the bmr_research DB.

INPUT:  /nas2/Projects/BomberMemorial/data-governance/extraction-runs/run_*.json
OUTPUT:
  - 1 row in enrichment_runs (the run)
  - N rows in sources (one per domain, UPSERT on domain)
  - N rows in scrape_log (one per URL)
  - N rows in claims (one per non-photo extraction, decomposed for structured types)
  - N rows in photo_claims (one per photo extraction; optional deep-test fetch)

Structured extraction decomposition:
  narrative   -> 1 claim (field_name='crash_narrative')
  crew.data.crew[]       -> 1 claim per crew member (field_name='crew_member')
  contact.data.contacts[] -> 1 claim per contact (field_name='contact')
  remembrance.data.events[] -> 1 claim per event (field_name='remembrance_event')
  remembrance.data.annual_service -> 1 claim (field_name='annual_service') if true
  community.data.story_text -> 1 claim (field_name='community_story')
  research.data.activities[] -> 1 claim per activity (field_name='research_activity')

Simple extractions (aircraft, social_media, photo):
  aircraft     -> claim (field_name='aircraft_serial', confidence from extraction)
  social_media -> claim (field_name='social_media_link', confidence from extraction)
  photo        -> photo_claims row (deep-test fetch if --fetch-photos)

Photo deep-test pipeline (when --fetch-photos):
  1. Resolve relative URL against parent_url
  2. Junk filter: skip SVG, common icon/logo/donate/justgiving path patterns
  3. Polite HTTP GET (1s rate limit per domain, 15s timeout)
  4. MIME sniff, SHA256 hash, PIL dimension extract
  5. Small image (< 200x200) -> is_icon=true
  6. After all fetched: second pass dedupe on content_hash, set is_duplicate + duplicate_of

USAGE:
  python3 scripts/ingest-extraction-run.py RUN_FILE [options]

OPTIONS:
  --dry-run            Print counts and exit, no DB writes
  --fetch-photos       Enable deep-test photo fetch loop (default: skip)
  --photo-limit N      Only fetch first N photos (sample mode)
  --skip-claims        Skip non-photo claims ingestion (photo-only run)
  --run-name NAME      Override enrichment_runs.name (default: derived from filename)
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import psycopg2
import psycopg2.extras
import requests
from PIL import Image


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_FILE = "/root/.claude/PAI/USER/CREDENTIALS/bmr-research-db.env"

# Tier classification for source domains.
# Everything not matched defaults to 'unverified'.
DEFINITIVE_DOMAINS = {
    "cwgc.org", "iwm.org.uk", "raf.mod.uk", "rafmuseum.org.uk",
    "royalairforce.mod.uk", "nationalarchives.gov.uk",
}
INSTITUTIONAL_SUFFIXES = (".gov", ".gov.uk", ".ac.uk", ".museum")
INSTITUTIONAL_DOMAINS = {
    "bbc.co.uk", "bbc.com", "wikipedia.org", "abmc.gov",
    "americanairmuseum.com", "imperialwarmuseums.org.uk",
}
RESEARCHED_PATTERNS = (
    "squadron", "bombercommand", "aviation", "aircrew", "raf",
    "memorial", "yorkshireaircraft", "peakdistrict", "warmemorial",
)

# Junk photo path patterns — reject before fetch
JUNK_PATH_RE = re.compile(
    r"(justgiving|donate|logo|icon|spinner|placeholder|footer|header|"
    r"social[-_]?(icon|button)|sprite|pixel|tracking|button|arrow|"
    r"favicon|apple-touch|gravatar|avatar[-_]?default)",
    re.IGNORECASE,
)
JUNK_EXT_RE = re.compile(r"\.(svg|ico|gif)($|\?)", re.IGNORECASE)
MIN_PHOTO_DIMENSION = 200  # px

HTTP_TIMEOUT = 15
DOMAIN_RATE_LIMIT_S = 1.0
USER_AGENT = "BomberMemorialBot/1.0 (+https://bombermemorial.co.uk/about; contact: admin@bombermemorial.co.uk)"


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def load_db_env():
    with open(VAULT_FILE) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

def connect():
    load_db_env()
    return psycopg2.connect(
        host=os.environ["BMR_DB_HOST"],
        port=int(os.environ["BMR_DB_PORT"]),
        dbname=os.environ["BMR_DB_NAME"],
        user=os.environ["BMR_DB_USER"],
        password=os.environ["BMR_DB_PASSWORD"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def classify_tier(domain: str) -> str:
    d = domain.lower()
    if d in DEFINITIVE_DOMAINS:
        return "definitive"
    if d in INSTITUTIONAL_DOMAINS or d.endswith(INSTITUTIONAL_SUFFIXES):
        return "institutional"
    if any(p in d for p in RESEARCHED_PATTERNS):
        return "researched"
    return "unverified"

def promote_confidence(domain: str, base: str) -> str:
    """Definitive-tier sources promote 'unverified' to 'probable'."""
    tier = classify_tier(domain)
    if base == "unverified" and tier in ("definitive", "institutional"):
        return "probable"
    return base

def resolve_photo_url(raw: str, parent_url: str) -> Optional[str]:
    """Convert possibly-relative URL to absolute. Return None if unresolvable."""
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("data:") or raw.startswith("javascript:"):
        return None
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if parent_url:
        return urljoin(parent_url, raw)
    return None

def is_junk_photo(url: str) -> bool:
    if not url:
        return True
    if JUNK_EXT_RE.search(url):
        return True
    if JUNK_PATH_RE.search(url):
        return True
    return False


# ---------------------------------------------------------------------------
# Source & scrape_log upsert
# ---------------------------------------------------------------------------

def upsert_source(cur, domain: str, existing: dict) -> int:
    if domain in existing:
        return existing[domain]
    tier = classify_tier(domain)
    cur.execute(
        """
        INSERT INTO sources (url, domain, name, tier, source_type, is_active, notes, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
        """,
        (
            f"https://{domain}",
            domain,
            domain,              # name = domain (refineable later)
            tier,
            "website",           # default source_type
            True,
            "Auto-created by ingest-extraction-run.py",
        ),
    )
    source_id = cur.fetchone()[0]
    existing[domain] = source_id
    return source_id

def create_scrape_log(cur, source_id: int, memorial_id: Optional[int], url: str,
                     status: str, run_id: int, extracted_data: dict,
                     error_message: Optional[str] = None) -> int:
    cur.execute(
        """
        INSERT INTO scrape_log (
            source_id, memorial_id, url, status, scraped_at,
            extracted_data, run_id, error_message, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, NOW(), NOW())
        RETURNING id
        """,
        (source_id, memorial_id, url, status,
         psycopg2.extras.Json(extracted_data), run_id, error_message),
    )
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Claim builders
# ---------------------------------------------------------------------------

def insert_claim(cur, memorial_id: int, source_id: int, scrape_log_id: int,
                 field_name: str, field_value: str, field_context: dict,
                 confidence: str, source_url: str, source_excerpt: Optional[str] = None):
    cur.execute(
        """
        INSERT INTO claims (
            memorial_id, source_id, scrape_log_id,
            field_name, field_value, field_context,
            confidence, status, source_url, source_excerpt,
            extraction_date, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, NOW(), NOW(), NOW())
        """,
        (memorial_id, source_id, scrape_log_id,
         field_name, field_value[:4000] if field_value else None,
         psycopg2.extras.Json(field_context or {}),
         confidence, source_url,
         source_excerpt[:2000] if source_excerpt else None),
    )

def decompose_extraction(ext: dict, parent_url: str, domain: str) -> list:
    """
    Return a list of (field_name, field_value, field_context, confidence) tuples
    for non-photo extractions. Photos are handled separately.
    Returns [] if the extraction should be skipped.
    """
    t = ext.get("type")
    out = []

    # Simple extractions
    if t == "aircraft":
        v = ext.get("value")
        if v:
            out.append(("aircraft_serial", str(v), ext.get("context") or {},
                        ext.get("confidence", "unverified")))
        return out

    if t == "social_media":
        v = ext.get("value")
        if v:
            out.append(("social_media_link", str(v), ext.get("context") or {},
                        ext.get("confidence", "unverified")))
        return out

    # Structured extractions (Granite)
    data = ext.get("data") or {}
    if not isinstance(data, dict):
        return out

    if t == "narrative":
        narr = data.get("narrative")
        if narr:
            ctx = {k: v for k, v in data.items() if k != "narrative"}
            out.append(("crash_narrative", str(narr), ctx,
                        promote_confidence(domain, "unverified")))
        return out

    if t == "crew":
        crew_list = data.get("crew") or []
        for c in crew_list:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            if not name:
                continue
            out.append(("crew_member", str(name), c,
                        promote_confidence(domain, "unverified")))
        return out

    if t == "contact":
        contacts = data.get("contacts") or []
        for c in contacts:
            if not isinstance(c, dict):
                continue
            label = c.get("org_name") or c.get("name") or c.get("email") or c.get("phone")
            if not label:
                continue
            out.append(("contact", str(label), c, "unverified"))
        return out

    if t == "remembrance":
        events = data.get("events") or []
        for e in events:
            if not isinstance(e, dict):
                continue
            name = e.get("name") or e.get("event") or e.get("description", "")[:60]
            if not name:
                continue
            out.append(("remembrance_event", str(name), e,
                        promote_confidence(domain, "unverified")))
        if data.get("annual_service"):
            out.append(("annual_service", "true",
                        {"date": data.get("service_date")},
                        promote_confidence(domain, "unverified")))
        return out

    if t == "community":
        story = data.get("story_text") or data.get("story")
        if story:
            ctx = {k: v for k, v in data.items() if k not in ("story_text", "story")}
            out.append(("community_story", str(story), ctx, "unverified"))
        return out

    if t == "research":
        activities = data.get("activities") or []
        for a in activities:
            if not isinstance(a, dict):
                continue
            label = a.get("researcher_name") or a.get("research_focus")
            if not label:
                continue
            out.append(("research_activity", str(label), a, "unverified"))
        return out

    return out


# ---------------------------------------------------------------------------
# Photo deep-test fetch
# ---------------------------------------------------------------------------

def fetch_and_hash(url: str, session: requests.Session) -> dict:
    """
    Fetch a photo URL and return a dict of fetch results.
    Keys: fetch_status, fetch_http_code, content_hash, mime_type, file_size,
          width, height, is_icon, fetch_error
    """
    result = {
        "fetch_status": None,
        "fetch_http_code": None,
        "content_hash": None,
        "mime_type": None,
        "file_size": None,
        "width": None,
        "height": None,
        "is_icon": False,
        "fetch_error": None,
    }

    if is_junk_photo(url):
        result["fetch_status"] = "skipped_junk"
        result["is_icon"] = True
        return result

    try:
        resp = session.get(url, timeout=HTTP_TIMEOUT, stream=True, allow_redirects=True)
        result["fetch_http_code"] = resp.status_code
        if resp.status_code >= 500:
            result["fetch_status"] = "http_5xx"
            return result
        if resp.status_code >= 400:
            result["fetch_status"] = "http_4xx"
            return result
        if resp.status_code >= 300:
            result["fetch_status"] = "http_3xx_unfollowed"
            return result

        ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        result["mime_type"] = ctype

        if not ctype.startswith("image/"):
            result["fetch_status"] = "skipped_not_image"
            return result

        content = resp.content
        result["file_size"] = len(content)
        result["content_hash"] = hashlib.sha256(content).hexdigest()

        # Dimensions via PIL
        try:
            img = Image.open(io.BytesIO(content))
            result["width"], result["height"] = img.size
        except Exception as e:
            result["fetch_error"] = f"PIL: {e}"
            result["fetch_status"] = "parse_error"
            return result

        # Icon heuristic
        if result["width"] < MIN_PHOTO_DIMENSION or result["height"] < MIN_PHOTO_DIMENSION:
            result["is_icon"] = True

        result["fetch_status"] = "ok"
        return result

    except requests.Timeout:
        result["fetch_status"] = "timeout"
        result["fetch_error"] = "HTTP timeout"
        return result
    except requests.RequestException as e:
        result["fetch_status"] = "parse_error"
        result["fetch_error"] = str(e)[:500]
        return result

def deep_test_photos(conn, extraction_run_id: int, limit: Optional[int]) -> dict:
    """
    Phase 2: walk photo_claims for this run where fetch_status IS NULL and fetch them.
    Polite per-domain rate limiting.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, original_url, memorial_id
        FROM photo_claims
        WHERE extraction_run_id = %s AND fetch_status IS NULL
        ORDER BY id
        """ + (f" LIMIT {int(limit)}" if limit else ""),
        (extraction_run_id,),
    )
    queued = cur.fetchall()
    cur.close()

    if not queued:
        return {"fetched": 0}

    print(f"[photos] Deep-test fetching {len(queued)} photos...")
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    last_fetch_per_domain = {}
    stats = {"fetched": 0, "ok": 0, "icons": 0, "junk": 0, "failed": 0}

    for i, (pc_id, url, mem_id) in enumerate(queued):
        domain = urlparse(url).netloc.lower()
        # Polite rate limit
        last = last_fetch_per_domain.get(domain, 0)
        wait = DOMAIN_RATE_LIMIT_S - (time.time() - last)
        if wait > 0:
            time.sleep(wait)

        result = fetch_and_hash(url, session)
        last_fetch_per_domain[domain] = time.time()

        upd = conn.cursor()
        upd.execute(
            """
            UPDATE photo_claims SET
                fetch_status = %s,
                fetch_http_code = %s,
                content_hash = %s,
                mime_type = %s,
                file_size = %s,
                width = %s,
                height = %s,
                is_icon = %s,
                fetch_error = %s,
                fetched_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            """,
            (result["fetch_status"], result["fetch_http_code"],
             result["content_hash"], result["mime_type"],
             result["file_size"], result["width"], result["height"],
             result["is_icon"], result["fetch_error"], pc_id),
        )
        upd.close()
        conn.commit()

        stats["fetched"] += 1
        if result["fetch_status"] == "ok":
            stats["ok"] += 1
            if result["is_icon"]:
                stats["icons"] += 1
        elif result["fetch_status"] in ("skipped_junk", "skipped_not_image"):
            stats["junk"] += 1
        else:
            stats["failed"] += 1

        if (i + 1) % 50 == 0:
            print(f"[photos] Progress: {i+1}/{len(queued)} "
                  f"(ok={stats['ok']} junk={stats['junk']} failed={stats['failed']})")

    # Dedupe pass: set is_duplicate + duplicate_of based on content_hash
    print("[photos] Running dedupe pass...")
    cur = conn.cursor()
    cur.execute(
        """
        WITH firsts AS (
            SELECT content_hash, MIN(id) AS first_id
            FROM photo_claims
            WHERE content_hash IS NOT NULL
            GROUP BY content_hash
            HAVING COUNT(*) > 1
        )
        UPDATE photo_claims pc
        SET is_duplicate = TRUE,
            duplicate_of = f.first_id,
            updated_at = NOW()
        FROM firsts f
        WHERE pc.content_hash = f.content_hash AND pc.id <> f.first_id
        """
    )
    stats["deduped"] = cur.rowcount
    conn.commit()
    cur.close()
    return stats


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest(run_file: str, args):
    print(f"[ingest] Loading {run_file}")
    with open(run_file) as f:
        data = json.load(f)

    summary = data.get("summary", {})
    results = data.get("results", [])
    print(f"[ingest] Run '{summary.get('run_id')}': {len(results)} URL results")

    conn = connect()
    cur = conn.cursor()

    # 1. Load memorial slug -> id map
    cur.execute("SELECT slug, id FROM memorials")
    slug_to_id = {row[0]: row[1] for row in cur.fetchall()}
    print(f"[ingest] Loaded {len(slug_to_id)} memorial slugs")

    # 2. Load existing source domain -> id map
    cur.execute("SELECT domain, id FROM sources")
    source_map = {row[0]: row[1] for row in cur.fetchall()}
    print(f"[ingest] Loaded {len(source_map)} existing sources")

    # 3. Create enrichment_runs row
    run_name = args.run_name or f"ingest_{summary.get('run_id', os.path.basename(run_file))}"
    cur.execute(
        """
        INSERT INTO enrichment_runs (
            name, source_domain, started_at, completed_at,
            urls_queued, urls_scraped, urls_failed, claims_created, notes
        )
        VALUES (%s, %s, NOW(), NOW(), %s, %s, %s, 0, %s)
        RETURNING id
        """,
        (
            run_name,
            "multi-domain",
            summary.get("urls_processed", len(results)),
            summary.get("urls_ok", 0),
            summary.get("urls_failed", 0),
            f"Phase 0 ingestion of {os.path.basename(run_file)}",
        ),
    )
    run_id = cur.fetchone()[0]
    print(f"[ingest] Created enrichment_runs row id={run_id} name='{run_name}'")
    conn.commit()

    # 4. Walk results, create scrape_log + claims + photo_claims
    stats = {
        "sources_created": 0,
        "scrape_log_rows": 0,
        "claims_inserted": 0,
        "photo_claims_inserted": 0,
        "photo_claims_skipped_junk": 0,
        "orphan_memorials": 0,
        "orphan_slugs": set(),
        "claims_by_field": {},
    }
    pre_source_count = len(source_map)

    if args.dry_run:
        conn.rollback()
        print("[ingest] --dry-run: would process results, exiting")
        return {"dry_run": True, "results": len(results)}

    for r in results:
        domain = r.get("domain")
        url = r.get("url")
        slug = r.get("memorial_slug")
        status = r.get("status", "extracted")

        if not domain or not url:
            continue

        memorial_id = slug_to_id.get(slug) if slug else None
        if slug and memorial_id is None:
            stats["orphan_memorials"] += 1
            stats["orphan_slugs"].add(slug)
            # We still create scrape_log (memorial_id NULL) but skip claims
            # since claims require a memorial_id

        source_id = upsert_source(cur, domain, source_map)
        # map scrape_status: results status values are 'ok','failed','not_found'
        # scrape_log enum allows 'extracted','failed' etc.
        sl_status = "extracted" if status == "ok" else (
            "failed" if status == "failed" else "failed"
        )
        err = None
        if status != "ok":
            err = str(r.get("errors") or r.get("error") or status)[:500]

        # Store extraction summary only in scrape_log (not full raw_content -> huge)
        extractions = r.get("extractions") or []
        extracted_summary = {
            "extraction_count": len(extractions),
            "content_hash": r.get("content_hash"),
            "clean_text_length": r.get("clean_text_length"),
            "title": r.get("title"),
            "types": list({e.get("type") for e in extractions if isinstance(e, dict)}),
        }

        sl_id = create_scrape_log(cur, source_id, memorial_id, url,
                                  sl_status, run_id, extracted_summary, err)
        stats["scrape_log_rows"] += 1

        if status != "ok" or not extractions:
            continue

        # Process extractions
        for ext in extractions:
            if not isinstance(ext, dict):
                continue

            if ext.get("type") == "photo":
                raw_url = ext.get("value")
                abs_url = resolve_photo_url(raw_url, url)
                if not abs_url:
                    stats["photo_claims_skipped_junk"] += 1
                    continue

                ctx = ext.get("context") or {}
                caption = ctx.get("caption")
                licence_clear = bool(ctx.get("licence_clear", False))

                # Quick junk filter BEFORE inserting — don't fill the table with garbage
                if is_junk_photo(abs_url):
                    stats["photo_claims_skipped_junk"] += 1
                    # But still insert with skipped_junk status so we have the audit trail
                    try:
                        cur.execute(
                            """
                            INSERT INTO photo_claims (
                                memorial_id, source_id, scrape_log_id,
                                original_url, raw_url, parent_url,
                                caption, credit, licence_clear,
                                fetch_status, is_icon, extraction_run_id,
                                confidence, status, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    'skipped_junk', TRUE, %s, 'unverified', 'pending',
                                    NOW(), NOW())
                            ON CONFLICT (memorial_id, original_url) DO NOTHING
                            """,
                            (memorial_id, source_id, sl_id,
                             abs_url, raw_url, url,
                             caption, domain, licence_clear, run_id),
                        )
                    except Exception as e:
                        print(f"[ingest] photo_claim junk insert error: {e}", file=sys.stderr)
                        conn.rollback()
                    continue

                try:
                    cur.execute(
                        """
                        INSERT INTO photo_claims (
                            memorial_id, source_id, scrape_log_id,
                            original_url, raw_url, parent_url,
                            caption, credit, licence_clear,
                            extraction_run_id, confidence, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                'unverified', 'pending', NOW(), NOW())
                        ON CONFLICT (memorial_id, original_url) DO NOTHING
                        """,
                        (memorial_id, source_id, sl_id,
                         abs_url, raw_url, url,
                         caption, domain, licence_clear, run_id),
                    )
                    if cur.rowcount > 0:
                        stats["photo_claims_inserted"] += 1
                except Exception as e:
                    print(f"[ingest] photo_claim insert error: {e}", file=sys.stderr)
                    conn.rollback()
                continue

            # Non-photo: skip if no memorial match (claims require memorial_id)
            if memorial_id is None:
                continue
            if args.skip_claims:
                continue

            try:
                decomposed = decompose_extraction(ext, url, domain)
            except Exception as e:
                print(f"[ingest] decompose error: {e}", file=sys.stderr)
                continue

            for field_name, field_value, field_context, conf in decomposed:
                try:
                    insert_claim(cur, memorial_id, source_id, sl_id,
                                 field_name, field_value, field_context,
                                 conf, url)
                    stats["claims_inserted"] += 1
                    stats["claims_by_field"][field_name] = \
                        stats["claims_by_field"].get(field_name, 0) + 1
                except Exception as e:
                    print(f"[ingest] claim insert error on {field_name}: {e}", file=sys.stderr)
                    conn.rollback()

        # Commit per-result so we can resume on crash
        conn.commit()

    stats["sources_created"] = len(source_map) - pre_source_count

    # Update run summary
    cur.execute(
        """
        UPDATE enrichment_runs
        SET claims_created = %s, completed_at = NOW()
        WHERE id = %s
        """,
        (stats["claims_inserted"], run_id),
    )
    conn.commit()

    # Photo deep test (Phase 2)
    photo_stats = {}
    if args.fetch_photos:
        photo_stats = deep_test_photos(conn, run_id, args.photo_limit)

    # Final report
    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print("INGEST REPORT")
    print("=" * 60)
    print(f"  Enrichment run ID: {run_id}")
    print(f"  Sources created:   {stats['sources_created']}")
    print(f"  Scrape_log rows:   {stats['scrape_log_rows']}")
    print(f"  Claims inserted:   {stats['claims_inserted']}")
    for field, n in sorted(stats["claims_by_field"].items(), key=lambda x: -x[1]):
        print(f"    {field:25} {n}")
    print(f"  Photo claims:      {stats['photo_claims_inserted']}")
    print(f"  Photo junk skipped in-line: {stats['photo_claims_skipped_junk']}")
    print(f"  Orphan memorials:  {stats['orphan_memorials']} "
          f"({len(stats['orphan_slugs'])} unique slugs)")
    if photo_stats:
        print()
        print("PHOTO DEEP-TEST")
        print(f"  Fetched:   {photo_stats['fetched']}")
        print(f"  OK:        {photo_stats['ok']}")
        print(f"  Icons:     {photo_stats['icons']}")
        print(f"  Junk:      {photo_stats['junk']}")
        print(f"  Failed:    {photo_stats['failed']}")
        print(f"  Deduped:   {photo_stats.get('deduped', 0)}")
    return {"run_id": run_id, "stats": stats, "photo_stats": photo_stats}


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_file", help="Path to run_*.json")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--fetch-photos", action="store_true")
    p.add_argument("--photo-limit", type=int, default=None)
    p.add_argument("--skip-claims", action="store_true")
    p.add_argument("--run-name", default=None)
    args = p.parse_args()

    if not os.path.exists(args.run_file):
        print(f"Run file not found: {args.run_file}", file=sys.stderr)
        sys.exit(1)

    ingest(args.run_file, args)


if __name__ == "__main__":
    main()
