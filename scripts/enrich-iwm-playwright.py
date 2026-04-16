#!/usr/bin/env python3
"""
BMR IWM Playwright Enrichment
Enriches 335 staging stubs with full data from JS-rendered IWM pages.
Uses Playwright headless Chromium to get inscription, location, crew, etc.

Usage:
  python3 scripts/enrich-iwm-playwright.py [--limit N] [--dry-run] [--parallel N]

SET NEW STANDARDS.
"""

import json
import os
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import psycopg2

# CLI args
DRY_RUN = '--dry-run' in sys.argv
LIMIT = None
PARALLEL = 4  # concurrent browser contexts
for i, arg in enumerate(sys.argv):
    if arg == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])
    if arg == '--parallel' and i + 1 < len(sys.argv):
        PARALLEL = int(sys.argv[i + 1])

DB_DSN = "host=localhost port=5434 dbname=bmr_research user=bmr password=BmrResearch2026xHeritage"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'enrich-iwm.log')


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def parse_iwm_rendered_text(text: str, html: str, url: str) -> dict:
    """Parse structured data from Playwright-rendered IWM page text."""
    data = {}

    # ---- Structured fields from Memorial Details section ----
    # These appear as "Label\nValue" pairs in the rendered text

    field_patterns = {
        'memorial_type': r'Memorial type\n([^\n]+)',
        'district': r'District\n([^\n]+)',
        'town': r'Town\n([^\n]+)',
        'county': r'County\n([^\n]+)',
        'country_field': r'Country\n([^\n]+)',
        'commemoration': r'Commemoration\n([^\n]+)',
        'wm_reference': r'WM Reference\n(\d+)',
    }
    for key, pattern in field_patterns.items():
        m = re.search(pattern, text)
        if m:
            data[key] = m.group(1).strip()

    # ---- Description ----
    m = re.search(r'Description\n(.+?)(?:\nInscription|\nInscription legible|\nCommemorations|\nComponents|\nListing|\nCondition)', text, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        # Clean up — remove "Support IWM" donation blocks that appear mid-text
        desc = re.sub(r'Support IWM.*?Make a Donation\n?', '', desc, flags=re.DOTALL).strip()
        if len(desc) > 15:
            data['description'] = desc[:2000]

    # ---- Inscription ----
    m = re.search(r'Inscription\n(.+?)(?:\nInscription legible|\nCommemorations|\nTotal names|\nComponents|\nListing|\nCondition)', text, re.DOTALL)
    if m:
        insc = m.group(1).strip()
        insc = re.sub(r'Support IWM.*?Make a Donation\n?', '', insc, flags=re.DOTALL).strip()
        if len(insc) > 5:
            data['inscription'] = insc[:3000]

    # ---- Total names on memorial ----
    m = re.search(r'Total names on memorial:\s*(\d+)', text)
    if m:
        data['names_count'] = int(m.group(1))

    # Died count
    m = re.search(r'Died:\s*(\d+)', text)
    if m:
        data['died_count'] = int(m.group(1))

    # ---- Grid reference ----
    m = re.search(r'(?:Grid [Rr]ef|OS Grid)[:\s]*([A-Z]{2}\s?\d{4,})', text)
    if m:
        data['grid_ref'] = m.group(1).strip()

    # ---- Coordinates from Google Maps link in HTML ----
    m = re.search(r'google\.com/maps/search/\?api=1&query=([-\d.]+),([-\d.]+)', html)
    if m:
        try:
            data['latitude'] = float(m.group(1))
            data['longitude'] = float(m.group(2))
        except ValueError:
            pass

    # ---- Photos from ciim5 media URLs ----
    photos = set()
    for m in re.finditer(r'(https://media\.iwm\.org\.uk/ciim5/memorials/[^"\'>\s?]+\.(?:jpg|jpeg|png))', html, re.IGNORECASE):
        photo_url = m.group(1).split('?')[0]
        photos.add(photo_url)
    if photos:
        # Prefer large versions
        large = [p for p in photos if 'large' in p.lower()]
        data['photos'] = (large or list(photos))[:10]

    # ---- IWM memorial ID from URL ----
    m = re.search(r'/memorial/(\d+)', url)
    if m:
        data['iwm_memorial_id'] = m.group(1)

    # ---- Responsibility/custodian ----
    m = re.search(r'Responsibility\n([^\n]+)', text)
    if m:
        data['responsibility'] = m.group(1).strip()

    return data


def extract_crash_date(text: str) -> str:
    """Extract crash date from inscription/description text."""
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
    }

    # DD Month YYYY
    m = re.search(
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
        text, re.IGNORECASE
    )
    if m:
        day = m.group(1).zfill(2)
        month = months.get(m.group(2).lower(), '')
        year = m.group(3)
        if month and 1939 <= int(year) <= 1947:
            return f'{year}-{month}-{day}'

    # Month DD, YYYY
    m = re.search(
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})',
        text, re.IGNORECASE
    )
    if m:
        month = months.get(m.group(1).lower(), '')
        day = m.group(2).zfill(2)
        year = m.group(3)
        if month and 1939 <= int(year) <= 1947:
            return f'{year}-{month}-{day}'

    # DD/MM/YYYY
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if m and 1939 <= int(m.group(3)) <= 1947:
        return f'{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}'

    return ''


