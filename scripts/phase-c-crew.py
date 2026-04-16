#!/usr/bin/env python3
"""Phase C addendum — merge crew claims with rank/role into memorial JSONs."""

import json, glob, os, sys, re
import psycopg2

MEMORIALS_DIR = 'public/data/memorials'
DRY_RUN = '--dry-run' in sys.argv

def connect():
    with open('/root/.claude/PAI/USER/CREDENTIALS/bmr-research-db.env') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
    return psycopg2.connect(
        host=os.environ['BMR_DB_HOST'], port=int(os.environ['BMR_DB_PORT']),
        dbname=os.environ['BMR_DB_NAME'], user=os.environ['BMR_DB_USER'],
        password=os.environ['BMR_DB_PASSWORD'])

def normalize_name(name):
    """Normalize for matching: lowercase, strip punctuation, initials expanded."""
    n = name.lower().strip()
    n = re.sub(r'[,.\-\(\)]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    # Handle "Surname, First" -> "first surname"
    parts = n.split()
    return ' '.join(parts)

def find_matching_crew(existing_crew, claim_name):
    """Find existing crew member that matches the claim name."""
    cn = normalize_name(claim_name)
    cn_parts = cn.split()
    if not cn_parts:
        return None

    for i, c in enumerate(existing_crew):
        en = normalize_name(c.get('name', ''))
        en_parts = en.split()

        # Exact match
        if cn == en:
            return i

        # Surname match (last word)
        if cn_parts and en_parts:
            # Check if any surname matches
            claim_surname = cn_parts[-1] if len(cn_parts) > 1 else cn_parts[0]
            existing_surname = en_parts[-1] if len(en_parts) > 1 else en_parts[0]
            if claim_surname == existing_surname and len(claim_surname) > 2:
                return i

            # Also check first word as surname (for "Surname, First" format)
            if cn_parts[0] == existing_surname and len(cn_parts[0]) > 2:
                return i
            if en_parts[0] == cn_parts[-1] and len(en_parts[0]) > 2:
                return i

    return None

def main():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT slug, id FROM memorials")
    slug_to_id = {r[0]: r[1] for r in cur.fetchall()}

    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))
    stats = {'modified': 0, 'crew_upgraded': 0, 'crew_added': 0, 'crew_name_improved': 0}

    for filepath in files:
        slug = os.path.basename(filepath).replace('.json', '')
        mem_id = slug_to_id.get(slug)
        if not mem_id:
            continue

        with open(filepath) as f:
            memorial = json.load(f)

        existing_crew = memorial.get('crew', [])

        # Get crew claims with rank/role in context
        cur.execute("""
            SELECT field_value, field_context FROM claims
            WHERE memorial_id = %s AND field_name = 'crew_member'
            AND confidence IN ('probable', 'verified')
            AND field_context IS NOT NULL
            AND (field_context->>'rank' IS NOT NULL AND field_context->>'rank' != ''
                 AND field_context->>'rank' != 'null')
        """, (mem_id,))
        claims = cur.fetchall()

        if not claims:
            continue

        changed = False
        for val, ctx in claims:
            if not isinstance(ctx, dict):
                continue

            rank = (ctx.get('rank') or '').strip()
            role = (ctx.get('role') or '').strip()
            name = ctx.get('name') or val
            fate = (ctx.get('fate') or '').strip()
            age = ctx.get('age')
            nationality = (ctx.get('nationality') or '').strip()
            burial = (ctx.get('burial_location') or '').strip()

            if not name or name in ('UNKNOWN', 'unknown', 'null'):
                continue
            # Skip mangled names (truncated by scraping)
            if len(name) < 3 or name.endswith('\\'):
                continue

            # Try to match with existing crew
            match_idx = find_matching_crew(existing_crew, name)

            if match_idx is not None:
                # Upgrade existing crew member
                c = existing_crew[match_idx]
                upgraded = False

                # Upgrade name if we have a fuller version
                if len(name) > len(c.get('name', '')) and not name.startswith('['):
                    c['name'] = name
                    stats['crew_name_improved'] += 1
                    upgraded = True

                # Add rank if missing or was "—"
                if rank and (not c.get('rank') or c['rank'] == '—'):
                    c['rank'] = rank
                    upgraded = True

                # Add role if missing
                if role and not c.get('role'):
                    c['role'] = role
                    upgraded = True

                # Add age if missing
                if age and not c.get('age'):
                    c['age'] = int(age) if str(age).isdigit() else None
                    upgraded = True

                # Add nationality if missing
                if nationality and not c.get('nationality'):
                    c['nationality'] = nationality
                    upgraded = True

                # Add burial if missing
                if burial and not c.get('burial_location'):
                    c['burial_location'] = burial
                    upgraded = True

                if upgraded:
                    stats['crew_upgraded'] += 1
                    changed = True

            else:
                # New crew member not in existing array
                new_crew = {
                    'name': name,
                    'rank': rank or '—',
                    'fate': fate.capitalize() if fate else 'Unknown',
                }
                if role:
                    new_crew['role'] = role
                if age and str(age).isdigit():
                    new_crew['age'] = int(age)
                if nationality:
                    new_crew['nationality'] = nationality
                if burial:
                    new_crew['burial_location'] = burial

                existing_crew.append(new_crew)
                stats['crew_added'] += 1
                changed = True

        if changed:
            memorial['crew'] = existing_crew
            stats['modified'] += 1
            if not DRY_RUN:
                with open(filepath, 'w') as f:
                    json.dump(memorial, f, indent=2)
            print(f'  ✓ {slug}: +{sum(1 for _ in claims)} claims processed')

    conn.close()

    print(f'\n{"="*60}')
    print(f'CREW ENRICHMENT COMPLETE')
    print(f'{"="*60}')
    for k, v in stats.items():
        print(f'  {k}: {v}')
    if DRY_RUN:
        print('  --dry-run: no files written')

if __name__ == '__main__':
    main()
