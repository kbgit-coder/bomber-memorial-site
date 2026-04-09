#!/usr/bin/env python3
"""
Scrape the 50/61 Squadrons Association UK/European Memorials pages.
Produces JSON output at /tmp/association-scrape-results.json

Site is HTTP only — HTTPS fails with SSL errors.
"""

import json
import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://www.no-50-and-no-61-squadrons-association.co.uk"
INDEX_PATH = "/the-memorials/uk-european-memorials/"
OUTPUT_PATH = "/tmp/association-scrape-results.json"
RATE_LIMIT_SECS = 2

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (compatible; BomberMemorialResearch/1.0; "
        "+https://bomber-memorial.co.uk)"
    )
})


def fetch(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return a BeautifulSoup object, or None on error."""
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        print(f"  ERROR fetching {url}: {exc}")
        return None


def discover_memorial_links(soup: BeautifulSoup) -> list[dict]:
    """
    Pull all links from the index page that look like memorial sub-pages.
    Returns list of dicts: {url, slug}
    """
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Resolve relative URLs
        full_url = urllib.parse.urljoin(BASE_URL, href)

        # Keep only links that are sub-pages of the memorials section
        # and aren't the index itself
        if (
            "/the-memorials/uk-european-memorials/" in full_url
            and full_url.rstrip("/") != (BASE_URL + INDEX_PATH).rstrip("/")
            and full_url not in seen
        ):
            slug = full_url.rstrip("/").split("/")[-1]
            links.append({"url": full_url, "slug": slug})
            seen.add(full_url)

    return links


def extract_serial(text: str, slug: str) -> str:
    """
    Try to find an aircraft serial number (e.g. ED393, LM123) from text or slug.
    Standard RAF serials: 2 letters + 3 digits, or single letter + 4 digits.
    """
    # Common bomber serial patterns
    patterns = [
        r"\b([A-Z]{2}\d{3})\b",   # ED393, LM227, etc.
        r"\b([A-Z]\d{4})\b",       # W4050, etc.
        r"\b([A-Z]{2}\d{4})\b",   # longer variant
    ]
    for pat in patterns:
        match = re.search(pat, text.upper())
        if match:
            return match.group(1)

    # Fall back to slug
    slug_upper = slug.upper().replace("-", "")
    for pat in patterns:
        match = re.search(pat, slug_upper)
        if match:
            return match.group(1)

    return ""


def extract_crew(text: str) -> list[str]:
    """
    Heuristic extraction of crew names from narrative text.
    Looks for patterns like:
      - F/Sgt John Smith
      - Sgt J. Smith
      - Pilot Officer Jane Doe
      - P/O, F/O, F/L, W/O, Sgt, F/Sgt, W/Cdr prefixes
    """
    rank_prefixes = (
        r"(?:Air(?:craftman|man)|A/C|Cpl|LAC|"
        r"Sgt|F/Sgt|W/O|P/O|F/O|F/L|S/L|W/C|G/C|"
        r"Pilot\s+Officer|Flying\s+Officer|Flight\s+(?:Lieutenant|Sergeant)|"
        r"Wing\s+Commander|Squadron\s+Leader|Warrant\s+Officer|"
        r"Sergeant|Corporal)"
    )
    pattern = rf"{rank_prefixes}\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})"
    matches = re.findall(pattern, text)

    # Deduplicate, preserve order
    seen = set()
    crew = []
    for name in matches:
        name_clean = name.strip()
        if name_clean and name_clean not in seen:
            seen.add(name_clean)
            crew.append(name_clean)

    return crew


def extract_location(text: str) -> str:
    """
    Try to pull a location string from the text.
    Looks for phrases like "crashed near X", "at X", "near X", etc.
    """
    patterns = [
        r"(?:crashed?|came down|struck|hit|fell)\s+(?:near|at|in|on)\s+([A-Z][^\.,\n]{3,60})",
        r"(?:near|at|in)\s+([A-Z][a-zA-Z ,]{3,50}),\s+(?:Yorkshire|Lincolnshire|Norfolk|"
        r"Suffolk|Germany|France|Holland|Belgium|Denmark|Netherlands|England|Scotland|Wales)",
        r"(?:memorial|grave|buried)\s+(?:at|in)\s+([A-Z][^\.,\n]{3,60})",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def scrape_memorial_page(url: str, slug: str) -> dict:
    """Scrape a single memorial page and return structured data."""
    print(f"  Scraping: {url}")
    soup = fetch(url)

    if soup is None:
        return {
            "url": url,
            "slug": slug,
            "serial": extract_serial("", slug),
            "title": "",
            "full_narrative": "",
            "location": "",
            "crew_mentioned": [],
            "error": "fetch_failed",
        }

    # Title: prefer <h1>, fall back to <title> tag
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else slug

    # Main content: this CMS uses #mainContent as the primary content container.
    # Fall back through progressively wider selectors if that isn't present.
    content_selectors = [
        "#mainContent",
        "#mainContentCenter",
        "article",
        "div.entry-content",
        "div.post-content",
        "main",
    ]
    content_el = None
    for sel in content_selectors:
        content_el = soup.select_one(sel)
        if content_el:
            break

    if content_el is None:
        content_el = soup.find("body")

    # Extract text, normalising whitespace
    raw_text = content_el.get_text(separator="\n") if content_el else ""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    full_narrative = "\n".join(lines)

    # Try title first for serial (most reliable source — e.g. "ED393 VN-K")
    serial = extract_serial(title, slug)
    # If title didn't yield one, try the narrative
    if not serial:
        serial = extract_serial(full_narrative, slug)
    location = extract_location(full_narrative)
    crew = extract_crew(full_narrative)

    return {
        "url": url,
        "slug": slug,
        "serial": serial,
        "title": title,
        "full_narrative": full_narrative,
        "location": location,
        "crew_mentioned": crew,
    }


def main():
    print(f"Fetching index: {BASE_URL + INDEX_PATH}")
    index_soup = fetch(BASE_URL + INDEX_PATH)

    if index_soup is None:
        print("FATAL: Could not fetch index page.")
        return

    links = discover_memorial_links(index_soup)
    print(f"Found {len(links)} memorial page links on index.")

    if not links:
        # Dump index HTML for debugging
        print("No links found — dumping page title for debug:")
        print(index_soup.title)
        return

    results = []
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] {link['slug']}")
        result = scrape_memorial_page(link["url"], link["slug"])
        results.append(result)
        if i < len(links):
            time.sleep(RATE_LIMIT_SECS)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results)} pages scraped.")
    print(f"Output saved to: {OUTPUT_PATH}")

    # Summary
    serials_found = [r["serial"] for r in results if r["serial"]]
    errors = [r for r in results if r.get("error")]
    print(f"Serials found: {len(serials_found)} / {len(results)}")
    print(f"Errors: {len(errors)}")
    if serials_found:
        print(f"Sample serials: {serials_found[:5]}")


if __name__ == "__main__":
    main()
