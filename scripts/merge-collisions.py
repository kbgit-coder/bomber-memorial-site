#!/usr/bin/env python3
"""
BMR Collision Merge — merges split collision pages into single Cloot Drove pattern pages.

Each collision becomes a single memorial page with:
- Combined title referencing both aircraft
- Merged crew with aircraft serial in role field: "Pilot (JB874)"
- Combined narratives, community, remembrance
- Deduplicated external narratives and sources
- Old split files removed

Run: python3 scripts/merge-collisions.py [--dry-run]
"""

import json
import os
import sys
import copy

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
dry_run = '--dry-run' in sys.argv

# ── Collision definitions ────────────────────────────────────────────
# Each collision: output_slug, title, files with serials

COLLISIONS = [
    {
        'output_slug': 'balkholme-halifax-mid-air-collision',
        'title': 'Balkholme Halifax Mid-Air Collision Memorial',
        'aircraft_type': 'Halifax III',
        'files': [
            ('balkholme-1-lk834.json', 'LK834'),
            ('balkholme-2-mz696.json', 'MZ696'),
        ],
    },
    {
        'output_slug': 'carleton-rode-b-24-mid-air-collision',
        'title': 'Carleton Rode B-24 Mid-Air Collision Memorial',
        'aircraft_type': 'B-24 Liberator',
        'files': [
            ('carleton-rode-1-b-24-44-10513-old-gl.json', '44-10513 "Old Glory"'),
            ('carleton-rode-2-b-24-42-50452-earthq.json', '42-50452 "Earthquake McGoon"'),
        ],
    },
    {
        'output_slug': 'hull-bridge-halifax-mid-air-collision',
        'title': 'Hull Bridge Halifax Mid-Air Collision Memorial',
        'aircraft_type': 'Halifax II',
        'files': [
            ('hull-bridge-1-jb874.json', 'JB874'),
            ('hull-bridge-2-bb373.json', 'BB373'),
        ],
    },
    {
        'output_slug': 'waithe-lancaster-mid-air-collision',
        'title': 'Waithe Lancaster Mid-Air Collision Memorial',
        'aircraft_type': 'Lancaster',
        'files': [
            ('waithe-1-jb678.json', 'JB678'),
            ('waithe-2-jb674.json', 'JB674'),
            ('waithe-4-jb560.json', 'JB560'),
        ],
    },
    {
        'output_slug': 'ulceby-lancaster-mid-air-collision',
        'title': 'Ulceby Lancaster Mid-Air Collision Memorial',
        'aircraft_type': 'Lancaster',
        'files': [
            ('ulceby-1-jb670.json', 'JB670'),
            ('ulceby-2-lm322.json', 'LM322'),
        ],
    },
]


def merge_text_fields(values, separator='\n\n'):
    """Merge multiple text values, deduplicating."""
    seen = set()
    parts = []
    for v in values:
        if not v or not v.strip():
            continue
        normalized = v.strip()
        if normalized not in seen:
            seen.add(normalized)
            parts.append(normalized)
    return separator.join(parts) if parts else ''


def merge_lists(lists, dedup_key=None):
    """Merge multiple lists, optionally deduplicating by a key."""
    if dedup_key:
        seen = set()
        result = []
        for lst in lists:
            for item in (lst or []):
                key = item.get(dedup_key, '') if isinstance(item, dict) else str(item)
                if key and key not in seen:
                    seen.add(key)
                    result.append(item)
                elif not key:
                    result.append(item)
        return result
    else:
        result = []
        for lst in lists:
            result.extend(lst or [])
        return result


def tag_crew_with_serial(crew, serial):
    """Add aircraft serial to crew role field: 'Pilot' → 'Pilot (JB874)'."""
    tagged = []
    for c in crew:
        c = copy.deepcopy(c)
        role = (c.get('role') or '').strip()
        if role:
            c['role'] = f'{role} ({serial})'
        else:
            c['role'] = f'Crew ({serial})'
        tagged.append(c)
    return tagged


def dedupe_crew(crew_list):
    """Remove duplicate crew entries (same name across aircraft).
    Keep the entry with more data (rank, role, age etc).
    """
    by_name = {}
    result = []
    for c in crew_list:
        name = (c.get('name') or '').strip().lower()
        if not name or name == 'unknown':
            result.append(c)
            continue

        if name in by_name:
            existing = by_name[name]
            # Score: count non-empty fields
            def score(entry):
                s = 0
                for k in ['rank', 'role', 'age', 'nationality', 'burial_location', 'fate_detail', 'bio', 'service_number']:
                    if entry.get(k):
                        s += 1
                return s
            if score(c) > score(existing):
                # Replace with better entry, but keep the serial tag from both
                existing_role = existing.get('role', '')
                new_role = c.get('role', '')
                # Combine aircraft references
                result = [x if x is not existing else c for x in result]
                by_name[name] = c
        else:
            by_name[name] = c
            result.append(c)

    return result