def extract_squadron(text: str) -> str:
    """Extract squadron from text."""
    m = re.search(r'(\d{1,3})\s*(?:Squadron|Sqdn?\.?|Sqn)', text, re.IGNORECASE)
    if m:
        return f'{m.group(1)} Squadron'
    return ''


def extract_crew_from_inscription(inscription: str) -> list:
    """Try to extract crew names from inscription text."""
    crew = []
    if not inscription:
        return crew

    # Common rank prefixes
    rank_pattern = r'(?:Pilot Officer|Flying Officer|Flight Lieutenant|Squadron Leader|Wing Commander|Group Captain|Sergeant|Flight Sergeant|Warrant Officer|P/O|F/O|F/Lt|S/Ldr|W/Cdr|Sgt|F/Sgt|W/O|Fg Off|Flt Lt|Flt Sgt|Wg Cdr|Gp Capt|Air Gunner|Navigator|Wireless Operator|Bomb Aimer|Flight Engineer|Rear Gunner|Mid Upper Gunner)'

    # Pattern: Rank Name (possibly with initials)
    for m in re.finditer(
        rf'({rank_pattern})\s+([A-Z][a-zA-Z.\s-]{{2,30}}?)(?:\s*[,\n/]|\s+(?:DFM|DFC|DSO|CGM|RAFVR|RAF|RAAF|RCAF|RNZAF|USAAF)|\s*$)',
        inscription
    ):
        rank = m.group(1).strip()
        name = m.group(2).strip().rstrip(',. ')
        if name and len(name) > 2:
            crew.append({'rank': rank, 'name': name})

    return crew[:12]  # Cap at 12 crew (max for any bomber)


