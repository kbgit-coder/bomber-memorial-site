#!/usr/bin/env python3
"""
BMR Link Graph Builder

Reads stored HTML from the scrape_log table and extracts every outbound link,
scores it using link_scorer.py v3.0, and writes the results to link_references.

Designed to run against already-scraped pages — does NOT perform any new HTTP requests.
Safe to run in parallel with the overnight extraction batch.

Usage:
    python3 scripts/build-link-graph.py              # Process all stored pages
    python3 scripts/build-link-graph.py --limit 50   # Process first 50
    python3 scripts/build-link-graph.py --domain iwm.org.uk  # Specific domain
    python3 scripts/build-link-graph.py --dry-run    # Show what would be processed
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# Module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from link_scorer import score_link, LinkScore

# ─── Config ──────────────────────────────────────────────────────────

DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"

MEMORIALS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "public", "data", "memorials",
)

RESULTS_DIR = "/nas2/Projects/BomberMemorial/data-governance/link-graph"

# Context window around each link (chars)
CONTEXT_WINDOW = 200


# ─── DB access ───────────────────────────────────────────────────────

def db_query_to_file(sql: str, tmp_file: str) -> bool:
    """Run a psql query, writing output to a file inside the container, then copy out."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c",
         f"\\copy ({sql}) TO '{tmp_file}'"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return False
    subprocess.run(["docker", "cp", f"{DB_CONTAINER}:{tmp_file}", tmp_file],
                   capture_output=True, timeout=30)
    return os.path.exists(tmp_file)


