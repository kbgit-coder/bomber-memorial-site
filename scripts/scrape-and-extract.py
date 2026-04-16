#!/usr/bin/env python3
"""
BMR Scrape-and-Extract Orchestrator

Fetches pages and runs all 13 data-type extractors against them.
Designed to run overnight on Dell with local Granite models.

Usage:
    # Process all queued URLs across all domains
    python3 scripts/scrape-and-extract.py --all

    # Process a specific domain
    python3 scripts/scrape-and-extract.py --domain iwm.org.uk

    # Re-extract from already-scraped pages (no fetching)
    python3 scripts/scrape-and-extract.py --re-extract --domain aircrewremembered.com

    # Process specific data types only
    python3 scripts/scrape-and-extract.py --all --types narrative,crew,remembrance

    # Dry run
    python3 scripts/scrape-and-extract.py --all --dry-run

    # Limit number of URLs
    python3 scripts/scrape-and-extract.py --all --limit 50
"""

import argparse
import hashlib
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

# ─── Config ──────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT = 300  # 5 min — Dell GPU is slow on 8B
DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"
DB_PASS = "BmrResearch2026xHeritage"
RATE_LIMIT = 2.5  # seconds between requests to same domain
UA = "Mozilla/5.0 (compatible; BomberMemorialResearch/1.0; +https://bombermemorial.co.uk)"
MAX_TEXT_FOR_GRANITE = 2000  # chars to send to Granite

# Add scripts dir for provenance module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_provenance import ProvenanceLog

# Bot-blocked domains — skip or use BrightData
BOT_BLOCKED = {
    "tracesofwar.com", "www.tracesofwar.com",
    "americanairmuseum.com", "www.americanairmuseum.com",
    "peakdistrict.gov.uk", "www.peakdistrict.gov.uk",
    "dartmoor.gov.uk", "www.dartmoor.gov.uk",
    "raf.mod.uk", "www.raf.mod.uk",
}

# Output paths
RESULTS_DIR = "/nas2/Projects/BomberMemorial/data-governance/extraction-runs"
LOG_FILE = "/nas2/Projects/BomberMemorial/data-governance/extraction-runs/latest-run.log"


# ─── Data structures ────────────────────────────────────────────────

@dataclass
class FetchResult:
    url: str
    domain: str
    status: str  # ok / failed / blocked / not_found / timeout
    raw_html: str = ""
    clean_text: str = ""
    title: str = ""
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
    granite_model: str = None


# ─── DB access ───────────────────────────────────────────────────────

def db_query(sql: str) -> str:
    """Run a psql query and return raw output."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip()


def db_exec(sql: str) -> bool:
    """Execute a DB statement (INSERT/UPDATE)."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode == 0


def get_queued_urls(domain: str = None, limit: int = None) -> list[dict]:
    """Get URLs to process from external_narratives in memorial JSONs."""
    memorials_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "public", "data", "memorials",
    )
    import glob
    urls = []
    for filepath in sorted(glob.glob(os.path.join(memorials_dir, "*.json"))):
        with open(filepath) as f:
            data = json.load(f)
        slug = os.path.basename(filepath).replace(".json", "")
        for narrative in data.get("external_narratives", []):
            url = narrative.get("original_url", "")
            if not url or "://" not in url:
                continue
            # Skip if already has full_narrative
            if narrative.get("full_narrative"):
                continue
            d = url.split("://")[1].split("/")[0].replace("www.", "")
            if domain and d != domain.replace("www.", ""):
                continue
            if d in BOT_BLOCKED:
                continue
            urls.append({
                "url": url,
                "domain": d,
                "memorial_slug": slug,
                "source_site": narrative.get("source_site", ""),
            })

    if limit:
        urls = urls[:limit]
    return urls


def get_stored_html(url: str) -> str | None:
    """Get stored HTML from scrape_log via temp file."""
    tmp_file = "/tmp/bmr_extract_html.txt"
    safe_url = url.replace("'", "''")
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c",
         f"\\copy (SELECT raw_content FROM scrape_log WHERE url = '{safe_url}' AND raw_content IS NOT NULL AND length(raw_content) > 100 LIMIT 1) TO '{tmp_file}'"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return None
    subprocess.run(["docker", "cp", f"{DB_CONTAINER}:{tmp_file}", tmp_file],
                   capture_output=True, timeout=30)
    if os.path.exists(tmp_file):
        with open(tmp_file) as f:
            content = f.read().strip()
        os.unlink(tmp_file)
        content = content.replace("\\n", "\n").replace("\\\\", "\\")
        return content if len(content) > 100 else None
    return None


