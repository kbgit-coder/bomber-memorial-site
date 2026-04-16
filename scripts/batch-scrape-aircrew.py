#!/usr/bin/env python3
"""Batch scrape aircrewremembered.com narrative content for memorial enrichment."""

import json
import glob
import os
import re
import sys
import time
import urllib.request
import urllib.parse

# Module import for provenance logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_provenance import ProvenanceLog

MEMORIALS_DIR = "/root/repos/bomber-memorial-site/public/data/memorials"
RATE_LIMIT_SECONDS = 2.0
OUTPUT_FILE = "/tmp/aircrew-scraped-all.json"
DOMAIN = "aircrewremembered.com"

def scrape_aircrew_page(url):
    """Scrape narrative content from an aircrewremembered.com page."""
    # Ensure https
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)

    # Extract main content - aircrewremembered uses a fairly standard layout
    # Remove script and style tags
    html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL)
    html_clean = re.sub(r'<nav[^>]*>.*?</nav>', '', html_clean, flags=re.DOTALL)

    # Extract text from paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_clean, flags=re.DOTALL)

    # Also get headings for structure
    headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_clean, flags=re.DOTALL)

    # Also get table content (crew lists are often in tables)
    table_cells = re.findall(r'<td[^>]*>(.*?)</td>', html_clean, flags=re.DOTALL)

    # Also get list items
    list_items = re.findall(r'<li[^>]*>(.*?)</li>', html_clean, flags=re.DOTALL)

    # Clean HTML tags from extracted text
    def clean_html(text):
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#\d+;', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # Build structured content
    content_parts = []

    for h in headings:
        cleaned = clean_html(h)
        if cleaned and len(cleaned) > 2 and len(cleaned) < 200:
            content_parts.append(f"## {cleaned}")

    for p in paragraphs:
        cleaned = clean_html(p)
        if cleaned and len(cleaned) > 20:  # Skip very short paragraphs (likely nav)
            content_parts.append(cleaned)

    # Add significant list items
    for li in list_items:
        cleaned = clean_html(li)
        if cleaned and len(cleaned) > 15:
            content_parts.append(f"- {cleaned}")

    content = "\n\n".join(content_parts)

    # Filter out common noise
    noise_patterns = [
        'cookie', 'privacy policy', 'subscribe', 'newsletter',
        'copyright', 'all rights reserved', 'powered by',
        'click here', 'read more', 'share this', 'follow us'
    ]

    lines = content.split('\n\n')
    filtered = [l for l in lines if not any(n in l.lower() for n in noise_patterns)]
    content = '\n\n'.join(filtered)

    return content if len(content) > 100 else None, None

def main():
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json")))
    print(f"Found {len(files)} memorial files")

    # Find all memorials with aircrewremembered references
    to_scrape = []
    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath) as f:
            data = json.load(f)

        aircrew_url = None
        for s in data.get('sources', []):
            if 'aircrewremembered' in s.get('url', ''):
                aircrew_url = s['url']
                break
        if not aircrew_url:
            for n in data.get('external_narratives', []):
                if 'aircrewremembered' in n.get('original_url', ''):
                    aircrew_url = n['original_url']
                    break

        if aircrew_url:
            # Check if already has full_narrative
            has_full = False
            for n in data.get('external_narratives', []):
                if 'aircrewremembered' in n.get('original_url', '') and n.get('full_narrative'):
                    has_full = True
                    break
            if not has_full:
                to_scrape.append((filepath, filename, aircrew_url))

    print(f"Need to scrape: {len(to_scrape)} pages")

    results = []
    success = 0
    errors = 0

    for i, (filepath, filename, url) in enumerate(to_scrape):
        time.sleep(RATE_LIMIT_SECONDS)

        content, error = scrape_aircrew_page(url)
        if content:
            results.append({
                'filename': filename,
                'filepath': filepath,
                'url': url,
                'content': content,
                'content_length': len(content)
            })
            success += 1
            print(f"  [{i+1}/{len(to_scrape)}] OK: {filename} ({len(content)} chars)")
        else:
            errors += 1
            print(f"  [{i+1}/{len(to_scrape)}] FAIL: {filename} - {error}")

    # Write results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {success} scraped, {errors} errors")
    print(f"Results written to {OUTPUT_FILE}")

    # Log to provenance
    log = ProvenanceLog()
    log.record_scrape(DOMAIN, {
        "pages_attempted": len(to_scrape),
        "pages_succeeded": success,
        "full_narratives_extracted": success,
        "script": "scripts/batch-scrape-aircrew.py",
        "output": OUTPUT_FILE,
        "notes": f"{errors} errors" if errors else "",
    })
    log.save()
    print(f"Provenance log updated for {DOMAIN}")

if __name__ == "__main__":
    main()
