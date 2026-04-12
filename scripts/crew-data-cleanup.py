#!/usr/bin/env python3
"""
BMR Crew Data Cleanup — fixes known data quality issues in memorial JSONs.

Issues addressed:
1. name == rank (1,122 entries) — rank field holds the name, clear rank to null
2. rank = first name (92 entries) — first name leaked into rank, clear rank
3. rank = role (55 entries) — role stored in rank field, move to role, clear rank
4. age > 65 (3 entries) — garbled CWGC numbers, set age to null
5. nationality = service branch (66 entries) — normalize to country name
6. name contains ALLCAPS with service number — normalise "Ernest A. HOAGG" patterns

Run: python3 scripts/crew-data-cleanup.py [--dry-run]
"""

import json
import glob
import os
import sys
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')

# --- Nationality normalization map ---
NATIONALITY_MAP = {
    # Service branches → country
    'RAF': 'British',
    'RAFVR': 'British',
    'RAF(VR)': 'British',
    'RAAF': 'Australian',
    'RCAF': 'Canadian',
    'RNZAF': 'New Zealander',
    'USAAF': 'American',
    'AAF': 'American',
    'SAAF': 'South African',
    'PAF': 'Polish',
    'WAAF': 'British',
    # Verbose/variant → canonical
    'USA': 'American',
    'US': 'American',
    'United States Army Air Force': 'American',
    'British (RAF)': 'British',
    'British (RAFVR)': 'British',
    'British (assumed)': 'British',
    'British (assumed from RAF service)': 'British',
    'British (implied by RAF)': 'British',
    'British (implied by context)': 'British',
    'British (RCAF)': 'British',
    'British (Northern Irish)': 'British',
    'RAF (British)': 'British',
    'United Kingdom': 'British',
    'Royaume-Uni': 'British',
    'English': 'British',
    'England': 'British',
    'Welsh': 'British',
    'Canada': 'Canadian',
    'Canadian (RCAF)': 'Canadian',
    'Royal Canadian Air Force': 'Canadian',
    'Canadian (Icelandic-born)': 'Canadian',
    'Australia': 'Australian',
    'Australian (RAAF)': 'Australian',
    'New Zealand': 'New Zealander',
    'Polish Air Force': 'Polish',
    'American (RCAF)': 'American',
    'American (serving with RCAF)': 'American',
    'American (serving RCAF)': 'American',
    'French (Free French Air Force)': 'French',
    'Free French': 'French',
}

# Known first names that appear as ranks
FIRST_NAMES = {
    'Robert', 'William', 'Thomas', 'James', 'John', 'George', 'Edward', 'Arthur',
    'Albert', 'Henry', 'Charles', 'Frederick', 'Frank', 'Harold', 'Herbert', 'Alfred',
    'Walter', 'Ernest', 'Leonard', 'Harry', 'Joseph', 'Richard', 'Jack', 'Ronald',
    'Kenneth', 'Norman', 'Leslie', 'Cyril', 'Bernard', 'Sidney', 'Stanley', 'Allan',
    'Raymond', 'Maurice', 'Reginald', 'Douglas', 'Gordon', 'Alan', 'Peter', 'Eric',
    'Donald', 'Dennis', 'Keith', 'Gerald', 'Roy', 'Clifford', 'Derek', 'Brian',
    'David', 'Philip', 'Wilfred', 'Cecil', 'Lawrence', 'Ivan', 'Horace', 'Basil',
    'Percy', 'Victor', 'Edgar', 'Claude', 'Ivor', 'Neville', 'Ralph', 'Trevor',
    'Colin', 'Roger', 'Hugh', 'Patrick', 'Ian', 'Martin', 'Michael', 'Anthony',
    'Andrew', 'Stephen', 'Paul', 'Terence', 'Barry', 'Graham', 'Glyn',
}

# Roles that appear as ranks
ROLES_AS_RANKS = {
    'pilot', 'navigator', 'wireless operator', 'flight engineer', 'bomb aimer',
    'air gunner', 'rear gunner', 'mid-upper gunner', 'observer', 'bombardier',
    'flight rigger', 'wireless operator/air gunner', 'fitter',
}

