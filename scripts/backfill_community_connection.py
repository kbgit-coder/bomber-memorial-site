#!/usr/bin/env python3
"""
Backfill community_connection for BMR memorial JSON files.

Scans all memorial JSON files across three directories and synthesises a
community_connection string from existing evidence fields where the field
is currently empty or null.

Evidence sources checked (in priority order):
  1. maintainer.organisation / maintainer.notes
  2. erected_by
  3. custodian (filtered — junk values like "Unknown"/"Local Residents" skipped)
  4. remembrance.annual_service / .events / .service_description
  5. local_contacts array (parish councils and non-legion orgs preferred)
  6. narrative (community keyword scan)
  7. memorial_details (community keyword scan, fallback only)
  8. inscription (parish/council/unveiled-by pattern, fallback only)

Rules:
  - Never fabricate. Only use data present in the record's own fields.
  - Do NOT touch records that already have a non-empty community_connection.
  - One sentence if only a bare org name with no other detail.
  - 2-4 sentences if richer evidence is present.
  - Cap at 4 sentences total.
"""

import json
import glob
import os
import re

DIRS = [
    "/home/holly/repos/bomber-memorial-site/public/data/memorials",
    "/home/holly/repos/bomber-memorial-site/international-memorials",
    "/home/holly/repos/bomber-memorial-site/ftr-memorials",
]

# Keywords indicating genuine community activity in free-text fields
COMMUNITY_KEYWORDS = [
    "parish council", "parish meeting", "town council", "district council",
    "borough council", "city council", "civic society", "heritage trust",
    "memorial trust", "squadron association", "squadron assoc",
    "community council", "memorial association", "air training corps",
    "parish", "trust", "associat", "committee", "fundrais",
    "subscri", "campaign", "annual service", "remembrance service",
    "unveiled by", "erected by", "maintained by", "donated by",
    "biannual", "reunion service", "dedication ceremony",
    "volunteers", "volunteer", "organis", "commemorat",
    "built by", "planted by",
]

# More targeted keywords for narrative/memorial_details — avoid false positives
NARRATIVE_COMMUNITY_KEYWORDS = [
    "parish council", "parish meeting", "memorial trust", "squadron association",
    "civic society", "community council", "heritage centre", "aviation museum",
    "fundrais", "subscri", "annual service", "reunion service",
    "biannual", "dedication ceremony", "unveiled by", "erected by",
    "volunteers", "organis", "built by",
    "loch ness wellington assoc", "pupils from",
    "school grounds", "planted in school", "school students",
    "comprehensive school", "primary school", "secondary school",
]

# Custodian values that are meaningless or junk — skip them
JUNK_CUSTODIANS = {
    "local residents",
    "local residents - see form",
    "unknown",
    "unkkown",
    "families",
    "family of the pilot.",
    "on private land and not accessible to public",
    "pcc",
}

# Event names that are clearly not real community events (data entry artefacts)
BAD_EVENT_NAME_PATTERNS = [
    r"^amendment",
    r"^addition/amendment",
    r"^posting to",
    r"^investigation$",
    r"^aircraft lost$",
    r"^bizarre",
    r"bombing mission over",
    r"bombing raid",
    r"beaufighter\s+[a-z0-9]+\s+of\s+",
    r"mosquito\s+[a-z0-9]+\s+of\s+",
    r"not specified",
    r"crew matrix",
]


def has_keyword(text: str, keywords: list) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def safe_str(v) -> str:
    return str(v).strip() if v else ""


def title_case_org(name: str) -> str:
    """Title-case an ALL-CAPS org name for readability."""
    if name == name.upper() and len(name) > 4:
        return name.title()
    return name


# ---------------------------------------------------------------------------
# Custodian classification
# ---------------------------------------------------------------------------

def custodian_verb(custodian: str) -> str:
    """Return the appropriate verb for describing custodian relationship."""
    lower = custodian.lower()
    if any(w in lower for w in ("church", "chapel", "cathedral", "parish church",
                                 "st ", "all saints", "st.", "holy")):
        return "cared for by"
    if any(w in lower for w in ("museum", "heritage centre", "visitor centre",
                                 "aviation centre", "heritage center")):
        return "held by"
    if any(w in lower for w in ("council", "civic", "city", "borough", "district",
                                 "parish", "village")):
        return "maintained by"
    if any(w in lower for w in ("association", "trust", "society", "club",
                                 "squadron", "veterans", "burn assoc")):
        return "maintained by"
    if any(w in lower for w in ("school", "college", "academy")):
        return "cared for by"
    return "maintained by"


