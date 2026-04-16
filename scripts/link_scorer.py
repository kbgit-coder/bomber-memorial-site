#!/usr/bin/env python3
"""
BMR Link Relevancy Scorer — v3.0

Scores outbound links discovered during scraping against the five dimensions
defined in Plans/2026-04-10_SPE_Link-Relevancy-Scorecard-v3.0.md.

Usage:
    from link_scorer import score_link, LinkScore

    score = score_link(
        anchor_text="Lancaster ED559 of 44 Squadron",
        target_url="https://aircrewremembered.com/ed559",
        source_url="https://example.com/page",
        link_position="content",
        surrounding_context="...text around the link...",
        source_domain_type="squadron_association",
    )
    print(score.total, score.tier, score.components)
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

# ─── Configuration ──────────────────────────────────────────────────

# Known bot-blocked domains (from scrape_provenance.py)
BOT_BLOCKED_DOMAINS = {
    "tracesofwar.com", "www.tracesofwar.com",
    "americanairmuseum.com", "www.americanairmuseum.com",
    "peakdistrict.gov.uk", "www.peakdistrict.gov.uk",
    "dartmoor.gov.uk", "www.dartmoor.gov.uk",
    "raf.mod.uk", "www.raf.mod.uk",
}

# Generic UI text — anchor text that indicates navigation/chrome
GENERIC_ANCHORS = {
    "click here", "read more", "home", "more info", "here", "link",
    "this link", "previous", "next", "back", "top", "menu", "skip to content",
    "contact", "about", "privacy", "terms", "cookie", "search",
    "share", "facebook", "twitter", "instagram", "email", "print",
    "subscribe", "login", "log in", "sign up", "register",
    "more", "view", "see more", "view more", "details", "learn more",
    "download", "help", "faq", "sitemap",
}

# Commercial content farm and clickbait domain patterns
CONTENT_FARM_PATTERNS = [
    r"buzzfeed", r"clickhole", r"listverse", r"answers\.com",
    r"ezinearticles", r"hubpages", r"squidoo", r"wikihow",
]

# Primary source references — for Dimension D
PRIMARY_SOURCE_KEYWORDS = [
    "cwgc", "commonwealth war graves",
    "national archives", "nationalarchives", "tna",
    "operational record book", "orb ",
    "squadron diary", "squadron diaries",
    "abmc", "american battle monuments",
    "combat report", "mission report",
    "iwm collections", "imperial war museum collections",
    "air historical branch", "ahb",
]


# ─── Subject specificity patterns ──────────────────────────────────

# Aircraft serial patterns
AIRCRAFT_SERIAL_PATTERNS = [
    re.compile(r"\b[A-Z]{2}\d{3}\b"),       # ED559, LM292, W4232
    re.compile(r"\b[A-Z]\d{4}\b"),           # W5719, R1014
    re.compile(r"\b[A-Z]{2}\d{4}\b"),        # LL505, NG269
    re.compile(r"\b\d{2}-\d{4,5}\b"),        # USAAF: 42-31322, 44-61999
]

# Squadron number patterns
SQUADRON_PATTERNS = [
    re.compile(r"\b\d{1,3}\s*(?:squadron|sqn|sqdn)\b", re.IGNORECASE),
    re.compile(r"\bno\.?\s*\d{1,3}\s*(?:squadron|sqn)\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:st|nd|rd|th)\s+(?:bomb|bombardment)\s+group\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}\s*bg\b", re.IGNORECASE),
]

# Crew name patterns (rank prefix + name)
CREW_RANK_PATTERN = re.compile(
    r"\b(?:f/o|sgt|p/o|f/l|s/l|w/o|f/sgt|g/c|w/c|"
    r"sergeant|pilot\s+officer|flying\s+officer|flight\s+(?:lieutenant|sergeant)|"
    r"squadron\s+leader|warrant\s+officer|wing\s+commander|group\s+captain)\.?\s+"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}",
    re.IGNORECASE,
)

# Crash / memorial keywords
CRASH_KEYWORDS = [
    "crash", "crashed", "crashing", "memorial", "wreck", "wreckage",
    "crew", "lost", "fallen", "killed", "died", "casualty", "casualties",
    "commemorate", "commemoration", "remembrance", "tribute",
    "shot down", "missing", "mia", "kia",
]

# Aircraft types
AIRCRAFT_TYPES = [
    "lancaster", "halifax", "wellington", "stirling", "mosquito",
    "hampden", "manchester", "whitley", "blenheim", "beaufort", "hudson",
    "b-17", "b17", "b-24", "b24", "flying fortress", "liberator", "fortress",
    "mitchell", "boston", "marauder",
]

# WW2 date pattern
WW2_DATE_PATTERN = re.compile(r"\b19(?:39|4[0-5])\b")

# Recent date patterns (for freshness approximation)
RECENT_DATE_PATTERN = re.compile(r"\b(202[0-6])\b")
RECENT_5Y_PATTERN = re.compile(r"\b(201[9]|202[0-6])\b")


# ─── Domain type classification ─────────────────────────────────────

def classify_domain_type(domain: str) -> str:
    """
    Classify a domain into a type for authority scoring.
    Returns one of: official_archive, squadron_association, individual_research,
    community_family, blog, aggregator, content_farm, unknown.
    """
    d = domain.lower().replace("www.", "")

    # Content farms
    for pattern in CONTENT_FARM_PATTERNS:
        if re.search(pattern, d):
            return "content_farm"

    # Official archives
    if any(k in d for k in [
        ".gov.uk", ".gov.au", ".gov.ca", ".gc.ca", ".mil",
        ".edu", ".ac.uk",
        "cwgc", "nationalarchives", "archives.gov", "awm.gov",
        "ibccdigitalarchive", "iwm.org.uk", "imperialwarmuseum",
        "bombercommandmuseum", "ahb", "abmc.gov",
    ]):
        return "official_archive"

    # Squadron associations / heritage groups / research projects
    if any(k in d for k in [
        "squadron", "sqn", "sqdn", "association",
        "bomb-group", "bombgroup", "bg-museum", "bgmuseum",
        "heritage", "history-society", "historysociety",
        "aviationarchaeology", "aviationtrails", "peakdistrictaircrashes",
        "dambusters", "pathfinders", "aircrewremembered",
        "warmemorialsonline", "rememberthefallen", "rolls-of-honour",
        "rollofhonour",
    ]):
        return "squadron_association"

    # Community/parish/family projects
    if any(k in d for k in [
        "parish.lincolnshire.gov.uk", "parishcouncil", "parish-council",
        "villagehall", "village.co.uk", "community.",
        "familyhistory", "genealogy",
    ]):
        return "community_family"

    # Known wikis
    if any(k in d for k in ["wikipedia", "wikia", "wiki.", ".wiki"]):
        return "aggregator"

    # Blog platforms
    if any(k in d for k in [
        "wordpress.com", "blogspot", "tumblr", "medium.com",
        "substack", "livejournal", "weebly", "wixsite",
    ]):
        return "blog"

    # Forums
    if any(k in d for k in ["forum", "reddit", "quora"]):
        return "blog"  # Treat forums as blogs for scoring

    # Social media
    if any(k in d for k in [
        "facebook.com", "twitter.com", "x.com", "instagram.com",
        "youtube.com", "linkedin.com", "tiktok.com", "flickr.com",
    ]):
        return "blog"

    # Local news aggregators
    if any(k in d for k in [
        "news", "telegraph", "advertiser", "gazette",
        "mercury", "herald", "times", "journal", "express",
    ]):
        return "aggregator"

    return "unknown"


# ─── Score dataclass ────────────────────────────────────────────────

@dataclass
class LinkScore:
    total: float = 0.0
    normalised: float = 0.0
    tier: str = "NOISE"
    dimension_a: float = 0.0  # Subject Specificity
    dimension_b: float = 0.0  # Content Depth
    dimension_c: float = 0.0  # Source Authority
    dimension_d: float = 0.0  # Content Substance
    dimension_e: float = 0.0  # Freshness
    components: dict = field(default_factory=dict)
    scrape_status: str = "unknown"
    unscrapable_reason: str = None
    outreach_candidate: bool = False

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "normalised": self.normalised,
            "tier": self.tier,
            "dimensions": {
                "A_subject_specificity": self.dimension_a,
                "B_content_depth": self.dimension_b,
                "C_source_authority": self.dimension_c,
                "D_content_substance": self.dimension_d,
                "E_freshness": self.dimension_e,
            },
            "components": self.components,
        }


# ─── Dimension A: Subject Specificity ───────────────────────────────

def score_subject_specificity(anchor: str, target_url: str, known_locations: set = None) -> tuple[float, dict]:
    """Dimension A: 0-30 points."""
    components = {}
    total = 0.0
    hits = 0

    anchor_lower = anchor.lower() if anchor else ""
    url_lower = target_url.lower() if target_url else ""
    combined = f"{anchor_lower} {url_lower}"

    def award(name: str, points: float):
        nonlocal total, hits
        # Diminishing returns: 1st hit full, 2nd hit 75%, 3rd hit 50%, 4th+ 25%
        if hits == 0:
            multiplier = 1.0
        elif hits == 1:
            multiplier = 0.75
        elif hits == 2:
            multiplier = 0.5
        else:
            multiplier = 0.25
        awarded = points * multiplier
        components[name] = awarded
        total += awarded
        hits += 1

    # Aircraft serial (+10)
    for pattern in AIRCRAFT_SERIAL_PATTERNS:
        if pattern.search(anchor) or pattern.search(target_url):
            award("aircraft_serial", 10)
            break

    # Named crew member (+8)
    if CREW_RANK_PATTERN.search(anchor):
        award("crew_name", 8)

    # Squadron number (+8)
    for pattern in SQUADRON_PATTERNS:
        if pattern.search(combined):
            award("squadron_reference", 8)
            break

    # Crash / memorial keywords (+6)
    if any(kw in anchor_lower for kw in CRASH_KEYWORDS):
        award("crash_memorial_keywords", 6)

    # Aircraft type (+5)
    if any(at in anchor_lower for at in AIRCRAFT_TYPES):
        award("aircraft_type", 5)

    # Known memorial location (fuzzy match) (+5)
    if known_locations:
        for loc in known_locations:
            loc_norm = loc.lower().replace("-", " ").replace("_", " ")
            if len(loc_norm) > 3 and loc_norm in anchor_lower:
                award("location_match", 5)
                components["location_match_name"] = loc
                break

    # WW2 date range (+3)
    if WW2_DATE_PATTERN.search(combined):
        award("ww2_date", 3)

    # Generic memorial/war keyword (+2)
    if ("memorial" in anchor_lower or "war" in anchor_lower) and "memorial_reference" not in components:
        award("generic_memorial_war", 2)

    # Cap at 30
    total = min(total, 30.0)
    return total, components


# ─── Dimension B: Content Depth ─────────────────────────────────────

def score_content_depth(anchor: str, target_url: str, link_position: str, surrounding_context: str) -> tuple[float, dict]:
    """Dimension B: 0-20 points."""
    components = {}
    total = 0.0

    anchor_lower = (anchor or "").strip().lower()

    # Penalty: generic UI text → skip scoring for this dimension
    if anchor_lower in GENERIC_ANCHORS or len(anchor_lower) < 3:
        components["skipped_generic_anchor"] = True
        return 0.0, components

    # Anchor text length > 30 chars (+5)
    if len(anchor) > 30:
        components["long_anchor_text"] = 5
        total += 5

    # Link position in main content (+5)
    if link_position == "content":
        components["main_content_position"] = 5
        total += 5

    # Context mentions specific details (+4)
    if surrounding_context:
        ctx_lower = surrounding_context.lower()
        has_date = bool(re.search(r"\b(19[3-4]\d|20\d{2})\b", surrounding_context))
        has_capital_name = bool(re.search(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b", surrounding_context))
        if has_date and has_capital_name:
            components["context_specific_details"] = 4
            total += 4

    # URL path suggests article (not category/tag/archive) (+3)
    if target_url:
        parsed = urlparse(target_url)
        path = parsed.path.lower()
        bad_patterns = ["/category/", "/tag/", "/archive/", "/search/", "/index", "/page/"]
        if path and path != "/" and not any(bp in path for bp in bad_patterns):
            components["article_path"] = 3
            total += 3

        # URL depth > 2 levels (+2)
        depth = len([p for p in path.split("/") if p])
        if depth > 2:
            components["deep_url_path"] = 2
            total += 2

        # Target is document file (+1)
        if any(path.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".rtf"]):
            components["document_file"] = 1
            total += 1

    return min(total, 20.0), components


# ─── Dimension C: Source Authority ──────────────────────────────────

DOMAIN_TYPE_POINTS = {
    "official_archive": 8,
    "squadron_association": 7,
    "individual_research": 6,
    "community_family": 4,
    "blog": 2,
    "aggregator": 1,
    "unknown": 1,
    "content_farm": -3,
}


def score_source_authority(target_domain: str) -> tuple[float, dict]:
    """Dimension C: 0-20 points."""
    components = {}
    total = 0.0

    domain_type = classify_domain_type(target_domain)
    components["domain_type"] = domain_type
    type_points = DOMAIN_TYPE_POINTS.get(domain_type, 1)
    components["domain_type_points"] = type_points
    total += type_points

    # Clamp to 0-20 range (allowing negative for content farms)
    return max(min(total, 20.0), -3.0), components


# ─── Dimension D: Content Substance ─────────────────────────────────

def score_content_substance(anchor: str, surrounding_context: str, target_url: str) -> tuple[float, dict]:
    """Dimension D: 0-15 points (pre-fetch approximation)."""
    components = {}
    total = 0.0

    combined = f"{anchor or ''} {surrounding_context or ''} {target_url or ''}".lower()

    # Primary source reference (+4) — pre-fetch approximation from context
    for keyword in PRIMARY_SOURCE_KEYWORDS:
        if keyword in combined:
            components["primary_source_ref"] = 4
            components["primary_source_matched"] = keyword
            total += 4
            break

    # Specific details in context (+3)
    if surrounding_context:
        has_full_date = bool(re.search(r"\b\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+19[3-4]\d\b", surrounding_context))
        has_location = bool(re.search(r"\bat\s+[A-Z][a-z]+", surrounding_context))
        if has_full_date or has_location:
            components["specific_details"] = 3
            total += 3

    # Long context around link (proxy for substantive content) (+3)
    if surrounding_context and len(surrounding_context) > 200:
        components["rich_context"] = 3
        total += 3

    # Note: full word count and image/caption signals require post-fetch
    # They will be computed in Stage 2 scoring

    return min(total, 15.0), components


# ─── Dimension E: Freshness ─────────────────────────────────────────

def score_freshness(target_url: str, surrounding_context: str, anchor: str) -> tuple[float, dict]:
    """Dimension E: -3 to +10 points (pre-fetch approximation)."""
    components = {}
    total = 0.0

    combined = f"{target_url or ''} {surrounding_context or ''} {anchor or ''}"

    # Recent date in URL or context (+5)
    if RECENT_DATE_PATTERN.search(combined):
        components["recent_activity"] = 5
        total += 5
    # Within 5 years (+3)
    elif RECENT_5Y_PATTERN.search(combined):
        components["active_5y"] = 3
        total += 3

    # Note: full freshness signals require post-fetch (page last-modified, copyright dates)
    # Penalties for stale+shallow also require post-fetch content analysis

    return total, components


# ─── Accessibility metadata (not scored) ────────────────────────────

def compute_accessibility(target_domain: str) -> tuple[str, str, bool]:
    """
    Returns (scrape_status, unscrapable_reason, outreach_candidate).
    Pre-fetch this is based only on known bot-blocked list.
    Post-fetch can refine based on response headers/content.
    """
    d = target_domain.lower().replace("www.", "")
    d_www = f"www.{d}"

    if d in BOT_BLOCKED_DOMAINS or d_www in BOT_BLOCKED_DOMAINS:
        return "bot_blocked", "Known bot-blocked domain (pre-fetch classification)", False

    return "unknown", None, False


# ─── Main scoring function ──────────────────────────────────────────

def score_link(
    anchor_text: str,
    target_url: str,
    source_url: str = None,
    link_position: str = "unknown",
    surrounding_context: str = "",
    source_domain_type: str = None,
    known_memorial_locations: set = None,
) -> LinkScore:
    """
    Score a discovered link using the v3.0 scorecard.
    Returns a LinkScore with all dimension scores, final tier, and accessibility metadata.
    """
    score = LinkScore()

    # Parse target URL
    try:
        parsed = urlparse(target_url)
        target_domain = parsed.netloc.replace("www.", "")
    except Exception:
        target_domain = ""

    if not target_domain or not target_url:
        score.tier = "NOISE"
        return score

    # Skip relative links, mailto, tel, javascript
    if target_url.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        score.tier = "NOISE"
        return score

    anchor_text = (anchor_text or "").strip()

    # Compute each dimension
    score.dimension_a, comp_a = score_subject_specificity(
        anchor_text, target_url, known_memorial_locations
    )
    score.dimension_b, comp_b = score_content_depth(
        anchor_text, target_url, link_position, surrounding_context
    )
    score.dimension_c, comp_c = score_source_authority(target_domain)
    score.dimension_d, comp_d = score_content_substance(
        anchor_text, surrounding_context, target_url
    )
    score.dimension_e, comp_e = score_freshness(
        target_url, surrounding_context, anchor_text
    )

    score.components = {
        "A": comp_a, "B": comp_b, "C": comp_c, "D": comp_d, "E": comp_e,
    }

    # Total raw score (range -5 to 95)
    score.total = (
        score.dimension_a + score.dimension_b + score.dimension_c
        + score.dimension_d + score.dimension_e
    )

    # Clamp negatives and normalise
    clamped = max(score.total, 0.0)
    score.normalised = min(clamped / 95.0, 1.0)

    # Assign tier
    if score.normalised >= 0.75:
        score.tier = "PRIMARY"
    elif score.normalised >= 0.50:
        score.tier = "SECONDARY"
    elif score.normalised >= 0.25:
        score.tier = "TERTIARY"
    elif score.normalised >= 0.10:
        score.tier = "BACKGROUND"
    else:
        score.tier = "NOISE"

    # Accessibility metadata
    status, reason, outreach = compute_accessibility(target_domain)
    score.scrape_status = status
    score.unscrapable_reason = reason
    score.outreach_candidate = outreach

    return score


# ─── CLI test ───────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick test
    test_cases = [
        {
            "anchor": "Lancaster ED559 of 617 Squadron lost over the Dortmund-Ems Canal",
            "url": "https://aircrewremembered.com/ed559-dambusters",
            "context": "On the night of 15/16 September 1943, Lancaster ED559 was lost with all crew killed at Ladbergen, Germany.",
            "position": "content",
        },
        {
            "anchor": "Home",
            "url": "https://example.com/",
            "context": "",
            "position": "nav",
        },
        {
            "anchor": "Memorial to Bomber Command",
            "url": "https://www.iwm.org.uk/memorials/item/memorial/86723",
            "context": "The memorial commemorates aircrew killed during WW2 operations.",
            "position": "content",
        },
        {
            "anchor": "Click here",
            "url": "https://www.facebook.com/share.php",
            "context": "",
            "position": "footer",
        },
        {
            "anchor": "TracesOfWar - Lancaster crash sites",
            "url": "https://www.tracesofwar.com/articles/5000/Lancaster-crash-sites.htm",
            "context": "Documented crash sites across Europe including primary CWGC records.",
            "position": "content",
        },
    ]

    known_locations = {"bleasby", "farnsfield", "coningsby"}

    print("=" * 70)
    print("BMR Link Scorer v3.0 — test cases")
    print("=" * 70)

    for i, tc in enumerate(test_cases, 1):
        score = score_link(
            anchor_text=tc["anchor"],
            target_url=tc["url"],
            link_position=tc["position"],
            surrounding_context=tc["context"],
            known_memorial_locations=known_locations,
        )
        print(f"\nTest {i}: {tc['anchor'][:60]}")
        print(f"  URL: {tc['url']}")
        print(f"  A={score.dimension_a:.1f}  B={score.dimension_b:.1f}  "
              f"C={score.dimension_c:.1f}  D={score.dimension_d:.1f}  E={score.dimension_e:.1f}")
        print(f"  Total: {score.total:.1f}/95  Normalised: {score.normalised:.3f}  "
              f"Tier: {score.tier}")
        print(f"  Scrape status: {score.scrape_status}  Outreach: {score.outreach_candidate}")
        if score.unscrapable_reason:
            print(f"  Reason: {score.unscrapable_reason}")
