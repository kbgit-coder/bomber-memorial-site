#!/usr/bin/env python3
"""
Audit all what3words codes in the Bomber Command Memorial Register.
Verifies each stored w3w against the actual coordinates and records results.
"""

import json
import os
import csv
import time
import re
import urllib.request
import urllib.parse
import glob

DATA_DIR = '/nas2/Projects/BomberMemorial/data/master/memorials'
OUT_CSV = '/nas2/Projects/BomberMemorial/monthly-updates/2026-04/w3w-verification.csv'
RATE_LIMIT = 1.2  # seconds between requests

CSV_FIELDS = [
    'entry_id', 'location_name', 'county', 'lat', 'lon',
    'original_w3w', 'original_w3w_tested', 'original_correct',
    'correct_w3w', 'new_w3w_tested', 'status', 'notes'
]

def fetch_url(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; BMR-audit/1.0)'}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        final_url = resp.geturl()
        html = resp.read().decode('utf-8', errors='replace')[:8000]
        return final_url, html
    except Exception as e:
        return None, str(e)

def get_w3w_for_coords(lat, lon):
    """Get correct w3w for lat/lon by scraping what3words."""
    url = f'https://what3words.com/{lat},{lon}'
    final_url, html = fetch_url(url)
    if not final_url:
        return None, f'fetch_failed: {html[:100]}'
    path = urllib.parse.urlparse(final_url).path.strip('/')
    if re.match(r'^[a-z]+\.[a-z]+\.[a-z]+$', path):
        return path, final_url
    # Fallback: search HTML for ///word.word.word pattern
    m = re.search(r'///([a-z]+\.[a-z]+\.[a-z]+)', html)
    if m:
        return m.group(1), 'from_html'
    # Also try unanchored w3w in common JSON/meta patterns
    m2 = re.search(r'"words"\s*:\s*"([a-z]+\.[a-z]+\.[a-z]+)"', html)
    if m2:
        return m2.group(1), 'from_html_json'
    return None, f'unexpected_path:{path[:80]}'

def test_w3w_code(w3w_code):
    """Test where a w3w code resolves to — return coordinate string or other info."""
    url = f'https://what3words.com/{w3w_code}'
    final_url, html = fetch_url(url)
    if not final_url:
        return 'fetch_failed'
    # Try to extract coordinates from page HTML
    coords = re.findall(r'(-?\d{1,3}\.\d{4,})[,\s]+(-?\d{1,3}\.\d{4,})', html)
    if coords:
        # Return the first plausible coordinate pair
        for lat_str, lon_str in coords:
            lat_f = float(lat_str)
            lon_f = float(lon_str)
            if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                return f'{lat_str},{lon_str}'
    # Check if final URL contains a w3w
    path = urllib.parse.urlparse(final_url).path.strip('/')
    if re.match(r'^[a-z]+\.[a-z]+\.[a-z]+$', path):
        return f'resolves_to:{path}'
    return f'url:{final_url[:80]}'

def is_international(data):
    country = data.get('country', 'United Kingdom')
    return country != 'United Kingdom'