# Regex for RAFVR with service number embedded in nationality
RAFVR_WITH_NUMBER = re.compile(r'^RAFVR\s+\d+$')
RAAF_WITH_NUMBER = re.compile(r'^RAAF\s+Aus/\d+$')

# Regex for ALLCAPS surnames that need title-casing
ALLCAPS_NAME = re.compile(r'^([A-Z][a-z]+\.?\s+[A-Z]\.?\s+)([A-Z]{3,})$')


def clean_crew(crew_list, memorial_id):
    """Clean a list of crew dicts. Returns (cleaned_list, changes_log)."""
    changes = []

    for c in crew_list:
        name = (c.get('name') or '').strip()
        rank = (c.get('rank') or '').strip()
        role = (c.get('role') or '').strip()
        age = c.get('age')
        nat = (c.get('nationality') or '').strip()

        # 0a. Fix newlines in names — "Surname\nForenames" → "Forenames Surname"
        if '\n' in name:
            parts = [p.strip() for p in name.split('\n') if p.strip()]
            if len(parts) == 2:
                new_name = f'{parts[1]} {parts[0]}'
                changes.append(f'  [{memorial_id}] newline name "{repr(name)}" → "{new_name}"')
                c['name'] = new_name
                name = new_name

        # 0b. Parse "Rank Name - role" pattern → extract clean name, set rank/role
        if ' - ' in name:
            name_part, role_part = name.split(' - ', 1)
            name_part = name_part.strip()
            role_part = role_part.strip()

            # Strip rank prefix from name_part
            RANK_PREFIXES = [
                'P/O', 'F/O', 'F/Lt', 'Fl/Lt', 'S/Ldr', 'W/Cdr', 'F/Sgt', 'W/O',
                'Sqn Ldr', 'Plt Off', 'Grp Capt', 'Wg Cdr', 'Air Cdre',
                'Sgt', 'Cpl', 'LAC', 'AC', 'Fl/Sgt', 'Flt Sgt', 'Flt Lt',
                'Flight Sergeant', 'Flying Officer', 'Pilot Officer',
                'Flight Lieutenant', 'Squadron Leader', 'Wing Commander',
                'Group Captain', 'Air Commodore',
                'Sergeant', 'Corporal', 'Warrant Officer',
                'Staff Sergeant', 'Technical Sergeant',
                '1st Lieutenant', '2nd Lieutenant', 'Captain', 'Major', 'Lieutenant',
            ]
            extracted_rank = None
            for prefix in sorted(RANK_PREFIXES, key=len, reverse=True):
                if name_part.lower().startswith(prefix.lower() + ' '):
                    extracted_rank = prefix
                    name_part = name_part[len(prefix):].strip()
                    break

            # Strip trailing service number and decorations/punctuation from name_part
            name_part = re.sub(r'\s+\d{4,}$', '', name_part).strip()
            name_part = re.sub(r',\s*$', '', name_part).strip()  # trailing commas
            name_part = re.sub(r'\s+(DFC|DFM|DSO|CGM|VC|AFC|MBE|OBE|CBE)\s*,?\s*$', '', name_part).strip()

            # Normalize role_part (underscore to space, title case)
            role_normalized = role_part.replace('_', ' ').title()

            # Apply: set clean name, rank, role
            if extracted_rank and not rank:
                c['rank'] = extracted_rank
            if role_normalized and not role:
                c['role'] = role_normalized

            changes.append(f'  [{memorial_id}] PARSED "Rank Name - role": "{name}" → name="{name_part}", rank={c.get("rank")}, role={c.get("role")}')
            c['name'] = name_part
            name = name_part

        # 1. name == rank — real name stored in both fields
        if name and rank and name == rank:
            if name.lower() in ROLES_AS_RANKS:
                # Both hold a role name — this is an unknown crew member
                c['name'] = 'Unknown'
                c['role'] = c.get('role') or name
                c['rank'] = None
                changes.append(f'  [{memorial_id}] name==rank==role "{name}" → name=Unknown, role={name}, rank=null')
            else:
                # Real name in rank field — clear rank
                c['rank'] = None
                changes.append(f'  [{memorial_id}] name==rank "{name}" → rank=null')

        # 2. rank is a first name
        elif rank in FIRST_NAMES:
            c['rank'] = None
            changes.append(f'  [{memorial_id}] rank=first_name "{rank}" for "{name}" → rank=null')

        # 3. rank is a role
        elif rank.lower() in ROLES_AS_RANKS:
            if not role:
                c['role'] = rank
            c['rank'] = None
            changes.append(f'  [{memorial_id}] rank=role "{rank}" for "{name}" → role={rank}, rank=null')

        # 4. age > 65 (garbled data)
        if age is not None and isinstance(age, (int, float)) and age > 65:
            changes.append(f'  [{memorial_id}] age={age} for "{name}" → null')
            c['age'] = None

        # 5. nationality normalization
        if nat:
            # Handle RAFVR with embedded service number
            if RAFVR_WITH_NUMBER.match(nat):
                # Extract service number, move to service_number if empty
                svc_num = nat.split()[-1]
                if not c.get('service_number'):
                    c['service_number'] = f'RAFVR {svc_num}'
                c['nationality'] = 'British'
                changes.append(f'  [{memorial_id}] nat="{nat}" for "{name}" → British (svc num extracted)')
            elif RAAF_WITH_NUMBER.match(nat):
                svc_num = nat.split()[-1]
                if not c.get('service_number'):
                    c['service_number'] = f'RAAF {svc_num}'
                c['nationality'] = 'Australian'
                changes.append(f'  [{memorial_id}] nat="{nat}" for "{name}" → Australian (svc num extracted)')
            elif nat in NATIONALITY_MAP:
                new_nat = NATIONALITY_MAP[nat]
                if new_nat != nat:
                    changes.append(f'  [{memorial_id}] nat="{nat}" for "{name}" → {new_nat}')
                    c['nationality'] = new_nat

        # 6. Service branch in role field — clear it (it's not a crew position)
        SERVICE_BRANCHES_ROLE = {'RAF', 'RAFVR', 'RCAF', 'RAAF', 'RNZAF', 'USAAF', 'SAAF', 'PAF', 'AAF', 'WAAF'}
        role_now = (c.get('role') or '').strip()
        if role_now in SERVICE_BRANCHES_ROLE:
            changes.append(f'  [{memorial_id}] role=service_branch "{role_now}" for "{name}" → null')
            c['role'] = None

        # 7. ALLCAPS surname normalization (e.g. "Ernest A. HOAGG" → "Ernest A. Hoagg")
        if name:
            m = ALLCAPS_NAME.match(name)
            if m:
                new_name = m.group(1) + m.group(2).title()
                changes.append(f'  [{memorial_id}] name "{name}" → "{new_name}"')
                c['name'] = new_name

    return crew_list, changes


