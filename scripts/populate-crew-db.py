#!/usr/bin/env python3
"""
BMR Crew UID Database Population
Parses existing memorial JSONs → crew_members, memorial_crew, incident, aircraft, source_link tables.
Generates bmr_uid for each crew member. Normalises service numbers.

Usage: python3 scripts/populate-crew-db.py [--dry-run]

SET NEW STANDARDS.
"""

import json
import glob
import hashlib
import os
import re
import sys
import psycopg2

DRY_RUN = '--dry-run' in sys.argv
DB_DSN = "host=localhost port=5434 dbname=bmr_research user=bmr password=BmrResearch2026xHeritage"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')


def normalise_service_number(raw: str) -> tuple:
    """Normalise service number to BRANCH/NUMBER format. Returns (normalised, branch)."""
    if not raw or raw in ('—', 'None', 'Unknown', ''):
        return (None, None)

    raw = raw.strip()

    # RCAF patterns: R/nnnnn, J/nnnnn, C/nnnnn, Rnnnnnn RCAF, J/nnnnn RCAF
    m = re.match(r'^([RJC])[/]?(\d{4,6})\s*(?:RCAF)?$', raw)
    if m:
        return (f'RCAF/{m.group(1)}{m.group(2)}', 'RCAF')

    # RAAF patterns: Aus/nnnnnn, AUS/nnnnnn, nnnnnn RAAF
    m = re.match(r'^(?:Aus|AUS)[/]?(\d{5,6})\s*(?:RAAF)?$', raw)
    if m:
        return (f'RAAF/{m.group(1)}', 'RAAF')
    m = re.match(r'^(\d{4,6})\s+RAAF$', raw)
    if m:
        return (f'RAAF/{m.group(1)}', 'RAAF')
    m = re.match(r'^RAAF\s+(?:Aus[/]?)?(\d{4,6})$', raw)
    if m:
        return (f'RAAF/{m.group(1)}', 'RAAF')

    # RNZAF patterns: NZnnnnn, NZ/nnnnn, nnnnnn RNZAF
    m = re.match(r'^NZ[/]?(\d{4,6})\s*(?:RNZAF)?$', raw)
    if m:
        return (f'RNZAF/NZ{m.group(1)}', 'RNZAF')
    m = re.match(r'^(\d{5,6})\s+RNZAF$', raw)
    if m:
        return (f'RNZAF/NZ{m.group(1)}', 'RNZAF')

    # USAAF patterns: O-nnnnn, T-nnnnnn
    m = re.match(r'^([OT])-?(\d{4,7})\s*(?:USAAF|USAAC)?$', raw)
    if m:
        return (f'USAAF/{m.group(1)}-{m.group(2)}', 'USAAF')

    # RAFVR patterns: nnnnnnn RAFVR, RAFVR nnnnnnn
    m = re.match(r'^(\d{4,7})\s+RAFVR$', raw)
    if m:
        return (f'RAFVR/{m.group(1)}', 'RAFVR')
    m = re.match(r'^RAFVR\s+(\d{4,7})$', raw)
    if m:
        return (f'RAFVR/{m.group(1)}', 'RAFVR')

    # RAF patterns: nnnnnnn RAF, nnnnnnn
    m = re.match(r'^(\d{4,7})\s+RAF$', raw)
    if m:
        return (f'RAF/{m.group(1)}', 'RAF')
    m = re.match(r'^(\d{4,7})$', raw)
    if m:
        return (f'RAF/{m.group(1)}', 'RAF')

    # Branch-only (no number): RAFVR, RCAF, etc.
    if raw in ('RAFVR', 'RCAF', 'RAAF', 'RNZAF', 'RAF', 'USAAC', 'RNVR'):
        return (None, raw)

    return (None, None)


def generate_crew_uid(name: str, memorial_slug: str, date_of_death: str = '') -> str:
    """Generate deterministic UID from crew identity."""
    key = f"{name.strip().lower()}|{memorial_slug}|{date_of_death}"
    return 'bmr-crew-' + hashlib.sha256(key.encode()).hexdigest()[:8]