def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    print(f'Found {len(files)} memorial files')

    # Ensure output dir exists
    out_dir = os.path.dirname(OUT_CSV)
    os.makedirs(out_dir, exist_ok=True)
    os.chmod(out_dir, 0o777)

    counts = {'CORRECT': 0, 'WRONG': 0, 'NO_COORDS': 0, 'FETCH_FAILED': 0, 'INTERNATIONAL': 0}
    request_count = 0

    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for i, filepath in enumerate(files):
            filename = os.path.basename(filepath)

            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)

            entry_id = data.get('id', filename.replace('.json', ''))
            location_name = data.get('location_name', '')
            county = data.get('county', '')
            lat = data.get('latitude')
            lon = data.get('longitude')
            original_w3w = data.get('what3words', '')

            if (i + 1) % 10 == 0:
                print(f'[{i+1}/{len(files)}] Processing {entry_id}...')

            # No coordinates case
            if lat is None or lon is None:
                row = {
                    'entry_id': entry_id,
                    'location_name': location_name,
                    'county': county,
                    'lat': '',
                    'lon': '',
                    'original_w3w': original_w3w,
                    'original_w3w_tested': '',
                    'original_correct': '',
                    'correct_w3w': '',
                    'new_w3w_tested': '',
                    'status': 'NO_COORDS',
                    'notes': 'No latitude/longitude in JSON'
                }
                writer.writerow(row)
                csvfile.flush()
                counts['NO_COORDS'] += 1
                print(f'  [{i+1}] NO_COORDS: {entry_id}')
                continue

            international = is_international(data)

            # Step 1: Get the correct w3w for these coords
            time.sleep(RATE_LIMIT)
            request_count += 1
            correct_w3w, correct_source = get_w3w_for_coords(lat, lon)

            if not correct_w3w:
                # Fetch failed for coords lookup
                row = {
                    'entry_id': entry_id,
                    'location_name': location_name,
                    'county': county,
                    'lat': lat,
                    'lon': lon,
                    'original_w3w': original_w3w,
                    'original_w3w_tested': '',
                    'original_correct': '',
                    'correct_w3w': '',
                    'new_w3w_tested': '',
                    'status': 'FETCH_FAILED',
                    'notes': f'Could not fetch w3w for coords: {correct_source[:120]}'
                }
                writer.writerow(row)
                csvfile.flush()
                counts['FETCH_FAILED'] += 1
                print(f'  [{i+1}] FETCH_FAILED (coords lookup): {entry_id}')
                continue

            # Step 2: Test the original w3w (where does it resolve to?)
            original_w3w_tested = ''
            if original_w3w:
                time.sleep(RATE_LIMIT)
                request_count += 1
                original_w3w_tested = test_w3w_code(original_w3w)

            # Step 3: Verify correct_w3w by fetching it back
            time.sleep(RATE_LIMIT)
            request_count += 1
            new_w3w_tested = test_w3w_code(correct_w3w)

            # Determine if original is correct
            original_correct = (original_w3w == correct_w3w) if original_w3w else False

            # Determine status
            if international:
                status = 'INTERNATIONAL'
                notes = f'International memorial — {data.get("country", "unknown country")}'
                if not original_correct:
                    notes += f'; w3w differs: stored={original_w3w}, correct={correct_w3w}'
            elif not original_w3w:
                status = 'WRONG'
                notes = 'No w3w stored in JSON'
                original_correct = False
            elif original_correct:
                status = 'CORRECT'
                notes = ''
            else:
                status = 'WRONG'
                notes = f'Stored w3w does not match coordinates'

            row = {
                'entry_id': entry_id,
                'location_name': location_name,
                'county': county,
                'lat': lat,
                'lon': lon,
                'original_w3w': original_w3w,
                'original_w3w_tested': original_w3w_tested,
                'original_correct': str(original_correct).upper(),
                'correct_w3w': correct_w3w,
                'new_w3w_tested': new_w3w_tested,
                'status': status,
                'notes': notes
            }
            writer.writerow(row)
            csvfile.flush()

            if international:
                counts['INTERNATIONAL'] += 1
            elif original_correct:
                counts['CORRECT'] += 1
            else:
                counts['WRONG'] += 1

            if status == 'CORRECT':
                pass  # quiet for correct ones
            else:
                print(f'  [{i+1}] {status}: {entry_id} | stored={original_w3w} | correct={correct_w3w}')

    # Set file permissions
    os.chmod(OUT_CSV, 0o666)

    total = sum(counts.values())
    print('\n' + '='*60)
    print('AUDIT COMPLETE')
    print('='*60)
    print(f'Total entries:   {total}')
    print(f'CORRECT:         {counts["CORRECT"]}')
    print(f'WRONG:           {counts["WRONG"]}')
    print(f'INTERNATIONAL:   {counts["INTERNATIONAL"]}')
    print(f'NO_COORDS:       {counts["NO_COORDS"]}')
    print(f'FETCH_FAILED:    {counts["FETCH_FAILED"]}')
    print(f'Total requests:  {request_count}')
    print(f'Output:          {OUT_CSV}')

if __name__ == '__main__':
    main()
