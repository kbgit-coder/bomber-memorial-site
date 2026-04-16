#!/usr/bin/env python3
"""
Granite rewrite pipeline for raw inscription narratives.

Takes the 44 memorials with raw plaque text as their "What Happened" narrative
and rewrites them as readable prose summaries. Preserves facts, fixes formatting.

Also:
- Moves community/thanks content to community_connection field
- Saves original inscription as a separate inscription field
- Generates link_description for external_narratives missing one

Usage:
  python3 scripts/rewrite-inscriptions.py [--dry-run] [--limit N] [--slug SLUG]
"""

import argparse
import glob
import json
import os
import re
import sys
import time

import requests

MEMORIALS_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite3.2:8b"  # 8b for rewrite quality — this is prose generation, not classification

REWRITE_PROMPT = """You are rewriting a WW2 memorial inscription into readable prose for a heritage website.

The memorial is: {title}
Squadron: {squadron}
Aircraft: {aircraft_type} {serial_number}
Date: {crash_date}
Location: {location}

The original text is a raw plaque inscription. It may be ALL CAPS, use "/" as line breaks, and include crew lists, service numbers, and thank-you messages mixed together.

RULES:
1. Write a clear 2-4 sentence narrative of WHAT HAPPENED — the crash, the mission, the loss
2. Use normal sentence case, not ALL CAPS
3. Do NOT list individual crew members by name — that data is shown separately in the Crew Table
4. Do NOT include service numbers, ages, or burial details
5. Do NOT include thank-you messages, appreciation text, or information about the memorial itself (who erected it, when)
6. Focus on: what operation/mission, what went wrong, how many lost, any unique circumstances
7. Keep it respectful and factual
8. If the inscription doesn't contain enough information for a narrative, write a minimal factual summary

INSCRIPTION TEXT:
{inscription}

Respond with ONLY the rewritten narrative text. No JSON, no markdown, no labels."""

COMMUNITY_PROMPT = """Extract the community/memorial story from this inscription text for a WW2 heritage website.

The text below is from a memorial plaque. Extract ONLY the parts about:
- Who erected/funded the memorial
- When it was dedicated
- Community involvement or thanks
- The physical memorial itself

Do NOT include crash details, crew names, or operational information.
Write 1-2 natural sentences. If there is no community content, respond with just "NONE".

TEXT:
{text}

Respond with ONLY the extracted community text or "NONE"."""

LINK_DESC_PROMPT = """Write a one-line description of what a reader will find at this external link about a WW2 memorial.

Memorial: {title}
Source website: {source_site}
Summary: {summary}

Write a brief description (15-25 words) starting with a noun or action, like:
"Full crew biographies and operational history"
"Memorial photographs and condition reports"
"Official war memorial register entry with location details"

Respond with ONLY the description text."""


def call_granite(prompt, max_tokens=300):
    """Call Granite via Ollama. Returns text response."""
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }, timeout=60)
        if resp.status_code != 200:
            return None
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"  Granite error: {e}", file=sys.stderr)
        return None


def is_inscription(text):
    """Detect raw plaque inscription text."""
    if not text or len(text) < 50:
        return False
    upper = text.replace(r'[^A-Za-z]', '')
    upper_chars = sum(1 for c in text if c.isupper() and c.isalpha())
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars == 0:
        return False
    caps_ratio = upper_chars / alpha_chars
    slashes = text.count('/')
    return caps_ratio > 0.6 or slashes > 8


def has_community_content(text):
    """Check if inscription contains community/thanks content."""
    t = text.lower()
    return any(kw in t for kw in [
        'wishes to place on record', 'appreciation', 'cooperation',
        'financial assistance', 'providing this site', 'grateful thanks',
        'erected by', 'unveiled', 'dedicated', 'donated', 'funded',
    ])