# ─── Fetcher ─────────────────────────────────────────────────────────

def fetch_url(url: str) -> FetchResult:
    """Fetch a URL with HTTPS→HTTP fallback."""
    domain = url.split("://")[1].split("/")[0].replace("www.", "")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    urls_to_try = [url]
    if url.startswith("https://"):
        urls_to_try.append(url.replace("https://", "http://"))
    elif url.startswith("http://"):
        urls_to_try.insert(0, url.replace("http://", "https://"))

    for try_url in urls_to_try:
        try:
            req = urllib.request.Request(try_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=20, context=ctx)
            html = resp.read().decode("utf-8", errors="ignore")
            clean = clean_html_to_text(html)
            return FetchResult(
                url=url, domain=domain, status="ok",
                raw_html=html, clean_text=clean,
                title=extract_title(html),
                images=extract_images(html),
                links=extract_links(html),
                content_hash=hashlib.sha256(clean.encode()).hexdigest()[:16],
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return FetchResult(url=url, domain=domain, status="not_found", error=f"HTTP 404")
        except Exception as e:
            last_error = str(e)

    return FetchResult(url=url, domain=domain, status="failed", error=last_error if 'last_error' in dir() else "Unknown error")


# ─── HTML cleaning ───────────────────────────────────────────────────

def clean_html_to_text(html: str) -> str:
    for tag in ["script", "style", "nav", "footer", "noscript", "svg"]:
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else ""


def extract_images(html: str) -> list:
    images = []
    for match in re.finditer(r'<img[^>]+>', html, re.IGNORECASE):
        tag = match.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if src:
            images.append({"url": src.group(1), "alt": alt.group(1) if alt else ""})
    return images


def extract_links(html: str) -> list:
    links = []
    for match in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        url = match.group(1)
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if url and not url.startswith("#") and not url.startswith("javascript:"):
            links.append({"url": url, "text": text})
    return links


# ─── Granite ─────────────────────────────────────────────────────────

def granite_call(model: str, prompt: str, json_format: bool = False) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2000},
    }
    if json_format:
        payload["format"] = "json"
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        return f"ERROR: {e}"