def normalize_crew_name(name):
    """Extract core name from various formats for dedup comparison.
    "Sgt Raymond Albert Rolph - flight_engineer" → "raymond albert rolph"
    "P/O Reginald Parfitt - pilot" → "reginald parfitt"
    "JOHN JOSEPH GODIN RCAF" → "john joseph godin"
    """
    if not name:
        return ''
    name = name.strip()

    # Remove "Rank Name - role" pattern: strip everything after " - "
    if ' - ' in name:
        name = name.split(' - ')[0].strip()

    # Remove leading rank abbreviations
    rank_prefixes = [
        'P/O', 'F/O', 'F/Lt', 'Fl/Lt', 'S/Ldr', 'W/Cdr', 'F/Sgt', 'W/O',
        'Sgt', 'Cpl', 'LAC', 'AC', 'Fl/Sgt', 'Flt Sgt', 'Flt Lt',
        'Flight Sergeant', 'Flying Officer', 'Pilot Officer',
        'Flight Lieutenant', 'Squadron Leader', 'Wing Commander',
        'Sergeant', 'Corporal', 'Warrant Officer',
        'Staff Sergeant', 'Technical Sergeant',
        '1st Lieutenant', '2nd Lieutenant', 'Captain', 'Major', 'Lieutenant',
    ]
    name_lower = name.lower()
    for prefix in sorted(rank_prefixes, key=len, reverse=True):
        if name_lower.startswith(prefix.lower() + ' '):
            name = name[len(prefix):].strip()
            break

    # Remove trailing service branch (RCAF, RAFVR, RAAF, etc)
    name = re.sub(r'\s+(RCAF|RAFVR|RAF|RAAF|RNZAF|USAAF|PAF|SAAF)\s*$', '', name, flags=re.I)

    # Remove service numbers (Aus/415220, 1234567, etc)
    name = re.sub(r'\s*[A-Za-z]{0,4}/?\d{4,}\s*', '', name).strip()

    # Remove parenthetical content — nicknames, numbers: (Joe), (5), (Aus Jim)
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name).strip()

    # Remove quotes — "Jim", 'Ted' etc
    name = re.sub(r'["""\'\u2018\u2019\u201c\u201d]', '', name).strip()

    # Remove placeholder entries
    if name.lower() in ('crew', 'crew members', 'unknown crew', 'me625 crew', 'nd981 crew'):
        return '__placeholder__'

    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    return name.lower().strip()


