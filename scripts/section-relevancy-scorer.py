#!/usr/bin/env python3
"""
BMR Section Relevancy Scorer — two-pass content quality gate.

Pass 1 (Memorial-level): Does each sentence belong on this memorial page at all?
  - Filters sidebar junk, unrelated historical content, boilerplate
  - Scores each sentence against the memorial's context (date, location, crew, aircraft)

Pass 2 (Section-level): Is each sentence in the correct section?
  - Classifies sentences into target sections based on content
  - Auto-moves clearly misplaced sentences
  - Flags ambiguous cases

Sections and their content rules:
  - narrative (What Happened): The crash itself — weather, mission, cause, impact, sequence of events
  - memorial_details (The Memorial): Physical memorial description, dedication events, unveilings, plaques, who erected it
  - community_connection: Who funded/campaigned for memorial, local involvement, school projects, community response
  - remembrance.events: RECURRING annual services, wreath laying, parades, anniversary commemorations
  - crew[].bio: Individual crew biography, family, pre-war life, training

Run: python3 scripts/section-relevancy-scorer.py [--dry-run] [--verbose]
"""

import json
import glob
import os
import sys
import re
import copy

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'memorials')
dry_run = '--dry-run' in sys.argv
verbose = '--verbose' in sys.argv

# ── Section classifiers ──────────────────────────────────────────────

# Patterns that indicate CRASH / WHAT HAPPENED content
CRASH_PATTERNS = [
    re.compile(r'\b(crash(ed|ing)?|struck|collid(ed|ing)|collision|mid-air)\b', re.I),
    re.compile(r'\b(engine fail|caught fire|explod|burst into flames)\b', re.I),
    re.compile(r'\b(wreckage|impact|plunged|dived|spun|stall(ed)?)\b', re.I),
    re.compile(r'\b(burn(ed|ing)|broke up|disintegrat)\b', re.I),
    re.compile(r'\b(went down|lost control|came down|fell to|plough(ed)?)\b', re.I),
    re.compile(r'\b(anti-aircraft|flak|shot down|enemy fire|fighter attack)\b', re.I),
    re.compile(r'\b(took off|return(ed|ing) from|on approach|circuit|overshoot)\b', re.I),
    re.compile(r'\b(training flight|cross-country|practice bomb|formation flying)\b', re.I),
    re.compile(r'\b(mission to|operation|target|bombing raid|sortie)\b', re.I),
    re.compile(r'\b(ditched|bailed out|parachut|abandon(ed)? (the )?aircraft)\b', re.I),
    re.compile(r'\b(fog|cloud|poor visibility|icing|storm|turbulence|weather)\b', re.I),
]

# Patterns that indicate MEMORIAL / DEDICATION content (one-off events about the memorial itself)
MEMORIAL_PATTERNS = [
    re.compile(r'\b(dedicat(ed|ion)|unveil(ed|ing)|erected|install(ed|ation)?)\b', re.I),
    re.compile(r'\b(plaque|memorial (was|is|consists|displays?|establis))\b', re.I),
    re.compile(r'\b(commission(ed)?|inaugurat|opened by|reveal(ed)?)\b', re.I),
    re.compile(r'\b(made of|carved|inscri(bed|ption)|engraved|bronze|stone|granite|marble)\b', re.I),
    re.compile(r'\b(located (at|near|in|on)|situated|stands (at|in|on|near))\b', re.I),
    re.compile(r'\b(rededication|rededicated|restored|refurbish|renovation)\b', re.I),
    re.compile(r'\b(anniversary of (the )?(memorial|crash)|memorial anniversary)\b', re.I),
    re.compile(r'\b(new memorial|memorial was built|memorial was placed)\b', re.I),
    re.compile(r'\b(establish(ed|ment)|founding|found(ed)?)\b', re.I),
    re.compile(r'\b(memorial display|display(ed|s)|exhibit(ed|ion)?)\b', re.I),
    re.compile(r'\b(cairn|cross|pillar|obelisk|headstone|tablet|board)\b', re.I),
    re.compile(r'\b(Imperial War Museum|IWM|collection)\b', re.I),
]

