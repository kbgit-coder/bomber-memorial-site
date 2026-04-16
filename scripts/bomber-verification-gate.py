#!/usr/bin/env python3
"""
BMR Bomber Verification Gate — GATE 0 (before all other gates)
Verifies every memorial JSON is actually a WW2 bomber crash memorial.
Catches false positives from town/surname matches (Halifax, Lancaster, etc.)

This gate must pass before schema validation, QA scan, or deploy.

Usage: python3 scripts/bomber-verification-gate.py [--fix]
  --fix: automatically remove false positives (move to rejected/)

Exit code 0 = all pass, 1 = false positives found.

SET NEW STANDARDS.
"""

import json
import os
import re
import shutil
import sys

FIX_MODE = '--fix' in sys.argv
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')
REJECTED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rejected-memorials')

# Town names / surnames that are also WW2 aircraft type names
AMBIGUOUS_NAMES = [
    'halifax', 'wellington', 'hampden', 'lancaster', 'stirling',
    'manchester', 'whitley', 'blenheim', 'sunderland',
]

# === NEGATIVE SIGNALS: NOT a bomber memorial ===
NOT_BOMBER_PATTERNS = [
    # Wrong war
    r'\bww1\b', r'world war 1', r'first world war', r'\bgreat war\b', r'1914.?1918',
    r'boer war', r'south african war', r'korean war', r'falklands', r'crimean war',
    r'afghanistan', r'iraq war', r'gulf war',
    # Army / Navy (not RAF)
    r'\b(?:pte|private|corporal|cpl|lance corporal|rifleman|guardsman|trooper|gunner|sapper|bombardier)\b(?!.*(?:raf|bomber|aircraft|crash))',
    r'\b(?:regiment|fusiliers|infantry|battalion|yeomanry|dragoon|hussars|lancers)\b',
    r'\b(?:royal navy|merchant navy|marines|commando)\b(?!.*air)',
    r'\b(?:artillery|sappers|royal engineers|signals)\b',
    # Religious / civic buildings (war memorials in churches/schools)
    r'(?:wesleyan|methodist|baptist|congregational|presbyterian|catholic|rc)\s+church.*(?:ww[12i]|war|memorial)',
    r'(?:church|chapel|parish|cathedral).*(?:ww[12i]|war memorial)',
    r'(?:grammar school|high school|academy).*ww[12i]',
    # Generic war memorials
    r'(?:bowling club|cricket club|rugby|football club|athletic club)',
    r'roll of honour.*(?:parish|church|school|company|firm|works|factory)',
    r'\bcenotaph\b', r'\bwar memorial$', r'\bbook of remembrance\b',
    r'parishioners.*ww[12]',
    # Famous non-bomber people/places
    r'duke of wellington', r'duke of lancaster', r'earl of halifax',
    r'wellington barracks', r'wellington monument', r'wellington arch',
    r'lancaster house', r'lancaster gate', r'stirling castle',
    # Non-memorial structures
    r'(?:ira bombing|restoration|hotel patrons)',
    r'(?:boy scouts|girl guides|ambulance brigade|constabulary|police)',
    r'(?:postal workers|co-operative|ltd of)',
]

# === POSITIVE SIGNALS: IS a bomber memorial ===
IS_BOMBER_PATTERNS = [
    # Aircraft manufacturers
    r'(?:avro|handley page|vickers|short|de havilland|boeing|consolidated|armstrong whitworth|fairey)',
    # Explicit bomber references
    r'\b(?:bomber|bomber command|pathfinder)\b',
    r'(?:crash|crashed|crash site|crash memorial|crash tree)',
    r'(?:aircrew|air crew|crew of)\b',
    # RAF-specific
    r'\b(?:raf|raaf|rcaf|rnzaf|usaaf|usaac)\b',
    r'(?:squadron|sqdn|sqn)\s*\d',
    r'\d+\s*(?:squadron|sqdn|sqn)',
    # RAF ranks (distinct from army)
    r'(?:pilot officer|flying officer|flight lieutenant|squadron leader|wing commander|group captain)',
    r'(?:flight sergeant|air gunner|navigator|bomb aimer|flight engineer|wireless operator|rear gunner|mid.upper gunner)',
    # Aircraft serial numbers (2 letters + 3-4 digits, or US pattern)
    r'\b[A-Z]{1,2}\d{3,5}\b',
    r'\b\d{2}-\d{4,6}\b',  # US serials
]