def db_query(sql: str) -> str:
    """Run a psql query and return stdout."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip()


def db_exec_file(sql_file: str) -> bool:
    """Execute SQL from a file."""
    subprocess.run(["docker", "cp", sql_file, f"{DB_CONTAINER}:/tmp/exec.sql"],
                   capture_output=True, timeout=30)
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-f", "/tmp/exec.sql"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"DB error: {result.stderr[:500]}")
        return False
    return True


def get_stored_pages(domain: str = None, limit: int = None) -> list[dict]:
    """Get list of scraped pages with non-empty raw_content."""
    where = "status IN ('scraped','extracted') AND raw_content IS NOT NULL AND length(raw_content) > 500"
    if domain:
        where += f" AND url LIKE '%{domain}%'"

    sql = f"SELECT id, url, length(raw_content) FROM scrape_log WHERE {where} ORDER BY length(raw_content) DESC"
    if limit:
        sql += f" LIMIT {limit}"

    raw = db_query(sql)
    pages = []
    for line in raw.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            pages.append({
                "id": int(parts[0]),
                "url": parts[1],
                "content_length": int(parts[2]),
            })
    return pages


def get_stored_html(scrape_log_id: int) -> str | None:
    """Get raw HTML from scrape_log by id."""
    tmp_file = f"/tmp/bmr_link_html_{scrape_log_id}.txt"
    ok = db_query_to_file(
        f"SELECT raw_content FROM scrape_log WHERE id = {scrape_log_id} AND raw_content IS NOT NULL LIMIT 1",
        tmp_file,
    )
    if not ok or not os.path.exists(tmp_file):
        return None
    with open(tmp_file) as f:
        content = f.read().strip()
    os.unlink(tmp_file)
    # psql COPY escapes
    content = content.replace("\\n", "\n").replace("\\\\", "\\")
    return content if len(content) > 100 else None


def load_memorial_locations() -> set:
    """Load all memorial location/village names for fuzzy matching."""
    locations = set()
    for filepath in glob.glob(os.path.join(MEMORIALS_DIR, "*.json")):
        slug = os.path.basename(filepath).replace(".json", "")
        # Slug itself is a good location candidate (lowercase, hyphenated)
        # Split into words and take capitalized ones
        locations.add(slug)
        try:
            with open(filepath) as f:
                data = json.load(f)
            if data.get("location_name"):
                locations.add(data["location_name"].lower())
            if data.get("county"):
                locations.add(data["county"].lower())
        except Exception:
            pass
    return locations


# ─── Link extraction from HTML ───────────────────────────────────────

def classify_link_position(link_tag) -> str:
    """
    Determine where the link sits in the page: content/sidebar/footer/nav/unknown.
    Walks up the DOM tree looking for semantic/structural parents.
    """
    current = link_tag
    for _ in range(15):  # Max 15 levels up
        current = current.parent
        if current is None or current.name is None:
            break
        name = current.name.lower()
        cls = " ".join(current.get("class", [])) if current.get("class") else ""
        id_attr = current.get("id", "") or ""
        cls_id = f"{cls} {id_attr}".lower()

        if name in ("nav", "header"):
            return "nav"
        if name == "footer":
            return "footer"
        if name == "aside":
            return "sidebar"
        if name in ("main", "article", "section"):
            return "content"

        # Class/id-based hints
        if any(k in cls_id for k in ["nav", "menu", "navbar", "breadcrumb"]):
            return "nav"
        if any(k in cls_id for k in ["footer", "site-footer"]):
            return "footer"
        if any(k in cls_id for k in ["sidebar", "widget-area", "secondary"]):
            return "sidebar"
        if any(k in cls_id for k in ["content", "article", "main-content", "entry-content", "post-content"]):
            return "content"

    return "unknown"


def extract_links_from_html(html: str, source_url: str) -> list[dict]:
    """
    Extract all <a> tags with anchor text, position classification, and surrounding context.
    Returns list of dicts ready for scoring.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    # Remove script/style nodes
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    links = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue

        # Resolve relative URLs
        try:
            absolute = urljoin(source_url, href)
        except Exception:
            absolute = href

        # Skip self-referential links
        if absolute == source_url or absolute.rstrip("/") == source_url.rstrip("/"):
            continue

        # Parse domain
        try:
            parsed = urlparse(absolute)
            domain = parsed.netloc.replace("www.", "")
        except Exception:
            continue

        if not domain:
            continue

        # Skip the source domain (we only want OUTBOUND links for network analysis)
        source_domain = urlparse(source_url).netloc.replace("www.", "") if source_url else ""
        if domain == source_domain:
            continue

        # Deduplicate per source page
        dedup_key = absolute
        if dedup_key in seen_urls:
            continue
        seen_urls.add(dedup_key)

        # Extract anchor text
        anchor = a.get_text(separator=" ", strip=True)
        if not anchor:
            # Try alt text from img child
            img = a.find("img")
            if img and img.get("alt"):
                anchor = img["alt"].strip()
        anchor = anchor[:500]  # Cap length

        # Classify position
        position = classify_link_position(a)

        # Extract surrounding context
        parent = a.parent
        if parent:
            context = parent.get_text(separator=" ", strip=True)[:CONTEXT_WINDOW * 2]
        else:
            context = anchor
        context = context[:CONTEXT_WINDOW * 2]

        links.append({
            "target_url": absolute,
            "target_domain": domain,
            "anchor_text": anchor,
            "link_context": context,
            "link_position": position,
        })

    return links


# ─── Memorial slug → id mapping ──────────────────────────────────────

def load_url_to_memorial_map() -> dict[str, int]:
    """
    Build a mapping from external_narrative URL → memorial slug.
    Used to set source_memorial_id when we can match a scrape_log URL to a memorial.
    """
    mapping = {}
    for filepath in sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json"))):
        slug = os.path.basename(filepath).replace(".json", "")
        try:
            with open(filepath) as f:
                data = json.load(f)
            for narrative in data.get("external_narratives", []):
                url = narrative.get("original_url", "")
                if url:
                    mapping[url] = slug
        except Exception:
            pass
    return mapping


# ─── Writing to DB ───────────────────────────────────────────────────