def dedupe_crew_within_memorial(crew_list, memorial_id):
    """Remove duplicate crew entries within a single memorial.
    Keeps the entry with the most data. Returns (deduped_list, changes).
    """
    if not crew_list or len(crew_list) <= 1:
        return crew_list, []

    changes = []
    seen = {}  # normalized_name → (index, crew_entry, data_score)

    def data_score(c):
        """Score how much useful data a crew entry has."""
        s = 0
        for k in ['rank', 'role', 'age', 'nationality', 'burial_location',
                   'fate_detail', 'bio', 'service_number', 'hometown', 'cwgc_url']:
            if c.get(k):
                s += 1
        # Penalize entries where name contains rank or role (garbled extraction)
        name = c.get('name', '')
        if ' - ' in name:
            s -= 5  # "Rank Name - role" format is clearly inferior
        if name == name.upper() and len(name) > 5:
            s -= 2  # ALLCAPS names are usually duplicates
        return s

    keep_indices = set()
    for i, c in enumerate(crew_list):
        name = (c.get('name') or '').strip()
        if not name or name.lower() == 'unknown':
            keep_indices.add(i)
            continue

        norm = normalize_crew_name(name)
        if not norm:
            keep_indices.add(i)
            continue

        # Remove placeholder entries
        if norm == '__placeholder__':
            changes.append(f'  [{memorial_id}] DEDUP: removed placeholder "{name}"')
            continue

        # Also try matching without short middle words (nicknames like "Jim", "Ted")
        norm_words = norm.split()
        norm_core = ' '.join(w for w in norm_words if len(w) > 3) if len(norm_words) > 3 else norm

        # Check for exact or core match
        matched_key = None
        if norm in seen:
            matched_key = norm
        else:
            for existing_norm in seen:
                existing_core = ' '.join(w for w in existing_norm.split() if len(w) > 3) if len(existing_norm.split()) > 3 else existing_norm
                if norm_core == existing_core and norm_core:
                    matched_key = existing_norm
                    break

        if matched_key:
            prev_idx, prev_entry, prev_score = seen[matched_key]
            cur_score = data_score(c)
            if cur_score > prev_score:
                keep_indices.discard(prev_idx)
                keep_indices.add(i)
                seen[matched_key] = (i, c, cur_score)
                changes.append(f'  [{memorial_id}] DEDUP: kept "{name}" (score={cur_score}), removed "{prev_entry.get("name","")}" (score={prev_score})')
            else:
                changes.append(f'  [{memorial_id}] DEDUP: kept "{prev_entry.get("name","")}" (score={prev_score}), removed "{name}" (score={cur_score})')
        else:
            seen[norm] = (i, c, data_score(c))
            keep_indices.add(i)

    deduped = [crew_list[i] for i in sorted(keep_indices)]
    return deduped, changes