def is_junk_custodian(custodian: str) -> bool:
    lower = custodian.strip().lower()
    if lower in JUNK_CUSTODIANS:
        return True
    if "see form" in lower:
        return True
    if "private land" in lower:
        return True
    # Personal addresses: contain digits (house numbers)
    if re.search(r"\d", custodian) and any(
        w in lower for w in ("house", "lane", "road", "street", "avenue", "way", "close")
    ):
        return True
    # Long descriptive sentences are not custodian names
    if len(custodian) > 80 and any(w in lower for w in ("part of the structure", "forms part")):
        return True
    # Looks like a personal address: initials + surname (ALL CAPS), multiple comma-separated parts
    # e.g. "J B HAMMOND, FRANCIS HOUSE, BRETTENHAM, SUDBURY"
    addr_parts = [p.strip() for p in custodian.split(",")]
    if len(addr_parts) >= 3 and re.match(r"^[A-Z]\s+[A-Z]\s+[A-Z]+$", addr_parts[0]):
        return True
    return False


def is_junk_org(org: str) -> bool:
    """Return True if a maintainer/erected_by org value is meaningless."""
    if not org:
        return True
    lower = org.strip().lower()
    junk = {"unknown", "unkkown", "n/a", "tbc", "tbd", "none", "unknown — unconfirmed from available sources"}
    if lower in junk:
        return True
    if lower.startswith("unknown"):
        return True
    return False


def is_bad_event_name(name: str) -> bool:
    """Return True if an event name is clearly a data artefact, not a real event."""
    lower = name.strip().lower()
    for pattern in BAD_EVENT_NAME_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def clean_memorial_details(text: str) -> str:
    """Remove embedded Python dict literals from memorial_details (data artefact)."""
    # Remove anything that looks like {'key': 'value', ...}
    cleaned = re.sub(r"\s*\{['\"][\w_]+['\"]:[^}]+\}", "", text)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Field extractors — each returns a list of sentence strings (may be empty)
# ---------------------------------------------------------------------------

def extract_maintainer(d: dict) -> list:
    maint = d.get("maintainer")
    if not isinstance(maint, dict):
        return []
    org = safe_str(maint.get("organisation"))
    notes = safe_str(maint.get("notes"))
    if not org or is_junk_org(org):
        return []
    org = title_case_org(org)
    parts = [f"The memorial is maintained by {org}."]
    if notes and has_keyword(notes, COMMUNITY_KEYWORDS):
        note_clean = notes.rstrip(".")
        if note_clean.lower().strip() != org.lower().strip():
            # Don't include notes that are essentially just restating the org name
            if len(note_clean) > len(org) + 5:
                # Only include first sentence of notes (avoid multi-sentence notes duplication)
                note_sents = split_sentences(note_clean)
                first_note = note_sents[0] if note_sents else note_clean
                # Skip if first note is very short or is "Parish council area." type filler
                if len(first_note) > 20 and not re.match(r"^[Pp]arish council area", first_note):
                    parts.append(first_note + ".")
    return parts


def extract_erected_by(d: dict) -> list:
    eb = safe_str(d.get("erected_by"))
    if not eb or is_junk_org(eb):
        return []
    # Strip generic filler appended by earlier enrichment scripts
    eb = re.sub(r",?\s*indicating a local connection[^.]*$", "", eb, flags=re.IGNORECASE).strip()
    eb = re.sub(r",?\s*indicating[^.]*connection[^.]*$", "", eb, flags=re.IGNORECASE).strip()
    if not eb or is_junk_org(eb):
        return []
    return [f"The memorial was erected by {title_case_org(eb)}."]


def extract_custodian(d: dict) -> list:
    c = safe_str(d.get("custodian"))
    if not c:
        return []
    if is_junk_custodian(c):
        return []
    c_display = title_case_org(c)
    verb = custodian_verb(c)
    return [f"The memorial is {verb} {c_display}."]


