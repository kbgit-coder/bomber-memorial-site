#!/usr/bin/env python3
"""
BMR IWM Candidate Ingestion Pipeline
Scrapes IWM memorial pages, extracts data, generates memorial JSONs.
Runs through UID pipeline. Quality-first.

Usage: python3 scripts/ingest-iwm-candidates.py [--limit N] [--dry-run]

SET NEW STANDARDS.
"""

import json
import hashlib
import os
import re
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
import psycopg2

DRY_RUN = '--dry-run' in sys.argv
LIMIT = None
for i, arg in enumerate(sys.argv):
    if arg == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

DB_DSN = "host=localhost port=5434 dbname=bmr_research user=bmr password=BmrResearch2026xHeritage"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
RATE_LIMIT = 2.0  # seconds between IWM requests


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self.skip > 0:
            self.skip -= 1
    def handle_data(self, data):
        if self.skip == 0:
            self.text.append(data)
    def get_text(self):
        return ' '.join(self.text)


def fetch_iwm_page(url: str) -> str:
    """Fetch IWM memorial page HTML."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; BomberMemorialRegister/1.0; +https://bombermemorial.co.uk; admin@bombermemorial.co.uk)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f'  FETCH ERROR: {e}')
        return ''


def parse_iwm_memorial(html: str, url: str) -> dict:
    """Extract memorial data from IWM page HTML.
    IWM pages are JS-rendered but key data is in the static HTML:
    - Coordinates from Google Maps link
    - Photos from ciim5 media URLs
    - Description and other text from visible content blocks
    """
    data = {}

    # Extract all visible text for searching
    visible_chunks = re.findall(r'>([^<]{10,})<', html)
    visible_text = ' '.join(c.strip() for c in visible_chunks)

    # Coordinates from Google Maps link
    m = re.search(r'google\.com/maps/search/\?api=1&query=([-\d.]+),([-\d.]+)', html)
    if m:
        try:
            data['latitude'] = float(m.group(1))
            data['longitude'] = float(m.group(2))
        except ValueError:
            pass

    # Photos from ciim5 media URLs (large versions only, deduped)
    photos = set()
    for m in re.finditer(r'(https://media\.iwm\.org\.uk/ciim5/memorials/[^"\'>\s?]+large[^"\'>\s?]*\.(?:jpg|jpeg|png))', html, re.IGNORECASE):
        photos.add(m.group(1))
    if not photos:
        # Fallback to any ciim5 photos
        for m in re.finditer(r'(https://media\.iwm\.org\.uk/ciim5/memorials/[^"\'>\s?]+\.(?:jpg|jpeg|png))', html, re.IGNORECASE):
            photos.add(m.group(1).split('?')[0])
    if photos:
        data['photos'] = list(photos)[:10]

    # Description — longest visible text chunk that describes the memorial
    desc_candidates = []
    for chunk in visible_chunks:
        chunk = chunk.strip()
        # Skip JSON, HTML entities, script content, navigation text
        if chunk.startswith('{') or chunk.startswith('[') or '\\/' in chunk:
            continue
        if '&lt;' in chunk or '&gt;' in chunk or '&amp;' in chunk:
            continue
        if len(chunk) > 40 and any(kw in chunk.lower() for kw in
            ['memorial', 'plaque', 'stone', 'crash', 'crew', 'aircraft', 'bomber',
             'erected', 'dedicated', 'planted', 'unveiled', 'remembrance',
             'churchyard', 'cemetery', 'cairn', 'cross', 'tablet', 'garden']):
            desc_candidates.append(chunk)
    if desc_candidates:
        data['description'] = max(desc_candidates, key=len)[:2000]

    # Inscription — look for text that reads like an inscription
    for chunk in visible_chunks:
        chunk = chunk.strip()
        if len(chunk) > 20 and chunk.upper() == chunk and any(kw in chunk.upper() for kw in
            ['MEMORY', 'REMEMBER', 'HONOUR', 'FALLEN', 'CREW', 'DIED', 'REST IN PEACE', 'DEDICATED']):
            data['inscription'] = chunk[:2000]
            break

    # Total names count
    m = re.search(r'Total names on memorial:\s*(\d+)', visible_text)
    if m:
        data['names_count'] = int(m.group(1))

    # Location — look for place/county/country text
    # Often in structured location blocks with county and country
    for chunk in visible_chunks:
        chunk = chunk.strip()
        if re.search(r'(England|Scotland|Wales|Northern Ireland)$', chunk) and ',' in chunk:
            data['location'] = chunk
            break

    # IWM memorial ID from URL
    m = re.search(r'/memorial/(\d+)', url)
    if m:
        data['iwm_memorial_id'] = m.group(1)

    return data


def extract_location_parts(location_str: str) -> dict:
    """Parse IWM location string into county/country."""
    if not location_str:
        return {}

    parts = [p.strip() for p in location_str.split(',')]
    result = {}

    # Last part is usually country (England, Scotland, Wales, Northern Ireland)
    uk_countries = {'england', 'scotland', 'wales', 'northern ireland'}
    if parts and parts[-1].strip().lower() in uk_countries:
        result['country'] = 'United Kingdom'
        if len(parts) >= 2:
            result['county'] = parts[-2].strip()
        if len(parts) >= 3:
            result['location_name'] = ', '.join(parts[:-2]).strip()
    elif parts:
        result['location_name'] = location_str
        result['country'] = 'United Kingdom'  # Default for IWM UK memorials

    return result


def extract_serial_from_title(title: str) -> str:
    """Try to extract aircraft serial number from memorial title."""
    # Common patterns: MZ519, JB596, 42-97578, PB366, W4270
    patterns = [
        r'\b([A-Z]{1,2}\d{3,5})\b',  # UK serials: MZ519, JB596
        r'\b(\d{2}-\d{4,6})\b',       # US serials: 42-97578
    ]
    for p in patterns:
        m = re.search(p, title)
        if m:
            return m.group(1)
    return ''


def extract_aircraft_type(title: str) -> str:
    """Extract aircraft type from title."""
    type_map = {
        r'lancaster': 'Lancaster',
        r'halifax': 'Halifax',
        r'wellington': 'Wellington',
        r'stirling': 'Stirling',
        r'mosquito': 'Mosquito',
        r'hampden': 'Hampden',
        r'whitley': 'Whitley',
        r'blenheim': 'Blenheim',
        r'b-?17|flying fortress': 'B-17 Flying Fortress',
        r'b-?24|liberator': 'B-24 Liberator',
        r'sunderland': 'Sunderland',
        r'manchester': 'Manchester',
    }
    for pattern, name in type_map.items():
        if re.search(pattern, title, re.IGNORECASE):
            return name
    return ''


def extract_crash_date(text: str) -> str:
    """Try to extract crash date from inscription or description text."""
    # Pattern: DD Month YYYY or Month DD, YYYY or YYYY-MM-DD
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
        'oct': '10', 'nov': '11', 'dec': '12',
    }

    # DD Month YYYY
    m = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', text, re.IGNORECASE)
    if m:
        day = m.group(1).zfill(2)
        month = months.get(m.group(2).lower(), '')
        year = m.group(3)
        if month and 1939 <= int(year) <= 1947:
            return f'{year}-{month}-{day}'

    # Month DD, YYYY
    m = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', text, re.IGNORECASE)
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


def is_genuine_bomber_memorial(title: str, details: dict) -> bool:
    """Final check: is this actually a bomber crash memorial?"""
    title_lower = title.lower()

    # Reject non-bomber entries that slipped through
    reject_patterns = [
        'south african war', 'boer war', 'first world war', 'world war 1',
        'korean war', 'falklands', 'gulf war', 'afghanistan',
        'imperial yeomanry', 'infantry', 'artillery', 'cavalry',
        'merchant navy', 'royal navy', 'army', 'commando',
        'prisoner of war', 'concentration camp',
        'church window', 'stained glass', 'book of remembrance',
    ]
    for p in reject_patterns:
        if p in title_lower:
            return False

    # Accept if title has aircraft type or crash reference
    if re.search(r'(lancaster|halifax|wellington|stirling|mosquito|hampden|whitley|blenheim|b-17|b-24|liberator|fortress|sunderland|manchester|bomber|crash)', title_lower):
        return True

    # Accept if inscription/description mentions bomber/crash
    desc = (details.get('description', '') + details.get('inscription', '')).lower()
    if re.search(r'(bomber|crashed|crew|aircraft|squadron.*raf)', desc):
        return True

    return False


def build_memorial_json(slug: str, title: str, iwm_data: dict, source_url: str) -> dict:
    """Build a memorial JSON from IWM data."""
    location_parts = extract_location_parts(iwm_data.get('location', ''))
    all_text = ' '.join([
        iwm_data.get('inscription', ''),
        iwm_data.get('description', ''),
        iwm_data.get('name', ''),
    ])

    serial = extract_serial_from_title(title) or extract_serial_from_title(all_text)
    aircraft_type = extract_aircraft_type(title) or extract_aircraft_type(all_text)
    crash_date = extract_crash_date(all_text)
    squadron = extract_squadron(all_text) or extract_squadron(title)

    memorial = {
        'id': slug,
        'title': title,
        'location_name': location_parts.get('location_name', iwm_data.get('location', '')),
        'county': location_parts.get('county', ''),
        'country': location_parts.get('country', 'United Kingdom'),
        'aircraft_type': aircraft_type,
        'serial_number': serial,
        'squadron': squadron,
        'crash_date': crash_date,
        'memorial_type': iwm_data.get('type', ''),
        'memorial_details': '\n'.join(f'{k}: {v}' for k, v in iwm_data.items()
                                        if k in ('name', 'type', 'description', 'location', 'grid_ref') and v),
        'inscription': iwm_data.get('inscription', ''),
        'sources': [{'title': 'IWM War Memorials Register', 'url': source_url}],
        'data_quality': 'Stub',
        'narrative': '',
        'crew': [],
        'contributor': 'IWM War Memorials Register',
        'last_updated': '2026-04-12',
    }

    # Add coordinates if available
    if iwm_data.get('latitude') and iwm_data.get('longitude'):
        memorial['latitude'] = iwm_data['latitude']
        memorial['longitude'] = iwm_data['longitude']

    return memorial


def main():
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()

    # Get viable candidates
    cur.execute("""
        SELECT slug, title, source_url FROM memorials
        WHERE status = 'candidate'
        AND (
            title ~* '(lancaster|halifax|wellington|stirling|mosquito|hampden|whitley|blenheim|b-17|b-24|liberator|fortress|sunderland|manchester|avro|handley|vickers|short|de havilland|boeing)'
            OR title ~* '(crash|crew|pilot|flight sergeant|sergeant|flying officer|squadron.*bomber)'
        )
        AND NOT title ~* '(battalion|regiment|ground staff|civilian|maintenance|memorial garden|war memorial$|cenotaph|roll of honour|chapel|church window|plaque.*general|museum|south african|boer|first world)'
        ORDER BY slug
    """)
    candidates = cur.fetchall()

    # Check for existing production slugs to avoid duplicates
    cur.execute("SELECT slug FROM memorials WHERE status = 'production'")
    production_slugs = {row[0] for row in cur.fetchall()}

    # Also check existing JSON files
    existing_jsons = {f.replace('.json', '') for f in os.listdir(DATA_DIR) if f.endswith('.json')}

    print(f'Candidates: {len(candidates)}')
    print(f'Production memorials: {len(production_slugs)}')
    print(f'Existing JSONs: {len(existing_jsons)}')

    if LIMIT:
        candidates = candidates[:LIMIT]
        print(f'Limited to: {LIMIT}')

    accepted = 0
    rejected = 0
    skipped_duplicate = 0
    fetch_errors = 0

    for i, (slug, title, source_url) in enumerate(candidates):
        # Skip duplicates
        if slug in production_slugs or slug in existing_jsons:
            skipped_duplicate += 1
            continue

        print(f'[{i+1}/{len(candidates)}] {slug}')

        # Fetch IWM page
        html = fetch_iwm_page(source_url)
        if not html:
            fetch_errors += 1
            continue

        # Parse memorial data
        iwm_data = parse_iwm_memorial(html, source_url)

        # Quality check: is this genuinely a bomber memorial?
        if not is_genuine_bomber_memorial(title, iwm_data):
            rejected += 1
            print(f'  REJECTED: not a bomber crash memorial')
            if not DRY_RUN:
                cur.execute("UPDATE memorials SET status = 'rejected', rejection_reason = 'Not bomber crash memorial' WHERE slug = %s", (slug,))
            continue

        # Build memorial JSON
        memorial = build_memorial_json(slug, title, iwm_data, source_url)

        # Write JSON file
        if not DRY_RUN:
            json_path = os.path.join(DATA_DIR, f'{slug}.json')
            json.dump(memorial, open(json_path, 'w'), indent=2)

            # Update DB status
            cur.execute("""
                UPDATE memorials SET
                    status = 'staging',
                    iwm_memorial_id = %s,
                    serial_number = %s,
                    crash_date = %s,
                    county = %s
                WHERE slug = %s
            """, (
                iwm_data.get('iwm_memorial_id'),
                memorial.get('serial_number') or None,
                memorial.get('crash_date') or None,
                memorial.get('county') or None,
                slug
            ))

        accepted += 1
        print(f'  ACCEPTED: {memorial.get("aircraft_type", "?")} {memorial.get("serial_number", "?")} — {memorial.get("county", "?")}')

        # Rate limit
        time.sleep(RATE_LIMIT)

    if not DRY_RUN:
        conn.commit()

    cur.close()
    conn.close()

    print(f"""
╔══════════════════════════════════════════════════╗
║  IWM CANDIDATE INGESTION COMPLETE                ║
╠══════════════════════════════════════════════════╣
║  Candidates processed: {len(candidates):<5}                     ║
║  Accepted:             {accepted:<5}                     ║
║  Rejected:             {rejected:<5}                     ║
║  Skipped (duplicate):  {skipped_duplicate:<5}                     ║
║  Fetch errors:         {fetch_errors:<5}                     ║
╚══════════════════════════════════════════════════╝
""")


if __name__ == '__main__':
    main()
