#!/usr/bin/env python3
"""
BMR Inscription Validator — Gate 10: Content Truth
Reads every inscription as a primary source document and validates
the structured JSON data against what the inscription actually says.

Uses Granite 8B (local Ollama) for comprehension.
Outputs a correction report with severity ratings.

Usage: python3 scripts/inscription-validator.py [--apply] [--limit N]
  --apply: auto-apply high-confidence corrections
  --limit N: process only first N memorials

SET NEW STANDARDS.
"""

import json
import os
import re
import sys
import time
import requests
from datetime import datetime
from collections import Counter

APPLY = '--apply' in sys.argv
LIMIT = None
for i, arg in enumerate(sys.argv):
    if arg == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'granite4:3b'

REPORT_FILE = os.path.join(REPORT_DIR, 'inscription-validation-report.md')
CORRECTIONS_FILE = os.path.join(REPORT_DIR, 'inscription-corrections.json')
LOG_FILE = os.path.join(REPORT_DIR, 'inscription-validator.log')


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def query_granite(inscription: str, current_data: dict) -> dict:
    """Send inscription + current data to Granite for comprehension."""
    prompt = f"""You are a WW2 aviation historian verifying memorial data. Read this inscription carefully and extract ONLY facts explicitly stated in the text.

INSCRIPTION TEXT:
{inscription}

CURRENT DATABASE RECORD:
- crash_date: {current_data.get('crash_date', '')}
- aircraft_type: {current_data.get('aircraft_type', '')}
- serial_number: {current_data.get('serial_number', '')}
- squadron: {current_data.get('squadron', '')}
- crew count: {len(current_data.get('crew', []))}
- community_connection: {current_data.get('community_connection', '')}

Return ONLY valid JSON:
{{
  "crash_date": "YYYY-MM-DD of the AIRCRAFT CRASH specifically (not other deaths/events on this memorial). null if not stated.",
  "crash_date_reasoning": "exact quote from inscription with the crash date",
  "aircraft_type": "aircraft type if mentioned. null if not.",
  "serial_number": "aircraft serial if mentioned. null if not.",
  "squadron": "squadron or unit if mentioned. null if not.",
  "crew_names_in_inscription": true or false,
  "crew_count_in_inscription": number of individual crew named, 0 if names redacted/placeholder,
  "civilian_casualties": true or false,
  "civilian_details": "ages, relationship to community if mentioned. null if none.",
  "multiple_events_on_memorial": true or false,
  "is_local_crash_site": true or false,
  "is_ftr_memorial": true or false,
  "community_impact": "any community connection mentioned (local people affected, who erected it, local organisations). null if none.",
  "corrections_needed": ["list each specific field that is WRONG in the current database, with what it should be"]
}}"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1, 'num_predict': 600}
        }, timeout=120)

        text = resp.json().get('response', '')
        # Extract JSON from response — handle common Granite formatting issues
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            json_str = text[start:end + 1]
            # Fix common JSON issues from Granite
            json_str = re.sub(r',\s*}', '}', json_str)  # trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # trailing commas in arrays
            json_str = json_str.replace('\n', ' ')  # newlines in strings
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        log(f'  Granite JSON parse error: {e}')
    except Exception as e:
        log(f'  Granite error: {e}')

    return None


def validate_memorial(slug: str, data: dict) -> dict:
    """Validate one memorial's data against its inscription."""
    inscription = (data.get('inscription', '') or '').strip()
    result = {
        'slug': slug,
        'title': data.get('title', ''),
        'has_inscription': bool(inscription),
        'inscription_length': len(inscription),
        'issues': [],
        'corrections': [],
        'severity': 'clean',  # clean, low, medium, high, critical
        'granite_response': None,
    }

    if not inscription or len(inscription) < 20:
        return result

    # Query Granite for comprehension
    granite = query_granite(inscription, data)
    if not granite:
        result['issues'].append('Granite query failed')
        result['severity'] = 'low'
        return result

    result['granite_response'] = granite

    # === VALIDATE CRASH DATE ===
    granite_date = granite.get('crash_date')
    current_date = data.get('crash_date', '')

    if granite_date and current_date and granite_date != current_date:
        result['issues'].append(f'CRASH DATE MISMATCH: DB has {current_date}, inscription says {granite_date}. Reasoning: {granite.get("crash_date_reasoning", "")}')
        result['corrections'].append({
            'field': 'crash_date',
            'current': current_date,
            'should_be': granite_date,
            'reasoning': granite.get('crash_date_reasoning', ''),
            'confidence': 'high',
        })
    elif granite_date and not current_date:
        result['issues'].append(f'CRASH DATE MISSING: inscription states {granite_date}')
        result['corrections'].append({
            'field': 'crash_date',
            'current': '',
            'should_be': granite_date,
            'reasoning': granite.get('crash_date_reasoning', ''),
            'confidence': 'high',
        })

    # === VALIDATE AIRCRAFT TYPE ===
    granite_aircraft = granite.get('aircraft_type')
    current_aircraft = data.get('aircraft_type', '')

    if granite_aircraft and not current_aircraft:
        result['issues'].append(f'AIRCRAFT TYPE MISSING: inscription mentions {granite_aircraft}')
        result['corrections'].append({
            'field': 'aircraft_type',
            'current': '',
            'should_be': granite_aircraft,
            'confidence': 'high',
        })

    # === VALIDATE SERIAL NUMBER ===
    granite_serial = granite.get('serial_number')
    current_serial = data.get('serial_number', '')

    if granite_serial and not current_serial:
        result['issues'].append(f'SERIAL NUMBER MISSING: inscription mentions {granite_serial}')
        result['corrections'].append({
            'field': 'serial_number',
            'current': '',
            'should_be': granite_serial,
            'confidence': 'high',
        })

    # === VALIDATE SQUADRON ===
    granite_sqn = granite.get('squadron')
    current_sqn = data.get('squadron', '')

    if granite_sqn and not current_sqn:
        result['issues'].append(f'SQUADRON MISSING: inscription mentions {granite_sqn}')
        result['corrections'].append({
            'field': 'squadron',
            'current': '',
            'should_be': granite_sqn,
            'confidence': 'medium',
        })

    # === CREW DATA ===
    crew_in_insc = granite.get('crew_names_in_inscription', False)
    crew_count_insc = granite.get('crew_count_in_inscription', 0)
    current_crew = data.get('crew', [])

    if crew_in_insc and crew_count_insc > 0 and len(current_crew) == 0:
        result['issues'].append(f'CREW MISSING: inscription has {crew_count_insc} crew names but crew list is empty')
        result['corrections'].append({
            'field': 'crew',
            'current': '0 crew',
            'should_be': f'{crew_count_insc} crew (extract from inscription)',
            'confidence': 'medium',
        })

    # === CIVILIAN CASUALTIES ===
    has_civilian = granite.get('civilian_casualties', False)
    civilian_details = granite.get('civilian_details')
    current_cc = data.get('community_connection', '')

    if has_civilian and not current_cc:
        result['issues'].append(f'CIVILIAN CASUALTIES NOT RECORDED: {civilian_details}')
        result['corrections'].append({
            'field': 'community_connection',
            'current': '',
            'should_be': civilian_details or 'Civilian casualties mentioned in inscription',
            'confidence': 'high',
        })

    # === COMMUNITY CONNECTION ===
    community = granite.get('community_impact')
    if community and not current_cc:
        result['issues'].append(f'COMMUNITY CONNECTION MISSING: {community}')
        result['corrections'].append({
            'field': 'community_connection',
            'current': '',
            'should_be': community,
            'confidence': 'medium',
        })

    # === FTR CHECK ===
    is_ftr = granite.get('is_ftr_memorial', False)
    is_local = granite.get('is_local_crash_site', True)

    if is_ftr and not is_local:
        result['issues'].append('FTR MEMORIAL: Granite identifies this as a Failed to Return memorial, not a local crash site')
        result['severity'] = 'critical'

    # === MULTIPLE EVENTS ===
    multi = granite.get('multiple_events_on_memorial', False)
    if multi:
        result['issues'].append('MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event')

    # === SEVERITY RATING ===
    if not result['issues']:
        result['severity'] = 'clean'
    elif any('MISMATCH' in i or 'CIVILIAN' in i for i in result['issues']):
        result['severity'] = 'high'
    elif any('MISSING' in i for i in result['issues']):
        result['severity'] = 'medium'
    elif any('FTR' in i for i in result['issues']):
        result['severity'] = 'critical'
    else:
        result['severity'] = 'low'

    return result