def split_sentences(text: str) -> list:
    """Split text into sentences, respecting common abbreviations like No., St., Dr., etc."""
    # Protect common abbreviations from triggering sentence splits
    protected = re.sub(r"\b(No|St|Dr|Mr|Mrs|Ms|Prof|Rev|Sgt|Flt|Sqn|Wg|Gp|Air|RAF|RCAF|RAAF)\.\s+",
                       r"\1__DOT__ ", text)
    sents = re.split(r"(?<=[.!?])\s+", protected)
    return [s.replace("__DOT__", ".").strip() for s in sents if s.strip()]


def extract_remembrance(d: dict) -> list:
    rem = d.get("remembrance")
    if not rem:
        return []
    parts = []
    if isinstance(rem, dict):
        sd = safe_str(rem.get("service_description"))
        if sd:
            sents = split_sentences(sd)
            return [" ".join(sents[:2]).strip()]
        annual = rem.get("annual_service")
        if annual:
            date = safe_str(rem.get("service_date"))
            if date:
                parts.append(f"An annual remembrance service is held at the memorial on {date}.")
            else:
                parts.append("An annual remembrance service is held at the memorial.")
        events = rem.get("events") or []
        if isinstance(events, list):
            # Filter to genuinely named events, not data artefacts
            named = [
                e for e in events
                if isinstance(e, dict) and e.get("name")
                and not is_bad_event_name(safe_str(e.get("name")))
            ]
            if named:
                ev = named[-1]
                ev_name = safe_str(ev.get("name"))
                ev_date = safe_str(ev.get("date"))
                # Skip if date is clearly invalid
                if ev_date and ev_date.lower() in ("not specified", "n/a", "tbc", "tbd", ""):
                    ev_date = ""
                if ev_date:
                    parts.append(f"A commemoration event, '{ev_name}', was held on {ev_date}.")
                elif ev_name:
                    parts.append(f"A commemoration event, '{ev_name}', has been held at the memorial.")
    elif isinstance(rem, list) and rem:
        first = rem[0]
        if isinstance(first, dict):
            desc = safe_str(first.get("description", "")).rstrip(".")
            if desc:
                parts.append(desc + ".")
    return parts


def extract_local_contacts(d: dict) -> list:
    lc = d.get("local_contacts")
    if not isinstance(lc, list) or not lc:
        return []

    # Filter to genuinely community-relevant contacts
    def is_community_contact(c):
        if not isinstance(c, dict):
            return False
        org_type = safe_str(c.get("org_type"))
        org_name = safe_str(c.get("org_name"))
        if not org_name:
            return False
        # Always include parish/civic orgs
        if org_type in ("parish_council", "civic_society", "memorial_trust",
                         "squadron_assoc", "aviation_museum", "heritage_centre"):
            return True
        # Include named British Legion branches only if there's no better contact
        return False

    community = [c for c in lc if is_community_contact(c)]

    # If no community contacts, fall back to non-british-legion
    if not community:
        community = [
            c for c in lc
            if isinstance(c, dict) and c.get("org_name")
            and safe_str(c.get("org_type")) not in ("british_legion", "legion_scotland", "cwgc")
        ]

    # Last resort: first entry regardless
    if not community and lc:
        if isinstance(lc[0], dict) and lc[0].get("org_name"):
            community = [lc[0]]

    if not community:
        return []

    names = [title_case_org(safe_str(c["org_name"])) for c in community[:2]]

    if len(names) == 1:
        return [f"{names[0]} supports the memorial."]
    return [f"{' and '.join(names)} support the memorial."]


def extract_narrative_community(narrative: str) -> list:
    """Pull community-relevant sentences from the narrative text."""
    if not has_keyword(narrative, NARRATIVE_COMMUNITY_KEYWORDS):
        return []
    sents = split_sentences(narrative.strip())
    community = [
        s.strip() for s in sents
        if s.strip() and has_keyword(s, NARRATIVE_COMMUNITY_KEYWORDS)
    ]
    if not community:
        return []
    combined = " ".join(community[:2])
    if len(combined) > 400:
        combined = community[0]
    return [combined] if combined else []