# Event names that are clearly about the memorial itself (not remembrance)
MEMORIAL_EVENT_NAME_PATTERNS = [
    re.compile(r'\b(dedicat|unveil|erect|install|establish|display|plaque|cairn|restor|rededic)', re.I),
    re.compile(r'\bmemorial\b.*\b(dedication|unveiling|erection|placement|ceremony|establishment)\b', re.I),
    re.compile(r'\b(casualty page|war memorial|founding|bothy)\b', re.I),
]

# Patterns that indicate REMEMBRANCE content (recurring, annual events)
REMEMBRANCE_PATTERNS = [
    re.compile(r'\b(annual(ly)?|every year|each year|yearly)\b', re.I),
    re.compile(r'\b(remembrance (service|day|sunday))\b', re.I),
    re.compile(r'\b(wreath[- ]?lay(ing)?|parade|march past)\b', re.I),
    re.compile(r'\b(commemoration|commemorat(ed|ive|ing))\b', re.I),
    re.compile(r'\b(anniversary service|anniversary ceremony)\b', re.I),
    re.compile(r'\b(poppy|armistice|november 11|lest we forget)\b', re.I),
    re.compile(r'\b(service (is |was )?held|ceremony (is |was )?held)\b', re.I),
    re.compile(r'\b(ongoing|continues to|tradition of|regular)\b', re.I),
]

# Patterns that indicate COMMUNITY content
COMMUNITY_PATTERNS = [
    re.compile(r'\b(fundrais|donat(ed|ion)|raised funds|contributed)\b', re.I),
    re.compile(r'\b(local (community|residents|people|council|authority))\b', re.I),
    re.compile(r'\b(villagers|parish|town council|borough)\b', re.I),
    re.compile(r'\b(campaign(ed)?|petition|effort|project)\b', re.I),
    re.compile(r'\b(school|children|pupils|students|teacher)\b', re.I),
    re.compile(r'\b(sponsored|funded by|paid for|grant)\b', re.I),
    re.compile(r'\b(cooperation|collaboration|partnership|volunteer)\b', re.I),
    re.compile(r'\b(appreciation|gratitude|thank|grateful)\b', re.I),
]

# Patterns that indicate CREW BIOGRAPHY content
CREW_BIO_PATTERNS = [
    re.compile(r'\b(born in|grew up|raised in|childhood)\b', re.I),
    re.compile(r'\b(before the war|pre-war|peacetime|civilian)\b', re.I),
    re.compile(r'\b(joined the (RAF|RCAF|RAAF|RNZAF|USAAF)|enlist(ed)?|volunteer(ed)?)\b', re.I),
    re.compile(r'\b(trained at|training at|OTU|posted to)\b', re.I),
    re.compile(r'\b(married|wife|husband|fiancée|sweetheart)\b', re.I),
    re.compile(r'\b(son of|daughter of|father (was|had)|mother)\b', re.I),
    re.compile(r'\b(family|brother|sister|survived by)\b', re.I),
    re.compile(r'\b(education|university|school|apprentice)\b', re.I),
]

# Patterns that indicate JUNK / NOT RELEVANT to this memorial
JUNK_PATTERNS = [
    re.compile(r'\b(click here|read more|visit our|website|homepage|navigation)\b', re.I),
    re.compile(r'\b(cookie|privacy policy|terms of use|subscribe|newsletter)\b', re.I),
    re.compile(r'\b(all rights reserved|copyright|©)\b', re.I),
    re.compile(r'\b(help desk|contact us for|support ticket)\b', re.I),
]


def score_sentence(sentence, patterns):
    """Score a sentence against a list of regex patterns. Returns count of matches."""
    return sum(1 for p in patterns if p.search(sentence))


def classify_sentence(sentence):
    """Classify a sentence into the most likely section.
    Returns (section_name, confidence) where confidence is the match count.
    """
    scores = {
        'narrative': score_sentence(sentence, CRASH_PATTERNS),
        'memorial_details': score_sentence(sentence, MEMORIAL_PATTERNS),
        'remembrance': score_sentence(sentence, REMEMBRANCE_PATTERNS),
        'community_connection': score_sentence(sentence, COMMUNITY_PATTERNS),
        'crew_bio': score_sentence(sentence, CREW_BIO_PATTERNS),
        'junk': score_sentence(sentence, JUNK_PATTERNS),
    }

    best = max(scores, key=scores.get)
    confidence = scores[best]

    # If no strong signal, return 'neutral'
    if confidence == 0:
        return 'neutral', 0

    # If top two are tied, it's ambiguous
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0] == sorted_scores[1]:
        return 'ambiguous', confidence

    return best, confidence


