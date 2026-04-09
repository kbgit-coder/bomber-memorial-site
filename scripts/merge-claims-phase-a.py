#!/usr/bin/env python3
"""
Phase A: Auto-accept high-confidence claims from the research DB.

Targets:
  - verified crew_member claims (RAF Commands — full structured JSON)
  - probable crew_member claims from institutional sources (IWM — names only)
  - probable memorial_details claims from institutional sources
  - probable crash_narrative claims from institutional sources

For IWM crew claims: parses "Surname, First — listed on memorial" into basic
CrewMember objects. Cross-references crew_summary text for rank/role hints.

Writes updated memorial JSONs and marks claims as accepted in the DB.

Usage: python3 scripts/merge-claims-phase-a.py [--dry-run]
"""

import json
import glob
import os
import re
import sys
import subprocess
from datetime import datetime

DRY_RUN = "--dry-run" in sys.argv
MEMORIALS_DIR = "public/data/memorials"
def db_query_json(sql):
    """Run a SQL query wrapped in json_agg and return list of dicts."""
    wrapped = f"SELECT COALESCE(json_agg(t), '[]'::json) FROM ({sql}) t"
    result = subprocess.run(
        ["docker", "exec", "bmr-research-db", "psql", "-U", "bmr", "-d", "bmr_research", "-t", "-A", "-c", wrapped],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"DB ERROR: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print(f"JSON parse error: {result.stdout[:200]}", file=sys.stderr)
        return []


def db_exec(sql):
    """Execute a SQL statement (no result expected)."""
    result = subprocess.run(
        ["docker", "exec", "bmr-research-db", "psql", "-U", "bmr", "-d", "bmr_research", "-c", sql],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"DB ERROR: {result.stderr}", file=sys.stderr)


def load_memorial(slug):
    """Load a memorial JSON file."""
    path = os.path.join(MEMORIALS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_memorial(slug, data):
    """Save a memorial JSON file."""
    path = os.path.join(MEMORIALS_DIR, f"{slug}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_iwm_name(field_value):
    """Parse 'Surname, FirstName — listed on memorial' into name string."""
    # Remove the " — listed on memorial" suffix
    name_part = re.sub(r"\s*[—–-]\s*listed on memorial.*$", "", field_value, flags=re.IGNORECASE).strip()
    # Remove trailing dots
    name_part = name_part.rstrip(".")

    if "," in name_part:
        parts = name_part.split(",", 1)
        surname = parts[0].strip()
        first = parts[1].strip() if len(parts) > 1 else ""

        # If first name is just initials like "P A" or "P A F", format nicely
        if first and all(len(p.rstrip(".")) <= 2 for p in first.split()):
            # Initials only — use "P.A. Surname" format
            initials = " ".join(p.rstrip(".") + "." for p in first.split() if p.rstrip("."))
            return f"{initials} {surname}"
        elif first and first.lower() != "n.a.":
            return f"{first} {surname}"
        else:
            return surname
    return name_part


def parse_rafcommands_crew(field_value):
    """Parse RAF Commands structured JSON crew claim into CrewMember."""
    try:
        data = json.loads(field_value)
    except (json.JSONDecodeError, TypeError):
        return None

    member = {"name": data.get("name", "Unknown")}

    if data.get("rank"):
        member["rank"] = data["rank"]
    if data.get("trade"):
        member["role"] = data["trade"]
    if data.get("service_number"):
        member["service_number"] = data["service_number"]
    if data.get("unit"):
        # Could extract squadron from unit
        pass
    if data.get("burial_details"):
        burial = data["burial_details"].strip()
        # Clean up trailing parens
        burial = re.sub(r"\s*\(\s*$", "", burial)
        if burial:
            member["burial_location"] = burial
    if data.get("date_of_death"):
        pass  # We track this at memorial level, not crew level

    member["fate"] = "Killed"
    return member


def extract_rank_from_summary(crew_summary, surname):
    """Try to find a rank for a given surname in crew_summary text."""
    if not crew_summary:
        return None

    rank_patterns = [
        (r"(?:Plt|P/O|Pilot)\s*(?:Off(?:\.)?|Officer)\s+" + re.escape(surname), "Plt Off"),
        (r"(?:Flt|F/Lt|Flight)\s*(?:Lt|Lieut(?:\.)?|Lieutenant)\s+" + re.escape(surname), "Flt Lt"),
        (r"(?:Sqn|S/Ldr|Squadron)\s*(?:Ldr|Leader)\s+" + re.escape(surname), "Sqn Ldr"),
        (r"(?:Wg|W/Cdr|Wing)\s*(?:Cdr|Commander)\s+" + re.escape(surname), "Wg Cdr"),
        (r"(?:Flt|F/Sgt|Flight)\s*(?:Sgt|Sergeant)\s+" + re.escape(surname), "Flt Sgt"),
        (r"(?:Sgt|Sergeant)\s+" + re.escape(surname), "Sgt"),
        (r"(?:W/O|Warrant)\s*(?:Off(?:\.)?|Officer)\s+" + re.escape(surname), "WO"),
        (r"(?:Grp|G/Capt|Group)\s*(?:Capt|Captain)\s+" + re.escape(surname), "Grp Capt"),
        (r"(?:LAC)\s+" + re.escape(surname), "LAC"),
    ]

    for pattern, rank in rank_patterns:
        if re.search(pattern, crew_summary, re.IGNORECASE):
            return rank
    return None


def names_match(existing_name, new_name):
    """Check if two crew member names likely refer to the same person."""
    # Normalise: lowercase, strip punctuation
    def normalise(n):
        return re.sub(r"[^a-z\s]", "", n.lower()).strip()

    e = normalise(existing_name)
    n = normalise(new_name)

    if e == n:
        return True

    # Check if surname matches and first name/initial matches
    e_parts = e.split()
    n_parts = n.split()

    if not e_parts or not n_parts:
        return False

    # Compare surnames (last word)
    if e_parts[-1] != n_parts[-1]:
        return False

    # Surnames match — check first name/initial overlap
    if len(e_parts) > 1 and len(n_parts) > 1:
        if e_parts[0][0] == n_parts[0][0]:
            return True

    return False


def main():
    print(f"Phase A Claims Merge {'(DRY RUN)' if DRY_RUN else ''}")
    print(f"{'=' * 60}")
    print(f"Date: {datetime.now().isoformat()}")
    print()

    # -------------------------------------------------------------------------
    # 1. Fetch all high-confidence crew claims
    # -------------------------------------------------------------------------
    crew_claims = db_query_json("""
        SELECT c.id, m.slug, c.field_value, c.confidence, s.name as source_name, s.tier, c.field_context::text
        FROM claims c
        JOIN memorials m ON c.memorial_id = m.id
        JOIN sources s ON c.source_id = s.id
        WHERE c.status = 'pending'
          AND c.field_name = 'crew_member'
          AND (c.confidence = 'verified'
               OR (c.confidence = 'probable' AND s.tier IN ('definitive', 'institutional')))
        ORDER BY m.slug, c.id
    """)

    print(f"Crew claims to process: {len(crew_claims)}")

    # -------------------------------------------------------------------------
    # 2. Fetch memorial_details claims
    # -------------------------------------------------------------------------
    details_claims = db_query_json("""
        SELECT c.id, m.slug, c.field_value, c.confidence, s.name as source_name
        FROM claims c
        JOIN memorials m ON c.memorial_id = m.id
        JOIN sources s ON c.source_id = s.id
        WHERE c.status = 'pending'
          AND c.field_name = 'memorial_details'
          AND c.confidence = 'probable' AND s.tier = 'institutional'
        ORDER BY m.slug
    """)

    print(f"Memorial details claims: {len(details_claims)}")

    # -------------------------------------------------------------------------
    # 3. Fetch crash_narrative claims
    # -------------------------------------------------------------------------
    narrative_claims = db_query_json("""
        SELECT c.id, m.slug, c.field_value, c.confidence, s.name as source_name
        FROM claims c
        JOIN memorials m ON c.memorial_id = m.id
        JOIN sources s ON c.source_id = s.id
        WHERE c.status = 'pending'
          AND c.field_name = 'crash_narrative'
          AND (c.confidence = 'verified'
               OR (c.confidence = 'probable' AND s.tier IN ('definitive', 'institutional')))
        ORDER BY m.slug
    """)

    print(f"Narrative claims: {len(narrative_claims)}")
    print()

    # -------------------------------------------------------------------------
    # 4. Process crew claims — group by memorial
    # -------------------------------------------------------------------------
    memorials_updated = {}
    claims_accepted = []
    claims_skipped = []

    # Group crew claims by slug
    crew_by_slug = {}
    for claim in crew_claims:
        crew_by_slug.setdefault(claim["slug"], []).append(claim)

    for slug, claims in crew_by_slug.items():
        memorial = load_memorial(slug)
        if not memorial:
            print(f"  SKIP {slug}: JSON file not found")
            claims_skipped.extend(c["id"] for c in claims)
            continue

        existing_crew = memorial.get("crew", [])
        existing_names = [m.get("name", "") for m in existing_crew]
        crew_summary = memorial.get("crew_summary", "")
        new_members = []

        for claim in claims:
            fv = claim["field_value"]
            # Determine if this is structured (RAF Commands) or plain text (IWM)
            if fv.startswith("{"):
                member = parse_rafcommands_crew(fv)
                if not member:
                    claims_skipped.append(claim["id"])
                    continue
            else:
                name = parse_iwm_name(fv)
                if not name or name.lower() == "n.a.":
                    claims_skipped.append(claim["id"])
                    continue

                member = {
                    "rank": "—",
                    "name": name,
                    "fate": "Killed",
                }

                # Try to extract rank from crew_summary
                surname = name.split()[-1] if name.split() else name
                rank = extract_rank_from_summary(crew_summary, surname)
                if rank:
                    member["rank"] = rank

            # Check for duplicates against existing crew
            is_duplicate = False
            for existing_name in existing_names:
                if names_match(existing_name, member["name"]):
                    is_duplicate = True
                    break

            # Also check against new members we're about to add
            for new_m in new_members:
                if names_match(new_m["name"], member["name"]):
                    is_duplicate = True
                    break

            if is_duplicate:
                claims_skipped.append(claim["id"])
                continue

            new_members.append(member)
            claims_accepted.append(claim["id"])

        if new_members:
            memorial.setdefault("crew", []).extend(new_members)
            memorials_updated[slug] = memorial
            print(f"  {slug}: +{len(new_members)} crew members (total: {len(memorial['crew'])})")

    print()

    # -------------------------------------------------------------------------
    # 5. Process memorial_details claims
    # -------------------------------------------------------------------------
    details_updated = 0
    for claim in details_claims:
        slug = claim["slug"]
        field_value = claim["field_value"]
        memorial = memorials_updated.get(slug) or load_memorial(slug)
        if not memorial:
            claims_skipped.append(claim["id"])
            continue

        existing = memorial.get("memorial_details", "")
        if existing and len(existing) >= len(field_value):
            # Already have equal or better data
            claims_skipped.append(claim["id"])
            continue

        memorial["memorial_details"] = field_value
        memorials_updated[slug] = memorial
        claims_accepted.append(claim["id"])
        details_updated += 1

    print(f"Memorial details updated: {details_updated}")

    # -------------------------------------------------------------------------
    # 6. Process narrative claims
    # -------------------------------------------------------------------------
    narratives_updated = 0
    for claim in narrative_claims:
        slug = claim["slug"]
        field_value = claim["field_value"]
        memorial = memorials_updated.get(slug) or load_memorial(slug)
        if not memorial:
            claims_skipped.append(claim["id"])
            continue

        existing = memorial.get("narrative", "")
        if existing and len(existing) >= len(field_value):
            claims_skipped.append(claim["id"])
            continue

        # Only set narrative if the claim is substantial (>50 chars)
        if len(field_value.strip()) < 50:
            claims_skipped.append(claim["id"])
            continue

        # Guard: reject IWM catalogue/inscription text masquerading as crash narrative
        # These should go in memorial_details, not narrative
        stripped_value = field_value.strip()
        iwm_catalogue_starts = ("Badge:", "Inscription:", "Name:", "Type:", "Description:")
        if stripped_value.startswith(iwm_catalogue_starts):
            print(f"  SKIP {slug}: narrative looks like IWM catalogue (starts with '{stripped_value[:20]}...')")
            claims_skipped.append(claim["id"])
            continue

        # Strip machine-appended Aircraft:/Squadrons: footer lines from claim generator
        import re as _re
        stripped_value = _re.sub(r'\n?Squadrons:.*$', '', stripped_value, flags=_re.MULTILINE | _re.DOTALL)
        stripped_value = _re.sub(r'\n?Aircraft:.*$', '', stripped_value, flags=_re.MULTILINE | _re.DOTALL)
        stripped_value = stripped_value.rstrip()

        if len(stripped_value) < 50:
            claims_skipped.append(claim["id"])
            continue

        memorial["narrative"] = stripped_value
        memorials_updated[slug] = memorial
        claims_accepted.append(claim["id"])
        narratives_updated += 1

    print(f"Narratives updated: {narratives_updated}")
    print()

    # -------------------------------------------------------------------------
    # 7. Summary and write
    # -------------------------------------------------------------------------
    print(f"{'=' * 60}")
    print(f"SUMMARY")
    print(f"  Memorials modified: {len(memorials_updated)}")
    print(f"  Claims accepted:    {len(claims_accepted)}")
    print(f"  Claims skipped:     {len(claims_skipped)} (duplicates, missing files, insufficient data)")
    print()

    if DRY_RUN:
        print("DRY RUN — no files written, no DB updated.")
        return

    # Write memorial JSONs
    for slug, memorial in memorials_updated.items():
        memorial["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        save_memorial(slug, memorial)
        print(f"  Wrote: {slug}.json")

    # Update DB — mark claims as accepted
    if claims_accepted:
        ids_str = ",".join(str(cid) for cid in claims_accepted)
        db_exec(f"""
            UPDATE claims
            SET status = 'accepted',
                reviewed_by = 'Holly (Phase A auto-accept)',
                reviewed_at = NOW(),
                review_notes = 'Auto-accepted: high-confidence claim from verified/institutional source'
            WHERE id IN ({ids_str})
        """)
        print(f"\n  DB: {len(claims_accepted)} claims marked as accepted")

    if claims_skipped:
        ids_str = ",".join(str(cid) for cid in claims_skipped)
        db_exec(f"""
            UPDATE claims
            SET review_notes = 'Phase A: skipped (duplicate or insufficient data)'
            WHERE id IN ({ids_str}) AND review_notes IS NULL
        """)
        print(f"  DB: {len(claims_skipped)} claims annotated as skipped")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
