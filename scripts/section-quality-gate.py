#!/usr/bin/env python3
"""
Section-level content relevancy and quality gate.
Scores every section on every memorial page. Flags issues that must be fixed
before production deploy.

Checks:
1. TITLE — broken parens, truncated, encoding issues
2. NARRATIVE — site chrome, navigation text, unrelated content
3. COMMUNITY — crash details in community section (wrong section)
4. REMEMBRANCE — crash events miscategorised as remembrance
5. CREW — garbled names, truncated text, role spillover
"""

import json, glob, os, re, sys

MEMORIALS_DIR = 'public/data/memorials'
FIX = '--fix' in sys.argv

# Site chrome patterns that should NEVER be in narrative content
SITE_CHROME = [
    r'(?i)check out active \w+ .* campaigns',
    r'(?i)NAFO Ukrainian',
    r'(?i)Cemetery WW2 (?:RAF )?Register',
    r'(?i)Coastal Command.*Lincolnshire.*WW2',
    r'(?i)Fighter Command.*Lincolnshire.*WW2',
    r'(?i)Lincolnshire Aircraft Production',
    r'(?i)(?:Brigg|Kirton|North Cotes|Scunthorpe) Cemetery WW2',
    r'(?i)cookie\s*(?:policy|consent|notice)',
    r'(?i)privacy policy',
    r'(?i)subscribe to (?:our|the)',
    r'(?i)share (?:this|on) (?:facebook|twitter)',
    r'(?i)leave a (?:comment|reply)',
    r'(?i)comments? (?:are )?closed',
    r'(?i)powered by wordpress',
    r'(?i)skip to (?:main )?content',
    r'(?i)← (?:previous|older)',
    r'(?i)(?:next|newer) →',
    r'(?i)click here to',
    r'(?i)Loading\.\.\.',
    r'(?i)search for:',
    r'(?i)your email address',
    r'(?i)Sign up for',
]

# Crash/operational content that belongs in What Happened, NOT remembrance
CRASH_IN_REMEMBRANCE = [
    r'(?i)crashed?\b',
    r'(?i)shot down',
    r'(?i)collided',
    r'(?i)took off',
    r'(?i)training (?:flight|exercise|sortie)',
    r'(?i)navigation exercise',
    r'(?i)operational (?:flight|mission|sortie)',
    r'(?i)Heavy Conversion Unit',
    r'(?i)all (?:crew|aboard) (?:were )?killed',
]

# Community section should not contain crash details
CRASH_IN_COMMUNITY = [
    r'(?i)crashed?\s+(?:near|at|into|on)',
    r'(?i)shot down by',
    r'(?i)all \d+ crew (?:were )?killed',
    r'(?i)raid on\b',
    r'(?i)returning from\b.*mission',
]

def check_title(m, slug):
    issues = []
    title = m.get('title', '')
    if '(' in title and ')' not in title:
        issues.append(('title', 'broken-paren', f'Unclosed parenthesis: {title}'))
    if ')' in title and '(' not in title:
        issues.append(('title', 'broken-paren', f'Unopened parenthesis: {title}'))
    if len(title) < 10:
        issues.append(('title', 'too-short', f'Title too short: {title}'))
    if title.endswith('...') or title.endswith('…'):
        issues.append(('title', 'truncated', f'Truncated title: {title}'))
    return issues

def check_narrative(m, slug):
    issues = []
    narr = m.get('narrative', '')
    if not narr:
        return issues
    for pattern in SITE_CHROME:
        if re.search(pattern, narr):
            match = re.search(pattern, narr).group(0)
            issues.append(('narrative', 'site-chrome', f'Site chrome in What Happened: "{match[:60]}"'))
    # Check for very long unstructured text (possible dump)
    if len(narr) > 2000 and narr.count('.') < 5:
        issues.append(('narrative', 'possible-dump', f'Long text ({len(narr)} chars) with few sentences'))
    return issues

def check_community(m, slug):
    issues = []
    comm = m.get('community_connection', '')
    if not comm:
        return issues
    for pattern in CRASH_IN_COMMUNITY:
        if re.search(pattern, comm):
            match = re.search(pattern, comm).group(0)
            issues.append(('community', 'crash-content', f'Crash detail in Community: "{match[:60]}"'))
    return issues

def check_remembrance(m, slug):
    issues = []
    rem = m.get('remembrance')
    if not rem or not rem.get('events'):
        return issues
    for event in rem['events']:
        name = event.get('name', '')
        desc = event.get('description', '')
        text = f'{name} {desc}'
        for pattern in CRASH_IN_REMEMBRANCE:
            if re.search(pattern, text):
                match = re.search(pattern, text).group(0)
                issues.append(('remembrance', 'crash-as-event', f'Crash info as remembrance event: "{name[:40]}" contains "{match}"'))
                break
    return issues

