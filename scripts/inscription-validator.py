#!/usr/bin/env python3
"""
BMR Inscription Validator — Gate 10: Content Truth
Reads every inscription as a primary source document and validates
the structured JSON data against what the inscription actually says.

Uses Claude (via PAI Inference tool) for comprehension.
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
import subprocess
from datetime import datetime
from collections import Counter

APPLY = '--apply' in sys.argv
LIMIT = None
for i, arg in enumerate(sys.argv):
    if arg == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INFERENCE_TOOL = os.path.expanduser('~/.claude/PAI/Tools/Inference.ts')

REPORT_FILE = os.path.join(REPORT_DIR, 'inscription-validation-report.md')
CORRECTIONS_FILE = os.path.join(REPORT_DIR, 'inscription-corrections.json')
LOG_FILE = os.path.join(REPORT_DIR, 'inscription-validator.log')


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def query_claude(inscription: str, current_data: dict) -> dict:
    """Send inscription + current data to Claude for comprehension via PAI Inference."""
    system_prompt = "You are a WW2 aviation historian verifying memorial data. Read inscriptions carefully and extract ONLY facts explicitly stated in the text. Return ONLY valid JSON with no markdown formatting. All dates must be ISO 8601 format (YYYY-MM-DD). Crash dates must fall within WW2 range (1939-09-01 to 1945-09-02). If a date is outside this range, set crash_date to null and note the discrepancy."

    user_prompt = f"""Read this inscription carefully and extract ONLY facts explicitly stated in the text.

INSCRIPTION TEXT:
{inscription}

CURRENT DATABASE RECORD:
- crash_date: {current_data.get('crash_date', '')}
- aircraft_type: {current_data.get('aircraft_type', '')}
- serial_number: {current_data.get('serial_number', '')}
- squadron: {current_data.get('squadron', '')}
- crew count: {len(current_data.get('crew', []))}
- community_connection: {current_data.get('community_connection', '')}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "crash_date": "YYYY-MM-DD of the AIRCRAFT CRASH specifically (not other deaths/events). null if not stated.",
  "crash_date_reasoning": "exact quote from inscription containing the date",
  "aircraft_type": "aircraft type if mentioned. null if not.",
  "serial_number": "aircraft serial if mentioned. null if not.",
  "squadron": "squadron or unit if mentioned. null if not.",
  "crew_names_in_inscription": true,
  "crew_count_in_inscription": 0,
  "crew_names_extracted": ["list of crew names found in inscription, empty if none"],
  "civilian_casualties": false,
  "civilian_details": "null if none",
  "multiple_events_on_memorial": false,
  "is_local_crash_site": true,
  "is_ftr_memorial": false,
  "community_impact": "null if none",
  "corrections_needed": []
}}"""

    try:
        result = subprocess.run(
            ['bun', INFERENCE_TOOL, '--level', 'standard', '--json',
             system_prompt, user_prompt],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            log(f'  Claude inference error: {result.stderr[:200]}')
            return None

        text = result.stdout.strip()
        # Extract JSON from response
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            json_str = text[start:end + 1]
            json_str = re.sub(r',\s*}', '}', json_str)  # trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # trailing commas in arrays
            parsed = json.loads(json_str)

            # Enforce WW2 date range
            crash_date = parsed.get('crash_date')
            if crash_date and crash_date != 'null':
                try:
                    dt = datetime.strptime(crash_date, '%Y-%m-%d')
                    if dt < datetime(1939, 9, 1) or dt > datetime(1945, 9, 2):
                        log(f'  Date outside WW2 range: {crash_date} — setting to null')
                        parsed['crash_date'] = None
                        parsed['corrections_needed'] = parsed.get('corrections_needed', []) + [f'Date {crash_date} outside WW2 range']
                except ValueError:
                    log(f'  Non-ISO date from Claude: {crash_date} — setting to null')
                    parsed['crash_date'] = None

            return parsed
    except json.JSONDecodeError as e:
        log(f'  Claude JSON parse error: {e}')
    except subprocess.TimeoutExpired:
        log(f'  Claude inference timeout')
    except Exception as e:
        log(f'  Claude error: {e}')

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
        'claude_response': None,
    }

    if not inscription or len(inscription) < 20:
        return result

    # Query Claude for comprehension
    claude = query_claude(inscription, data)
    if not claude:
        result['issues'].append('Claude query failed')
        result['severity'] = 'low'
        return result

    result['claude_response'] = claude

    # === VALIDATE CRASH DATE ===
    claude_date = claude.get('crash_date')
    current_date = data.get('crash_date', '')

    if claude_date and current_date and claude_date != current_date:
        result['issues'].append(f'CRASH DATE MISMATCH: DB has {current_date}, inscription says {claude_date}. Reasoning: {claude.get("crash_date_reasoning", "")}')
        result['corrections'].append({
            'field': 'crash_date',
            'current': current_date,
            'should_be': claude_date,
            'reasoning': claude.get('crash_date_reasoning', ''),
            'confidence': 'high',
        })
    elif claude_date and not current_date:
        result['issues'].append(f'CRASH DATE MISSING: inscription states {claude_date}')
        result['corrections'].append({
            'field': 'crash_date',
            'current': '',
            'should_be': claude_date,
            'reasoning': claude.get('crash_date_reasoning', ''),
            'confidence': 'high',
        })

    # === VALIDATE AIRCRAFT TYPE ===
    claude_aircraft = claude.get('aircraft_type')
    current_aircraft = data.get('aircraft_type', '')

    if claude_aircraft and not current_aircraft:
        result['issues'].append(f'AIRCRAFT TYPE MISSING: inscription mentions {claude_aircraft}')
        result['corrections'].append({
            'field': 'aircraft_type',
            'current': '',
            'should_be': claude_aircraft,
            'confidence': 'high',
        })

    # === VALIDATE SERIAL NUMBER ===
    claude_serial = claude.get('serial_number')
    current_serial = data.get('serial_number', '')

    if claude_serial and not current_serial:
        result['issues'].append(f'SERIAL NUMBER MISSING: inscription mentions {claude_serial}')
        result['corrections'].append({
            'field': 'serial_number',
            'current': '',
            'should_be': claude_serial,
            'confidence': 'high',
        })

    # === VALIDATE SQUADRON ===
    claude_sqn = claude.get('squadron')
    current_sqn = data.get('squadron', '')

    if claude_sqn and not current_sqn:
        result['issues'].append(f'SQUADRON MISSING: inscription mentions {claude_sqn}')
        result['corrections'].append({
            'field': 'squadron',
            'current': '',
            'should_be': claude_sqn,
            'confidence': 'medium',
        })

    # === CREW DATA ===
    crew_in_insc = claude.get('crew_names_in_inscription', False)
    crew_count_insc = claude.get('crew_count_in_inscription', 0)
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
    has_civilian = claude.get('civilian_casualties', False)
    civilian_details = claude.get('civilian_details')
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
    community = claude.get('community_impact')
    if community and not current_cc:
        result['issues'].append(f'COMMUNITY CONNECTION MISSING: {community}')
        result['corrections'].append({
            'field': 'community_connection',
            'current': '',
            'should_be': community,
            'confidence': 'medium',
        })

    # === FTR CHECK ===
    is_ftr = claude.get('is_ftr_memorial', False)
    is_local = claude.get('is_local_crash_site', True)

    if is_ftr and not is_local:
        result['issues'].append('FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site')
        result['severity'] = 'critical'

    # === MULTIPLE EVENTS ===
    multi = claude.get('multiple_events_on_memorial', False)
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

        # Rate limit Claude inference calls
        time.sleep(1.0)

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