def enrich_memorial(slug: str, source_url: str, existing_json: dict, page) -> dict:
    """Enrich a single memorial using a Playwright page."""
    try:
        page.goto(source_url, timeout=30000, wait_until='networkidle')
        page.wait_for_timeout(1500)  # Let JS render

        html = page.content()
        text = page.inner_text('body')
    except Exception as e:
        log(f'  FETCH ERROR {slug}: {e}')
        return None

    if len(text) < 100:
        log(f'  EMPTY PAGE {slug}: only {len(text)} chars')
        return None

    # Parse the rendered page
    iwm_data = parse_iwm_rendered_text(text, html, source_url)

    if not iwm_data.get('description') and not iwm_data.get('inscription') and not iwm_data.get('county'):
        log(f'  NO DATA {slug}: page rendered but no extractable fields')
        return None

    # Build enriched fields — only overwrite if new data is better
    enriched = dict(existing_json)

    # Location fields
    if iwm_data.get('county') and not existing_json.get('county'):
        enriched['county'] = iwm_data['county']
    if iwm_data.get('town'):
        location_name = iwm_data['town']
        if iwm_data.get('district') and iwm_data['district'] != iwm_data['town']:
            location_name = f"{iwm_data['town']}, {iwm_data['district']}"
        if not existing_json.get('location_name'):
            enriched['location_name'] = location_name
    if iwm_data.get('country_field'):
        enriched['country'] = 'United Kingdom'

    # Coordinates
    if iwm_data.get('latitude') and not existing_json.get('latitude'):
        enriched['latitude'] = iwm_data['latitude']
        enriched['longitude'] = iwm_data['longitude']

    # Memorial type
    if iwm_data.get('memorial_type') and not existing_json.get('memorial_type'):
        enriched['memorial_type'] = iwm_data['memorial_type']

    # Description → memorial_details
    if iwm_data.get('description'):
        enriched['memorial_details'] = iwm_data['description']

    # Inscription
    if iwm_data.get('inscription') and not existing_json.get('inscription'):
        enriched['inscription'] = iwm_data['inscription']

    # Extract crash date from inscription/description
    all_text = ' '.join(filter(None, [
        iwm_data.get('inscription', ''),
        iwm_data.get('description', ''),
        existing_json.get('title', ''),
    ]))
    if not existing_json.get('crash_date'):
        crash_date = extract_crash_date(all_text)
        if crash_date:
            enriched['crash_date'] = crash_date

    # Squadron
    if not existing_json.get('squadron'):
        squadron = extract_squadron(all_text)
        if squadron:
            enriched['squadron'] = squadron

    # Crew from inscription
    if not existing_json.get('crew') or len(existing_json.get('crew', [])) == 0:
        crew = extract_crew_from_inscription(iwm_data.get('inscription', ''))
        if crew:
            enriched['crew'] = crew

    # Grid reference
    if iwm_data.get('grid_ref'):
        enriched['grid_ref'] = iwm_data['grid_ref']

    # Photos
    if iwm_data.get('photos') and not existing_json.get('photos'):
        enriched['photos'] = iwm_data['photos']

    # Names count metadata
    if iwm_data.get('names_count'):
        enriched['names_on_memorial'] = iwm_data['names_count']
    if iwm_data.get('died_count'):
        enriched['died_count'] = iwm_data['died_count']

    # Responsibility/custodian
    if iwm_data.get('responsibility'):
        enriched['custodian'] = iwm_data['responsibility']

    # Upgrade data quality if we got meaningful data
    has_inscription = bool(enriched.get('inscription'))
    has_location = bool(enriched.get('county'))
    has_description = bool(enriched.get('memorial_details') and
                          'This record comprises' not in enriched.get('memorial_details', ''))

    if has_inscription and has_location:
        enriched['data_quality'] = 'Good'
    elif has_inscription or has_location or has_description:
        enriched['data_quality'] = 'Basic'
    # else stays 'Stub'

    enriched['last_updated'] = '2026-04-12'

    return enriched


