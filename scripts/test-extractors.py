#!/usr/bin/env python3
"""
Test harness for the BMR extractor architecture.
Pulls stored HTML from the research DB and runs all extraction logic against it.
Tests against 3 diverse site types to validate the design.

Usage: python3 scripts/test-extractors.py
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict

import requests

# ─── Config ──────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"
DB_PASS = "BmrResearch2026xHeritage"

TEST_URLS = [
    # 1. IWM — institutional, structured memorial register
    "https://www.iwm.org.uk/memorials/item/memorial/86723",
    # 2. Peak District Air Crashes — heritage/research site with detailed crash narratives
    "https://www.peakdistrictaircrashes.co.uk/crash_sites/peak-district/vickers-wellington-w5719-upper-tor/",
    # 3. War Memorials Online — community site with condition reports
    "https://www.warmemorialsonline.org.uk/memorial/267102/",
]


# ─── Data structures ────────────────────────────────────────────────

@dataclass
class FetchResult:
    url: str
    domain: str
    status: str
    raw_html: str
    clean_text: str
    title: str
    images: list = field(default_factory=list)
    links: list = field(default_factory=list)
    content_hash: str = ""
    error: str = None


@dataclass
class ExtractionResult:
    data_type: str
    claim_field: str
    field_value: str
    field_context: dict
    confidence: str
    source_excerpt: str
    extraction_method: str


# ─── HTML cleaning ───────────────────────────────────────────────────

def clean_html_to_text(html: str) -> str:
    """Strip HTML to clean text, removing noise sections."""
    # Remove script, style, nav, footer, cookie banners
    for tag in ["script", "style", "nav", "footer", "noscript", "svg"]:
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Remove common noise patterns
    noise_patterns = [
        r'<div[^>]*class="[^"]*(?:cookie|consent|banner|popup|modal|sidebar|nav|menu|footer|header)[^"]*"[^>]*>.*?</div>',
    ]
    for pattern in noise_patterns:
        html = re.sub(pattern, "", html, flags=re.DOTALL | re.IGNORECASE)

    # Extract text from remaining HTML
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"&#\d+;", "", text)
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # But preserve paragraph breaks
    text = re.sub(r"\s{3,}", "\n\n", text)

    return text


def extract_title(html: str) -> str:
    """Extract page title."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else ""


def extract_images(html: str) -> list:
    """Extract img tags with context."""
    images = []
    for match in re.finditer(r'<img[^>]+>', html, re.IGNORECASE):
        tag = match.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if src:
            images.append({
                "url": src.group(1),
                "alt": alt.group(1) if alt else "",
            })
    return images


def extract_links(html: str) -> list:
    """Extract all links with anchor text."""
    links = []
    for match in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        url = match.group(1)
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if url and not url.startswith("#") and not url.startswith("javascript:"):
            links.append({"url": url, "text": text})
    return links


# ─── DB access ───────────────────────────────────────────────────────

def get_stored_html(url: str) -> str | None:
    """Get stored raw HTML from the scrape_log via temp file (avoids stdout issues with large content)."""
    # Write to temp file inside container, then docker cp out
    tmp_file = "/tmp/bmr_test_html.txt"
    # Use COPY to write to file inside container
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c",
         f"\\copy (SELECT raw_content FROM scrape_log WHERE url = '{url}' AND raw_content IS NOT NULL LIMIT 1) TO '{tmp_file}'"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  DB query error: {result.stderr.strip()}")
        return None
    # Copy file out of container
    subprocess.run(["docker", "cp", f"{DB_CONTAINER}:{tmp_file}", tmp_file],
                   capture_output=True, timeout=30)
    if os.path.exists(tmp_file):
        with open(tmp_file) as f:
            content = f.read().strip()
        os.unlink(tmp_file)
        # Unescape psql COPY escapes (\\n → \n, \\\\ → \\)
        content = content.replace("\\n", "\n").replace("\\\\", "\\")
        return content if len(content) > 100 else None
    return None


