#!/usr/bin/env python3
"""
BMR Candidate Ingestion Pipeline — fetches, classifies, and persists memorial candidates.

Flow:
  1. Fetch candidate data from source (IWM, WMO, etc)
  2. Persist raw candidate to DB with status='candidate'
  3. Scope-classify (bomber-command / coastal / fighter / other)
  4. Update DB with classification
  5. Generate stubs for in-scope candidates

ALL candidates go to the database. Nothing stays in memory or temp files.
Rejected candidates stay in DB with status='rejected' and a reason.

Usage:
  python3 scripts/ingest-candidates.py --source iwm --fetch
  python3 scripts/ingest-candidates.py --classify [--limit N]
  python3 scripts/ingest-candidates.py --generate-stubs [--limit N]
  python3 scripts/ingest-candidates.py --status
"""

import json
import os
import sys
import re
import time
import subprocess
import requests
import psycopg2
from psycopg2.extras import execute_values

INFERENCE_TOOL = os.path.expanduser('~/.claude/PAI/Tools/Inference.ts')

# DB connection via docker exec for reliability
def db_query(sql, params=None):
    """Execute a query via docker exec."""
    if params:
        # Simple parameter substitution for docker exec
        for p in params:
            sql = sql.replace('%s', f"'{p}'", 1) if isinstance(p, str) else sql.replace('%s', str(p), 1)
    result = subprocess.run(
        ['docker', 'exec', 'bmr-research-db', 'psql', '-U', 'bmr', '-d', 'bmr_research',
         '-t', '-A', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f'  DB ERROR: {result.stderr[:200]}')
        return None
    return result.stdout.strip()


def db_exec(sql):
    """Execute a statement via docker exec."""
    result = subprocess.run(
        ['docker', 'exec', 'bmr-research-db', 'psql', '-U', 'bmr', '-d', 'bmr_research', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f'  DB ERROR: {result.stderr[:200]}')
        return False
    return True


def fetch_iwm_candidates():
    """Fetch bomber-related memorial candidates from IWM War Memorials Register."""
    # Get existing IWM IDs already in DB
    existing = db_query("SELECT source_id FROM memorials WHERE source_id LIKE 'iwm-%'")
    existing_ids = set(existing.split('\n')) if existing else set()
    print(f'Existing IWM candidates in DB: {len(existing_ids)}')

    # Search IWM
    search_terms = [
        'bomber+command+crash', 'raf+bomber+crash+memorial',
        'lancaster+crash+memorial', 'halifax+crash+memorial',
        'wellington+crash+memorial', 'bomber+command+memorial',
        'aircrew+killed+memorial', 'raf+crash+site',
        'bomber+crew+memorial', 'stirling+crash',
        'mosquito+crash+memorial', 'hampden+crash',
    ]

    all_ids = set()
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; BMR-Research/1.0)'}

    for term in search_terms:
        for page in range(1, 8):
            url = f'https://www.iwm.org.uk/memorials/search?query={term}&page={page}'
            try:
                resp = requests.get(url, headers=headers, timeout=20)
                ids = re.findall(r'/memorials/item/memorial/(\d+)', resp.text)
                if not ids:
                    break
                all_ids.update(ids)
                time.sleep(3)  # Rate limit — respect IWM
            except Exception as e:
                print(f'  Timeout/error on {term} page {page}: {e}')
                break
        print(f'  [{term}] found {len(all_ids)} total so far')

    new_ids = all_ids - {eid.replace('iwm-', '') for eid in existing_ids}
    print(f'\nTotal IWM IDs found: {len(all_ids)}')
    print(f'New (not in DB): {len(new_ids)}')

    # Fetch basic data for each new candidate and insert to DB
    inserted = 0
    for iwm_id in sorted(new_ids):
        url = f'https://www.iwm.org.uk/memorials/item/memorial/{iwm_id}'
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            html = resp.text

            # Extract basic fields from HTML
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            title = title_match.group(1).strip() if title_match else f'IWM Memorial {iwm_id}'

            # Extract location
            location_match = re.search(r'Location.*?<[^>]*>([^<]+)</[^>]*>', html, re.S)
            location = location_match.group(1).strip() if location_match else ''

            # Extract county/country
            county = ''
            country = 'United Kingdom'

            # Generate slug
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:80]

            # Check not already in production JSONs
            json_path = f'public/data/memorials/{slug}.json'
            if os.path.exists(json_path):
                print(f'  SKIP {iwm_id}: slug {slug} already exists as JSON')
                continue

            # Insert to DB
            sql = f"""
                INSERT INTO memorials (slug, title, county, country, source_url, source_id, status, data_quality)
                VALUES ('{slug.replace("'", "''")}', '{title.replace("'", "''")}', '{county}', '{country}',
                        '{url}', 'iwm-{iwm_id}', 'candidate', 'Stub')
                ON CONFLICT (slug) DO NOTHING;
            """
            db_exec(sql)
            inserted += 1
            time.sleep(2)

        except Exception as e:
            print(f'  Error fetching {iwm_id}: {e}')
            continue

    print(f'\nInserted {inserted} new candidates to DB')