def merge_remembrance(values):
    """Merge remembrance data which can be string, list of events, or object."""
    events = []
    texts = []
    for v in values:
        if not v:
            continue
        if isinstance(v, list):
            events.extend(v)
        elif isinstance(v, dict):
            # Object with events key or text
            if 'events' in v:
                events.extend(v['events'])
            if 'text' in v:
                texts.append(v['text'])
        elif isinstance(v, str) and v.strip():
            texts.append(v.strip())

    # Dedupe events by name
    seen_names = set()
    unique_events = []
    for e in events:
        if isinstance(e, dict):
            name = e.get('name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                unique_events.append(e)
            elif not name:
                unique_events.append(e)
        else:
            unique_events.append(e)

    if unique_events and texts:
        return {'events': unique_events, 'text': merge_text_fields(texts)}
    elif unique_events:
        return unique_events
    elif texts:
        return merge_text_fields(texts)
    return None


def merge_collision(collision_def):
    """Merge a collision's source files into a single memorial."""
    sources = []
    for filename, serial in collision_def['files']:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f'  WARNING: {filename} not found, skipping')
            continue
        with open(filepath) as f:
            data = json.load(f)
        sources.append((data, serial))

    if not sources:
        return None

    # Start from first source as base
    base = copy.deepcopy(sources[0][0])

    # Set merged identity
    base['id'] = collision_def['output_slug']
    base['title'] = collision_def['title']
    base['aircraft_type'] = collision_def['aircraft_type']

    # Merge squadrons
    squadrons = list(set(
        (s[0].get('squadron') or '').strip()
        for s in sources
        if (s[0].get('squadron') or '').strip()
    ))
    base['squadron'] = ' / '.join(sorted(squadrons)) if len(squadrons) > 1 else (squadrons[0] if squadrons else '')

    # Merge narratives
    narratives = [(s[0].get('narrative') or '').strip() for s in sources]
    base['narrative'] = merge_text_fields(narratives)

    # Merge community_connection
    communities = [(s[0].get('community_connection') or '').strip() for s in sources]
    base['community_connection'] = merge_text_fields(communities)

    # Merge remembrance
    remembrances = [s[0].get('remembrance') for s in sources]
    merged_remembrance = merge_remembrance(remembrances)
    if merged_remembrance:
        base['remembrance'] = merged_remembrance
    elif 'remembrance' in base:
        del base['remembrance']

    # Merge and tag crew
    all_crew = []
    for data, serial in sources:
        tagged = tag_crew_with_serial(data.get('crew', []), serial)
        all_crew.extend(tagged)
    base['crew'] = dedupe_crew(all_crew)

    # Update crew_summary
    killed = sum(1 for c in base['crew'] if (c.get('fate') or '').lower() == 'killed')
    survived = sum(1 for c in base['crew'] if (c.get('fate') or '').lower() == 'survived')
    total = len(base['crew'])
    summary_parts = [f'{total} crew recorded']
    if killed:
        summary_parts.append(f'{killed} killed')
    if survived:
        summary_parts.append(f'{survived} survived')
    base['crew_summary'] = '; '.join(summary_parts)

    # Merge external narratives (dedupe by url)
    ext_narrs = merge_lists(
        [s[0].get('external_narratives', []) for s in sources],
        dedup_key='url'
    )
    base['external_narratives'] = ext_narrs

    # Merge sources (dedupe by name)
    all_sources = merge_lists(
        [s[0].get('sources', []) for s in sources],
        dedup_key='name'
    )
    base['sources'] = all_sources

    # Merge memorial_details
    all_details = [s[0].get('memorial_details') for s in sources if s[0].get('memorial_details')]
    if all_details:
        base['memorial_details'] = all_details[0]  # Take the most detailed
        for d in all_details[1:]:
            if isinstance(d, dict) and isinstance(base['memorial_details'], dict):
                for k, v in d.items():
                    if k not in base['memorial_details'] or not base['memorial_details'][k]:
                        base['memorial_details'][k] = v

    # Merge photos
    all_photos = merge_lists(
        [s[0].get('photos', []) for s in sources],
        dedup_key='url' if sources[0][0].get('photos') and isinstance(sources[0][0].get('photos', [None])[0], dict) else None
    )
    if all_photos:
        base['photos'] = all_photos

    # Keep best coordinates
    base['latitude'] = sources[0][0].get('latitude')
    base['longitude'] = sources[0][0].get('longitude')

    # Memorial type
    base['memorial_type'] = 'Mid-Air Collision Memorial'

    return base


def main():
    print()
    print('BMR Collision Merge')
    print('=' * 50)
    print(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
    print()

    for collision in COLLISIONS:
        slug = collision['output_slug']
        source_files = [f for f, _ in collision['files']]
        print(f'Merging: {" + ".join(source_files)}')
        print(f'  → {slug}.json')

        merged = merge_collision(collision)
        if not merged:
            print(f'  SKIP: no source files found')
            continue

        print(f'  Title: {merged["title"]}')
        print(f'  Crew: {len(merged.get("crew", []))}')
        print(f'  Squadron: {merged.get("squadron", "")}')
        print(f'  Ext narratives: {len(merged.get("external_narratives", []))}')

        if not dry_run:
            # Write merged file
            output_path = os.path.join(DATA_DIR, f'{slug}.json')
            with open(output_path, 'w') as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
                f.write('\n')
            print(f'  WRITTEN: {output_path}')

            # Remove source files
            for filename, _ in collision['files']:
                source_path = os.path.join(DATA_DIR, filename)
                if os.path.exists(source_path):
                    os.remove(source_path)
                    print(f'  REMOVED: {filename}')

        print()

    # Summary
    total_sources = sum(len(c['files']) for c in COLLISIONS)
    total_merged = len(COLLISIONS)
    net_reduction = total_sources - total_merged
    print(f'Collisions merged: {total_merged}')
    print(f'Source files: {total_sources} → {total_merged} merged files')
    print(f'Net memorial count change: -{net_reduction}')


if __name__ == '__main__':
    main()
