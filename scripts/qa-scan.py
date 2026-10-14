#!/usr/bin/env python3
"""
BMR QA Scanner — Full Page Specification Gate
Runs against built HTML in out/ directory. Must PASS before deploy.

Usage: python3 scripts/qa-scan.py [--fix] [--verbose]
Exit code 0 = all gates pass, 1 = failures found.

SET NEW STANDARDS — quality is #1.
"""

import json
import glob
import os
import re
import sys
from html.parser import HTMLParser
from collections import Counter

VERBOSE = '--verbose' in sys.argv
FIX_MODE = '--fix' in sys.argv
MEMORIAL_DIR = os.path.join(os.path.dirname(__file__), '..', 'out', 'memorial')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'out', 'data', 'memorials')
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')


class TextExtractor(HTMLParser):
    """Extract visible text from HTML, excluding script/style tags."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_depth = 0
        self.skip_tags = {'script', 'style', 'noscript'}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip_depth > 0:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)


def extract_visible_text(html):
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()


def check_memorial_page(slug, html, data):
    """Run all QA gates against a single memorial page. Returns list of (severity, message) tuples."""
    issues = []
    text = extract_visible_text(html)

    # ═══════════════════════════════════════════════════════════
    # GATE 1: Page Structure
    # ═══════════════════════════════════════════════════════════

    # 1.1 Page title must be valid
    title_match = re.search(r'<title>(.*?)</title>', html)
    if not title_match:
        issues.append(('CRITICAL', 'No <title> tag found'))
    elif 'Not Found' in title_match.group(1):
        issues.append(('CRITICAL', 'Page title says "Memorial Not Found"'))
    elif len(title_match.group(1)) < 10:
        issues.append(('WARNING', f'Page title suspiciously short: "{title_match.group(1)}"'))

    # 1.2 H1 heading must exist
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if not h1_match:
        issues.append(('CRITICAL', 'No <h1> heading found'))

    # 1.3 No error messages or broken states
    for marker in ['Memorial Not Found', 'Error:', 'Something went wrong']:
        if marker in text:
            issues.append(('CRITICAL', f'Error text found on page: "{marker}"'))

    # ═══════════════════════════════════════════════════════════
    # GATE 2: The Memorial Section
    # ═══════════════════════════════════════════════════════════

    # 2.1 "The Memorial" section must exist
    if 'The Memorial' not in html:
        issues.append(('ERROR', 'Missing "The Memorial" section'))

    # 2.2 Inscription subsection must exist
    if 'Inscription' not in html:
        issues.append(('ERROR', 'Missing Inscription subsection'))

    # 2.3 ALL CAPS inscription text should be converted to title case in rendering
    # Check the rendered HTML inscription block for long ALL CAPS strings
    insc_match = re.search(r'Inscription</div>(.*?)</div>', html, re.DOTALL)
    if insc_match:
        insc_text = re.sub(r'<[^>]+>', '', insc_match.group(1)).strip()
        insc_letters = [c for c in insc_text if c.isalpha()]
        if len(insc_letters) > 20:
            upper_ratio = sum(1 for c in insc_letters if c.isupper()) / len(insc_letters)
            if upper_ratio > 0.7:
                issues.append(('ERROR', f'Inscription still renders as ALL CAPS ({upper_ratio:.0%} uppercase)'))

    # 2.4 No raw placeholders in visible text
    raw_placeholders = [
        (r'\(NAMES?\)', 'Raw (NAMES) placeholder'),
        (r'\(HALFPINT\)', 'Raw (HALFPINT) annotation'),
        (r'\(name\)', 'Raw (name) placeholder'),
    ]
    for pattern, desc in raw_placeholders:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(('ERROR', f'{desc} in visible text'))

    # ═══════════════════════════════════════════════════════════
    # GATE 3: Narrative Quality
    # ═══════════════════════════════════════════════════════════

    narrative = data.get('narrative', '')
    if narrative:
        # 3.1 No article dump markers
        for marker in ['ARTICLE DUMP:', 'SOURCE URL:', '---\n', 'Retrieved from http']:
            if marker in narrative:
                issues.append(('ERROR', f'Raw article dump marker in narrative: "{marker[:30]}"'))

        # 3.2 No raw HTML in narrative
        if re.search(r'<(?:p|div|span|br|table|tr|td|ul|li|ol|h[1-6])\b', narrative):
            issues.append(('WARNING', 'HTML tags found in narrative text'))

        # 3.3 No AI-generated refusal text
        ai_refusals = ['does not explicitly', 'the text does not', 'I cannot', 'As an AI ']
        for phrase in ai_refusals:
            if phrase.lower() in narrative.lower():
                # Verify it's not a false positive like "as an Air Test"
                idx = narrative.lower().find(phrase.lower())
                context = narrative[idx:idx+40]
                if phrase == 'As an AI ' and 'air' in context.lower()[:10]:
                    continue
                issues.append(('ERROR', f'AI refusal/hallucination text in narrative: "{phrase.strip()}"'))

    # ═══════════════════════════════════════════════════════════
    # GATE 4: Community Connection Quality
    # ═══════════════════════════════════════════════════════════

    cc = data.get('community_connection', '')
    if cc:
        ai_refusals = ['does not explicitly', 'the text does not', 'I cannot', 'As an AI', 'no specific']
        for phrase in ai_refusals:
            if phrase.lower() in cc.lower():
                idx = cc.lower().find(phrase.lower())
                context = cc[idx:idx+40]
                if phrase == 'As an AI' and 'air' in context.lower()[:10]:
                    continue
                issues.append(('ERROR', f'AI refusal text in community_connection: "{phrase}"'))

    # ═══════════════════════════════════════════════════════════
    # GATE 5: Crew Data Quality
    # ═══════════════════════════════════════════════════════════

    crew = data.get('crew', [])
    if crew:
        # 5.1 No duplicate crew entries (surname match check)
        names_normalised = []
        for c in crew:
            name = (c.get('name') or '').strip().lower()
            name = re.sub(r'\s+(rafvr|raaf|rnzaf|raf)\s*\([^)]+\)', '', name)
            names_normalised.append(name)

        dupes = {n: c for n, c in Counter(names_normalised).items() if c > 1 and len(n) > 3}
        if dupes:
            for name, count in dupes.items():
                issues.append(('ERROR', f'Duplicate crew entry: "{name}" appears {count} times'))

        # 5.2 Crew names must be actual people (not organisations, regiments, parse errors)
        not_people_patterns = [
            r'regiment', r'fusiliers', r'infantry', r'medical corps', r'history society',
            r'squadron$', r'memorial$', r'church$', r'council$', r'trust$', r'museum$',
            r'association$', r'committee$', r'school$', r'foundation$', r'charity$',
        ]
        for c in crew:
            name = (c.get('name') or '').strip()
            rank = (c.get('rank') or '').strip()
            # Newlines in rank/name = parse error
            if '\n' in rank or '\n' in name:
                issues.append(('ERROR', f'Crew entry has newlines (parse error): rank="{rank[:30]}" name="{name[:30]}"'))
            # Organisation names as crew
            for pattern in not_people_patterns:
                if re.search(pattern, name, re.IGNORECASE) or re.search(pattern, rank, re.IGNORECASE):
                    issues.append(('ERROR', f'Organisation/non-person in crew list: "{name}"'))
                    break
            # Rank is clearly not a military rank (contains multiple words that aren't rank abbreviations)
            if rank and len(rank) > 20 and not any(r in rank.lower() for r in ['sgt','lt','off','cpl','w/o','f/o','p/o','pilot','sergeant','corporal','lieutenant','captain','major','colonel','warrant','flying','wing','group']):
                issues.append(('ERROR', f'Invalid rank (too long, not military): "{rank[:50]}"'))

        # 5.3 No "None" as rank
        for c in crew:
            if c.get('rank') == 'None':
                issues.append(('WARNING', f'Crew member "{c.get("name","?")}" has rank "None"'))

        # 5.3 Rank not duplicated in name (e.g. "Sgt Sgt Smith")
        for c in crew:
            rank = c.get('rank', '')
            name = c.get('name', '')
            if rank and name.startswith(rank + ' '):
                issues.append(('ERROR', f'Rank "{rank}" duplicated in name: "{rank} {name}"'))

        # 5.4 Narrative vs crew fate cross-check
        fates = [c.get('fate', '').lower() for c in crew]
        all_killed = all(f in ('killed', 'kia', 'died', 'lost') for f in fates if f)
        narrative_lower = narrative.lower() if narrative else ''

        if all_killed and len(crew) > 1:
            # Check if narrative mentions actual survivors (not false positives like "no survivors" or "aircraft survived")
            false_positive_patterns = [
                r'no\s+survivors', r'none\s+(?:of\s+)?(?:the\s+)?(?:crew\s+)?survived',
                r'there were no survivors',
                r'not\s+(?:a\s+)?surviv', r'did\s+not\s+surviv', r'without\s+survivor',
                r'surviving\s+(?:accounts?|records?|evidence|documentation|fragment)',
                r'survived\s+(?:a|the|an)\s+(?:earlier|previous|crash|impact)\b',
                r'had\s+survived\s+the\s+(?:long|round|trip|journey|flight)',
                r'initially\s+survived.*(?:died|passed)',
            ]
            survivor_phrases = [
                r'(?:one|the|sole)\s+(?:crew\s+)?(?:member\s+)?surviv(?:ed|or)',
                r'only\s+the\s+\w+\s+\w*\s*surviv',
                r'managed\s+to\s+(?:escape|bail)',
                r'parachuted\s+to\s+safety',
                r'evaded\s+capture', r'was\s+taken\s+prisoner', r'became\s+a\s+pow',
            ]
            for phrase in survivor_phrases:
                match = re.search(phrase, narrative_lower)
                if match:
                    # Check it's not negated or a false positive
                    start = max(0, match.start() - 50)
                    context = narrative_lower[start:match.end() + 30]
                    is_false_positive = any(re.search(fp, context) for fp in false_positive_patterns)
                    if not is_false_positive:
                        issues.append(('ERROR', f'Narrative mentions "{match.group()}" but all {len(crew)} crew listed as killed — check for missing survivor'))
                        break

        if not all_killed:
            # Check for crew listed as survived but narrative says all killed
            survived = [c for c in crew if c.get('fate', '').lower() in ('survived', 'pow', 'evaded')]
            all_killed_phrases = ['all crew were killed', 'all crew killed', 'no survivors',
                                  'none survived', 'all perished', 'all were killed', 'all lost their lives']
            if survived:
                for phrase in all_killed_phrases:
                    if phrase in narrative_lower:
                        issues.append(('ERROR', f'Narrative says "{phrase}" but {len(survived)} crew listed as survived'))
                        break

        # 5.5 Crew count sanity check — if narrative states crew count, verify
        count_match = re.search(r'(\d+)\s+(?:crew|men|airmen)\s+(?:aboard|on board|were)', narrative_lower) if narrative else None
        if count_match:
            stated = int(count_match.group(1))
            actual = len(crew)
            if abs(stated - actual) > 3 and actual > 0:
                issues.append(('WARNING', f'Narrative mentions {stated} crew but {actual} crew records exist'))

    # ═══════════════════════════════════════════════════════════
    # GATE 6: Content Rendering
    # ═══════════════════════════════════════════════════════════

    # 6.1 No "undefined" or "null" rendered as visible text
    for bad_val in ['undefined', 'null']:
        # Check visible text, not in compound words
        if re.search(r'\b' + bad_val + r'\b', text):
            # Filter false positives (e.g. "null and void")
            if bad_val == 'null' and 'null and' in text.lower():
                continue
            # Check it's not in a reasonable context
            issues.append(('WARNING', f'"{bad_val}" found in visible text (verify not a false positive)'))

    # 6.2 No escaped HTML entities rendered as text
    if '&lt;p&gt;' in text or '&lt;br&gt;' in text or '&lt;div' in text:
        issues.append(('ERROR', 'Escaped HTML tags rendered as visible text'))

    # 6.3 No raw JSON in visible text
    if '{"' in text and '":' in text:
        issues.append(('ERROR', 'Raw JSON appears in visible text'))

    # ═══════════════════════════════════════════════════════════
    # GATE 7: Data Completeness
    # ═══════════════════════════════════════════════════════════

    # 7.1 County must be a valid UK administrative region (not a geographic area)
    county = data.get('county', '')
    country = data.get('country', '')
    invalid_county_patterns = [
        'IWM-Registered', 'Peak District', 'Pennines', 'Dartmoor', 'Lake District',
        'Brecon Beacons', 'Snowdonia', 'Other Wales', 'General Yorkshire',
    ]
    if county:
        for pattern in invalid_county_patterns:
            if pattern in county:
                issues.append(('ERROR', f'Invalid county "{county}" — must be a real UK administrative region'))
                break
    elif country == 'United Kingdom':
        issues.append(('WARNING', f'UK memorial with no county set'))

    # 7.2 Title should include aircraft type (not just serial number)
    title = data.get('title', '')
    if re.match(r'^.+\d{4,}[- ]?\d*\s+Memorial$', title):
        # Title is "Location SerialNumber Memorial" with no aircraft type
        if data.get('aircraft_type') and data['aircraft_type'].split()[0] not in title:
            issues.append(('WARNING', f'Title "{title}" uses serial number without aircraft type'))

    return issues


def main():
    html_files = sorted(glob.glob(os.path.join(MEMORIAL_DIR, '*.html')))
    data_files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))

    if not html_files:
        print('ERROR: No HTML files found in out/memorial/. Run `next build` first.')
        sys.exit(1)

    # Build slug -> data lookup
    data_by_slug = {}
    for f in data_files:
        slug = os.path.basename(f).replace('.json', '')
        data_by_slug[slug] = json.load(open(f))

    total = 0
    failures = 0
    warnings = 0
    all_issues = []

    for html_file in html_files:
        slug = os.path.basename(html_file).replace('.html', '')
        html = open(html_file, 'r', errors='replace').read()
        data = data_by_slug.get(slug, {})
        total += 1

        issues = check_memorial_page(slug, html, data)

        criticals = [i for i in issues if i[0] == 'CRITICAL']
        errors = [i for i in issues if i[0] == 'ERROR']
        warns = [i for i in issues if i[0] == 'WARNING']

        if criticals or errors:
            failures += 1
            all_issues.append((slug, issues))
        if warns and not criticals and not errors:
            warnings += 1
            if VERBOSE:
                all_issues.append((slug, issues))

    # Report
    passed = total - failures - warnings
    print(f'''
╔══════════════════════════════════════════════════╗
║  BMR QA SCAN — SET NEW STANDARDS                 ║
╠══════════════════════════════════════════════════╣
║  Pages scanned:  {total:<5}                          ║
║  PASSED:         {passed:<5}                          ║
║  WARNINGS:       {warnings:<5}                          ║
║  FAILED:         {failures:<5}                          ║
╚══════════════════════════════════════════════════╝
''')

    if all_issues:
        print('ISSUES:')
        for slug, issues in all_issues:
            print(f'\n  {slug}:')
            for severity, msg in issues:
                icon = {'CRITICAL': '🔴', 'ERROR': '🟠', 'WARNING': '🟡'}.get(severity, '?')
                print(f'    {icon} [{severity}] {msg}')

    if failures > 0:
        print(f'\n❌ QA GATE FAILED — {failures} page(s) have errors. Fix before deploy.')
        sys.exit(1)
    else:
        print(f'\n✅ QA GATE PASSED — all {total} pages meet specification.')
        sys.exit(0)


if __name__ == '__main__':
    main()