def fetch_live(url: str) -> str | None:
    """Fetch a URL live as fallback."""
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; BMR-Test/1.0)"})
        resp = urllib.request.urlopen(req, timeout=20, context=ctx)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Live fetch failed: {e}")
        return None


# ─── Granite integration ─────────────────────────────────────────────

def granite_call(model: str, prompt: str, json_format: bool = False, max_tokens: int = 2000) -> str:
    """Call Granite via Ollama."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": max_tokens},
    }
    if json_format:
        payload["format"] = "json"

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        return f"ERROR: {e}"


# ─── Regex pre-filters ───────────────────────────────────────────────

def prefilter_aircraft(text: str) -> list:
    """Find aircraft serial number patterns."""
    patterns = [
        r"\b([A-Z]{2}\d{3})\b",   # ED393, LM227
        r"\b([A-Z]\d{4})\b",       # W5719
        r"\b(\d{2}-\d{4,5})\b",   # USAAF: 42-31322, 44-61999
    ]
    found = []
    for pat in patterns:
        found.extend(re.findall(pat, text))
    return list(set(found))


def prefilter_emails(text: str) -> list:
    """Find email addresses."""
    return list(set(re.findall(r'[\w.-]+@[\w.-]+\.\w{2,}', text)))


def prefilter_phones(text: str) -> list:
    """Find UK phone numbers."""
    return list(set(re.findall(r'(?:0\d{3,4}[\s.-]?\d{6,7}|\+44[\s.-]?\d{3,4}[\s.-]?\d{6,7})', text)))


def prefilter_social(text: str, links: list) -> list:
    """Find social media profile links."""
    platforms = {
        "facebook.com/": "facebook",
        "twitter.com/": "twitter",
        "x.com/": "twitter",
        "instagram.com/": "instagram",
        "youtube.com/": "youtube",
        "linkedin.com/": "linkedin",
    }
    found = []
    all_urls = [l["url"] for l in links]
    for url in all_urls:
        for pattern, platform in platforms.items():
            if pattern in url.lower():
                found.append({"platform": platform, "url": url})
    return found


def prefilter_keywords(text: str) -> dict:
    """Check for keywords that indicate presence of each data type."""
    text_lower = text.lower()
    return {
        "remembrance": any(k in text_lower for k in [
            "annual service", "remembrance", "ceremony", "commemoration",
            "wreath", "dedication", "unveiling", "service held",
            "held each year", "every year", "annual event",
        ]),
        "community": any(k in text_lower for k in [
            "fundrais", "community", "school", "children", "pupils",
            "villagers", "local people", "erected by", "unveiled by",
            "campaign", "petition", "volunteers",
        ]),
        "research": any(k in text_lower for k in [
            "researched by", "investigated by", "documented by",
            "excavat", "extensive research", "years of research",
            "aviation archaeological", "heritage group", "history society",
            "museum", "archive", "archivist", "historian",
            "recovered", "artefact", "artifact", "wreckage",
        ]),
        "media": any(k in text_lower for k in [
            "youtube", "documentary", "bbc", "itv", "channel 4",
            "film", "podcast", "broadcast", "television",
        ]),
        "condition": any(k in text_lower for k in [
            "condition", "restored", "renovated", "repaired",
            "deteriorat", "vandalised", "overgrown", "weathered",
            "good condition", "poor condition", "fair condition",
        ]),
        "books": any(k in text_lower for k in [
            "published", "isbn", "book", "volume", "chapter",
            "press", "edition", "authored", "written by",
        ]),
    }


# ─── Granite extraction prompts ─────────────────────────────────────

CLASSIFY_PROMPT = """Analyse the following text from a web page about a WW2 bomber crash site or memorial.
For each category below, answer YES or NO based on whether the text contains that type of information:

1. REMEMBRANCE: Does the text describe a remembrance event, annual service, memorial ceremony, or commemoration?
2. COMMUNITY: Does the text describe community involvement in creating, maintaining, or caring for a memorial (fundraising, school projects, local initiatives)?
3. RESEARCH: Does the text reference research or investigation conducted by a specific named person, group, museum, or organisation?
4. CONDITION: Does the text describe the physical condition, restoration, or maintenance state of a memorial?
5. BOOKS: Does the text reference specific books, publications, or written works about this crash or memorial?

