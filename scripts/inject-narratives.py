#!/usr/bin/env python3
"""Inject scraped aircrewremembered.com content into memorial JSON files."""

import json
import os
import sys

# Module import for provenance logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_provenance import ProvenanceLog

MEMORIALS_DIR = "/root/repos/bomber-memorial-site/public/data/memorials"
SCRAPED_FILE = "/tmp/aircrew-scraped-all.json"

def truncate_content(content, max_chars=5000):
    """Truncate content to a reasonable size for JSON storage, ending at a sentence."""
    if len(content) <= max_chars:
        return content
    # Find the last sentence end before max_chars
    truncated = content[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.7:  # At least 70% of content
        return truncated[:last_period + 1]
    return truncated + "..."

def main():
    with open(SCRAPED_FILE) as f:
        scraped = json.load(f)

    print(f"Loaded {len(scraped)} scraped results")

    updated = 0
    for item in scraped:
        filepath = item['filepath']
        url = item['url']
        content = item['content']

        if not os.path.exists(filepath):
            print(f"  SKIP (file gone): {item['filename']}")
            continue

        with open(filepath) as f:
            data = json.load(f)

        # Find the matching external_narrative entry
        found = False
        narratives = data.get('external_narratives', [])
        for narrative in narratives:
            orig_url = narrative.get('original_url', '')
            if 'aircrewremembered' in orig_url:
                # Add full_narrative field with truncated content
                narrative['full_narrative'] = truncate_content(content)
                narrative['date_retrieved'] = '2026-03-24'
                narrative['still_live'] = True
                found = True
                break

        if not found:
            # No existing narrative entry — add one
            if 'external_narratives' not in data:
                data['external_narratives'] = []
            data['external_narratives'].append({
                'source_site': 'Aircrew Remembered',
                'original_url': url,
                'summary': truncate_content(content, 500),
                'full_narrative': truncate_content(content),
                'date_retrieved': '2026-03-24',
                'still_live': True
            })

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        updated += 1
        print(f"  OK: {item['filename']} ({len(truncate_content(content))} chars)")

    print(f"\nDone: {updated} memorials enriched with narrative content")

    # Update provenance stats — count actual full_narrative entries per domain
    if updated > 0:
        log = ProvenanceLog()
        # Recount from the now-updated files to get accurate stats
        from collections import Counter
        domain_full_text = Counter()
        domain_memorials = Counter()
        import glob
        for fp in glob.glob(os.path.join(MEMORIALS_DIR, "*.json")):
            with open(fp) as fh:
                data = json.load(fh)
            slug = os.path.basename(fp).replace(".json", "")
            for n in data.get("external_narratives", []):
                url = n.get("original_url", "")
                if "://" not in url:
                    continue
                domain = url.split("://")[1].split("/")[0].replace("www.", "")
                if n.get("full_narrative"):
                    domain_full_text[domain] += 1
                    domain_memorials[domain] += 1
        # Update domains that were touched
        for domain in domain_full_text:
            log.update_domain_stats(
                domain,
                memorials_linked=domain_memorials[domain],
                entries_with_full_text=domain_full_text[domain],
            )
        log.save()
        print("Provenance stats updated")

if __name__ == "__main__":
    main()
