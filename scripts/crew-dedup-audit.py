#!/usr/bin/env python3
"""
BMR-139: Crew deduplication audit
Scans all memorial JSON files, finds fuzzy duplicate crew members across memorials.
"""

import json
import os
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

MEMORIALS_DIR = Path(__file__).parent.parent / "public" / "data" / "memorials"
REPORT_PATH = Path(__file__).parent.parent / "MEMORY" / "BMR-139-dedup-report.md"

# ── helpers ──────────────────────────────────────────────────────────────────

DECORATION_SUFFIXES = re.compile(
    r'\b(DFC|DFM|DSO|AFC|CGM|BEM|MBE|OBE|CBE|VC|MM|GM|MiD|Bar|DFC\*|DSO\*)\b',
    re.IGNORECASE
)

def normalise_name(raw: str) -> str:
    """Lower-case, strip decorations, strip extra whitespace, expand initials."""
    name = raw.strip()
    name = DECORATION_SUFFIXES.sub('', name)
    # normalise unicode
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

def normalise_service_number(sn: str) -> str:
    """Upper-case, no spaces/hyphens — strip RCAF/RAAF/RNZAF/SAAF labels."""
    if not sn:
        return ''
    sn = sn.strip().upper()
    sn = re.sub(r'\s+', '', sn)
    sn = re.sub(r'-', '', sn)
    # Drop pure-label values like 'RCAF' or 'RAAF'
    if re.fullmatch(r'[A-Z]+', sn) and len(sn) <= 5:
        return ''
    return sn

def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def is_likely_placeholder(name: str) -> bool:
    return bool(re.search(r'unknown|crew member \d+', name, re.IGNORECASE))

# ── load all crew ─────────────────────────────────────────────────────────────

def load_all_crew():
    records = []  # list of dicts
    file_count = 0
    crew_total = 0

    for path in sorted(MEMORIALS_DIR.glob("*.json")):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except json.JSONDecodeError as e:
            print(f"WARN: could not parse {path.name}: {e}")
            continue

        file_count += 1
        memorial_id = data.get("id", path.stem)
        crew = data.get("crew", [])

        for member in crew:
            name = member.get("name", "").strip()
            if not name or is_likely_placeholder(name):
                continue
            sn = member.get("service_number", "") or ""
            records.append({
                "memorial_id": memorial_id,
                "name": name,
                "service_number": sn,
                "rank": member.get("rank", ""),
                "norm_name": normalise_name(name),
                "norm_sn": normalise_service_number(sn),
            })
            crew_total += 1

    return records, file_count, crew_total

# ── deduplication logic ───────────────────────────────────────────────────────