def split_sentences(text):
    """Split text into sentences, preserving meaningful boundaries."""
    if not text or not text.strip():
        return []
    # Split on sentence-ending punctuation followed by space/newline
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Also split on double newlines (paragraph breaks)
    result = []
    for s in sentences:
        parts = re.split(r'\n\n+', s)
        result.extend(p.strip() for p in parts if p.strip())
    return [s for s in result if len(s) > 10]  # Skip tiny fragments


def score_memorial_relevancy(sentence, memorial):
    """Pass 1: Is this sentence relevant to this specific memorial?
    Returns True if relevant, False if junk/unrelated.
    """
    # Junk check
    if score_sentence(sentence, JUNK_PATTERNS) > 0:
        return False

    # Binary/corrupted data check
    if re.search(r'[\x00-\x08\x0e-\x1f]', sentence) or sentence.count('?') > len(sentence) * 0.1:
        return False

    # Very short or generic
    if len(sentence) < 15:
        return True  # Too short to judge

    return True  # Default: keep. We're conservative — only remove clear junk.


def assess_narrative_specificity(text, memorial):
    """Pass 1 whole-field check: Is this narrative about THIS memorial?

    Scores the full narrative against memorial-specific context.
    Returns (is_specific, specificity_score) where:
      - is_specific=True: keep the narrative
      - is_specific=False: narrative is a generic article dump, should be cleared

    We check: crew names, location name, aircraft serial, squadron number.
    A narrative that mentions NONE of these in 800+ chars is almost certainly
    a scraped article about the broader topic, not this specific crash.
    """
    if not text or len(text) < 400:
        return True, 999  # Short narratives get a pass

    text_lower = text.lower()
    score = 0

    # Check crew names (only names with 2+ words to avoid false positives)
    # Common short surnames that appear in general text — require full name match
    COMMON_SURNAMES = {
        'smith', 'jones', 'brown', 'wilson', 'taylor', 'williams', 'ross',
        'clark', 'hall', 'hill', 'king', 'lee', 'wood', 'young', 'white',
        'bell', 'ward', 'cook', 'moore', 'allen', 'martin', 'scott', 'green',
        'wright', 'baker', 'adams', 'davis', 'lewis', 'walker', 'evans',
        'thomas', 'roberts', 'jackson', 'morgan', 'harris', 'thompson', 'cole',
        'day', 'page', 'ford', 'hunt', 'west', 'shaw', 'long', 'fox',
        'read', 'cross', 'north', 'east', 'new', 'mean', 'over', 'under',
    }
    crew_names = [
        c.get('name', '').strip().lower()
        for c in memorial.get('crew', [])
        if c.get('name') and len(c.get('name', '').strip()) > 5
        and c.get('name', '').strip().lower() != 'unknown'
    ]
    for name in crew_names:
        parts = name.split()
        if len(parts) >= 2:
            surname = parts[-1]
            if surname in COMMON_SURNAMES:
                # For common surnames, require the full name
                if name in text_lower:
                    score += 2
                    break
            elif len(surname) > 3 and surname in text_lower:
                score += 2
                break
        elif name in text_lower:
            score += 2
            break

    # Check location name — try multiple location words, county too
    location = (memorial.get('location_name') or '').strip().lower()
    county = (memorial.get('county') or '').strip().lower()

    def clean_words(text):
        """Extract clean words from a location/station string."""
        # Remove parenthetical content, strip punctuation
        text = re.sub(r'\([^)]*\)', '', text)
        words = re.split(r'[\s,/]+', text)
        return [re.sub(r'[^a-z]', '', w) for w in words
                if len(re.sub(r'[^a-z]', '', w)) > 3
                and re.sub(r'[^a-z]', '', w) not in ('near', 'area', 'the', 'site', 'from')]

    if location:
        loc_words = clean_words(location)
        for w in loc_words:
            if w in text_lower:
                score += 2
                break
    if county and len(county) > 4:
        county_clean = re.sub(r'[^a-z\s]', '', county).strip()
        if county_clean and county_clean in text_lower:
            score += 1

    # Check station name
    station = (memorial.get('station') or '').strip().lower()
    if station:
        station_words = clean_words(station)
        # Also check full station name (e.g. "RAF Lichfield")
        station_clean = re.sub(r'[^a-z\s]', '', station).strip()
        if station_clean and station_clean in text_lower:
            score += 2
        else:
            for w in station_words:
                if w not in ('raf',) and w in text_lower:
                    score += 2
                    break

    # Check aircraft serial — also check in title/ID since serial_number field may be empty
    serial = (memorial.get('serial_number') or '').strip().lower()
    if serial and len(serial) > 2 and serial in text_lower:
        score += 2
    else:
        # Try extracting serial from the memorial ID (e.g. "bleasby-4-jb132" → "jb132")
        id_str = (memorial.get('id') or '').lower()
        id_serial_match = re.search(r'[a-z]{1,2}\d{3,4}', id_str)
        if id_serial_match and id_serial_match.group() in text_lower:
            score += 2

    # Check squadron number (just the number part)
    squadron = (memorial.get('squadron') or '').strip()
    sq_match = re.search(r'(\d+)', squadron)
    if sq_match:
        sq_num = sq_match.group(1)
        if re.search(r'\b' + sq_num + r'\b', text):
            score += 1

    # Check memorial title words
    title = (memorial.get('title') or '').lower()
    title_words = [w for w in title.split() if len(w) > 4 and w not in ('memorial', 'bomber', 'command', 'crash', 'lancaster', 'halifax', 'wellington')]
    title_matches = sum(1 for w in title_words if w in text_lower)
    if title_matches >= 2:
        score += 1

    # Check aircraft type mentioned alongside crash-specific language
    aircraft = (memorial.get('aircraft_type') or '').strip().lower()
    if aircraft and len(aircraft) > 3 and aircraft in text_lower:
        # Aircraft type alone isn't specific enough (lots of articles mention "Lancaster")
        # But if combined with any crash keyword, count it
        if any(p.search(text) for p in CRASH_PATTERNS[:6]):
            score += 1

    # Binary/corrupted data — immediate fail
    non_ascii = sum(1 for c in text[:200] if ord(c) > 127)
    if non_ascii > 20:
        return False, -1

    # Site header patterns — "Article Title | SiteName" at the start
    # These are always scraped article dumps regardless of content relevancy
    if re.match(r'^.{0,80}\|', text):
        return False, -2

    # "Site Name - Article Title" pattern at start
    if re.match(r'^[A-Z][^.]{0,50}\s[-–—]\s', text) and not any(p.search(text[:100]) for p in CRASH_PATTERNS[:3]):
        score -= 2

    # Starts with "Welcome to" or similar site chrome
    if re.match(r'^(Welcome to|About|Home|Navigation|Menu|Search)', text, re.I):
        return False, -3

    # Threshold: long narratives (800+ chars) need at least score 2 to pass
    # Medium narratives (400-800) need at least score 1
    if len(text) >= 800:
        return score >= 2, score
    elif len(text) >= 400:
        return score >= 1, score
    else:
        return True, score


