#!/usr/bin/env python3
"""
BMR Layer 1 — Classify all memorials into crash type categories.

Uses structured data (operation_type, cause_of_loss, crew_summary, narrative)
to assign each memorial a crash_category and narrative_quality score.

Categories:
  - operational-combat: Shot down by flak/fighters during bombing raid
  - operational-return: Crashed on return from operations (weather, damage, fuel)
  - training: OTU/HCU/LFS training accidents
  - mid-air-collision: Formation flying, circuit, or night collision
  - weather: Fog, icing, cloud — primary cause was weather
  - mechanical: Engine failure, structural failure
  - takeoff-landing: Crashed on takeoff or approach/landing
  - ferry-transport: Delivery/ferry/VIP flights
  - general-memorial: Not a specific crash — commemorative memorial
  - unknown: Insufficient data to classify

Also scores narrative quality 0-5:
  0: No narrative
  1: Fragment or meta-description
  2: Basic facts only (date, type, serial)
  3: Decent factual account
  4: Good — has cause, crew, context
  5: Excellent — Farnsfield quality (human story, depth, tight prose)

Run: python3 scripts/classify-crash-types.py [--apply] [--report]
"""

import json
import glob
import os
import sys
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
apply_changes = '--apply' in sys.argv
report_mode = '--report' in sys.argv


def classify_crash_type(d):
    """Classify a memorial into a crash type category."""
    op_type = (d.get('operation_type') or '').strip().lower()
    cause = (d.get('cause_of_loss') or '').strip().lower()
    title = (d.get('title') or '').lower()
    narr = (d.get('narrative') or '').lower()
    crew_summary = (d.get('crew_summary') or '').lower()
    squadron = (d.get('squadron') or '').lower()
    combined = f"{op_type} {cause} {title} {narr[:500]} {crew_summary}"

    # General memorials (not a specific crash)
    if any(x in title for x in ['general memorial', 'bomber command memorial', 'museum', 'gateway']):
        return 'general-memorial'
    if 'memorial to' in title and 'crash' not in title and len(d.get('crew', [])) == 0:
        return 'general-memorial'

    # Mid-air collision
    if 'collision' in combined or 'mid-air' in combined:
        return 'mid-air-collision'

    # Training
    training_signals = ['training', 'otu', 'hcu', 'lfs', 'conversion unit', 'finishing school',
                        'practice', 'cross-country', 'navigation exercise', 'circuit']
    if any(x in combined for x in training_signals):
        return 'training'
    # Squadron-based training detection
    if any(x in squadron for x in ['otu', 'hcu', 'lfs', 'conversion', 'training']):
        return 'training'

    # Weather primary cause
    weather_signals = ['fog', 'icing', 'cloud', 'visibility', 'weather', 'black thursday',
                       'night of the fog', 'lost in cloud', 'low cloud']
    if any(x in cause for x in weather_signals):
        return 'weather'
    if any(x in combined for x in ['thick fog', 'dense fog', 'freezing fog', 'iced up', 'lost in cloud']):
        return 'weather'

    # Mechanical failure
    mech_signals = ['engine fail', 'engine fire', 'mechanical', 'structural', 'broke up',
                    'disintegrat', 'undercarriage', 'propeller', 'hydraulic']
    if any(x in cause for x in mech_signals):
        return 'mechanical'
    if any(x in combined for x in ['engine caught fire', 'engine failed', 'mechanical failure']):
        return 'mechanical'

    # Operational — combat
    combat_signals = ['shot down', 'flak', 'fighter', 'night fighter', 'anti-aircraft',
                      'enemy fire', 'intercepted', 'intruder', 'luftwaffe']
    if any(x in combined for x in combat_signals):
        return 'operational-combat'

    # Operational — return from ops
    ops_return_signals = ['return from', 'returning from', 'on return', 'homeward',
                          'ran out of fuel', 'diverted']
    if any(x in combined for x in ops_return_signals):
        return 'operational-return'

    # Operational — general (bombing, raid, target mentioned)
    ops_signals = ['bombing', 'raid', 'target', 'sortie', 'berlin', 'operation',
                   'ops', 'operational', 'attacking']
    if any(x in op_type for x in ['operational', 'bombing', 'raid']):
        return 'operational-combat'
    if any(x in combined for x in ops_signals):
        return 'operational-combat'

    # Takeoff/landing
    to_land_signals = ['takeoff', 'take off', 'taking off', 'landing', 'approach',
                       'overshoot', 'circuit', 'runway', 'undershot']
    if any(x in combined for x in to_land_signals):
        return 'takeoff-landing'

    # Ferry/transport
    ferry_signals = ['ferry', 'delivery', 'transport', 'vip', 'passenger']
    if any(x in combined for x in ferry_signals):
        return 'ferry-transport'

    return 'unknown'