def find_duplicates(records):
    """
    Returns a list of duplicate-pair dicts, categorised:
      - exact_sn: same non-empty service number, different memorials
      - exact_name: same normalised name, different memorials
      - fuzzy_name: high similarity (≥0.85) normalised name, different memorials
    """
    pairs = []
    seen_pairs = set()

    # Index by normalised service number
    by_sn = defaultdict(list)
    for rec in records:
        if rec["norm_sn"]:
            by_sn[rec["norm_sn"]].append(rec)

    for sn, group in by_sn.items():
        # Only interested in cross-memorial duplicates
        memorials = {r["memorial_id"] for r in group}
        if len(memorials) < 2:
            continue
        # Emit all cross-memorial pairs
        for i, a in enumerate(group):
            for b in group[i+1:]:
                if a["memorial_id"] == b["memorial_id"]:
                    continue
                key = tuple(sorted([f"{a['memorial_id']}:{a['name']}", f"{b['memorial_id']}:{b['name']}"]))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                name_sim = name_similarity(a["norm_name"], b["norm_name"])
                pairs.append({
                    "type": "exact_sn",
                    "confidence": 0.95 if name_sim >= 0.85 else 0.80,
                    "service_number": sn,
                    "name_similarity": round(name_sim, 3),
                    "a_memorial": a["memorial_id"],
                    "a_name": a["name"],
                    "a_rank": a["rank"],
                    "b_memorial": b["memorial_id"],
                    "b_name": b["name"],
                    "b_rank": b["rank"],
                })

    # Index by normalised name
    by_name = defaultdict(list)
    for rec in records:
        if rec["norm_name"]:
            by_name[rec["norm_name"]].append(rec)

    for norm_name, group in by_name.items():
        memorials = {r["memorial_id"] for r in group}
        if len(memorials) < 2:
            continue
        for i, a in enumerate(group):
            for b in group[i+1:]:
                if a["memorial_id"] == b["memorial_id"]:
                    continue
                key = tuple(sorted([f"{a['memorial_id']}:{a['name']}", f"{b['memorial_id']}:{b['name']}"]))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                # Determine confidence
                sn_match = (a["norm_sn"] and b["norm_sn"] and a["norm_sn"] == b["norm_sn"])
                conf = 0.90 if sn_match else 0.80
                pairs.append({
                    "type": "exact_name",
                    "confidence": conf,
                    "service_number": a["norm_sn"] or b["norm_sn"] or "",
                    "name_similarity": 1.0,
                    "a_memorial": a["memorial_id"],
                    "a_name": a["name"],
                    "a_rank": a["rank"],
                    "a_sn": a["service_number"],
                    "b_memorial": b["memorial_id"],
                    "b_name": b["name"],
                    "b_rank": b["rank"],
                    "b_sn": b["service_number"],
                })

    # Fuzzy name — compare all names across memorials where norm names differ
    all_records = [r for r in records if r["norm_name"]]
    for i, a in enumerate(all_records):
        for b in all_records[i+1:]:
            if a["memorial_id"] == b["memorial_id"]:
                continue
            key = tuple(sorted([f"{a['memorial_id']}:{a['name']}", f"{b['memorial_id']}:{b['name']}"]))
            if key in seen_pairs:
                continue
            if a["norm_name"] == b["norm_name"]:
                continue  # already caught above
            sim = name_similarity(a["norm_name"], b["norm_name"])
            if sim < 0.85:
                continue
            seen_pairs.add(key)
            sn_match = (a["norm_sn"] and b["norm_sn"] and a["norm_sn"] == b["norm_sn"])
            conf = 0.85 if sn_match else 0.70
            pairs.append({
                "type": "fuzzy_name",
                "confidence": conf,
                "service_number": "",
                "name_similarity": round(sim, 3),
                "a_memorial": a["memorial_id"],
                "a_name": a["name"],
                "a_rank": a["rank"],
                "a_sn": a["service_number"],
                "b_memorial": b["memorial_id"],
                "b_name": b["name"],
                "b_rank": b["rank"],
                "b_sn": b["service_number"],
            })

    pairs.sort(key=lambda p: (-p["confidence"], -p["name_similarity"]))
    return pairs

# ── report generation ─────────────────────────────────────────────────────────