def build_ghost_index(files):
    """Build index of crew names across all memorials to identify ghost entries.

    Ghost crew = same name on 3+ memorials, no rank, no role, fate Unknown/None.
    These are extraction artefacts (sidebar famous aces, fragments, etc).
    """
    name_index = {}
    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)
        slug = data.get('id', os.path.basename(filepath).replace('.json', ''))
        for c in data.get('crew', []):
            name = (c.get('name') or '').strip().lower()
            if name and name != 'unknown':
                if name not in name_index:
                    name_index[name] = []
                name_index[name].append({
                    'memorial': slug,
                    'rank': c.get('rank'),
                    'role': c.get('role'),
                    'fate': c.get('fate'),
                })

    ghost_names = set()
    for name, entries in name_index.items():
        if len(entries) >= 3:
            all_ghost = all(
                not e['rank'] and not e['role'] and (e['fate'] in (None, 'Unknown', 'unknown'))
                for e in entries
            )
            if all_ghost:
                ghost_names.add(name)

    # Also flag obvious non-name strings regardless of count
    NON_NAMES = {'the', 'forename', 'memorials', 'col', 'not explicitly named', 'unknown crew'}
    ghost_names.update(NON_NAMES)

    return ghost_names


def remove_ghost_crew(crew_list, ghost_names, memorial_id):
    """Remove ghost crew entries. Returns (filtered_list, changes_log)."""
    changes = []
    filtered = []
    for c in crew_list:
        name = (c.get('name') or '').strip().lower()
        if name in ghost_names:
            changes.append(f'  [{memorial_id}] REMOVED ghost crew "{c.get("name","")}"')
        else:
            filtered.append(c)
    return filtered, changes


def main():
    dry_run = '--dry-run' in sys.argv

    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    if not files:
        print(f'ERROR: No memorial files found in {DATA_DIR}')
        sys.exit(1)

    # Phase 1: Build ghost crew index across all files
    ghost_names = build_ghost_index(files)
    print(f'Ghost crew names identified: {len(ghost_names)}')

    total_changes = []
    ghost_removed = 0
    files_modified = 0

    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)

        memorial_id = data.get('id', os.path.basename(filepath).replace('.json', ''))
        crew = data.get('crew', [])
        if not crew:
            continue

        # Phase 1: field-level cleanup
        cleaned_crew, changes = clean_crew(crew, memorial_id)

        # Phase 2: remove ghost crew entries
        deghosted_crew, ghost_changes = remove_ghost_crew(cleaned_crew, ghost_names, memorial_id)
        ghost_removed += len(ghost_changes)
        changes.extend(ghost_changes)

        # Phase 3: deduplicate within memorial
        final_crew, dedup_changes = dedupe_crew_within_memorial(deghosted_crew, memorial_id)
        changes.extend(dedup_changes)

        if changes:
            total_changes.extend(changes)
            files_modified += 1
            if not dry_run:
                data['crew'] = final_crew
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')

    # Summary
    print()
    print('BMR Crew Data Cleanup')
    print('=' * 50)
    print(f'Files scanned:   {len(files)}')
    print(f'Files modified:  {files_modified}')
    print(f'Total fixes:     {len(total_changes)}')
    print(f'Mode:            {"DRY RUN" if dry_run else "APPLIED"}')
    print()

    print(f'Ghost crew removed: {ghost_removed}')
    print()

    # Categorize changes
    cats = {
        'name==rank': 0, 'rank=first_name': 0, 'rank=role': 0,
        'age': 0, 'nationality': 0, 'allcaps_name': 0, 'ghost_removed': 0,
        'role=service_branch': 0
    }
    for c in total_changes:
        if 'name==rank' in c:
            cats['name==rank'] += 1
        elif 'rank=first_name' in c:
            cats['rank=first_name'] += 1
        elif 'rank=role' in c:
            cats['rank=role'] += 1
        elif 'age=' in c and '→ null' in c:
            cats['age'] += 1
        elif 'nat=' in c:
            cats['nationality'] += 1
        elif 'name "' in c and '→ "' in c:
            cats['allcaps_name'] += 1
        elif 'REMOVED ghost' in c:
            cats['ghost_removed'] += 1
        elif 'role=service_branch' in c:
            cats['role=service_branch'] += 1

    print('By category:')
    for cat, count in cats.items():
        if count:
            print(f'  {cat}: {count}')
    print()

    if '--verbose' in sys.argv or dry_run:
        print('Changes:')
        for c in total_changes:
            print(c)


if __name__ == '__main__':
    main()