def process_memorial(filepath, args):
    """Process a single memorial file. Returns True if modified."""
    with open(filepath) as f:
        memorial = json.load(f)

    slug = os.path.basename(filepath).replace('.json', '')
    narrative = memorial.get('narrative', '')
    modified = False
    actions = []

    # 1. Rewrite inscription narratives
    if narrative and is_inscription(narrative):
        # Save original as inscription field
        if 'inscription' not in memorial:
            memorial['inscription'] = narrative
            actions.append('saved original inscription')

        # Extract community content before rewriting
        if has_community_content(narrative) and not memorial.get('community_connection'):
            community_text = call_granite(COMMUNITY_PROMPT.format(text=narrative))
            if community_text and community_text != "NONE" and len(community_text) > 20:
                memorial['community_connection'] = community_text
                actions.append(f'extracted community_connection ({len(community_text)} chars)')
            time.sleep(1)

        # Rewrite narrative
        rewritten = call_granite(REWRITE_PROMPT.format(
            title=memorial.get('title', slug),
            squadron=memorial.get('squadron', 'Unknown'),
            aircraft_type=memorial.get('aircraft_type', 'Unknown'),
            serial_number=memorial.get('serial_number', ''),
            crash_date=memorial.get('crash_date', 'Unknown'),
            location=memorial.get('location_name', 'Unknown'),
            inscription=narrative,
        ))

        if rewritten and len(rewritten) > 30:
            memorial['narrative'] = rewritten
            actions.append(f'rewrote narrative ({len(narrative)} → {len(rewritten)} chars)')
            modified = True
        time.sleep(1)

    # 2. Generate link_description for external narratives missing one
    for n in memorial.get('external_narratives', []):
        if n.get('summary') and not n.get('link_description'):
            desc = call_granite(LINK_DESC_PROMPT.format(
                title=memorial.get('title', slug),
                source_site=n.get('source_site', 'Unknown'),
                summary=n.get('summary', ''),
            ))
            if desc and len(desc) > 10 and len(desc) < 200:
                # Clean up any quotes or prefixes Granite might add
                desc = desc.strip('"\'').strip()
                if desc.startswith('What you'):
                    desc = desc.split(':', 1)[-1].strip()
                n['link_description'] = desc
                actions.append(f'added link_description for {n.get("source_site", "?")}')
                modified = True
            time.sleep(1)

    if modified and not args.dry_run:
        with open(filepath, 'w') as f:
            json.dump(memorial, f, indent=2)

    return modified, actions


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--slug', default=None)
    args = p.parse_args()

    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))
    if args.slug:
        files = [f for f in files if args.slug in os.path.basename(f)]

    # First pass: identify candidates
    candidates = []
    for filepath in files:
        with open(filepath) as f:
            m = json.load(f)
        slug = os.path.basename(filepath).replace('.json', '')
        narrative = m.get('narrative', '')
        needs_inscription_rewrite = narrative and is_inscription(narrative)
        needs_link_desc = any(
            n.get('summary') and not n.get('link_description')
            for n in m.get('external_narratives', [])
        )
        if needs_inscription_rewrite or needs_link_desc:
            candidates.append((filepath, slug, needs_inscription_rewrite, needs_link_desc))

    print(f"[rewrite] Found {len(candidates)} candidates "
          f"({sum(1 for _,_,r,_ in candidates if r)} inscriptions, "
          f"{sum(1 for _,_,_,l in candidates if l)} need link descriptions)")

    if args.limit:
        candidates = candidates[:args.limit]

    modified = 0
    for i, (filepath, slug, _, _) in enumerate(candidates):
        print(f"\n[{i+1}/{len(candidates)}] {slug}")
        was_modified, actions = process_memorial(filepath, args)
        if was_modified:
            modified += 1
        for a in actions:
            print(f"  ✓ {a}")

    print(f"\n{'='*60}")
    print(f"REWRITE COMPLETE")
    print(f"{'='*60}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Modified: {modified}")
    if args.dry_run:
        print(f"  --dry-run: no files written")


if __name__ == '__main__':
    main()