def write_report(pairs, file_count, crew_total):
    exact_sn = [p for p in pairs if p["type"] == "exact_sn"]
    exact_name = [p for p in pairs if p["type"] == "exact_name"]
    fuzzy = [p for p in pairs if p["type"] == "fuzzy_name"]

    # "Clear duplicates" = same SN + name similarity >= 0.85
    clear = [p for p in pairs if p["type"] == "exact_sn" and p["name_similarity"] >= 0.85]
    # Same SN, different name — could be data error or reuse of service number
    sn_only = [p for p in pairs if p["type"] == "exact_sn" and p["name_similarity"] < 0.85]

    lines = [
        "# BMR-139 Crew Deduplication Audit",
        "",
        f"**Run date:** 2026-10-23",
        f"**Memorial files scanned:** {file_count}",
        f"**Total crew records (non-placeholder):** {crew_total}",
        f"**Total duplicate pairs found:** {len(pairs)}",
        "",
        "## Summary",
        "",
        f"| Category | Pairs |",
        f"|----------|-------|",
        f"| Same service number + matching name (clear duplicate) | {len(clear)} |",
        f"| Same service number, name differs (SN collision / data error) | {len(sn_only)} |",
        f"| Same normalised name, different SN or no SN | {len(exact_name)} |",
        f"| Fuzzy name match (≥85% similarity) | {len(fuzzy)} |",
        f"| **Total** | **{len(pairs)}** |",
        "",
        "### Interpretation",
        "",
        "- **Clear duplicates** (same SN + matching name on different memorials) are the most likely real-world cases of one person commemorated on multiple memorials — flag for human review, do not auto-remove.",
        "- **SN collision** pairs need individual inspection: service numbers were occasionally reused across air forces, or transcription errors occurred.",
        "- **Exact name / fuzzy name** matches without a corroborating SN are lower-confidence — common names (John Smith, William Jones) will generate false positives.",
        "",
    ]

    if clear:
        lines += [
            "## Clear Duplicates — Same SN + Matching Name",
            "",
            "_These are most likely the same person commemorated on multiple memorials. Flag for review._",
            "",
            "| Confidence | SN | Name Similarity | Memorial A | Name A | Rank A | Memorial B | Name B | Rank B |",
            "|------------|----|-----------------|------------|--------|--------|------------|--------|--------|",
        ]
        for p in clear:
            lines.append(
                f"| {p['confidence']:.2f} | {p['service_number']} | {p['name_similarity']:.3f} "
                f"| {p['a_memorial']} | {p['a_name']} | {p['a_rank']} "
                f"| {p['b_memorial']} | {p['b_name']} | {p['b_rank']} |"
            )
        lines.append("")

    if sn_only:
        lines += [
            "## Same Service Number, Name Mismatch",
            "",
            "_Low name similarity despite matching SN. Could be transcription error, SN reuse, or same person under different name forms._",
            "",
            "| Confidence | SN | Name Similarity | Memorial A | Name A | Memorial B | Name B |",
            "|------------|----|-----------------|------------|--------|------------|--------|",
        ]
        for p in sn_only:
            lines.append(
                f"| {p['confidence']:.2f} | {p['service_number']} | {p['name_similarity']:.3f} "
                f"| {p['a_memorial']} | {p['a_name']} "
                f"| {p['b_memorial']} | {p['b_name']} |"
            )
        lines.append("")

    if exact_name:
        lines += [
            "## Same Normalised Name, Different Memorial",
            "",
            "_Matched on name alone. May be coincidental for common names._",
            "",
            "| Confidence | Name Sim | Memorial A | Name A | SN A | Memorial B | Name B | SN B |",
            "|------------|----------|------------|--------|------|------------|--------|------|",
        ]
        for p in exact_name:
            lines.append(
                f"| {p['confidence']:.2f} | {p['name_similarity']:.3f} "
                f"| {p['a_memorial']} | {p['a_name']} | {p.get('a_sn','')} "
                f"| {p['b_memorial']} | {p['b_name']} | {p.get('b_sn','')} |"
            )
        lines.append("")

    if fuzzy:
        lines += [
            "## Fuzzy Name Matches (≥85% similarity)",
            "",
            "_Probable spelling variants, abbreviations, or transcription differences._",
            "",
            "| Confidence | Name Sim | Memorial A | Name A | SN A | Memorial B | Name B | SN B |",
            "|------------|----------|------------|--------|------|------------|--------|------|",
        ]
        for p in fuzzy:
            lines.append(
                f"| {p['confidence']:.2f} | {p['name_similarity']:.3f} "
                f"| {p['a_memorial']} | {p['a_name']} | {p.get('a_sn','')} "
                f"| {p['b_memorial']} | {p['b_name']} | {p.get('b_sn','')} |"
            )
        lines.append("")

    lines += [
        "---",
        "_Generated by scripts/crew-dedup-audit.py — BMR-139_",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Report written to {REPORT_PATH}")
    return clear, sn_only, exact_name, fuzzy

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading crew records…")
    records, file_count, crew_total = load_all_crew()
    print(f"  {file_count} files, {crew_total} crew records")

    print("Finding duplicates…")
    pairs = find_duplicates(records)
    print(f"  {len(pairs)} pairs found")

    clear, sn_only, exact_name, fuzzy = write_report(pairs, file_count, crew_total)

    print("\n=== SUMMARY ===")
    print(f"Clear duplicates (same SN + name match):     {len(clear)}")
    print(f"SN collision (same SN, name mismatch):       {len(sn_only)}")
    print(f"Exact name match (different memorial):       {len(exact_name)}")
    print(f"Fuzzy name matches (>=85%):                  {len(fuzzy)}")
    print(f"Total pairs:                                 {len(pairs)}")

if __name__ == "__main__":
    main()
