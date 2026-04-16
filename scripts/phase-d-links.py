#!/usr/bin/env python3
"""Phase D — Generate link_description for all external narratives missing one."""

import json, glob, os, sys, time, requests

MEMORIALS_DIR = 'public/data/memorials'
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite4:3b"
DRY_RUN = '--dry-run' in sys.argv

def call_granite(prompt, retries=1):
    for attempt in range(retries + 1):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.3, "num_predict": 60},
            }, timeout=30)
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                # Clean up
                text = text.strip('"\'').strip()
                if text.startswith('What you'):
                    text = text.split(':', 1)[-1].strip()
                if text.startswith('Discover '):
                    text = text[9:]
                    text = text[0].upper() + text[1:]
                if len(text) > 10 and len(text) < 200:
                    return text
        except:
            if attempt < retries:
                time.sleep(3)
    return None

def main():
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, '*.json')))

    total = 0
    done = 0
    failed = 0
    modified_files = 0

    # First count
    for f in files:
        with open(f) as fh:
            m = json.load(fh)
        for n in m.get('external_narratives', []):
            if n.get('summary') and not n.get('link_description'):
                total += 1

    print(f'Phase D: {total} link descriptions to generate')
    if DRY_RUN:
        print('--dry-run: exiting')
        return

    processed = 0
    for fi, filepath in enumerate(files):
        with open(filepath) as f:
            m = json.load(f)

        slug = os.path.basename(filepath).replace('.json', '')
        title = m.get('title', slug)
        changed = False

        for n in m.get('external_narratives', []):
            if n.get('link_description') or not n.get('summary'):
                continue

            desc = call_granite(
                f"Write a one-line description (15-25 words) of what a reader will find at this link.\n"
                f"Memorial: {title}\nSource: {n.get('source_site', '?')}\n"
                f"Summary: {n.get('summary', '')[:200]}\n"
                f"Respond with ONLY the description, starting with a noun or action word."
            )

            if desc:
                n['link_description'] = desc
                changed = True
                done += 1
            else:
                failed += 1

            processed += 1
            if processed % 50 == 0:
                print(f'  [{processed}/{total}] done={done} failed={failed}')

            time.sleep(0.5)  # Light rate limit — 3B is fast

        if changed:
            with open(filepath, 'w') as f:
                json.dump(m, f, indent=2)
            modified_files += 1

    print(f'\n{"="*60}')
    print(f'PHASE D COMPLETE')
    print(f'{"="*60}')
    print(f'  Generated: {done}')
    print(f'  Failed: {failed}')
    print(f'  Files modified: {modified_files}')

if __name__ == '__main__':
    main()