def classify_candidates(limit=50):
    """Scope-classify candidates using Claude Haiku."""
    # Get unclassified candidates
    rows = db_query(f"""
        SELECT id, slug, title, source_url
        FROM memorials
        WHERE status = 'candidate' AND scope IS NULL
        ORDER BY id
        LIMIT {limit}
    """)

    if not rows:
        print('No unclassified candidates found')
        return

    candidates = []
    for line in rows.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 4:
            candidates.append({
                'id': parts[0].strip(),
                'slug': parts[1].strip(),
                'title': parts[2].strip(),
                'source_url': parts[3].strip(),
            })

    print(f'Classifying {len(candidates)} candidates...')

    for c in candidates:
        title = c['title']

        # Quick keyword classification first — no need for Claude on obvious cases
        title_lower = title.lower()
        if any(w in title_lower for w in ['bomber command', 'lancaster', 'halifax', 'wellington',
                                           'stirling', 'mosquito', 'hampden', 'whitley', 'b-17',
                                           'b-24', 'liberator', 'flying fortress']):
            scope = 'bomber-command'
            method = 'keyword'
        elif any(w in title_lower for w in ['fighter', 'spitfire', 'hurricane', 'typhoon', 'tempest']):
            scope = 'fighter-command'
            method = 'keyword'
        elif any(w in title_lower for w in ['coastal', 'sunderland', 'catalina', 'hudson patrol']):
            scope = 'coastal-command'
            method = 'keyword'
        elif 'general war memorial' in title_lower or 'cenotaph' in title_lower:
            scope = 'general-memorial'
            method = 'keyword'
        else:
            # Ambiguous — use Claude Haiku
            try:
                result = subprocess.run(
                    ['bun', INFERENCE_TOOL, '--level', 'fast', '--timeout', '15000',
                     'Classify this WW2 memorial. Reply with ONLY one of: bomber-command, fighter-command, coastal-command, training-command, transport-command, general-memorial, unknown. No explanation.',
                     f'Memorial title: {title}'],
                    capture_output=True, text=True, timeout=20
                )
                scope = result.stdout.strip().lower().replace(' ', '-')
                if scope not in ('bomber-command', 'fighter-command', 'coastal-command',
                                 'training-command', 'transport-command', 'general-memorial'):
                    scope = 'unknown'
                method = 'claude-haiku'
            except:
                scope = 'unknown'
                method = 'timeout'

        # Update DB
        db_exec(f"UPDATE memorials SET scope = '{scope}' WHERE id = {c['id']}")
        print(f'  [{c["slug"][:40]}] → {scope} ({method})')

    # Summary
    print('\nClassification complete. Status:')
    status = db_query("""
        SELECT scope, COUNT(*) FROM memorials
        WHERE status = 'candidate'
        GROUP BY scope ORDER BY COUNT(*) DESC
    """)
    if status:
        for line in status.strip().split('\n'):
            print(f'  {line}')


def show_status():
    """Show current pipeline status."""
    print('BMR Candidate Pipeline Status')
    print('=' * 40)

    status = db_query("""
        SELECT status, scope, COUNT(*)
        FROM memorials
        GROUP BY status, scope
        ORDER BY status, scope
    """)
    if status:
        for line in status.strip().split('\n'):
            print(f'  {line}')

    print()
    total = db_query("SELECT COUNT(*) FROM memorials")
    production = db_query("SELECT COUNT(*) FROM memorials WHERE status = 'production'")
    candidates = db_query("SELECT COUNT(*) FROM memorials WHERE status = 'candidate'")
    bomber_scope = db_query("SELECT COUNT(*) FROM memorials WHERE status = 'candidate' AND scope = 'bomber-command'")
    print(f'Total in DB: {total}')
    print(f'Production: {production}')
    print(f'Candidates: {candidates}')
    print(f'Bomber Command scope candidates: {bomber_scope}')


def main():
    if '--status' in sys.argv:
        show_status()
    elif '--source' in sys.argv and 'iwm' in sys.argv and '--fetch' in sys.argv:
        fetch_iwm_candidates()
    elif '--classify' in sys.argv:
        limit = 50
        for i, arg in enumerate(sys.argv):
            if arg == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
        classify_candidates(limit)
    elif '--generate-stubs' in sys.argv:
        print('Stub generation not yet implemented — run --classify first')
    else:
        print('Usage:')
        print('  --source iwm --fetch     Fetch candidates from IWM')
        print('  --classify [--limit N]   Scope-classify candidates')
        print('  --generate-stubs         Generate memorial stubs for in-scope candidates')
        print('  --status                 Show pipeline status')


if __name__ == '__main__':
    main()