Text (first 3000 characters):
{text}

Answer exactly in this format, one per line:
1. YES or NO
2. YES or NO
3. YES or NO
4. YES or NO
5. YES or NO"""

NARRATIVE_PROMPT = """Extract the crash narrative from the following text about a WW2 aircraft crash.
Return a JSON object with these fields:
- "narrative": The main story of what happened (the crash, mission, circumstances). 2-5 paragraphs. Exclude navigation, copyright, headers, unrelated content.
- "crash_date": The date of the crash if mentioned (format: YYYY-MM-DD or partial date)
- "aircraft_type": The aircraft type (e.g. Lancaster, Wellington, Halifax, B-17)
- "squadron": Squadron or unit mentioned
- "mission": What the mission was (target, operation name)

Text:
{text}"""

CREW_PROMPT = """Extract all crew member details from this text about a WW2 aircraft crash.
Return a JSON object with a "crew" array. For each crew member include:
- "rank": military rank
- "name": full name
- "role": crew position (pilot, navigator, bomb aimer, wireless operator, rear gunner, etc.)
- "fate": what happened to them (killed, survived, POW, evaded)
- "age": age if mentioned
- "burial_location": where they are buried if mentioned
- "nationality": if mentioned
- "decorations": any medals or awards (DFC, DFM, etc.)

Only include people who were clearly crew members of the aircraft. Do not include other people mentioned in the text.

Text:
{text}"""

REMEMBRANCE_PROMPT = """Extract remembrance and commemoration details from this text about a WW2 memorial.
Return a JSON object with:
- "annual_service": true/false — is there a recurring annual event?
- "service_date": when it occurs (specific date or pattern like "second Sunday in November")
- "events": array of events, each with "name", "date", "description", "organiser"
- "last_known_event": most recent event date mentioned

Text:
{text}"""

COMMUNITY_PROMPT = """Extract community connection stories from this text about a WW2 memorial.
IMPORTANT: Only include information explicitly stated in the text. Do not infer, speculate, or add information not present.

Return a JSON object with:
- "story_text": 1-3 paragraphs describing community involvement (who built the memorial, why, fundraising, personal connections). Use only facts from the text.
- "key_people": array of named individuals involved in the community effort (not crew members)
- "organisations": array of groups, schools, councils involved
- "story_type": one of: fundraising, personal_connection, school_project, family, restoration, dedication

Text:
{text}"""

RESEARCH_PROMPT = """Extract details about research or investigation activity mentioned in this text about a WW2 crash site or memorial.
IMPORTANT: Only include information explicitly stated in the text. Do not infer or speculate.

Return a JSON object with:
- "activities": array of research activities found, each with:
  - "researcher_name": person or group name
  - "researcher_type": individual / group / museum / archive / academic / family
  - "research_focus": what they researched
  - "output_type": investigation / excavation / publication / database / exhibition / archive / website_section / documentary
  - "output_description": what they found or produced
  - "depth_signals": array of phrases indicating deep work (e.g. "10 years of research", "recovered wreckage")

Text:
{text}"""

CONTACT_PROMPT = """Extract organisation contact details from this text.
Return a JSON object with a "contacts" array. For each contact include:
- "org_name": organisation name
- "org_type": parish_council / memorial_trust / museum / heritage_group / squadron_association / church / school / other
- "email": email address if found
- "phone": phone number if found
- "website": website URL if found
- "contact_name": named person if visible

Only include real organisation contacts, not generic website navigation or privacy policy links.