def apply_corrections(slug: str, data: dict, corrections: list) -> bool:
    """Apply high-confidence corrections to memorial JSON."""
    changed = False

    for c in corrections:
        if c['confidence'] != 'high':
            continue

        field = c['field']
        new_value = c['should_be']

        if field in ('crash_date', 'aircraft_type', 'serial_number', 'squadron', 'community_connection'):
            if new_value and new_value != 'null':
                data[field] = new_value
                changed = True

    if changed:
        data['last_validated'] = datetime.now().strftime('%Y-%m-%d')
        path = os.path.join(DATA_DIR, f'{slug}.json')
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    return changed


def main():
    start = datetime.now()
    log(f'\n{"=" * 70}')
    log(f'BMR INSCRIPTION VALIDATOR — Gate 10: Content Truth')
    log(f'Started: {start.strftime("%Y-%m-%d %H:%M")}')
    log(f'Mode: {"APPLY corrections" if APPLY else "REPORT only"}')
    log(f'{"=" * 70}')

    # Load all memorials
    memorials = []
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(DATA_DIR, fname)) as f:
            data = json.load(f)
        if (data.get('inscription', '') or '').strip():
            memorials.append((fname.replace('.json', ''), data))

    log(f'Memorials with inscriptions: {len(memorials)}')

    if LIMIT:
        memorials = memorials[:LIMIT]
        log(f'Limited to: {LIMIT}')

    # Process each memorial
    results = []
    applied = 0

    for i, (slug, data) in enumerate(memorials):
        if i % 10 == 0:
            log(f'Processing {i+1}/{len(memorials)}...')

        result = validate_memorial(slug, data)
        results.append(result)

        if result['issues']:
            log(f'  [{result["severity"].upper():8s}] {slug}: {len(result["issues"])} issues')
            for issue in result['issues'][:3]:
                log(f'    → {issue[:100]}')

        # Apply high-confidence corrections if --apply
        if APPLY and result['corrections']:
            if apply_corrections(slug, data, result['corrections']):
                applied += 1

        # Rate limit Ollama
        time.sleep(0.5)

    end = datetime.now()
    duration = (end - start).total_seconds()

    # === GENERATE REPORT ===
    severity_counts = Counter(r['severity'] for r in results)
    issue_types = Counter()
    for r in results:
        for i in r['issues']:
            category = i.split(':')[0].strip()
            issue_types[category] += 1

    all_corrections = []
    for r in results:
        for c in r['corrections']:
            all_corrections.append({**c, 'slug': r['slug'], 'title': r['title']})

    # Write corrections JSON
    with open(CORRECTIONS_FILE, 'w') as f:
        json.dump(all_corrections, f, indent=2)

    # Write report
    lines = []
    lines.append(f'# BMR Inscription Validation Report — {start.strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'')
    lines.append(f'**Duration:** {duration:.0f}s | **Memorials checked:** {len(results)} | **Mode:** {"APPLIED" if APPLY else "REPORT ONLY"}')
    lines.append(f'')
    lines.append(f'## Summary')
    lines.append(f'')
    lines.append(f'| Severity | Count |')
    lines.append(f'|----------|-------|')
    for sev in ['critical', 'high', 'medium', 'low', 'clean']:
        lines.append(f'| {sev} | {severity_counts.get(sev, 0)} |')
    lines.append(f'')
    lines.append(f'## Issue Categories')
    lines.append(f'')
    for cat, count in issue_types.most_common():
        lines.append(f'- **{cat}**: {count}')
    lines.append(f'')

    if APPLY:
        lines.append(f'## Corrections Applied: {applied}')
        lines.append(f'')

    # Critical issues
    critical = [r for r in results if r['severity'] == 'critical']
    if critical:
        lines.append(f'## CRITICAL — Requires Immediate Action ({len(critical)})')
        lines.append(f'')
        for r in critical:
            lines.append(f'### {r["slug"]}')
            lines.append(f'**{r["title"]}**')
            for i in r['issues']:
                lines.append(f'- {i}')
            lines.append(f'')

    # High severity
    high = [r for r in results if r['severity'] == 'high']
    if high:
        lines.append(f'## HIGH — Data Corrections Needed ({len(high)})')
        lines.append(f'')
        for r in high:
            lines.append(f'**{r["slug"]}** — {r["title"]}')
            for i in r['issues']:
                lines.append(f'- {i}')
            for c in r['corrections']:
                lines.append(f'  - Fix `{c["field"]}`: `{c["current"]}` → `{c["should_be"]}` (confidence: {c["confidence"]})')
            lines.append(f'')

    # Medium
    medium = [r for r in results if r['severity'] == 'medium']
    if medium:
        lines.append(f'## MEDIUM — Missing Data ({len(medium)})')
        lines.append(f'')
        for r in medium:
            lines.append(f'- **{r["slug"]}**: {"; ".join(r["issues"][:2])}')

    lines.append(f'')
    lines.append(f'---')
    lines.append(f'*Generated {end.strftime("%Y-%m-%d %H:%M:%S")} | Corrections file: {CORRECTIONS_FILE}*')

    with open(REPORT_FILE, 'w') as f:
        f.write('\n'.join(lines))

    # Console summary
    log(f'\n{"=" * 70}')
    log(f'INSCRIPTION VALIDATION COMPLETE')
    log(f'{"=" * 70}')
    log(f'  Duration:     {duration:.0f}s ({duration/60:.1f} min)')
    log(f'  Checked:      {len(results)}')
    log(f'  Clean:        {severity_counts.get("clean", 0)}')
    log(f'  Low:          {severity_counts.get("low", 0)}')
    log(f'  Medium:       {severity_counts.get("medium", 0)}')
    log(f'  High:         {severity_counts.get("high", 0)}')
    log(f'  Critical:     {severity_counts.get("critical", 0)}')
    log(f'  Corrections:  {len(all_corrections)} total, {applied} applied')
    log(f'')
    log(f'  Report: {REPORT_FILE}')
    log(f'  Corrections: {CORRECTIONS_FILE}')
    log(f'{"=" * 70}')

    # Exit code: fail if critical issues found
    if severity_counts.get('critical', 0) > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