def extract_memorial_details_community(md: str) -> list:
    """Pull a community-relevant sentence from memorial_details (fallback only)."""
    # Extra patterns for memorial_details that need regex — must be genuinely community-oriented
    EXTRA_PATTERNS = [
        r"built\s+in\s+\d{4}\s+by\s+[A-Z][a-zA-Z]+\s+(?:Comprehensive|Primary|Secondary|High|Grammar)",
        r"planted\s+in\s+school\s+grounds",
        r"school\s+grounds",
        r"loch\s+ness\s+wellington",
        r"pupils\s+from",
    ]
    has_extra = any(re.search(p, md, re.IGNORECASE) for p in EXTRA_PATTERNS)
    if not has_keyword(md, NARRATIVE_COMMUNITY_KEYWORDS) and not has_extra:
        return []
    sents = re.split(r"(?<=[.!?])\s+", md.strip())
    for s in sents:
        if s.strip() and (has_keyword(s, NARRATIVE_COMMUNITY_KEYWORDS) or
                          any(re.search(p, s, re.IGNORECASE) for p in EXTRA_PATTERNS)):
            return [s.strip()]
    return []


def extract_inscription_community(inscription: str) -> list:
    """Extract community info from inscription text (last resort)."""
    if not inscription:
        return []

    # Unveiled by
    m = re.search(r"unveiled by\s+([^/\n]+)", inscription, re.IGNORECASE)
    if m:
        who = m.group(1).strip().rstrip("./")
        # Avoid very long matches or obvious noise
        if 5 < len(who) < 120:
            return [f"The memorial was unveiled by {title_case_org(who)}."]

    # Donated by
    m = re.search(r"donated by\s+([^/\n]+)", inscription, re.IGNORECASE)
    if m:
        who = title_case_org(m.group(1).strip().rstrip("./"))
        if 5 < len(who) < 120:
            return [f"The memorial was donated by {who}."]

    # Erected by — only match if the who is a plausible org/person name, not a sentence fragment
    m = re.search(r"erected by\s+([^/\n]+)", inscription, re.IGNORECASE)
    if m:
        who = m.group(1).strip().rstrip("./")
        # Strip generic filler phrases
        who = re.sub(r",?\s*indicating[^,]*$", "", who, flags=re.IGNORECASE).strip()
        # Must be a plausible org/person (not a sentence fragment ending with articles/prepositions)
        # Also skip if it looks like a truncated sentence (ends mid-phrase)
        if (5 < len(who) < 120
                and not who.lower().endswith((" the", " a", " an", " of", " and", " to",
                                              " by", " in", " on", " at", " for", " with"))
                and not re.search(r"\s+(the|a|an|of|and|to|by|in|on|at|for|with)\s+[a-z]+$",
                                  who.lower())):
            return [f"The memorial was erected by {title_case_org(who)}."]

    # Named parish council / town council / squadron association as erecting body
    # Match as a standalone line (NOT embedded in "IN HOPE PARISH" type phrasing)
    lines = [line.strip() for line in re.split(r"[/\n]", inscription) if line.strip()]
    for line in lines[:6]:
        m = re.match(
            r"^([A-Z][A-Z\s\.&']+(?:PARISH COUNCIL|PARISH MEETING|TOWN COUNCIL|CITY COUNCIL|"
            r"DISTRICT COUNCIL|BOROUGH COUNCIL|CIVIC SOCIETY|MEMORIAL TRUST|MEMORIAL ASSOCIATION|"
            r"SQUADRON ASSOCIATION|AIR TRAINING CORPS|ROYAL BRITISH LEGION|BRITISH LEGION))\s*$",
            line.strip(),
            re.IGNORECASE,
        )
        if m:
            org = title_case_org(m.group(1).strip())
            return [f"The memorial was erected by {org}."]

    return []


# ---------------------------------------------------------------------------
# Main synthesis function
# ---------------------------------------------------------------------------

