#!/usr/bin/env python3
"""
Phase C — Merge probable/verified claims into memorial JSONs.

Processes: crash_narrative, community_story, remembrance_event, memorial_details,
           annual_service. Skips crew_member (needs IWM Names scrape first for quality),
           aircraft_serial (already displayed), social_media_link (site chrome).

Section relevancy: each claim is placed in the correct page section.
"""

import json, glob, os, sys, time
import psycopg2

MEMORIALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    '..', 'repos', 'bomber-memorial-site', 'public', 'data', 'memorials')
if not os.path.isdir(MEMORIALS_DIR):
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

def is_sentence_community(text):
    """Check if text is about the community/memorial, not the crash or crew."""
    t = text.lower()
    community_kw = ['erected', 'dedicated', 'unveiled', 'memorial was', 'funded',
                     'community', 'parish', 'association', 'sculpture', 'plaque',
                     'stone of remembrance', 'maintained', 'restored']
    crash_kw = ['crashed', 'shot down', 'killed', 'raid', 'operation', 'mission',
                'collided', 'took off', 'returned', 'lost']
    comm_score = sum(1 for kw in community_kw if kw in t)
    crash_score = sum(1 for kw in crash_kw if kw in t)
    return comm_score > crash_score

def merge_narrative(memorial, claims):
    """Merge crash_narrative claims — only if better than existing."""
    existing = memorial.get('narrative', '')
    if not claims:
        return False

    # Pick best claim: longest probable narrative that isn't a raw inscription
    best = None
    for val, ctx, src in claims:
        if not val or len(val) < 30:
            continue
        # Skip if it's just a page title or "Not explicitly stated"
        if val.startswith('MLI') or 'Not explicitly' in val:
            continue
        # Skip if ALL CAPS
        upper = sum(1 for c in val if c.isupper() and c.isalpha())
        alpha = sum(1 for c in val if c.isalpha())
        if alpha > 20 and upper / alpha > 0.6:
            continue
        if best is None or len(val) > len(best[0]):
            best = (val, ctx, src)

    if not best:
        return False

    # Only replace if existing is empty, raw inscription, or much shorter
    if existing:
        is_raw = False
        upper = sum(1 for c in existing if c.isupper() and c.isalpha())
        alpha = sum(1 for c in existing if c.isalpha())
        if alpha > 20 and upper / alpha > 0.6:
            is_raw = True

        # Don't replace a good narrative with a shorter one
        if not is_raw and len(existing) >= len(best[0]) * 0.8:
            return False

    memorial['narrative'] = best[0]
    return True