def split_name(full_name: str) -> tuple:
    """Split full name into (forenames, surname)."""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return ('', 'Unknown')
    if len(parts) == 1:
        return ('', parts[0])
    return (' '.join(parts[:-1]), parts[-1])


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    print(f'Processing {len(files)} memorial files...')

    if DRY_RUN:
        print('[DRY RUN — no database writes]')

    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()

    crew_count = 0
    crew_linked = 0
    incidents_created = 0
    aircraft_created = 0
    sources_created = 0
    sn_normalised = 0

    for f in files:
        d = json.load(open(f))
        slug = os.path.basename(f).replace('.json', '')

        # Get memorial DB id
        cur.execute("SELECT id FROM memorials WHERE slug = %s", (slug,))
        row = cur.fetchone()
        if not row:
            continue
        memorial_db_id = row[0]

        crash_date = d.get('crash_date', '')
        # Validate date format
        if crash_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', crash_date):
            crash_date = ''  # Invalid date like "WW2", "Various WW2"

        # Create/update incident
        serial = d.get('serial_number', '')
        if crash_date and serial:
            incident_id = f"bmr-inc-{crash_date}-{serial}"
            if not DRY_RUN:
                cur.execute("""
                    INSERT INTO incident (id, date, location_name, county, country, latitude, longitude, cause, operation_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (incident_id, crash_date or None, d.get('location_name'),
                      d.get('county'), d.get('country'),
                      d.get('latitude'), d.get('longitude'),
                      d.get('crash_category'), d.get('operation_type')))
                incidents_created += cur.rowcount

        # Create/update aircraft
        if serial:
            if not DRY_RUN:
                cur.execute("""
                    INSERT INTO aircraft (serial_number, aircraft_type, squadron, station)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (serial_number) DO NOTHING
                """, (serial, d.get('aircraft_type'), d.get('squadron'), d.get('station')))
                aircraft_created += cur.rowcount

        # Extract external IDs from sources
        for s in d.get('sources', []) or []:
            url = s.get('url', '')
            if not url:
                continue
            domain = url.split('/')[2] if url.startswith('http') and len(url.split('/')) > 2 else ''

            # IWM memorial ID
            m = re.search(r'iwm\.org\.uk/memorials/item/memorial/(\d+)', url)
            if m and not DRY_RUN:
                cur.execute("UPDATE memorials SET iwm_memorial_id = %s WHERE id = %s AND iwm_memorial_id IS NULL",
                           (m.group(1), memorial_db_id))

            # ASN wikibase ID
            m = re.search(r'aviation-safety\.net/wikibase/(\d+)', url)
            if m and not DRY_RUN:
                cur.execute("UPDATE memorials SET asn_wikibase_id = %s WHERE id = %s AND asn_wikibase_id IS NULL",
                           (m.group(1), memorial_db_id))

            # Store all source links
            if domain and not DRY_RUN:
                cur.execute("""
                    INSERT INTO source_link (entity_type, entity_id, source_domain, source_url, source_title)
                    VALUES ('memorial', %s, %s, %s, %s)
                    ON CONFLICT (entity_type, entity_id, source_url) DO NOTHING
                """, (slug, domain, url, s.get('title', '')))
                sources_created += cur.rowcount

        # Process crew
        for c in d.get('crew', []) or []:
            name = (c.get('name') or '').strip()
            if not name or name == 'Unknown':
                continue

            forenames, surname = split_name(name)
            bmr_uid = generate_crew_uid(name, slug, crash_date)

            # Normalise service number
            sn_raw = c.get('service_number', '')
            sn_norm, branch = normalise_service_number(sn_raw)
            if sn_norm:
                sn_normalised += 1

            # Detect branch from nationality if not from service number
            if not branch:
                nat = (c.get('nationality') or '').lower()
                if 'canadian' in nat:
                    branch = 'RCAF'
                elif 'australian' in nat:
                    branch = 'RAAF'
                elif 'new zealand' in nat:
                    branch = 'RNZAF'
                elif 'american' in nat:
                    branch = 'USAAF'
                elif 'polish' in nat:
                    branch = 'PAF'
                elif 'british' in nat:
                    branch = 'RAF'

            if not DRY_RUN:
                # Upsert crew member
                cur.execute("""
                    INSERT INTO crew_members (
                        surname, first_name, rank, service_number, age, role,
                        nationality, fate, fate_detail, burial_location, cwgc_url,
                        cwgc_verified, hometown, decorations, bio,
                        bmr_uid, service_number_normalised, service_number_raw, branch,
                        date_of_death, nickname
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s
                    )
                    ON CONFLICT (bmr_uid) DO UPDATE SET
                        service_number_normalised = COALESCE(EXCLUDED.service_number_normalised, crew_members.service_number_normalised),
                        branch = COALESCE(EXCLUDED.branch, crew_members.branch),
                        updated_at = NOW()
                    RETURNING id
                """, (
                    surname, forenames, c.get('rank'), sn_raw or None,
                    c.get('age'), c.get('role'),
                    c.get('nationality'), c.get('fate'), c.get('fate_detail'),
                    c.get('burial_location'), c.get('cwgc_url'),
                    c.get('cwgc_verified', False), c.get('hometown'),
                    c.get('decorations'), c.get('bio'),
                    bmr_uid, sn_norm, sn_raw or None, branch,
                    crash_date or None, None
                ))
                crew_db_id = cur.fetchone()[0]

                # Link crew to memorial
                cur.execute("""
                    INSERT INTO memorial_crew (memorial_id, crew_member_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (memorial_db_id, crew_db_id))
                crew_linked += cur.rowcount

            crew_count += 1

    if not DRY_RUN:
        conn.commit()

    cur.close()
    conn.close()

    print(f"""
BMR Crew UID Population Complete
═══════════════════════════════════
  Crew records:        {crew_count}
  Crew-memorial links: {crew_linked}
  Service numbers normalised: {sn_normalised}
  Incidents created:   {incidents_created}
  Aircraft created:    {aircraft_created}
  Source links:        {sources_created}
""")


if __name__ == '__main__':
    main()
