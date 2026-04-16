#!/usr/bin/env python3
"""
BMR Narrative Generator — creates Farnsfield-quality What Happened narratives.

Two modes:
  --generate: Create narratives for Q0-Q2 memorials (empty/fragment/basic)
  --consolidate: Rewrite Q3-Q4 raw/long narratives into consolidated prose

Uses Granite 8B via Ollama for generation, structured data + external narrative
summaries as source material.

Narrative template by crash type:
  - operational-combat: Mission context → what went wrong → the crash → crew fate → human detail
  - training: What they were training for → what went wrong → where → crew fate → youth angle
  - mid-air-collision: Both aircraft → how it happened → where → combined fate
  - weather: The conditions → the mission → what went wrong → the crash → crew fate
  - mechanical: The aircraft → what failed → the crash → crew fate
  - general-memorial: What this memorial represents → who it commemorates

Target: 400-800 characters. Tight prose. Named crew. Specific details.

Run: python3 scripts/generate-narratives.py --generate [--limit N] [--dry-run]
     python3 scripts/generate-narratives.py --consolidate [--limit N] [--dry-run]
     python3 scripts/generate-narratives.py --slug <slug> [--dry-run]
"""

import json
import glob
import os
import sys
import re
import requests
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
INFERENCE_TOOL = os.path.expanduser('~/.claude/PAI/Tools/Inference.ts')
MODEL = 'claude-sonnet'  # Via PAI Inference --level standard

dry_run = '--dry-run' in sys.argv
mode_generate = '--generate' in sys.argv
mode_consolidate = '--consolidate' in sys.argv
single_slug = None
limit = 999

for i, arg in enumerate(sys.argv):
    if arg == '--slug' and i + 1 < len(sys.argv):
        single_slug = sys.argv[i + 1]
    if arg == '--limit' and i + 1 < len(sys.argv):
        limit = int(sys.argv[i + 1])


def call_claude(system_prompt, user_prompt):
    """Call Claude Sonnet via PAI Inference tool."""
    import subprocess
    try:
        result = subprocess.run(
            ['bun', INFERENCE_TOOL, '--level', 'standard', '--timeout', '60000',
             system_prompt, user_prompt],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f'  ERROR: Inference returned {result.returncode}: {result.stderr[:200]}')
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f'  ERROR: Inference timed out')
        return None
    except Exception as e:
        print(f'  ERROR calling Claude: {e}')
        return None


def build_context(d):
    """Build context string from memorial structured data."""
    parts = []

    if d.get('crash_date'):
        parts.append(f"Date: {d['crash_date']}")
    if d.get('aircraft_type'):
        serial = d.get('serial_number', '')
        parts.append(f"Aircraft: {d['aircraft_type']}" + (f" {serial}" if serial else ""))
    if d.get('squadron'):
        parts.append(f"Squadron: {d['squadron']}")
    if d.get('station'):
        parts.append(f"Station: {d['station']}")
    if d.get('operation_type'):
        parts.append(f"Operation: {d['operation_type']}")
    if d.get('operation_target'):
        parts.append(f"Target: {d['operation_target']}")
    if d.get('cause_of_loss'):
        parts.append(f"Cause: {d['cause_of_loss']}")
    if d.get('crew_summary'):
        parts.append(f"Crew summary: {d['crew_summary']}")
    if d.get('location_name'):
        parts.append(f"Crash location: {d['location_name']}")

    # Key crew details
    crew = d.get('crew', [])
    if crew:
        crew_lines = []
        for c in crew[:10]:  # Limit to avoid prompt bloat
            name = c.get('name', 'Unknown')
            rank = c.get('rank', '')
            role = c.get('role', '')
            age = c.get('age', '')
            nat = c.get('nationality', '')
            fate = c.get('fate', '')
            line = f"  {rank} {name}".strip()
            if role:
                line += f", {role}"
            if age:
                line += f", age {age}"
            if nat:
                line += f", {nat}"
            if fate:
                line += f" — {fate}"
            crew_lines.append(line)
        parts.append(f"Crew ({len(crew)} members):\n" + "\n".join(crew_lines))

    # External narrative summaries
    ext = d.get('external_narratives', [])
    if ext:
        ext_lines = []
        for en in ext[:5]:
            desc = en.get('link_description') or en.get('summary', '')
            if desc:
                ext_lines.append(f"  [{en.get('source_site', '')}]: {desc[:200]}")
        if ext_lines:
            parts.append("Source summaries:\n" + "\n".join(ext_lines))

    return "\n".join(parts)


def build_prompt_generate(d):
    """Build prompt for generating a new narrative."""
    context = build_context(d)
    crash_type = d.get('crash_category', 'unknown')

    return f"""Write a "What Happened" narrative for a WW2 bomber crash memorial page.

RULES:
- Write 4-6 sentences, 400-700 characters total
- Focus ONLY on this specific crash — not the broader war or campaign
- Open with the crew's mission or purpose, not a date
- Name the pilot by rank and surname
- State the cause clearly (weather, enemy action, mechanical, etc.)
- State the outcome: how many killed, any survivors
- Include one human detail: an age, a hometown, a personal fact
- Use crew members' actual names from the data — do not abbreviate or mangle initials
- Do NOT reference crash categories, quality scores, or metadata
- Do NOT add attribution, preamble, or closing remarks
- Tone: respectful, factual, understated — like a heritage information board

Memorial data:
{context}

Narrative:"""