def score_narrative_quality(d):
    """Score narrative quality 0-5."""
    narr = (d.get('narrative') or '').strip()

    if not narr:
        return 0

    if len(narr) < 100:
        return 1

    # Check for meta-descriptions
    if re.match(r'^(The text|This content)', narr, re.I):
        return 1

    score = 2  # Has some content

    # Check for specific elements that make a good narrative
    has_crew_names = bool(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', narr))
    has_cause = bool(re.search(r'engine|fire|flak|fog|collision|weather|mechanical|shot down', narr, re.I))
    has_outcome = bool(re.search(r'killed|survived|bailed|died|lost|perished|rescued', narr, re.I))
    has_human_detail = bool(re.search(r'youngest|oldest|aged \d|year.?old|married|wife|son of|family|home|village', narr, re.I))
    has_mission_context = bool(re.search(r'squadron|mission|operation|target|raid|training|exercise', narr, re.I))
    has_location = bool(re.search(r'crashed (at|near|into)|came down|struck|hit the', narr, re.I))

    if has_cause: score += 0.5
    if has_outcome: score += 0.5
    if has_crew_names: score += 0.5
    if has_mission_context: score += 0.5
    if has_human_detail: score += 0.5
    if has_location: score += 0.5

    # Length bonus
    if 400 < len(narr) < 1500:
        score += 0.5  # Good length — not too short, not a dump

    # Cap at 5
    return min(5, round(score))


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    if not files:
        print(f'ERROR: No memorial files found in {DATA_DIR}')
        sys.exit(1)

    results = []
    type_counts = {}
    quality_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    changes = 0

    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)

        slug = data.get('id', os.path.basename(filepath).replace('.json', ''))
        crash_type = classify_crash_type(data)
        quality = score_narrative_quality(data)

        type_counts[crash_type] = type_counts.get(crash_type, 0) + 1
        quality_counts[quality] = quality_counts.get(quality, 0) + 1

        existing_type = data.get('crash_category', '')
        existing_quality = data.get('narrative_quality_score')

        if apply_changes:
            if data.get('crash_category') != crash_type or data.get('narrative_quality_score') != quality:
                data['crash_category'] = crash_type
                data['narrative_quality_score'] = quality
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                changes += 1

        results.append({
            'slug': slug,
            'crash_type': crash_type,
            'quality': quality,
            'narr_len': len(data.get('narrative', '') or ''),
            'crew': len(data.get('crew', [])),
            'has_cause': bool(data.get('cause_of_loss')),
            'has_ext_narr': len(data.get('external_narratives', [])),
        })

    # Summary
    print()
    print('BMR Crash Type Classification — Layer 1')
    print('=' * 55)
    print()

    print('Crash Type Distribution:')
    for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = '█' * (count // 2) + ('▌' if count % 2 else '')
        print(f'  {ct:25s} {count:3d} {bar}')
    print()

    print('Narrative Quality Distribution:')
    labels = {0: 'Empty', 1: 'Fragment', 2: 'Basic facts', 3: 'Decent', 4: 'Good', 5: 'Excellent'}
    for q in range(6):
        count = quality_counts[q]
        bar = '█' * (count // 2) + ('▌' if count % 2 else '')
        print(f'  {q} ({labels[q]:12s}) {count:3d} {bar}')
    print()

    if apply_changes:
        print(f'Applied: {changes} files updated with crash_category + narrative_quality_score')
    else:
        print('Dry run — use --apply to write crash_category and narrative_quality_score to files')

    # Detailed report
    if report_mode:
        print()
        print('=' * 55)
        print('DETAILED REPORT BY CRASH TYPE')
        print('=' * 55)
        for ct in sorted(type_counts.keys()):
            items = [r for r in results if r['crash_type'] == ct]
            print(f'\n--- {ct} ({len(items)} memorials) ---')

            # Quality breakdown
            q_breakdown = {}
            for item in items:
                q_breakdown[item['quality']] = q_breakdown.get(item['quality'], 0) + 1

            print(f'  Quality: ' + ', '.join(f'{labels[q]}={c}' for q, c in sorted(q_breakdown.items())))

            # Prioritise: which need narrative improvement?
            needs_work = [r for r in items if r['quality'] <= 2]
            if needs_work:
                print(f'  Needs narrative work ({len(needs_work)}):')
                for r in sorted(needs_work, key=lambda x: x['quality']):
                    enrichable = 'ext_narr' if r['has_ext_narr'] > 0 else 'data_only'
                    print(f'    Q{r["quality"]} {r["slug"]} (crew={r["crew"]}, {enrichable}, {r["has_ext_narr"]} links)')


if __name__ == '__main__':
    main()