def check_crew(m, slug):
    issues = []
    for c in m.get('crew', []):
        name = c.get('name', '')
        rank = c.get('rank', '')
        role = c.get('role', '')
        # Garbled names (contain fragments of other text)
        if any(kw in name.lower() for kw in ['killed', 'survived', 'squadron', 'crew was', 'commissioned']):
            issues.append(('crew', 'garbled-name', f'Garbled crew name: "{name[:60]}"'))
        if any(kw in rank.lower() for kw in ['killed', 'survived', 'crew', 'from', 'near', 'flight from']):
            issues.append(('crew', 'garbled-rank', f'Garbled rank: "{rank[:60]}" for {name[:30]}'))
        if role and len(role) > 80:
            issues.append(('crew', 'role-spillover', f'Role too long ({len(role)} chars) for {name[:30]}'))
        if name == 'Unknown' or name == 'unknown':
            issues.append(('crew', 'unknown-crew', f'Unknown crew member entry'))
    return issues

def fix_issues(m, issues):
    """Auto-fix what we can."""
    fixed = 0

    # Fix narrative site chrome — strip matching lines
    narr = m.get('narrative', '')
    if narr and any(i[1] == 'site-chrome' for i in issues):
        lines = narr.split('\n')
        clean = []
        for line in lines:
            skip = False
            for pattern in SITE_CHROME:
                if re.search(pattern, line):
                    skip = True
                    break
            if not skip:
                clean.append(line)
        m['narrative'] = '\n'.join(clean).strip()
        fixed += 1

    # Fix remembrance — remove crash events, they're not remembrance
    rem = m.get('remembrance')
    if rem and rem.get('events'):
        crash_issues = [i for i in issues if i[1] == 'crash-as-event']
        if crash_issues:
            clean_events = []
            for event in rem['events']:
                text = f'{event.get("name","")} {event.get("description","")}'
                is_crash = False
                for pattern in CRASH_IN_REMEMBRANCE:
                    if re.search(pattern, text):
                        is_crash = True
                        break
                if not is_crash:
                    clean_events.append(event)
            if clean_events:
                rem['events'] = clean_events
            else:
                del m['remembrance']
            fixed += 1

    # Fix broken titles — can't auto-fix, just flag
    # Fix garbled crew — remove entries with garbled names
    crew = m.get('crew', [])
    crew_issues = [i for i in issues if i[0] == 'crew' and i[1] in ('garbled-name', 'garbled-rank')]
    if crew_issues:
        clean_crew = []
        for c in crew:
            name = c.get('name', '')
            rank = c.get('rank', '')
            garbled = False
            if any(kw in name.lower() for kw in ['killed', 'survived', 'squadron', 'crew was', 'commissioned']):
                garbled = True
            if any(kw in rank.lower() for kw in ['killed', 'survived', 'crew', 'from', 'near', 'flight from']):
                garbled = True
            if name in ('Unknown', 'unknown'):
                garbled = True
            if not garbled:
                clean_crew.append(c)
        m['crew'] = clean_crew
        fixed += 1

    return fixed

def main():
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))
    all_issues = []
    fixed_files = 0

    for filepath in files:
        slug = os.path.basename(filepath).replace('.json', '')
        with open(filepath) as f:
            m = json.load(f)

        issues = []
        issues.extend(check_title(m, slug))
        issues.extend(check_narrative(m, slug))
        issues.extend(check_community(m, slug))
        issues.extend(check_remembrance(m, slug))
        issues.extend(check_crew(m, slug))

        if issues:
            for i in issues:
                all_issues.append((slug, *i))

            if FIX:
                fixes = fix_issues(m, issues)
                if fixes > 0:
                    with open(filepath, 'w') as f:
                        json.dump(m, f, indent=2)
                    fixed_files += 1

    # Summary
    from collections import Counter
    issue_types = Counter()
    for slug, section, issue_type, detail in all_issues:
        issue_types[f'{section}:{issue_type}'] += 1

    print(f'{"="*60}')
    print(f'SECTION QUALITY GATE — {len(files)} memorials')
    print(f'{"="*60}')
    print(f'Total issues: {len(all_issues)}')
    print(f'Memorials with issues: {len(set(i[0] for i in all_issues))}')

    if FIX:
        print(f'Files auto-fixed: {fixed_files}')

    print(f'\nIssue frequency:')
    for k, v in issue_types.most_common():
        print(f'  {k:40} {v}')

    print(f'\nAll issues:')
    for slug, section, itype, detail in all_issues:
        print(f'  {slug[:45]:45} [{section}:{itype}] {detail[:70]}')

main()
