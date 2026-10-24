#!/usr/bin/env python3
"""
enrich-cwgc-urls.py
BMR-144 / BMR-131 — Add cwgc_url search links to crew records without one.

URL pattern: https://www.cwgc.org/find-records/find-war-dead/search-results/?Surname=...&Forename=...&ServiceNum=...
Uses CWGC's own form field names (Forename= for full names, Initials= for initial-only names).

Scope:
- Adds cwgc_url to ANY crew member who:
    (a) is Killed (CWGC only records casualties)
    (b) has a parseable name (not "Unknown")
    (c) does not already have a cwgc_url

Notes:
- CWGC search-results endpoint returns 403 from headless HTTP (Azure WAF JS challenge).
  The URLs resolve correctly in a real browser — this is bot-protection, not a bad URL.
- cwgc_verified is NOT set to True — these are search links, not verified matches.
  Verification requires a human to confirm the CWGC record matches the crew member.
- Service numbers: placeholder-only values (RCAF, RAAF, RAFVR with no digits) are not
  appended to the search URL as they would corrupt the query. Branch prefixes like
  "RAFVR 1234567" are stripped to extract the numeric part.

Usage:
    python3 scripts/enrich-cwgc-urls.py [--dry-run]
"""

import json
import glob
import os
import re
import sys
from urllib.parse import quote

MEMORIALS_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "memorials")
DRY_RUN = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# Decorations to strip from names before parsing
# ---------------------------------------------------------------------------

DECORATIONS = {
    'DFC', 'DFM', 'AFC', 'AFM', 'DSO', 'CGM', 'DCM', 'BEM', 'MM', 'MiD', 'Bar',
    'DFC*', 'DSO*', 'VC', 'GC', 'GM', 'OBE', 'MBE', 'CBE',
}

