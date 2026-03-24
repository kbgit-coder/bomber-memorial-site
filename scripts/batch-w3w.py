#!/usr/bin/env python3
"""Batch convert lat/lng to what3words for all memorial JSON files."""

import json
import glob
import os
import re
import time
import urllib.request
import urllib.parse
import sys

MEMORIALS_DIR = "/nas2/Holly/Projects/bomber-memorial-site/public/data/memorials"
RATE_LIMIT_SECONDS = 1.5  # Be respectful to what3words

def get_w3w(lat, lng):
    """Convert lat/lng to what3words via website."""
    url = f"https://what3words.com/{lat},{lng}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8")[:10000]
        match = re.search(r"///([a-z]+\.[a-z]+\.[a-z]+)", html)
        if match:
            return match.group(1)
        # Check URL path as fallback
        final_url = resp.geturl()
        path = urllib.parse.urlparse(final_url).path.strip("/")
        if re.match(r"^[a-z]+\.[a-z]+\.[a-z]+$", path):
            return path
    except Exception as e:
        print(f"  ERROR: {e}")
    return None

def main():
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json")))
    print(f"Found {len(files)} memorial files")

    updated = 0
    skipped_has_w3w = 0
    skipped_no_coords = 0
    errors = 0

    for i, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        with open(filepath) as f:
            data = json.load(f)

        # Skip if already has what3words
        if data.get("what3words"):
            skipped_has_w3w += 1
            continue

        # Skip if no coordinates
        lat = data.get("latitude")
        lng = data.get("longitude")
        if lat is None or lng is None:
            print(f"  [{i+1}/{len(files)}] SKIP (no coords): {filename}")
            skipped_no_coords += 1
            continue

        # Rate limit
        time.sleep(RATE_LIMIT_SECONDS)

        w3w = get_w3w(lat, lng)
        if w3w:
            data["what3words"] = w3w
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            updated += 1
            print(f"  [{i+1}/{len(files)}] OK: {filename} → {w3w}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(files)}] FAIL: {filename}")

    print(f"\nDone: {updated} updated, {skipped_has_w3w} already had w3w, {skipped_no_coords} no coords, {errors} errors")

if __name__ == "__main__":
    main()