def build_community_connection(d: dict) -> str | None:
    """
    Synthesise a community_connection string from the record's own fields.
    Returns None if there is no usable evidence.
    """
    parts = []

    def add_parts(new_parts: list):
        for p in new_parts:
            p = p.strip()
            if not p:
                continue
            p_lower = p.lower()
            # Avoid near-duplicates — check if a 40-char prefix already appears
            existing_lower = " ".join(parts).lower()
            if p_lower[:40] in existing_lower:
                continue
            # Also avoid if the new part is largely a subset of what's already there
            if len(p_lower) > 20 and p_lower[:-1] in existing_lower:
                continue
            parts.append(p)

    # 1. Maintainer (highest authority — explicitly set field)
    add_parts(extract_maintainer(d))

    # 2. Erected by
    add_parts(extract_erected_by(d))

    # 3. Custodian (only meaningful values)
    if not parts:
        add_parts(extract_custodian(d))

    # 4. Remembrance / services / events
    add_parts(extract_remembrance(d))

    # 5. Local contacts — only add if they mention an org not already in parts
    lc_parts = extract_local_contacts(d)
    for lc_p in lc_parts:
        # Extract the org name from "OrgName supports the memorial."
        m = re.match(r"^(.+?)\s+supports the memorial", lc_p)
        if m:
            lc_org_lower = m.group(1).lower()
            # Skip if this org name is already mentioned in existing parts
            if any(lc_org_lower in p.lower() for p in parts):
                continue
        add_parts([lc_p])

    # 6. Narrative community sentences (up to 2 sentences)
    narrative = safe_str(d.get("narrative"))
    if narrative:
        add_parts(extract_narrative_community(narrative))

    # 7. Memorial details (fallback — only if no parts yet)
    if not parts:
        md = clean_memorial_details(safe_str(d.get("memorial_details")))
        if md:
            add_parts(extract_memorial_details_community(md))

    # 8. Inscription (last resort — parish/unveiled patterns)
    if not parts:
        inscription = safe_str(d.get("inscription"))
        if inscription:
            add_parts(extract_inscription_community(inscription))

    if not parts:
        return None

    # Cap at 4 sentences
    parts = parts[:4]
    result = " ".join(parts)
    # Fix double periods and extra whitespace
    result = re.sub(r"\.{2,}", ".", result)
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def process_file(filepath: str) -> tuple:
    """
    Returns (status, candidate_cc) where status is one of:
      'skipped_has_cc'       — already had community_connection
      'skipped_no_evidence'  — empty CC but no usable evidence found
      'updated'              — synthesised and wrote a new CC
      'error:<msg>'          — JSON parse or write error
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        return f"error:{e}", None

    if not isinstance(data, dict):
        return "skipped_not_dict", None

    existing = data.get("community_connection")
    if existing and str(existing).strip():
        return "skipped_has_cc", None

    candidate = build_community_connection(data)
    if not candidate:
        return "skipped_no_evidence", None

    data["community_connection"] = candidate

    try:
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except OSError as e:
        return f"error:{e}", None

    return "updated", candidate


def main():
    all_files = []
    for directory in DIRS:
        all_files.extend(glob.glob(os.path.join(directory, "*.json")))
    all_files.sort()

    total_scanned = 0
    total_updated = 0
    total_skipped_cc = 0
    total_skipped_no_evidence = 0
    total_errors = 0
    updated_records = []  # list of (filepath, cc_text)

    for filepath in all_files:
        basename = os.path.basename(filepath)
        if basename.startswith("_"):
            continue  # skip _ftr-summary.data.json etc.

        total_scanned += 1
        status, cc_text = process_file(filepath)

        if status == "skipped_has_cc":
            total_skipped_cc += 1
        elif status == "skipped_no_evidence":
            total_skipped_no_evidence += 1
        elif status == "updated":
            total_updated += 1
            updated_records.append((filepath, cc_text))
        elif status.startswith("error:"):
            total_errors += 1
            print(f"  ERROR: {basename}: {status[6:]}")

    # Report updated records
    print("=" * 72)
    print("UPDATED RECORDS")
    print("=" * 72)
    for filepath, cc_text in updated_records:
        rel = os.path.relpath(filepath, "/home/holly/repos/bomber-memorial-site")
        print(f"\n  {rel}")
        display = cc_text[:320] + ("..." if len(cc_text) > 320 else "")
        print(f"  CC: {display}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  Total scanned          : {total_scanned}")
    print(f"  Updated                : {total_updated}")
    print(f"  Skipped (already had CC): {total_skipped_cc}")
    print(f"  Skipped (no evidence)  : {total_skipped_no_evidence}")
    if total_errors:
        print(f"  Errors                 : {total_errors}")


if __name__ == "__main__":
    main()