Text:
{text}"""


# ─── Main test logic ─────────────────────────────────────────────────

def process_page(url: str):
    """Full extraction pipeline for one page."""
    print(f"\n{'='*80}")
    print(f"TESTING: {url}")
    print(f"{'='*80}")

    # 1. Get HTML — try stored first, fall back to live
    print("\n[1] Fetching HTML...")
    html = get_stored_html(url)
    if html:
        print(f"  Got stored HTML from DB: {len(html):,} chars")
    else:
        print("  No stored HTML, fetching live...")
        html = fetch_live(url)
        if not html:
            print("  FAILED — skipping this URL")
            return None

    print(f"  HTML size: {len(html):,} chars")

    # 2. Clean and parse
    print("\n[2] Cleaning HTML...")
    clean_text = clean_html_to_text(html)
    title = extract_title(html)
    images = extract_images(html)
    links = extract_links(html)
    domain = url.split("://")[1].split("/")[0].replace("www.", "")
    content_hash = hashlib.sha256(clean_text.encode()).hexdigest()[:16]

    fetch_result = FetchResult(
        url=url, domain=domain, status="ok",
        raw_html=html, clean_text=clean_text, title=title,
        images=images, links=links, content_hash=content_hash,
    )

    print(f"  Title: {title}")
    print(f"  Clean text: {len(clean_text):,} chars")
    print(f"  Images found: {len(images)}")
    print(f"  Links found: {len(links)}")
    print(f"  Content hash: {content_hash}")

    # 3. Regex pre-filters
    print("\n[3] Running regex pre-filters...")
    serials = prefilter_aircraft(clean_text)
    emails = prefilter_emails(clean_text)
    phones = prefilter_phones(clean_text)
    socials = prefilter_social(clean_text, links)
    keywords = prefilter_keywords(clean_text)

    print(f"  Aircraft serials: {serials or 'none'}")
    print(f"  Emails: {emails or 'none'}")
    print(f"  Phones: {phones or 'none'}")
    print(f"  Social links: {len(socials)}")
    print(f"  Keyword flags: {', '.join(k for k, v in keywords.items() if v) or 'none'}")

    # 4. Granite 3B classification (batched)
    print("\n[4] Running Granite 3B classification...")
    text_for_granite = clean_text[:2000]
    classify_result = granite_call("granite4:3b", CLASSIFY_PROMPT.replace("{text}", text_for_granite), max_tokens=100)
    print(f"  Raw classification:\n    {classify_result.strip()}")

    # Parse classification results
    classifications = {}
    type_map = {1: "remembrance", 2: "community", 3: "research", 4: "condition", 5: "books"}
    for line in classify_result.strip().split("\n"):
        line = line.strip()
        for num, name in type_map.items():
            if line.startswith(f"{num}."):
                classifications[name] = "YES" in line.upper()

    print(f"  Parsed: {classifications}")

    # 5. Granite 8B extractions
    print("\n[5] Running Granite 8B extractions...")
    extractions = {}

    # Always run narrative and crew extraction
    print("  [5a] Narrative extraction...")
    narr_raw = granite_call("granite3.2:8b", NARRATIVE_PROMPT.replace("{text}", text_for_granite), json_format=True)
    try:
        extractions["narrative"] = json.loads(narr_raw)
    except json.JSONDecodeError:
        extractions["narrative"] = {"raw": narr_raw[:500], "parse_error": True}

    print("  [5b] Crew extraction...")
    crew_raw = granite_call("granite3.2:8b", CREW_PROMPT.replace("{text}", text_for_granite), json_format=True)
    try:
        extractions["crew"] = json.loads(crew_raw)
    except json.JSONDecodeError:
        extractions["crew"] = {"raw": crew_raw[:500], "parse_error": True}

    # Contact extraction (always run — cheap)
    print("  [5c] Contact extraction...")
    contact_raw = granite_call("granite3.2:8b", CONTACT_PROMPT.replace("{text}", text_for_granite), json_format=True)
    try:
        extractions["contact"] = json.loads(contact_raw)
    except json.JSONDecodeError:
        extractions["contact"] = {"raw": contact_raw[:500], "parse_error": True}

    # Conditional extractions based on classification
    if classifications.get("remembrance"):
        print("  [5d] Remembrance extraction (flagged by classifier)...")
        rem_raw = granite_call("granite3.2:8b", REMEMBRANCE_PROMPT.replace("{text}", text_for_granite), json_format=True)
        try:
            extractions["remembrance"] = json.loads(rem_raw)
        except json.JSONDecodeError:
            extractions["remembrance"] = {"raw": rem_raw[:500], "parse_error": True}

    if classifications.get("community"):
        print("  [5e] Community connection extraction (flagged by classifier)...")
        comm_raw = granite_call("granite3.2:8b", COMMUNITY_PROMPT.replace("{text}", text_for_granite), json_format=True)
        try:
            extractions["community"] = json.loads(comm_raw)
        except json.JSONDecodeError:
            extractions["community"] = {"raw": comm_raw[:500], "parse_error": True}

    if classifications.get("research"):
        print("  [5f] Research activity extraction (flagged by classifier)...")
        res_raw = granite_call("granite3.2:8b", RESEARCH_PROMPT.replace("{text}", text_for_granite), json_format=True)
        try:
            extractions["research"] = json.loads(res_raw)
        except json.JSONDecodeError:
            extractions["research"] = {"raw": res_raw[:500], "parse_error": True}

    # 6. Compile results
    print(f"\n{'─'*80}")
    print(f"RESULTS FOR: {url}")
    print(f"Domain: {domain}")
    print(f"{'─'*80}")

    result = {
        "url": url,
        "domain": domain,
        "title": title,
        "content_hash": content_hash,
        "clean_text_length": len(clean_text),
        "prefilters": {
            "aircraft_serials": serials,
            "emails": emails,
            "phones": phones,
            "social_links": socials,
            "keyword_flags": {k: v for k, v in keywords.items() if v},
        },
        "classifications": classifications,
        "extractions": extractions,
        "images_count": len(images),
        "links_count": len(links),
    }

    # Pretty print
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str)[:5000])
    if len(json.dumps(result, indent=2)) > 5000:
        print("  ... (truncated)")

    return result


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  BMR EXTRACTOR ARCHITECTURE — TEST HARNESS                  ║")
    print("║  Testing against 3 diverse site types                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Verify Granite is available
    print("\nChecking Granite availability...")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"  Models available: {models}")
        if "granite4:3b" not in models or "granite3.2:8b" not in models:
            print("  WARNING: Missing required Granite models!")
    except Exception as e:
        print(f"  ERROR: Cannot reach Ollama: {e}")
        return

    all_results = []
    for url in TEST_URLS:
        result = process_page(url)
        if result:
            all_results.append(result)
        print()

    # Write full results to file
    output_path = "/tmp/bmr-extractor-test-results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n\nFull results written to: {output_path}")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for r in all_results:
        print(f"\n{r['domain']}:")
        print(f"  Title: {r['title'][:80]}")
        print(f"  Content: {r['clean_text_length']:,} chars")
        print(f"  Serials: {r['prefilters']['aircraft_serials']}")
        print(f"  Emails: {r['prefilters']['emails']}")
        print(f"  Keywords flagged: {list(r['prefilters']['keyword_flags'].keys())}")
        print(f"  Classifications: {r['classifications']}")
        print(f"  Extractions run: {list(r['extractions'].keys())}")
        for etype, edata in r['extractions'].items():
            if isinstance(edata, dict) and not edata.get("parse_error"):
                if etype == "crew" and "crew" in edata:
                    print(f"    crew: {len(edata['crew'])} members found")
                elif etype == "narrative" and "narrative" in edata:
                    print(f"    narrative: {len(edata.get('narrative', '')):.0f} chars")
                elif etype == "remembrance":
                    events = edata.get("events", [])
                    print(f"    remembrance: {len(events)} events, annual={edata.get('annual_service')}")
                elif etype == "community":
                    print(f"    community: {len(edata.get('story_text', ''))} chars, type={edata.get('story_type')}")
                elif etype == "research":
                    acts = edata.get("activities", [])
                    print(f"    research: {len(acts)} activities found")
                elif etype == "contact":
                    contacts = edata.get("contacts", [])
                    print(f"    contacts: {len(contacts)} organisations")
            elif isinstance(edata, dict) and edata.get("parse_error"):
                print(f"    {etype}: PARSE ERROR")


if __name__ == "__main__":
    main()