def escape_sql(s: str) -> str:
    """Escape single quotes for SQL string literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"


def write_links_batch(rows: list[dict]) -> int:
    """Write a batch of scored links to link_references table."""
    if not rows:
        return 0

    sql_lines = ["INSERT INTO link_references (source_scrape_log_id, source_url, source_memorial_id, target_url, target_domain, anchor_text, link_context, link_position, pre_fetch_score, score_components, tier, scrape_status, unscrapable_reason, outreach_candidate) VALUES"]
    values = []
    for row in rows:
        vals = [
            str(row["source_scrape_log_id"]) if row["source_scrape_log_id"] else "NULL",
            escape_sql(row["source_url"][:2000]),
            "NULL",  # source_memorial_id — set separately
            escape_sql(row["target_url"][:2000]),
            escape_sql(row["target_domain"][:500]),
            escape_sql(row["anchor_text"][:500]) if row["anchor_text"] else "NULL",
            escape_sql(row["link_context"][:2000]) if row["link_context"] else "NULL",
            escape_sql(row["link_position"]),
            str(row["pre_fetch_score"]),
            escape_sql(json.dumps(row["score_components"])),
            escape_sql(row["tier"]),
            escape_sql(row["scrape_status"]),
            escape_sql(row["unscrapable_reason"]) if row["unscrapable_reason"] else "NULL",
            "TRUE" if row["outreach_candidate"] else "FALSE",
        ]
        values.append("(" + ", ".join(vals) + ")")

    sql = sql_lines[0] + " " + ",\n".join(values) + " ON CONFLICT (source_scrape_log_id, target_url) DO NOTHING;"

    # Write SQL to temp file and execute
    tmp_sql = f"/tmp/bmr_link_insert_{os.getpid()}.sql"
    with open(tmp_sql, "w") as f:
        f.write(sql)

    ok = db_exec_file(tmp_sql)
    os.unlink(tmp_sql)

    return len(rows) if ok else 0


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BMR Link Graph Builder")
    parser.add_argument("--domain", help="Process only stored pages from this domain")
    parser.add_argument("--limit", type=int, help="Limit number of pages to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()

    print("=" * 70)
    print("BMR Link Graph Builder — v3.0")
    print("=" * 70)

    # Load known memorial locations for fuzzy matching
    print("\nLoading memorial locations...")
    known_locations = load_memorial_locations()
    print(f"  {len(known_locations)} locations loaded")

    # Load URL → memorial slug mapping
    print("Loading URL → memorial mapping...")
    url_to_memorial = load_url_to_memorial_map()
    print(f"  {len(url_to_memorial)} URLs mapped to memorials")

    # Get stored pages
    print(f"\nQuerying stored pages{' for ' + args.domain if args.domain else ''}...")
    pages = get_stored_pages(domain=args.domain, limit=args.limit)
    print(f"  {len(pages)} pages found")

    if args.dry_run:
        # Show domain distribution
        domains = Counter()
        for p in pages:
            try:
                d = urlparse(p["url"]).netloc.replace("www.", "")
                domains[d] += 1
            except Exception:
                pass
        print("\nDomain distribution:")
        for d, c in domains.most_common(20):
            print(f"  {d}: {c}")
        print(f"  ... ({len(domains)} unique domains total)")
        return

    # Create output directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary_file = os.path.join(RESULTS_DIR, f"link_graph_run_{run_id}.json")

    # Process pages
    print(f"\nProcessing {len(pages)} pages...")
    stats = {
        "pages_processed": 0,
        "pages_failed": 0,
        "links_discovered": 0,
        "links_written": 0,
        "tier_counts": Counter(),
        "scrape_status_counts": Counter(),
        "top_domains": Counter(),
        "outreach_candidates": 0,
    }

    BATCH_SIZE = 100
    batch = []

    for i, page in enumerate(pages, 1):
        if i % 10 == 0 or i == 1:
            print(f"  [{i}/{len(pages)}] {page['url'][:80]} ({page['content_length']:,} chars)")

        # Get HTML
        html = get_stored_html(page["id"])
        if not html:
            stats["pages_failed"] += 1
            continue

        # Extract links
        links = extract_links_from_html(html, page["url"])
        stats["links_discovered"] += len(links)

        # Memorial ID for this source page
        memorial_slug = url_to_memorial.get(page["url"])

        # Score each link
        for link in links:
            score = score_link(
                anchor_text=link["anchor_text"],
                target_url=link["target_url"],
                source_url=page["url"],
                link_position=link["link_position"],
                surrounding_context=link["link_context"],
                known_memorial_locations=known_locations,
            )

            # Only persist non-noise for efficiency
            if score.tier == "NOISE":
                stats["tier_counts"]["NOISE"] += 1
                continue

            row = {
                "source_scrape_log_id": page["id"],
                "source_url": page["url"],
                "source_memorial_slug": memorial_slug,
                "target_url": link["target_url"],
                "target_domain": link["target_domain"],
                "anchor_text": link["anchor_text"],
                "link_context": link["link_context"],
                "link_position": link["link_position"],
                "pre_fetch_score": round(score.normalised, 4),
                "score_components": {
                    "raw_total": round(score.total, 2),
                    "normalised": round(score.normalised, 4),
                    "dimensions": {
                        "A": round(score.dimension_a, 2),
                        "B": round(score.dimension_b, 2),
                        "C": round(score.dimension_c, 2),
                        "D": round(score.dimension_d, 2),
                        "E": round(score.dimension_e, 2),
                    },
                    "details": score.components,
                },
                "tier": score.tier,
                "scrape_status": score.scrape_status,
                "unscrapable_reason": score.unscrapable_reason,
                "outreach_candidate": score.outreach_candidate,
            }
            batch.append(row)

            stats["tier_counts"][score.tier] += 1
            stats["scrape_status_counts"][score.scrape_status] += 1
            stats["top_domains"][link["target_domain"]] += 1
            if score.outreach_candidate:
                stats["outreach_candidates"] += 1

            # Flush batch
            if len(batch) >= BATCH_SIZE:
                written = write_links_batch(batch)
                stats["links_written"] += written
                batch = []

        stats["pages_processed"] += 1

    # Flush remaining batch
    if batch:
        written = write_links_batch(batch)
        stats["links_written"] += written

    # Write summary
    summary = {
        "run_id": run_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "pages_processed": stats["pages_processed"],
        "pages_failed": stats["pages_failed"],
        "links_discovered": stats["links_discovered"],
        "links_written": stats["links_written"],
        "links_noise_filtered": stats["tier_counts"].get("NOISE", 0),
        "tier_distribution": dict(stats["tier_counts"]),
        "scrape_status_distribution": dict(stats["scrape_status_counts"]),
        "outreach_candidates": stats["outreach_candidates"],
        "top_20_target_domains": dict(stats["top_domains"].most_common(20)),
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    os.chmod(summary_file, 0o666)

    print(f"\n{'=' * 70}")
    print("GRAPH BUILD COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Pages processed: {stats['pages_processed']}/{len(pages)}")
    print(f"  Links discovered: {stats['links_discovered']:,}")
    print(f"  Links written (non-noise): {stats['links_written']:,}")
    print(f"  Noise filtered: {stats['tier_counts'].get('NOISE', 0):,}")
    print(f"\n  Tier distribution:")
    for tier in ["PRIMARY", "SECONDARY", "TERTIARY", "BACKGROUND"]:
        print(f"    {tier}: {stats['tier_counts'].get(tier, 0):,}")
    print(f"\n  Outreach candidates: {stats['outreach_candidates']}")
    print(f"  Bot blocked: {stats['scrape_status_counts'].get('bot_blocked', 0):,}")
    print(f"\n  Summary written: {summary_file}")


if __name__ == "__main__":
    main()
