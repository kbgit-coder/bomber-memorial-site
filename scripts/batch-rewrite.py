#!/usr/bin/env python3
"""Batch rewrite raw inscriptions — Phase B. Focused, fast, no link descriptions."""

import json, glob, os, re, sys, time, requests

MEMORIALS_DIR = '/root/repos/bomber-memorial-site/public/data/memorials'
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite3.2:8b"

def is_raw_inscription(text):
    if not text or len(text) < 50: return False
    upper = sum(1 for c in text if c.isupper() and c.isalpha())
    alpha = sum(1 for c in text if c.isalpha())
    return alpha > 0 and upper / alpha > 0.6

def call_granite(prompt, retries=2):
    for attempt in range(retries + 1):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.3, "num_predict": 250},
            }, timeout=90)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except:
            if attempt < retries:
                time.sleep(5)
    return None

def has_community_content(text):
    t = text.lower()
    return any(kw in t for kw in [
        'wishes to place on record', 'appreciation', 'cooperation',
        'financial assistance', 'providing this site', 'grateful thanks',
        'erected by', 'unveiled', 'dedicated on', 'donated', 'funded by',
    ])

def process(slug, filepath):
    with open(filepath) as f:
        m = json.load(f)

    narr = m.get('narrative', '')
    if not is_raw_inscription(narr) or m.get('inscription'):
        return False

    # Save original
    m['inscription'] = narr

    # Extract community content
    if has_community_content(narr) and not m.get('community_connection'):
        community = call_granite(f"""Extract ONLY the community/memorial dedication content from this inscription.
Write 1-2 sentences about who erected it, when dedicated, community involvement.
Do NOT include crash details or crew names. If none found, respond "NONE".

TEXT: {narr[:1500]}

Respond with ONLY the community text or NONE.""")
        if community and community != "NONE" and len(community) > 20:
            m['community_connection'] = community
            print(f'    community: {community[:80]}...')
        time.sleep(1)

    # Rewrite narrative
    rewritten = call_granite(f"""Rewrite this WW2 memorial inscription as 2-4 readable sentences.

Memorial: {m.get('title', slug)}
Squadron: {m.get('squadron', 'Unknown')}
Aircraft: {m.get('aircraft_type', '')} {m.get('serial_number', '')}
Date: {m.get('crash_date', 'Unknown')}

RULES: Normal case. Do NOT list crew names. Do NOT include thanks/memorial info. Focus on what happened.

INSCRIPTION: {narr[:1500]}

Respond with ONLY the rewritten text.""")

    if rewritten and len(rewritten) > 30:
        m['narrative'] = rewritten
        print(f'    narrative: {rewritten[:80]}...')
    else:
        print(f'    FAILED to rewrite')
        return False

    with open(filepath, 'w') as f:
        json.dump(m, f, indent=2)
    return True

# Main
files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))
targets = []
for f in files:
    slug = os.path.basename(f).replace('.json','')
    with open(f) as fh:
        m = json.load(fh)
    if m.get('narrative') and is_raw_inscription(m['narrative']) and not m.get('inscription'):
        targets.append((slug, f))

print(f'Phase B: {len(targets)} inscriptions to rewrite')
done = 0
failed = 0

for i, (slug, filepath) in enumerate(targets):
    print(f'\n[{i+1}/{len(targets)}] {slug}')
    ok = process(slug, filepath)
    if ok:
        done += 1
    else:
        failed += 1
    time.sleep(1)

print(f'\n{"="*60}')
print(f'PHASE B COMPLETE: {done} rewritten, {failed} failed')
