#!/usr/bin/env python3
"""
Backfill crew nationality fields across all BMR memorial JSONs.

Sources used (in order of priority):
  1. service_number field — suffix RCAF/RAAF/RNZAF/RAF/RAFVR/RNVR/USAAF/USAAC,
     or prefix AUS/ NZ/ J/ C/ (Commonwealth service prefixes)
  2. memorial squadron field — nationality markers in the squadron name
  3. all-British infer — all other crew on the same memorial already have
     nationality='British' (high confidence only)

Unknown: if none of the above resolve, the field is left blank.
"""

import json
import os
import re
import glob

DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "public", "data", "memorials"
)


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def infer_from_service_number(sn: str) -> str | None:
    """Map a service_number string to a nationality, or return None."""
    if not sn:
        return None
    sn = sn.strip()
    sn_upper = sn.upper()
    parts = sn_upper.split()
    if not parts:
        return None

    suffix = parts[-1]
    prefix = parts[0]

    # Suffix-based (e.g. "R/102085 RCAF", "576765 RAF", "T-190798 USAAF")
    if suffix == "RCAF":
        return "Canadian"
    if suffix == "RAAF":
        return "Australian"
    if suffix == "RNZAF":
        return "New Zealander"
    if suffix in ("RAF", "RAFVR", "RNVR"):
        return "British"
    if suffix in ("USAAF", "USAAC"):
        return "American"

    # Prefix-based Commonwealth service numbers
    if prefix.startswith("AUS/"):
        return "Australian"
    if prefix.startswith("NZ/") or (prefix.startswith("NZ") and len(prefix) > 4):
        return "New Zealander"
    # RCAF commissioned officers: J/ prefix; other Canadian: C/ prefix
    if prefix.startswith("J/") or prefix.startswith("C/"):
        return "Canadian"
    # Standalone USAAF/USAAC as the entire service_number
    if sn_upper in ("USAAF", "USAAC"):
        return "American"

    return None


def infer_from_squadron(sq: str) -> str | None:
    """Map a squadron string to a nationality, or return None."""
    if not sq:
        return None
    sq_upper = sq.upper()

    if any(x in sq_upper for x in ("AUSTRALIAN", "RAAF", "(RAAF)")):
        return "Australian"
    if any(x in sq_upper for x in ("CANADIAN", "RCAF")):
        return "Canadian"
    # NZ: must be a token — "(NZ)", " NZ)", "NZ ", "NEW ZEALAND", "RNZAF"
    if any(x in sq_upper for x in ("(NZ)", " NZ)", "NZ ", "NEW ZEALAND", "RNZAF")):
        return "New Zealander"
    if any(x in sq_upper for x in ("POLISH", "SILESIAN", "MASOVIA", "POMERANIAN")):
        return "Polish"
    if any(x in sq_upper for x in ("FRENCH", "LORRAINE", "TUNISIE")):
        return "French"
    if any(x in sq_upper for x in ("CZECH", "CZECHOSLOVAK")):
        return "Czech"
    if "NORWEGIAN" in sq_upper:
        return "Norwegian"
    # American units
    if "USAAF" in sq_upper or "USAAC" in sq_upper:
        return "American"
    if any(x in sq_upper for x in ("BOMB GROUP", "BOMBARDMENT GROUP", "BOMB SQDN", "BOMB SQD")):
        return "American"
    # Numbered Bomb Groups e.g. "385th BG", "492 BG", "96th BG"
    if re.search(r"\b\d+(ST|ND|RD|TH)? BG(,|\s|$)", sq_upper) or sq_upper.endswith(" BG"):
        return "American"

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))

    total_missing = 0
    filled_service = 0
    filled_squadron = 0
    filled_all_british = 0
    still_unknown = 0

    for filepath in files:
        with open(filepath, encoding="utf-8") as fh:
            memorial = json.load(fh)

        crew = memorial.get("crew", [])
        squadron = memorial.get("squadron", "") or ""

        # Pre-compute squadron-level nationality
        sq_nat = infer_from_squadron(squadron)

        # Check all-British rule:
        # All crew members that ALREADY have a nationality must all be British,
        # and at least one such member must exist.
        crew_with_nat = [c for c in crew if c.get("nationality")]
        all_other_british = (
            len(crew_with_nat) > 0
            and all(c["nationality"] == "British" for c in crew_with_nat)
        )

        changed = False
        for member in crew:
            if member.get("nationality"):
                continue  # already filled

            total_missing += 1
            sn = member.get("service_number", "") or ""

            # Method 1: service_number
            nat = infer_from_service_number(sn)
            if nat:
                member["nationality"] = nat
                filled_service += 1
                changed = True
                continue

            # Method 2: squadron name
            nat = sq_nat
            if nat:
                member["nationality"] = nat
                filled_squadron += 1
                changed = True
                continue

            # Method 3: all other crew are British
            if all_other_british:
                member["nationality"] = "British"
                filled_all_british += 1
                changed = True
                continue

            # Unknown — leave blank
            still_unknown += 1

        if changed:
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(memorial, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    total_filled = filled_service + filled_squadron + filled_all_british
    print("=" * 60)
    print("BMR nationality backfill — results")
    print("=" * 60)
    print(f"Total crew missing nationality (before):  {total_missing}")
    print(f"Filled via service_number:                {filled_service}")
    print(f"Filled via squadron name:                 {filled_squadron}")
    print(f"Filled via all-British inference:         {filled_all_british}")
    print(f"  ── total filled:                        {total_filled}")
    print(f"Remaining unknown:                        {still_unknown}")
    print("=" * 60)


if __name__ == "__main__":
    main()