def process_text_field(text, current_section, memorial_id, memorial):
    """Process a text field: score each sentence for section relevancy.
    Returns (cleaned_text, moves, removals) where:
      - cleaned_text: text with misplaced sentences removed
      - moves: list of (sentence, target_section) for sentences that belong elsewhere
      - removals: list of (sentence, reason) for junk
    """
    if not text or not text.strip():
        return text, [], []

    sentences = split_sentences(text)
    kept = []
    moves = []
    removals = []

    for sentence in sentences:
        # Pass 1: Memorial-level relevancy
        if not score_memorial_relevancy(sentence, memorial):
            removals.append((sentence, 'junk'))
            continue

        # Pass 2: Section-level relevancy
        target_section, confidence = classify_sentence(sentence)

        if target_section == 'neutral' or target_section == 'ambiguous':
            # No strong signal — keep in current section
            kept.append(sentence)
        elif target_section == current_section:
            # Already in the right section
            kept.append(sentence)
        elif confidence >= 2:
            # Strong signal it belongs elsewhere — move it
            moves.append((sentence, target_section))
        else:
            # Weak signal (confidence=1) — keep in place, not confident enough to move
            kept.append(sentence)

    cleaned = ' '.join(kept) if kept else ''
    return cleaned, moves, removals


def process_remembrance_events(events, memorial_id, memorial):
    """Process remembrance events: classify each event.
    Returns (kept_events, memorial_events, other_moves).
    """
    kept = []
    memorial_events = []  # Should be in memorial_details
    other_moves = []

    for event in events:
        if not isinstance(event, dict):
            kept.append(event)
            continue

        name = event.get('name', '')
        desc = event.get('description', '')
        combined = f"{name}. {desc}"

        # First check: does the event NAME itself indicate a memorial event?
        name_is_memorial = any(p.search(name) for p in MEMORIAL_EVENT_NAME_PATTERNS)

        target, confidence = classify_sentence(combined)

        if name_is_memorial or (target == 'memorial_details' and confidence >= 1):
            # This is a dedication/unveiling/display — belongs in memorial details
            memorial_events.append(event)
        elif target == 'narrative' and confidence >= 2:
            # This is crash content — shouldn't be in remembrance
            other_moves.append((event, 'narrative'))
        else:
            # Keep in remembrance
            kept.append(event)

    return kept, memorial_events, other_moves