def process_batch(stubs, batch_id):
    """Process a batch of stubs with a single browser instance."""
    from playwright.sync_api import sync_playwright

    results = {'enriched': 0, 'failed': 0, 'no_data': 0}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (compatible; BomberMemorialRegister/1.0; +https://bombermemorial.co.uk)',
        )

        page = context.new_page()

        for i, (slug, source_url) in enumerate(stubs):
            log(f'  [B{batch_id}:{i+1}/{len(stubs)}] {slug}')

            # Read existing JSON
            json_path = os.path.join(DATA_DIR, f'{slug}.json')
            if not os.path.exists(json_path):
                log(f'    SKIP: no JSON file')
                results['failed'] += 1
                continue

            with open(json_path) as f:
                existing = json.load(f)

            # Enrich
            enriched = enrich_memorial(slug, source_url, existing, page)

            if enriched is None:
                results['no_data'] += 1
                continue

            # Write enriched JSON
            if not DRY_RUN:
                with open(json_path, 'w') as f:
                    json.dump(enriched, f, indent=2)

            # Count what we got
            fields_added = []
            for k in ['inscription', 'county', 'memorial_type', 'crash_date', 'squadron', 'crew']:
                if enriched.get(k) and not existing.get(k):
                    if k == 'crew' and isinstance(enriched[k], list):
                        fields_added.append(f'crew({len(enriched[k])})')
                    else:
                        val = str(enriched[k])[:30]
                        fields_added.append(f'{k}={val}')

            log(f'    ENRICHED: quality={enriched["data_quality"]} | +{", ".join(fields_added) or "metadata only"}')
            results['enriched'] += 1

            # Respectful rate limit
            time.sleep(1.5)

        context.close()
        browser.close()

    return results


def main():
    log(f'\n{"=" * 60}')
    log(f'BMR IWM PLAYWRIGHT ENRICHMENT — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    log(f'DRY_RUN={DRY_RUN}  LIMIT={LIMIT}  PARALLEL={PARALLEL}')
    log(f'{"=" * 60}')

    # Get staging stubs from DB
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT slug, source_url FROM memorials
        WHERE status = 'staging'
        ORDER BY slug
    """)
    stubs = cur.fetchall()
    cur.close()
    conn.close()

    log(f'Staging stubs to enrich: {len(stubs)}')

    if LIMIT:
        stubs = stubs[:LIMIT]
        log(f'Limited to: {LIMIT}')

    # Split into batches for parallel processing
    batch_size = max(1, len(stubs) // PARALLEL)
    batches = []
    for i in range(0, len(stubs), batch_size):
        batches.append(stubs[i:i + batch_size])

    log(f'Split into {len(batches)} batches of ~{batch_size} each')

    # Process batches
    # For stability, run sequentially but with page reuse within each batch
    # (Playwright sync API doesn't work well across threads)
    total = {'enriched': 0, 'failed': 0, 'no_data': 0}

    for batch_idx, batch in enumerate(batches):
        log(f'\n--- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} stubs) ---')
        result = process_batch(batch, batch_idx + 1)
        for k in total:
            total[k] += result[k]

    # Update DB statuses based on enriched JSON quality
    if not DRY_RUN:
        conn = psycopg2.connect(DB_DSN)
        cur = conn.cursor()
        updated = 0
        for slug, _ in stubs:
            json_path = os.path.join(DATA_DIR, f'{slug}.json')
            if not os.path.exists(json_path):
                continue
            with open(json_path) as f:
                memorial = json.load(f)
            cur.execute("""
                UPDATE memorials SET
                    county = COALESCE(NULLIF(%s, ''), county),
                    crash_date = COALESCE(NULLIF(%s, '')::date, crash_date),
                    serial_number = COALESCE(NULLIF(%s, ''), serial_number),
                    iwm_memorial_id = COALESCE(NULLIF(%s, ''), iwm_memorial_id)
                WHERE slug = %s AND status = 'staging'
            """, (
                memorial.get('county', ''),
                memorial.get('crash_date', ''),
                memorial.get('serial_number', ''),
                memorial.get('sources', [{}])[0].get('url', '').split('/')[-1] if memorial.get('sources') else '',
                slug,
            ))
            updated += 1
        conn.commit()
        cur.close()
        conn.close()
        log(f'DB updated: {updated} memorials')

    log(f"""
{'=' * 60}
BMR IWM PLAYWRIGHT ENRICHMENT COMPLETE
{'=' * 60}
  Total processed:  {total['enriched'] + total['failed'] + total['no_data']}
  Enriched:         {total['enriched']}
  No data found:    {total['no_data']}
  Failed/skipped:   {total['failed']}
{'=' * 60}
""")


if __name__ == '__main__':
    main()