def build_prompt_consolidate(d):
    """Build prompt for consolidating a raw narrative into quality prose."""
    context = build_context(d)
    existing = d.get('narrative', '')
    crash_type = d.get('crash_category', 'unknown')

    return f"""Rewrite this raw text into a concise, memorial-quality "What Happened" narrative.

RULES:
- Write 4-6 sentences, 500-800 characters total
- Extract ONLY facts about this specific aircraft and crew from the raw text
- Strip all article headers, site names, general campaign history, and padding
- Open with the crew's mission or purpose, not a date
- Name the pilot by rank and surname
- State the cause of the crash clearly
- State the outcome: how many killed, any survivors
- Include one human detail if present: an age, a hometown, a personal fact
- Use crew members' actual names — do not abbreviate or mangle initials
- Do NOT reference crash categories, metadata, or source attributions
- Do NOT add preamble or closing remarks — just the narrative prose
- Tone: respectful, factual, understated — like a heritage information board

Memorial data:
{context}

Raw text to rewrite:
{existing[:1500]}

Narrative:"""


def process_memorial(filepath):
    """Process a single memorial — generate or consolidate narrative."""
    with open(filepath) as f:
        data = json.load(f)

    slug = data.get('id', os.path.basename(filepath).replace('.json', ''))
    quality = data.get('narrative_quality_score', 0)
    narr = (data.get('narrative') or '').strip()
    narr_len = len(narr)

    # Decide mode
    if single_slug:
        # Explicit slug — always process
        if quality <= 2 or not narr:
            mode = 'generate'
        else:
            mode = 'consolidate'
    elif mode_generate and quality <= 2:
        mode = 'generate'
    elif mode_consolidate and quality >= 3 and narr_len > 1200:
        # Skip international memorials for now
        INTERNATIONAL = ['amsterdam', 'auckland', 'berlin', 'brussels', 'canberra', 'eindhoven',
                         'normandy', 'paris', 'trenton', 'roermond', 'slovenia', 'tinian', 'hiroshima',
                         'florennes', 'hamburg', 'nanton']
        if any(x in slug for x in INTERNATIONAL):
            return None
        # Skip already processed by Claude
        if data.get('narrative_source', '').startswith('generated-claude'):
            return None
        mode = 'consolidate'
    else:
        return None

    # Build prompt
    if mode == 'generate':
        prompt = build_prompt_generate(data)
    else:
        prompt = build_prompt_consolidate(data)

    print(f'  [{slug}] {mode} (Q{quality}, {narr_len}c → target 400-800c)')

    if dry_run:
        return {'slug': slug, 'mode': mode, 'status': 'dry-run'}

    # Call Claude via PAI Inference
    system_prompt = "You write concise, accurate memorial narratives for WW2 bomber crash sites. You ONLY state facts present in the provided data. You NEVER invent biographical details, hometowns, personality traits, or any information not explicitly given. If data is missing, omit it — do not fill gaps with plausible fiction."
    result = call_claude(system_prompt, prompt)
    if not result:
        return {'slug': slug, 'mode': mode, 'status': 'error'}

    # Clean up result — remove any preamble Granite might add
    result = re.sub(r'^(Here is|Here\'s|The narrative|Narrative:)\s*', '', result, flags=re.I).strip()
    result = re.sub(r'^[""]|[""]$', '', result).strip()

    # Validate length
    if len(result) < 100:
        print(f'    WARNING: Result too short ({len(result)}c), skipping')
        return {'slug': slug, 'mode': mode, 'status': 'too-short'}

    if len(result) > 1000:
        # Truncate at last complete sentence within 1000c
        truncated = result[:1000]
        last_period = truncated.rfind('.')
        if last_period > 300:
            result = truncated[:last_period + 1]

    # Write back
    data['narrative'] = result
    data['narrative_source'] = 'generated-claude-sonnet'
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f'    OK: {len(result)}c')
    return {'slug': slug, 'mode': mode, 'status': 'ok', 'length': len(result)}


def main():
    if single_slug:
        filepath = os.path.join(DATA_DIR, f'{single_slug}.json')
        if not os.path.exists(filepath):
            print(f'ERROR: {single_slug}.json not found')
            sys.exit(1)
        result = process_memorial(filepath)
        if result and not dry_run and result.get('status') == 'ok':
            with open(filepath) as f:
                d = json.load(f)
            print(f'\nGenerated narrative:')
            print(d.get('narrative', ''))
        return

    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    if not files:
        print(f'ERROR: No files in {DATA_DIR}')
        sys.exit(1)

    print(f'BMR Narrative Generator')
    print(f'Mode: {"generate" if mode_generate else "consolidate"} {"(dry run)" if dry_run else ""}')
    print()

    processed = 0
    results = {'ok': 0, 'error': 0, 'too-short': 0, 'dry-run': 0}

    for filepath in files:
        if processed >= limit:
            break
        result = process_memorial(filepath)
        if result:
            processed += 1
            results[result.get('status', 'error')] += 1
            if not dry_run and result.get('status') == 'ok':
                time.sleep(1)  # Rate limit Granite

    print(f'\nProcessed: {processed}')
    for status, count in results.items():
        if count:
            print(f'  {status}: {count}')


if __name__ == '__main__':
    main()