def process_memorial(data, memorial_id):
    """Process a single memorial through both passes.
    Returns (modified_data, changes_log).
    """
    changes = []
    modified = copy.deepcopy(data)
    sentences_to_add = {}  # section -> [sentences]

    # Pass 0: Remove extraction meta-descriptions
    # "The text describes..." / "This content is about..." — artefacts from Granite extraction
    META_DESC_RE = re.compile(
        r'^(The (text|content|section|passage|memorial|community|narrative) '
        r'(describes|is about|contains|discusses|mentions|refers to|details|outlines|provides))',
        re.I
    )
    for field in ['narrative', 'community_connection']:
        val = (modified.get(field) or '').strip()
        if val and META_DESC_RE.match(val):
            # Check if it contains memorial description content worth saving
            mem_content_match = len(re.findall(
                r'\b(plaque|inscription|memorial|tablet|stone|cairn|dedicated)\b', val, re.I
            ))
            if mem_content_match >= 2:
                # Move to memorial_details instead of discarding
                changes.append(f'  [{memorial_id}] {field} → memorial_details (meta-desc with memorial content): "{val[:80]}..."')
                sentences_to_add.setdefault('memorial_details', []).append(val)
            else:
                changes.append(f'  [{memorial_id}] {field} CLEARED — extraction meta-description: "{val[:80]}..."')
            modified[field] = ''

    # Pass 1 whole-field: Check if narrative is a generic article dump
    narrative = (modified.get('narrative') or '').strip()
    if narrative:
        is_specific, spec_score = assess_narrative_specificity(narrative, modified)
        if not is_specific:
            changes.append(f'  [{memorial_id}] NARRATIVE CLEARED — article dump (specificity={spec_score}, len={len(narrative)}): "{narrative[:80]}..."')
            modified['narrative'] = ''
            narrative = ''

    # Pass 1 whole-field: Check community_connection for article dumps too
    community_raw = (modified.get('community_connection') or '').strip()
    if community_raw:
        is_specific_cc, spec_score_cc = assess_narrative_specificity(community_raw, modified)
        if not is_specific_cc:
            changes.append(f'  [{memorial_id}] COMMUNITY CLEARED — article dump (specificity={spec_score_cc}, len={len(community_raw)}): "{community_raw[:80]}..."')
            modified['community_connection'] = ''
            community_raw = ''

    # Pass 2 sentence-level: Process narrative (What Happened)
    narrative = (modified.get('narrative') or '').strip()
    if narrative:
        cleaned, moves, removals = process_text_field(
            narrative, 'narrative', memorial_id, modified
        )
        if moves or removals:
            modified['narrative'] = cleaned
            for sentence, target in moves:
                changes.append(f'  [{memorial_id}] narrative → {target}: "{sentence[:60]}..."')
                sentences_to_add.setdefault(target, []).append(sentence)
            for sentence, reason in removals:
                changes.append(f'  [{memorial_id}] narrative REMOVED ({reason}): "{sentence[:60]}..."')

    # Pass 2 sentence-level: Process community_connection
    community = (modified.get('community_connection') or '').strip()
    if community:
        cleaned, moves, removals = process_text_field(
            community, 'community_connection', memorial_id, modified
        )
        if moves or removals:
            modified['community_connection'] = cleaned
            for sentence, target in moves:
                changes.append(f'  [{memorial_id}] community → {target}: "{sentence[:60]}..."')
                sentences_to_add.setdefault(target, []).append(sentence)
            for sentence, reason in removals:
                changes.append(f'  [{memorial_id}] community REMOVED ({reason}): "{sentence[:60]}..."')

    # Process remembrance
    remembrance = modified.get('remembrance')
    if remembrance:
        if isinstance(remembrance, dict) and 'events' in remembrance:
            events = remembrance.get('events', [])
            kept_events, memorial_events, other_moves = process_remembrance_events(
                events, memorial_id, modified
            )
            if memorial_events or other_moves:
                remembrance['events'] = kept_events
                modified['remembrance'] = remembrance
                for event in memorial_events:
                    name = event.get('name', 'unnamed')
                    changes.append(f'  [{memorial_id}] remembrance → memorial_details: event "{name[:60]}"')
                    # Build dedication text from event
                    desc = event.get('description', '')
                    date = event.get('date', '')
                    ded_text = f"{name}"
                    if date:
                        ded_text += f" ({date})"
                    if desc:
                        ded_text += f": {desc}"
                    sentences_to_add.setdefault('memorial_details', []).append(ded_text)
                for event, target in other_moves:
                    name = event.get('name', 'unnamed') if isinstance(event, dict) else str(event)
                    changes.append(f'  [{memorial_id}] remembrance → {target}: event "{name[:60]}"')

        elif isinstance(remembrance, list):
            kept_events, memorial_events, other_moves = process_remembrance_events(
                remembrance, memorial_id, modified
            )
            if memorial_events or other_moves:
                modified['remembrance'] = kept_events if kept_events else None
                for event in memorial_events:
                    name = event.get('name', 'unnamed') if isinstance(event, dict) else str(event)
                    changes.append(f'  [{memorial_id}] remembrance → memorial_details: event "{name[:60]}"')
                    desc = event.get('description', '') if isinstance(event, dict) else ''
                    date = event.get('date', '') if isinstance(event, dict) else ''
                    ded_text = f"{name}"
                    if date:
                        ded_text += f" ({date})"
                    if desc:
                        ded_text += f": {desc}"
                    sentences_to_add.setdefault('memorial_details', []).append(ded_text)

    # Apply moved sentences to their target sections
    for target_section, sentences in sentences_to_add.items():
        if target_section == 'memorial_details':
            # Append to memorial_details as text
            existing = modified.get('memorial_details', '')
            if isinstance(existing, dict):
                # memorial_details is sometimes a dict — append to description
                existing_desc = existing.get('description', '')
                existing['description'] = (existing_desc + '\n\n' + '\n\n'.join(sentences)).strip()
                modified['memorial_details'] = existing
            else:
                existing = existing or ''
                modified['memorial_details'] = (existing + '\n\n' + '\n\n'.join(sentences)).strip()

        elif target_section == 'narrative':
            existing = modified.get('narrative', '') or ''
            modified['narrative'] = (existing + '\n\n' + '\n\n'.join(sentences)).strip()

        elif target_section == 'community_connection':
            existing = modified.get('community_connection', '') or ''
            modified['community_connection'] = (existing + '\n\n' + '\n\n'.join(sentences)).strip()

    # Pass 3: Cross-section awareness
    # If community_connection is about the memorial AND memorial_details already has content,
    # the community text is redundant — move unique parts or clear
    community_final = (modified.get('community_connection') or '').strip()
    md_final = modified.get('memorial_details', '')
    md_final_str = md_final if isinstance(md_final, str) else md_final.get('description', '') if isinstance(md_final, dict) else str(md_final)
    md_final_len = len(md_final_str)

    if community_final and md_final_len > 100:
        # Count memorial-related words in community
        mem_word_count = len(re.findall(
            r'\b(memorial|plaque|tablet|inscription|erected|dedicated|stone|cairn|monument|unveil|dedicat)\b',
            community_final, re.I
        ))
        # Count actual community words
        comm_word_count = len(re.findall(
            r'\b(fundrais|donat|community|village|parish|resident|campaign|school|volunteer|local people|raised)\b',
            community_final, re.I
        ))

        # Also check for genuine community narrative (local impact, human stories)
        community_narrative_words = len(re.findall(
            r'\b(crash|farmer|family|bodies|buried|recovered|planted|trees?|local|villager|mark|spot|memory|home)\b',
            community_final, re.I
        ))

        if mem_word_count >= 3 and comm_word_count == 0 and community_narrative_words == 0:
            # Clearly all memorial-description content, no community story — clear it
            changes.append(f'  [{memorial_id}] community CLEARED — memorial content redundant with memorial_details ({mem_word_count} memorial words, 0 community words)')
            modified['community_connection'] = ''

    # Pass 3b: Check remembrance events that are actually crash events
    rem_final = modified.get('remembrance')
    if rem_final:
        events_list = []
        if isinstance(rem_final, dict):
            events_list = rem_final.get('events', [])
        elif isinstance(rem_final, list):
            events_list = rem_final

        kept_events = []
        for event in events_list:
            if not isinstance(event, dict):
                kept_events.append(event)
                continue
            name = event.get('name', '')
            desc = event.get('description', '')
            combined = f"{name}. {desc}"

            # Check if this is primarily crash content
            crash_score = score_sentence(combined, CRASH_PATTERNS)
            rem_score = score_sentence(combined, REMEMBRANCE_PATTERNS)
            mem_score = score_sentence(combined, MEMORIAL_PATTERNS)

            if crash_score >= 1 and rem_score == 0 and mem_score == 0:
                changes.append(f'  [{memorial_id}] remembrance event REMOVED — crash content: "{name[:60]}"')
            elif re.match(r'^(memorial of|crash of|next of kin|collision|flight |squadron )', name, re.I):
                # Not remembrance events — person memorials, crash references, crew data
                changes.append(f'  [{memorial_id}] remembrance event REMOVED — non-remembrance: "{name[:60]}"')
            else:
                kept_events.append(event)

        if len(kept_events) != len(events_list):
            if isinstance(rem_final, dict):
                rem_final['events'] = kept_events
                modified['remembrance'] = rem_final
            elif isinstance(rem_final, list):
                modified['remembrance'] = kept_events if kept_events else None

    return modified, changes


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.json')))
    if not files:
        print(f'ERROR: No memorial files found in {DATA_DIR}')
        sys.exit(1)

    total_changes = []
    files_modified = 0
    total_moves = 0
    total_removals = 0

    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)

        memorial_id = data.get('id', os.path.basename(filepath).replace('.json', ''))
        modified, changes = process_memorial(data, memorial_id)

        if changes:
            total_changes.extend(changes)
            files_modified += 1
            moves = sum(1 for c in changes if '→' in c and 'REMOVED' not in c)
            removals = sum(1 for c in changes if 'REMOVED' in c)
            total_moves += moves
            total_removals += removals

            if not dry_run:
                with open(filepath, 'w') as f:
                    json.dump(modified, f, indent=2, ensure_ascii=False)
                    f.write('\n')

    # Summary
    print()
    print('BMR Section Relevancy Scorer')
    print('=' * 50)
    print(f'Files scanned:    {len(files)}')
    print(f'Files modified:   {files_modified}')
    print(f'Sentences moved:  {total_moves}')
    print(f'Sentences removed: {total_removals}')
    print(f'Mode:             {"DRY RUN" if dry_run else "APPLIED"}')
    print()

    # Categorize moves
    move_cats = {}
    for c in total_changes:
        if '→' in c and 'REMOVED' not in c:
            # Extract "source → target"
            parts = c.split('→')
            if len(parts) >= 2:
                source = parts[0].split(']')[-1].strip()
                target = parts[1].split(':')[0].strip()
                key = f'{source} → {target}'
                move_cats[key] = move_cats.get(key, 0) + 1

    if move_cats:
        print('Move categories:')
        for cat, count in sorted(move_cats.items(), key=lambda x: -x[1]):
            print(f'  {cat}: {count}')
        print()

    if verbose or dry_run:
        print('Changes:')
        for c in total_changes:
            print(c)


if __name__ == '__main__':
    main()