# Rank prefixes that sometimes appear at start of name strings
RANK_PREFIX_RE = re.compile(
    r'^(?:Fl/Sgt|F/Sgt|F/O|Fl/Lt|S/Ldr|Wg/Cdr|Grp/Cpt|A/Cdre|A/Mshl|Mshl|'
    r'F\.Sgt|P/O|W/O|Sgt|Cpl|LAC|AC[12]?|Sqn?\.?\s*Ldr|Wg\.?\s*Cdr|'
    r'F/L|F/C|S/L|W/C|G/C|Flt\.?\s*Lt)\s+',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Service number helpers
# ---------------------------------------------------------------------------

PLACEHOLDER_SNS = {
    '', '—', 'RCAF', 'RAFVR', 'RNVR', 'USAAC', 'USAAF', 'RAAF', 'R',
    '— (civilian)', '— RCAF', 'RAF', 'SAAF', 'RNZAF', 'RCNVR', 'Unknown',
}

BRANCH_PREFIXES = ['RAAF ', 'RAFVR ', 'RNZAF ', 'RCAF ', 'SAAF ', 'RAF ']


def clean_service_number(svc: str) -> str:
    """
    Return a CWGC-searchable service number, or empty string if not usable.
    Strips branch prefixes (e.g. 'RAFVR 1234567' -> '1234567').
    Keeps country prefixes (e.g. 'RAAF Aus/417794' -> 'Aus/417794').
    """
    svc = svc.strip()
    if svc in PLACEHOLDER_SNS:
        return ''
    for prefix in BRANCH_PREFIXES:
        if svc.startswith(prefix):
            svc = svc[len(prefix):]
            break
    # If still no digits, not a real service number
    if not any(c.isdigit() for c in svc):
        return ''
    return svc


# ---------------------------------------------------------------------------
# Name parsing
# ---------------------------------------------------------------------------

def strip_decorations(name: str) -> str:
    parts = name.split()
    clean = []
    i = 0
    while i < len(parts):
        if parts[i].rstrip('.,').strip() in DECORATIONS:
            i += 1
            continue
        clean.append(parts[i])
        i += 1
    return ' '.join(clean).strip()


def clean_name_for_search(name: str) -> str | None:
    """
    Strip rank prefixes, service numbers embedded in name strings, branch acronyms,
    and rank-in-parentheses qualifiers that some names contain.
    Returns None if nothing useful remains.
    """
    name = name.strip().lstrip('. ')
    # Remove rank-in-parens at start: "(Inst) ", "(U.T) "
    name = re.sub(r'^\([^)]+\)\s+', '', name).strip()
    # Remove rank prefix
    name = RANK_PREFIX_RE.sub('', name).strip()
    # Remove Fl/Lt. style prefix if still present
    name = re.sub(r'^[A-Z][a-z]*/[A-Z][a-z]*\.\s+', '', name).strip()
    # Remove service number at end: " J/6686", " R/154030"
    name = re.sub(r'\s+[A-Z]{0,4}/?\d{4,}$', '', name).strip()
    # Remove RCAF/branch + service number in parens at end: " RCAF (R/154030)"
    name = re.sub(r'\s+(?:RCAF|RAFVR|RAF|RAAF|RNZAF)\s*\([^)]+\)$', '', name, flags=re.IGNORECASE).strip()
    # Remove standalone branch acronym at end: " RCAF"
    name = re.sub(r'\s+(?:RCAF|RAFVR|RAAF|RNZAF|RNVR|SAAF)$', '', name, flags=re.IGNORECASE).strip()
    # Remove rank-in-parens embedded: " (p/o) ", " (sgt.) "
    name = re.sub(r'\s*\([a-z]{1,5}\.?\s*[a-z]*\.?\)\s*', ' ', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+', ' ', name).strip()
    if not name or len(name) < 2:
        return None
    return name


def is_initials_part(part: str) -> bool:
    """True if token looks like initials (all uppercase, <= 3 chars) or dotted initials."""
    p = re.sub(r'\.', '', part)
    if re.match(r'^[A-Z]{1,3}$', p):
        return True
    if re.match(r'^[A-Z](\.[A-Z])*\.?$', part):
        return True
    return False


def parse_name_for_cwgc(name_str: str) -> tuple[str | None, str | None, str | None]:
    """
    Returns (surname, first_param, param_type) where param_type is 'Forename' or 'Initials'.
    Returns (None, None, None) if the name is not parseable.
    """
    name = clean_name_for_search(name_str)
    if not name:
        return None, None, None
    name = strip_decorations(name).strip()
    name = re.sub(r'\s+', ' ', name).strip()

    parts = name.split()
    if not parts:
        return None, None, None
    if len(parts) == 1:
        return parts[0], None, None

    surname = parts[-1]
    first_parts = parts[:-1]

    if all(is_initials_part(p) for p in first_parts):
        initials = ''.join(re.sub(r'\.', '', p) for p in first_parts)
        return surname, initials, 'Initials'
    else:
        return surname, ' '.join(first_parts), 'Forename'


def build_cwgc_url(name: str, service_number: str = '') -> str | None:
    """Construct CWGC search URL. Returns None if name is not parseable."""
    surname, first, param_type = parse_name_for_cwgc(name)
    if not surname:
        return None

    params = f"Surname={quote(surname)}"
    if first and param_type:
        params += f"&{param_type}={quote(first)}"
    svc = clean_service_number(service_number)
    if svc:
        params += f"&ServiceNum={quote(svc)}"

    return f"https://www.cwgc.org/find-records/find-war-dead/search-results/?{params}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    files = sorted(glob.glob(os.path.join(MEMORIALS_DIR, "*.json")))

    added = 0
    skipped_not_killed = 0
    skipped_no_name = 0
    skipped_unparseable = 0
    files_modified = 0

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        modified = False

        for member in data.get("crew", []):
            cwgc = member.get("cwgc_url", "").strip()
            name = member.get("name", "").strip()
            fate = member.get("fate", "").strip()
            svc = member.get("service_number", "")

            # Skip if already has a URL
            if cwgc:
                continue

            # Only add for killed crew (CWGC records casualties)
            if fate.lower() != "killed":
                skipped_not_killed += 1
                continue

            # Must have a usable name
            if not name or name.lower() == "unknown":
                skipped_no_name += 1
                continue

            url = build_cwgc_url(name, svc)
            if not url:
                skipped_unparseable += 1
                continue

            member["cwgc_url"] = url
            added += 1
            modified = True

        if modified:
            files_modified += 1
            if not DRY_RUN:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

    mode = "DRY RUN" if DRY_RUN else "APPLIED"
    print(f"[{mode}] cwgc_url enrichment complete")
    print(f"  URLs added:                 {added}")
    print(f"  Files modified:             {files_modified}")
    print(f"  Skipped (not killed):       {skipped_not_killed}")
    print(f"  Skipped (no name):          {skipped_no_name}")
    print(f"  Skipped (unparseable name): {skipped_unparseable}")


if __name__ == "__main__":
    main()