def merge_community(memorial, claims):
    """Merge community_story claims — sentence-level relevancy check."""
    if not claims or memorial.get('community_connection'):
        return False

    # Filter to only community-relevant sentences
    community_parts = []
    for val, ctx, src in claims:
        if not val or len(val) < 20:
            continue
        # Split into sentences, keep only community-relevant ones
        sentences = [s.strip() for s in val.replace('. ', '.\n').split('\n') if s.strip()]
        for sent in sentences:
            if is_sentence_community(sent) and len(sent) > 20:
                community_parts.append(sent)

    if not community_parts:
        return False

    # Dedupe and join (max 3 sentences)
    seen = set()
    unique = []
    for p in community_parts:
        key = p[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    text = ' '.join(unique[:3])
    if not text.endswith('.'):
        text += '.'

    memorial['community_connection'] = text
    return True

def merge_remembrance(memorial, claims):
    """Merge remembrance_event claims."""
    if not claims:
        return False

    existing = memorial.get('remembrance', {})
    events = existing.get('events', []) if existing else []
    existing_names = {e.get('name', '').lower() for e in events}

    added = 0
    for val, ctx, src in claims:
        if not val:
            continue
        ctx = ctx if isinstance(ctx, dict) else {}
        name = val
        if name.lower() in existing_names or 'dedication' in name.lower() and any('dedication' in n for n in existing_names):
            continue
        events.append({
            'name': name,
            'date': ctx.get('date'),
            'description': ctx.get('description'),
        })
        existing_names.add(name.lower())
        added += 1

    if added == 0:
        return False

    memorial['remembrance'] = {
        **(existing or {}),
        'events': events,
    }
    return True

def merge_memorial_details(memorial, claims):
    """Merge memorial_details claims into The Memorial section fields."""
    if not claims:
        return False

    changed = False
    for val, ctx, src in claims:
        if not val:
            continue
        val_lower = val.lower()

        # Parse structured memorial_details values
        lines = val.split('\n')
        for line in lines:
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if not value:
                continue

            if key == 'type' and not memorial.get('memorial_type'):
                memorial['memorial_type'] = value
                changed = True
            elif key == 'description' and not memorial.get('memorial_description'):
                memorial['memorial_description'] = value
                changed = True
            elif key == 'name' and not memorial.get('memorial_name'):
                memorial['memorial_name'] = value
                changed = True

    return changed

def merge_annual_service(memorial, claims):
    """Set annual_service flag on remembrance."""
    if not claims:
        return False
    existing = memorial.get('remembrance', {}) or {}
    if existing.get('annual_service'):
        return False

    for val, ctx, src in claims:
        if val and val.lower() == 'true':
            memorial['remembrance'] = {
                **existing,
                'annual_service': True,
                'service_date': (ctx or {}).get('date'),
            }
            return True
    return False

def main():
    conn = connect()
    cur = conn.cursor()

    # Load slug -> memorial_id mapping
    cur.execute("SELECT slug, id FROM memorials")
    slug_to_id = {r[0]: r[1] for r in cur.fetchall()}

    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))

    stats = {'modified': 0, 'narratives': 0, 'community': 0,
             'remembrance': 0, 'memorial_details': 0, 'annual': 0,
             'claims_accepted': 0}

    for filepath in files:
        slug = os.path.basename(filepath).replace('.json', '')
        mem_id = slug_to_id.get(slug)
        if not mem_id:
            continue

        with open(filepath) as f:
            memorial = json.load(f)

        changed = False

        # Get claims by type
        for field_name, merge_fn, stat_key in [
            ('crash_narrative', merge_narrative, 'narratives'),
            ('community_story', merge_community, 'community'),
            ('remembrance_event', merge_remembrance, 'remembrance'),
            ('memorial_details', merge_memorial_details, 'memorial_details'),
            ('annual_service', merge_annual_service, 'annual'),
        ]:
            cur.execute("""
                SELECT field_value, field_context, source_url
                FROM claims
                WHERE memorial_id = %s AND field_name = %s
                AND confidence IN ('probable', 'verified') AND status = 'pending'
            """, (mem_id, field_name))
            claims = cur.fetchall()

            if claims and merge_fn(memorial, claims):
                changed = True
                stats[stat_key] += 1
                stats['claims_accepted'] += len(claims)

                # Mark claims as accepted
                if not DRY_RUN:
                    cur.execute("""
                        UPDATE claims SET status = 'accepted', reviewed_by = 'phase-c-auto',
                        reviewed_at = NOW()
                        WHERE memorial_id = %s AND field_name = %s
                        AND confidence IN ('probable', 'verified') AND status = 'pending'
                    """, (mem_id, field_name))

        if changed:
            stats['modified'] += 1
            if not DRY_RUN:
                with open(filepath, 'w') as f:
                    json.dump(memorial, f, indent=2)
            print(f'  ✓ {slug}')

    if not DRY_RUN:
        conn.commit()
    conn.close()

    print(f'\n{"="*60}')
    print(f'PHASE C COMPLETE')
    print(f'{"="*60}')
    for k, v in stats.items():
        print(f'  {k}: {v}')
    if DRY_RUN:
        print('  --dry-run: no files or DB written')

if __name__ == '__main__':
    main()