def check_memorial(slug, data):
    """Check if a memorial is genuinely a bomber crash memorial.
    Returns (is_valid, confidence, reasons).
    """
    title = data.get('title', '')
    title_lower = title.lower()
    inscription = (data.get('inscription', '') or '').lower()
    narrative = (data.get('narrative', '') or '').lower()
    details = (data.get('memorial_details', '') or '').lower()
    all_text = f"{title_lower} {inscription} {narrative} {details}"

    positive_signals = []
    negative_signals = []

    # Check positive signals
    for pattern in IS_BOMBER_PATTERNS:
        if re.search(pattern, all_text, re.IGNORECASE):
            positive_signals.append(pattern[:40])

    # Check negative signals
    for pattern in NOT_BOMBER_PATTERNS:
        if re.search(pattern, all_text, re.IGNORECASE):
            negative_signals.append(pattern[:40])

    # Check ambiguous name trap
    has_ambiguous_name = False
    for name in AMBIGUOUS_NAMES:
        if name in title_lower:
            has_ambiguous_name = True
            break

    # === DECISION LOGIC ===

    # Strong positive: manufacturer name in title → almost certainly a bomber
    if re.search(r'(?:avro|handley page|vickers|short|de havilland|boeing|consolidated)', title_lower):
        return True, 'high', positive_signals

    # Strong positive: "crash" in title
    if 'crash' in title_lower:
        return True, 'high', positive_signals

    # Strong positive: "crew of" in title
    if 'crew of' in title_lower or 'aircrew' in title_lower:
        return True, 'high', positive_signals

    # Strong positive: "bomber" in title
    if 'bomber' in title_lower:
        return True, 'high', positive_signals

    # Strong positive: squadron number in title
    if re.search(r'\d+\s*(?:squadron|sqdn|sqn)', title_lower):
        return True, 'high', positive_signals

    # If title contains only an ambiguous name and has negative signals → false positive
    if has_ambiguous_name and negative_signals and not positive_signals:
        return False, 'high', negative_signals

    # If title contains ambiguous name, no strong positive, some negative → likely false positive
    if has_ambiguous_name and negative_signals and len(positive_signals) <= 1:
        # The one positive might just be a serial-number-like pattern in an address
        return False, 'medium', negative_signals

    # No ambiguous name, has positives → valid
    if positive_signals and not negative_signals:
        return True, 'high', positive_signals

    # Mixed signals → flag for review
    if positive_signals and negative_signals:
        if len(positive_signals) > len(negative_signals):
            return True, 'low', positive_signals
        else:
            return False, 'low', negative_signals

    # No signals either way — suspicious
    if not positive_signals and not negative_signals:
        return False, 'low', ['no_bomber_indicators']

    return True, 'medium', positive_signals


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  BMR BOMBER VERIFICATION GATE — GATE 0           ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    false_positives = []
    uncertain = []
    confirmed = []

    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith('.json'):
            continue
        slug = fname.replace('.json', '')
        with open(os.path.join(DATA_DIR, fname)) as f:
            data = json.load(f)

        is_valid, confidence, reasons = check_memorial(slug, data)

        if not is_valid and confidence in ('high', 'medium'):
            false_positives.append((slug, confidence, reasons))
        elif not is_valid and confidence == 'low':
            uncertain.append((slug, reasons))
        else:
            confirmed.append(slug)

    total = len(false_positives) + len(uncertain) + len(confirmed)

    print(f"  Scanned:          {total}")
    print(f"  Confirmed bomber: {len(confirmed)}")
    print(f"  FALSE POSITIVES:  {len(false_positives)}")
    print(f"  Uncertain:        {len(uncertain)}")
    print()

    if false_positives:
        print("FALSE POSITIVES (will block deploy):")
        for slug, conf, reasons in false_positives:
            print(f"  ❌ {slug} (confidence={conf})")
            for r in reasons[:2]:
                print(f"     → {r}")

        if FIX_MODE:
            os.makedirs(REJECTED_DIR, exist_ok=True)
            for slug, _, _ in false_positives:
                src = os.path.join(DATA_DIR, f'{slug}.json')
                dst = os.path.join(REJECTED_DIR, f'{slug}.json')
                if os.path.exists(src):
                    shutil.move(src, dst)
            print(f"\n  Moved {len(false_positives)} false positives to {REJECTED_DIR}/")

    if uncertain:
        print(f"\nUNCERTAIN (review recommended, non-blocking):")
        for slug, reasons in uncertain:
            print(f"  ⚠️  {slug}: {', '.join(reasons[:2])}")

    print()
    if false_positives:
        print(f"❌ BOMBER VERIFICATION FAILED — {len(false_positives)} false positive(s) found.")
        print(f"   Run with --fix to remove them, or manually review.")
        return 1
    else:
        print(f"✅ BOMBER VERIFICATION PASSED — all {len(confirmed)} memorials confirmed.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