def granite_classify(text: str) -> dict:
    """Batched 3B classification — one call, five answers."""
    prompt = f"""Analyse the following text from a web page about a WW2 bomber crash site or memorial.
For each category, answer YES or NO:

1. REMEMBRANCE: Does the text describe a remembrance event, annual service, or memorial ceremony?
2. COMMUNITY: Does the text describe community involvement in creating, maintaining, or caring for a memorial?
3. RESEARCH: Does the text reference research or investigation by a specific named person or group?
4. CONDITION: Does the text describe the physical condition or restoration of a memorial?
5. BOOKS: Does the text reference specific books or publications?

Text (first 2000 chars):
{text[:2000]}

Answer one per line:
1. YES or NO
2. YES or NO
3. YES or NO
4. YES or NO
5. YES or NO"""

    raw = granite_call("granite4:3b", prompt, max_tokens=100) if hasattr(granite_call, '__wrapped__') else ""
    # Simplified call
    payload = {
        "model": "granite4:3b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 100},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        raw = resp.json()["response"]
    except Exception:
        return {}

    type_map = {1: "remembrance", 2: "community", 3: "research", 4: "condition", 5: "books"}
    classifications = {}
    for line in raw.strip().split("\n"):
        for num, name in type_map.items():
            if line.strip().startswith(f"{num}."):
                classifications[name] = "YES" in line.upper()
    return classifications


def granite_extract(prompt_template: str, text: str) -> dict:
    """Run 8B structured extraction."""
    raw = granite_call("granite3.2:8b", prompt_template.replace("{text}", text[:MAX_TEXT_FOR_GRANITE]), json_format=True)
    if raw.startswith("ERROR:"):
        return {"_error": raw}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_error": "JSON parse failed", "_raw": raw[:500]}


# ─── Extraction prompts ─────────────────────────────────────────────

PROMPTS = {
    "narrative": """Extract the crash narrative from this text about a WW2 aircraft crash.
IMPORTANT: Only include information EXPLICITLY stated in the text. Do not infer, speculate, or fabricate details.
If the text does not contain a crash narrative (e.g. it is just a database listing, register entry, or link page), return {{"narrative": null, "crash_date": null, "aircraft_type": null, "squadron": null, "mission": null}}.
Return JSON: {{"narrative": "...", "crash_date": "YYYY-MM-DD or null", "aircraft_type": "...", "squadron": "...", "mission": "..."}}

Text:
{text}""",

    "crew": """Extract all crew member details from this text about a WW2 aircraft crash.
IMPORTANT: Only include people EXPLICITLY named as crew members in the text. Do not infer names from page titles, location names, or memorial names. If no crew members are explicitly listed, return {{"crew": []}}.
Return JSON: {{"crew": [{{"rank": "...", "name": "...", "role": "...", "fate": "killed/survived/POW/evaded/unknown", "age": null, "burial_location": null, "nationality": null, "decorations": null}}]}}

Text:
{text}""",

    "contact": """Extract organisation contact details from this text.
IMPORTANT: Only real organisations, not navigation links or privacy policies.
Return JSON: {{"contacts": [{{"org_name": "...", "org_type": "parish_council/memorial_trust/museum/heritage_group/squadron_association/church/other", "email": null, "phone": null, "website": null, "contact_name": null}}]}}

Text:
{text}""",

    "remembrance": """Extract remembrance and commemoration details from this text about a WW2 memorial.
IMPORTANT: Only include events explicitly described. Do not speculate.
Return JSON: {{"annual_service": true/false, "service_date": "...", "events": [{{"name": "...", "date": "...", "description": "...", "organiser": "..."}}], "last_known_event": "..."}}

Text:
{text}""",

    "community": """Extract community connection stories from this text about a WW2 memorial.
IMPORTANT: Only include information explicitly stated in the text. Do not infer or speculate.
Return JSON: {{"story_text": "1-3 paragraphs from the text", "key_people": ["..."], "organisations": ["..."], "story_type": "fundraising/personal_connection/school_project/family/restoration/dedication"}}

Text:
{text}""",

    "research": """Extract details about research or investigation activity mentioned in this text.
IMPORTANT: Only include information explicitly stated. Do not infer.
Return JSON: {{"activities": [{{"researcher_name": "...", "researcher_type": "individual/group/museum/archive/academic/family", "research_focus": "...", "output_type": "investigation/excavation/publication/database/exhibition/archive/website_section", "output_description": "...", "depth_signals": ["..."]}}]}}

Text:
{text}""",
}


# ─── Regex extractors ────────────────────────────────────────────────

def extract_regex(fetch_result: FetchResult) -> list[ExtractionResult]:
    """Run all regex-based extractors."""
    results = []
    text = fetch_result.clean_text

    # Aircraft serials
    for pat in [r"\b([A-Z]{2}\d{3})\b", r"\b([A-Z]\d{4})\b", r"\b(\d{2}-\d{4,5})\b"]:
        for serial in set(re.findall(pat, text)):
            results.append(ExtractionResult(
                data_type="aircraft", claim_field="aircraft_serial",
                field_value=serial, field_context={},
                confidence="probable", source_excerpt="",
                extraction_method="regex",
            ))

    # Social media
    platforms = {"facebook.com/": "facebook", "twitter.com/": "twitter", "x.com/": "twitter",
                 "instagram.com/": "instagram", "youtube.com/": "youtube"}
    for link in fetch_result.links:
        for pattern, platform in platforms.items():
            if pattern in link["url"].lower() and "/share" not in link["url"].lower():
                results.append(ExtractionResult(
                    data_type="social_media", claim_field="social_media_link",
                    field_value=link["url"],
                    field_context={"platform": platform, "profile_name": link.get("text", "")},
                    confidence="verified", source_excerpt="",
                    extraction_method="regex",
                ))

    # Emails
    for email in set(re.findall(r'[\w.-]+@[\w.-]+\.\w{2,}', text)):
        if not any(x in email for x in ["example.com", "noreply", "cookie", "privacy"]):
            results.append(ExtractionResult(
                data_type="contact", claim_field="contact_email",
                field_value=email, field_context={},
                confidence="verified", source_excerpt="",
                extraction_method="regex",
            ))

    # Phones
    for phone in set(re.findall(r'(?:0\d{3,4}[\s.-]?\d{6,7})', text)):
        results.append(ExtractionResult(
            data_type="contact", claim_field="contact_phone",
            field_value=phone, field_context={},
            confidence="verified", source_excerpt="",
            extraction_method="regex",
        ))

    # Photos — images with meaningful alt text
    for img in fetch_result.images:
        alt = img.get("alt", "")
        if len(alt) > 10 and not any(x in alt.lower() for x in ["logo", "icon", "banner", "avatar", "button"]):
            results.append(ExtractionResult(
                data_type="photo", claim_field="photo_reference",
                field_value=img["url"],
                field_context={"caption": alt, "licence_clear": False},
                confidence="unverified", source_excerpt="",
                extraction_method="html_parse",
            ))

    return results


# ─── Keyword pre-filter ──────────────────────────────────────────────

def keyword_prefilter(text: str) -> dict:
    text_lower = text.lower()
    return {
        "remembrance": any(k in text_lower for k in [
            "annual service", "remembrance", "ceremony", "commemoration",
            "wreath", "dedication", "unveiling", "held each year",
        ]),
        "community": any(k in text_lower for k in [
            "fundrais", "community", "school", "children", "villagers",
            "local people", "erected by", "unveiled by", "volunteers",
        ]),
        "research": any(k in text_lower for k in [
            "researched by", "investigated by", "excavat", "extensive research",
            "aviation archaeological", "heritage group", "history society",
            "historian", "recovered", "artefact", "wreckage",
        ]),
        "condition": any(k in text_lower for k in [
            "condition", "restored", "renovated", "deteriorat",
            "good condition", "poor condition", "vandalised",
        ]),
        "books": any(k in text_lower for k in [
            "published", "isbn", "book", "volume", "authored", "written by",
        ]),
    }


# ─── Main orchestrator ──────────────────────────────────────────────

def process_url(url: str, domain: str, memorial_slug: str,
                types: set | None, re_extract: bool = False) -> dict:
    """Process a single URL through the full pipeline."""

    result = {
        "url": url, "domain": domain, "memorial_slug": memorial_slug,
        "status": "pending", "extractions": [], "errors": [],
    }

    # 1. Get content
    if re_extract:
        html = get_stored_html(url)
        if not html:
            result["status"] = "no_stored_html"
            return result
        fetch = FetchResult(
            url=url, domain=domain, status="ok", raw_html=html,
            clean_text=clean_html_to_text(html), title=extract_title(html),
            images=extract_images(html), links=extract_links(html),
            content_hash=hashlib.sha256(clean_html_to_text(html).encode()).hexdigest()[:16],
        )
    else:
        fetch = fetch_url(url)

    if fetch.status != "ok":
        result["status"] = fetch.status
        result["errors"].append(fetch.error or fetch.status)
        return result

    # 2. Regex extractors (always run)
    regex_results = extract_regex(fetch)
    result["extractions"].extend([
        {"type": r.data_type, "field": r.claim_field, "value": r.field_value,
         "context": r.field_context, "confidence": r.confidence, "method": r.extraction_method}
        for r in regex_results
    ])

    # 3. Keyword pre-filter
    keywords = keyword_prefilter(fetch.clean_text)

    # 4. Granite 3B classification (only for flagged keywords)
    classifications = {}
    if any(keywords.values()):
        classifications = granite_classify(fetch.clean_text)

    # 5. Granite 8B extractions
    text = fetch.clean_text[:MAX_TEXT_FOR_GRANITE]

    # Minimum content guard — skip narrative/crew extraction on sparse pages
    has_enough_content = len(fetch.clean_text) >= 500

    # Always extract narrative + crew (core data) if enough content
    for etype in ["narrative", "crew", "contact"]:
        if types and etype not in types:
            continue
        if etype in ("narrative", "crew") and not has_enough_content:
            result["extractions"].append({
                "type": etype, "data": {"_skipped": "insufficient content", "clean_text_length": len(fetch.clean_text)},
                "method": "skipped",
            })
            continue
        extracted = granite_extract(PROMPTS[etype], text)
        if not extracted.get("_error"):
            result["extractions"].append({
                "type": etype, "data": extracted, "method": "granite_8b",
            })
        else:
            result["errors"].append(f"{etype}: {extracted['_error']}")

    # Conditional extractions
    for etype in ["remembrance", "community", "research"]:
        if types and etype not in types:
            continue
        if classifications.get(etype) or keywords.get(etype):
            extracted = granite_extract(PROMPTS[etype], text)
            if not extracted.get("_error"):
                result["extractions"].append({
                    "type": etype, "data": extracted, "method": "granite_8b",
                })
            else:
                result["errors"].append(f"{etype}: {extracted['_error']}")

    result["status"] = "ok"
    result["content_hash"] = fetch.content_hash
    result["clean_text_length"] = len(fetch.clean_text)
    result["title"] = fetch.title
    return result


def main():
    parser = argparse.ArgumentParser(description="BMR Scrape-and-Extract Orchestrator")
    parser.add_argument("--domain", help="Process specific domain only")
    parser.add_argument("--all", action="store_true", help="Process all queued URLs")
    parser.add_argument("--re-extract", action="store_true", help="Re-extract from stored HTML")
    parser.add_argument("--types", help="Comma-separated list of types to extract")
    parser.add_argument("--limit", type=int, help="Limit number of URLs to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()

    if not args.domain and not args.all:
        parser.error("Specify --domain DOMAIN or --all")

    types = set(args.types.split(",")) if args.types else None

    # Verify Granite
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"Granite models: {models}")
    except Exception:
        print("ERROR: Cannot reach Ollama at localhost:11434")
        sys.exit(1)

    # Get URLs
    urls = get_queued_urls(domain=args.domain, limit=args.limit)
    print(f"URLs to process: {len(urls)}")

    if args.dry_run:
        domains = defaultdict(int)
        for u in urls:
            domains[u["domain"]] += 1
        print("\nDomain breakdown:")
        for d, c in sorted(domains.items(), key=lambda x: -x[1]):
            print(f"  {d}: {c}")
        return

    # Create output directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(RESULTS_DIR, f"run_{run_id}.json")

    # Process
    all_results = []
    stats = {"ok": 0, "failed": 0, "total_extractions": 0, "domains_processed": set()}
    start_time = time.time()

    # Group by domain for rate limiting
    by_domain = defaultdict(list)
    for u in urls:
        by_domain[u["domain"]].append(u)

    domain_order = sorted(by_domain.keys(), key=lambda d: -len(by_domain[d]))

    for domain in domain_order:
        domain_urls = by_domain[domain]
        print(f"\n{'='*60}")
        print(f"DOMAIN: {domain} ({len(domain_urls)} URLs)")
        print(f"{'='*60}")

        domain_start = time.time()
        domain_results = {"ok": 0, "failed": 0, "extractions": 0}

        for i, u in enumerate(domain_urls, 1):
            if i > 1:
                time.sleep(RATE_LIMIT)

            print(f"  [{i}/{len(domain_urls)}] {u['memorial_slug']}...", end=" ", flush=True)

            result = process_url(
                u["url"], u["domain"], u["memorial_slug"],
                types=types, re_extract=args.re_extract,
            )
            all_results.append(result)

            if result["status"] == "ok":
                domain_results["ok"] += 1
                stats["ok"] += 1
                n_extractions = len(result["extractions"])
                domain_results["extractions"] += n_extractions
                stats["total_extractions"] += n_extractions
                print(f"OK ({n_extractions} extractions)")
            else:
                domain_results["failed"] += 1
                stats["failed"] += 1
                print(f"FAIL: {result['status']}")

            if result.get("errors"):
                for err in result["errors"]:
                    print(f"    ERROR: {err[:100]}")

        stats["domains_processed"].add(domain)
        domain_elapsed = time.time() - domain_start
        print(f"  Domain complete: {domain_results['ok']}/{len(domain_urls)} OK, "
              f"{domain_results['extractions']} extractions, {domain_elapsed:.0f}s")

        # Update provenance after each domain
        provenance = ProvenanceLog()
        provenance.record_scrape(domain, {
            "pages_attempted": len(domain_urls),
            "pages_succeeded": domain_results["ok"],
            "script": "scripts/scrape-and-extract.py",
            "notes": f"Extractions: {domain_results['extractions']}, Failed: {domain_results['failed']}",
        })
        provenance.save()

    # Write results
    elapsed = time.time() - start_time
    summary = {
        "run_id": run_id,
        "started": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed),
        "urls_processed": len(all_results),
        "urls_ok": stats["ok"],
        "urls_failed": stats["failed"],
        "total_extractions": stats["total_extractions"],
        "domains_processed": len(stats["domains_processed"]),
        "types_requested": list(types) if types else "all",
        "re_extract": args.re_extract,
    }

    output = {"summary": summary, "results": all_results}
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    # Set NAS permissions
    os.chmod(output_file, 0o666)

    print(f"\n{'='*60}")
    print(f"RUN COMPLETE")
    print(f"{'='*60}")
    print(f"  URLs: {stats['ok']}/{len(all_results)} OK")
    print(f"  Extractions: {stats['total_extractions']}")
    print(f"  Domains: {len(stats['domains_processed'])}")
    print(f"  Elapsed: {elapsed/60:.1f} minutes")
    print(f"  Results: {output_file}")


if __name__ == "__main__":
    main()
