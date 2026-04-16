#!/usr/bin/env python3
"""
Seed the scrape-provenance.json from:
1. Research DB sources table (226 domains with tier + metadata)
2. Memorial JSON external_narratives (711 entries across 224 domains)
3. Known scrape history from enrichment_runs table

Creates the initial provenance log with full domain inventory.
Run once, then individual scripts maintain it going forward.
"""

import glob
import json
import os
import subprocess
import sys

# Add scripts dir to path for module import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_provenance import ProvenanceLog, BOT_BLOCKED_DOMAINS

MEMORIALS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "public", "data", "memorials",
)

DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"


def run_db_query(sql: str) -> str:
    """Run a psql query against the research DB and return raw output."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  DB query error: {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def load_db_sources() -> dict[str, dict]:
    """Load all source domains from the research DB."""
    raw = run_db_query(
        "SELECT domain, name, tier, source_type, description, is_active, last_checked "
        "FROM sources ORDER BY domain;"
    )
    sources = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 7:
            continue
        domain, name, tier, source_type, desc, is_active, last_checked = parts[:7]
        key = domain.replace("www.", "")
        sources[key] = {
            "domain": domain,
            "name": name,
            "tier": tier,
            "source_type": source_type or "",
            "description": desc or "",
            "is_active": is_active == "t",
            "last_checked": last_checked if last_checked else None,
        }
    return sources


def load_enrichment_history() -> dict[str, list[dict]]:
    """Load scrape run history from enrichment_runs table, grouped by domain."""
    raw = run_db_query(
        "SELECT source_domain, started_at::date, urls_queued, urls_scraped, urls_failed, name "
        "FROM enrichment_runs WHERE source_domain IS NOT NULL ORDER BY started_at;"
    )
    history = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        domain, date, queued, scraped, failed, name = parts[:6]
        key = domain.replace("www.", "")
        if key not in history:
            history[key] = []
        history[key].append({
            "date": date,
            "pages_attempted": int(queued) if queued else 0,
            "pages_succeeded": int(scraped) if scraped else 0,
            "script": f"mine-all-external-urls.py ({name})",
            "notes": f"Failed: {failed}" if failed and int(failed) > 0 else "",
        })
    return history


def scan_memorial_narratives() -> dict[str, dict]:
    """Scan all memorial JSONs for external_narrative domain stats."""
    domain_stats = {}  # domain -> {entries, with_full_text, memorials}

    for filepath in sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json"))):
        with open(filepath) as f:
            data = json.load(f)

        slug = os.path.basename(filepath).replace(".json", "")
        for narrative in data.get("external_narratives", []):
            url = narrative.get("original_url", "")
            if "://" not in url:
                continue
            domain = url.split("://")[1].split("/")[0].replace("www.", "")
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "entries": 0,
                    "with_full_text": 0,
                    "memorial_slugs": set(),
                }
            domain_stats[domain]["entries"] += 1
            domain_stats[domain]["memorial_slugs"].add(slug)
            if narrative.get("full_narrative"):
                domain_stats[domain]["with_full_text"] += 1

    # Convert sets to counts
    for v in domain_stats.values():
        v["memorials_linked"] = len(v["memorial_slugs"])
        del v["memorial_slugs"]

    return domain_stats


def detect_bot_policy(domain: str) -> str:
    """Check if domain is in the bot-blocked list."""
    for blocked in BOT_BLOCKED_DOMAINS:
        if domain in blocked or blocked.replace("www.", "") == domain.replace("www.", ""):
            return "blocked"
    return "unknown"


def main():
    print("=== BMR Scrape Provenance Seeder ===\n")

    # Step 1: Load from research DB
    print("1. Loading sources from research DB...")
    db_sources = load_db_sources()
    print(f"   Found {len(db_sources)} domains in DB")

    # Step 2: Load enrichment history
    print("2. Loading enrichment run history...")
    enrichment_history = load_enrichment_history()
    print(f"   Found history for {len(enrichment_history)} domains")

    # Step 3: Scan memorial JSONs
    print("3. Scanning memorial JSON external_narratives...")
    narrative_stats = scan_memorial_narratives()
    print(f"   Found {len(narrative_stats)} domains in memorial files")

    # Step 4: Merge into provenance log
    print("4. Merging into provenance log...")
    log = ProvenanceLog()

    # All unique domains from both sources
    all_domains = set(db_sources.keys()) | set(narrative_stats.keys())
    print(f"   Total unique domains: {len(all_domains)}")

    for domain in sorted(all_domains):
        db_info = db_sources.get(domain, {})
        narr_info = narrative_stats.get(domain, {})

        display_name = db_info.get("name", "")
        source_tier = db_info.get("tier", "")
        bot_policy = detect_bot_policy(domain)

        entry = log.add_domain(
            domain=db_info.get("domain", domain),
            display_name=display_name,
            source_tier=source_tier,
            bot_policy=bot_policy,
            memorials_linked=narr_info.get("memorials_linked", 0),
            entries_with_full_text=narr_info.get("with_full_text", 0),
        )

        # Attach enrichment history from DB
        if domain in enrichment_history:
            for run in enrichment_history[domain]:
                # Filter out empty notes
                if not run.get("notes"):
                    del run["notes"]
                entry["scrape_history"].append(run)
            entry["last_checked"] = enrichment_history[domain][-1]["date"]

    # Step 5: Add known manual scrape history (aircrew + association)
    print("5. Adding known manual scrape history...")

    # Use narrative_stats for accurate full_text counts
    aircrew_stats = narrative_stats.get("aircrewremembered.com", {})
    assoc_stats = narrative_stats.get("no-50-and-no-61-squadrons-association.co.uk", {})

    # Aircrew Remembered — batch-scrape-aircrew.py ran 2026-03-24
    aircrew = log.get_domain("aircrewremembered.com")
    if aircrew and not any(h.get("script", "").startswith("scripts/batch-scrape") for h in aircrew.get("scrape_history", [])):
        log.record_scrape("aircrewremembered.com", {
            "pages_attempted": 46,
            "pages_succeeded": 45,
            "full_narratives_extracted": 0,  # Don't double-count — already in add_domain
            "script": "scripts/batch-scrape-aircrew.py",
            "output": "/tmp/aircrew-scraped-all.json",
            "notes": "1 page timeout (retry needed)",
        })
        # Override date to actual date
        aircrew["scrape_history"][-1]["date"] = "2026-03-24"
        aircrew["last_checked"] = "2026-04-09"
        aircrew["entries_with_full_text"] = aircrew_stats.get("with_full_text", 45)
        aircrew["memorials_linked"] = aircrew_stats.get("memorials_linked", 46)
        aircrew["scrape_method"] = "scripts/batch-scrape-aircrew.py"
        aircrew["content_type"] = "crew_stories_detailed"

    # 50/61 Association — scrape-association-memorials.py ran 2026-04-09
    assoc_domain = "no-50-and-no-61-squadrons-association.co.uk"
    assoc = log.get_domain(assoc_domain)
    if assoc and not any("scrape-association" in h.get("script", "") for h in assoc.get("scrape_history", [])):
        log.record_scrape(assoc_domain, {
            "pages_attempted": 27,
            "pages_succeeded": 27,
            "full_narratives_extracted": 0,  # Don't double-count
            "script": "scripts/scrape-association-memorials.py",
            "output": "/nas2/Projects/BomberMemorial/Research/50-61-Association/2026-04-09_scrape_27-european-memorials.json",
            "notes": "W4769 appears twice (2 different URLs). 23 European stubs unmatched.",
        })
        assoc["scrape_history"][-1]["date"] = "2026-04-09"
        assoc["entries_with_full_text"] = assoc_stats.get("with_full_text", 27)
        assoc["memorials_linked"] = assoc_stats.get("memorials_linked", 3)
        assoc["scrape_method"] = "scripts/scrape-association-memorials.py"
        assoc["access"] = "http_only"
        assoc["content_type"] = "memorial_pages_with_crew"

    # Step 6: Save
    log.save()
    summary = log.summary()
    print(f"\n=== Provenance Log Created ===")
    print(f"   Path: {log.path}")
    print(f"   Total domains: {summary['total_domains']}")
    print(f"   With scrape history: {summary['domains_with_scrape_history']}")
    print(f"   Never scraped: {summary['domains_never_scraped']}")
    print(f"   Total full text entries: {summary['total_full_text_entries']}")
    print(f"   Bot-blocked: {summary['bot_blocked_domains']}")


if __name__ == "__main__":
    main()
