#!/usr/bin/env python3
"""Batch replace Wikipedia badge URLs with rafweb.org and other authoritative sources."""

import json
import glob
import os
import re
import urllib.request

MEMORIALS_DIR = "/nas2/Holly/Projects/bomber-memorial-site/public/data/memorials"

# RAF squadrons -> rafweb.org pattern: https://rafweb.org/Badges/RAFHT/{number}.jpg
# This covers all standard RAF squadrons. OTUs and HCUs may not have badges.

# Known RAF squadron mottos (from authoritative sources)
SQUADRON_MOTTOS = {
    "7": "Per diem per noctem",       # By day and by night
    "12": "Leads the field",
    "15": "Aim sure",
    "18": "With courage and faith",
    "44": "The king's thunderbolts",
    "49": "Cave canem",               # Beware of the dog
    "50": "From defence to attack",
    "61": "Per ardua ad aethera tendo", # Through difficulties I reach the skies
    "75": "Ake ake kia kaha",         # For ever and ever be strong (Maori)
    "78": "Nobody unprepared",
    "83": "Strike to defend",
    "90": "Caelestiibus idem",        # The same in the heavens
    "97": "Achieve your aim",
    "100": "Sarang tebuan jangan dijolok", # Never stir up a hornets' nest
    "103": "Noli me tangere",         # Touch me not
    "106": "Pro libertate",           # For freedom
    "114": "With speed I strike",
    "115": "Despite the elements",
    "138": "For freedom",
    "150": "In night and storm we bomb",
    "156": "We light the way",
    "158": "Strength in unity",
    "207": "Semper paratus",           # Always prepared
    "218": "In time",
    "228": "We seek far",
    "300": "Walczmy o wolnosc",       # We fight for freedom (Polish)
    "304": "Ludzie czinu",            # Men of action (Polish)
    "425": "Je te plumerai",          # I shall pluck you (French Canadian)
    "428": "Usque ad finem",          # To the very end
    "460": "Strike and return",
    "500": "Speed",
    "578": "Accuracy",
    "582": "Praecedimus",             # We go before
    "608": "Ictus calcaris",          # A kick of the spur
    "617": "Apres moi le deluge",     # After me, the flood
}

# USAAF badge URLs from authoritative sources (to be filled from research agent)
USAAF_BADGES = {
    # Bomb Groups - using americanairmuseum.com or official USAF heritage
    # These will be populated from research results
}

def extract_squadron_number(squadron_str):
    """Extract the primary squadron number from the squadron field."""
    nums = re.findall(r'\d+', squadron_str)
    return nums[0] if nums else None

def is_usaaf(squadron_str, badge_url):
    """Check if this is a USAAF unit."""
    return ('BG' in squadron_str or 'Bomb Group' in squadron_str or
            'USAAF' in squadron_str or 'Bombardment' in badge_url)

def is_otu(squadron_str):
    """Check if this is an Operational Training Unit."""
    return 'OTU' in squadron_str

def is_hcu(squadron_str):
    """Check if this is a Heavy Conversion Unit."""
    return 'HCU' in squadron_str or 'Heavy Conversion' in squadron_str

def verify_url(url):
    """Check if a URL returns HTTP 200."""
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status == 200
    except Exception:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=5)
            return resp.status == 200
        except Exception:
            return False

def get_badge_url(squadron_str, current_badge):
    """Get the replacement badge URL for a squadron."""
    num = extract_squadron_number(squadron_str)
    if not num:
        return None, None

    if is_usaaf(squadron_str, current_badge):
        return USAAF_BADGES.get(num), None

    if is_otu(squadron_str) or is_hcu(squadron_str):
        # OTUs and HCUs generally don't have squadron badges
        # Try rafweb.org anyway
        url = f"https://rafweb.org/Badges/RAFHT/{num}.jpg"
        if verify_url(url):
            return url, SQUADRON_MOTTOS.get(num)
        return None, None  # Remove badge rather than keep Wikipedia

    # Standard RAF squadron
    url = f"https://rafweb.org/Badges/RAFHT/{num}.jpg"
    return url, SQUADRON_MOTTOS.get(num)

def main():
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json")))
    print(f"Found {len(files)} memorial files")

    updated = 0
    removed = 0
    skipped = 0
    verified = 0
    failed_verify = []

    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath) as f:
            data = json.load(f)

        badge = data.get('squadron_badge_url', '')
        if not badge or ('wikipedia' not in badge.lower() and 'wikimedia' not in badge.lower()):
            continue

        squadron = data.get('squadron', '')
        new_url, motto = get_badge_url(squadron, badge)

        if new_url:
            if verify_url(new_url):
                data['squadron_badge_url'] = new_url
                if motto:
                    data['squadron_motto'] = motto
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                updated += 1
                verified += 1
                print(f"  OK: {filename} -> {new_url}")
            else:
                failed_verify.append((filename, new_url))
                # Remove the Wikipedia badge rather than keep it
                del data['squadron_badge_url']
                if 'squadron_motto' in data:
                    del data['squadron_motto']
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                removed += 1
                print(f"  REMOVED (verify failed): {filename} -> {new_url}")
        else:
            # No replacement found - remove Wikipedia badge
            del data['squadron_badge_url']
            if 'squadron_motto' in data:
                del data['squadron_motto']
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            removed += 1
            print(f"  REMOVED (no source): {filename} [{squadron}]")

    print(f"\nDone: {updated} updated ({verified} verified), {removed} badges removed, {skipped} skipped")
    if failed_verify:
        print(f"\nFailed verification ({len(failed_verify)}):")
        for fn, url in failed_verify:
            print(f"  {fn}: {url}")

if __name__ == "__main__":
    main()
