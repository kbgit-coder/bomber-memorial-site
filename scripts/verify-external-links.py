#!/usr/bin/env python3
"""
verify-external-links.py
BMR-107 — Scan all 222 memorial JSONs, verify external URLs, update still_live flags.

URL fields scanned:
  - external_narratives[].original_url  (primary; still_live updated in-place)
  - sources[].url
  - maintainer.website
  - local_contacts[].website
  - squadron_badge_url
  - crew[].cwgc_url  --> SKIPPED (generic search pages)

Dependencies: requests (stdlib-adjacent), concurrent.futures (stdlib)
"""

import json
import os
import sys
import time
import glob
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MEMORIALS_DIR = "/root/repos/bomber-memorial-site/public/data/memorials"
OUTPUT_PATH = "/tmp/link-verification-results.json"
TIMEOUT = 15          # seconds per request
DOMAIN_DELAY = 0.5    # seconds between requests to the same domain
MAX_WORKERS = 5       # parallel workers (across different domains)
SLOW_THRESHOLD = 10   # seconds

# ---------------------------------------------------------------------------
# Thread-safe domain rate limiter
# ---------------------------------------------------------------------------

_domain_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_domain_last_request: dict[str, float] = defaultdict(float)
_domain_lock_registry = threading.Lock()


def get_domain_lock(domain: str) -> threading.Lock:
    with _domain_lock_registry:
        return _domain_locks[domain]


def rate_limit_domain(domain: str) -> None:
    lock = get_domain_lock(domain)
    with lock:
        elapsed = time.monotonic() - _domain_last_request[domain]
        if elapsed < DOMAIN_DELAY:
            time.sleep(DOMAIN_DELAY - elapsed)
        _domain_last_request[domain] = time.monotonic()


# ---------------------------------------------------------------------------
# HTTP session factory
# ---------------------------------------------------------------------------

def make_session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=0))
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (compatible; BomberMemorialBot/1.0; "
            "+https://bombermemorial.org/link-checker)"
        )
    })
    return session


_thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = make_session()
    return _thread_local.session


# ---------------------------------------------------------------------------
# URL extraction
# ---------------------------------------------------------------------------

def extract_urls(memorial: dict) -> list[tuple[str, str]]:
    """
    Returns list of (url, field_name) tuples.
    Skips crew[].cwgc_url per spec.
    """
    pairs: list[tuple[str, str]] = []

    for entry in memorial.get("external_narratives", []):
        url = entry.get("original_url", "").strip()
        if url:
            pairs.append((url, "external_narratives"))

    for src in memorial.get("sources", []):
        url = src.get("url", "").strip()
        if url:
            pairs.append((url, "sources"))

    maintainer_url = memorial.get("maintainer", {}).get("website", "").strip()
    if maintainer_url:
        pairs.append((maintainer_url, "website"))

    for contact in memorial.get("local_contacts", []):
        url = contact.get("website", "").strip()
        if url:
            pairs.append((url, "website"))

    badge_url = memorial.get("squadron_badge_url", "").strip()
    if badge_url:
        pairs.append((badge_url, "squadron_badge_url"))

    return pairs


# ---------------------------------------------------------------------------
# Link verification
# ---------------------------------------------------------------------------

def check_url(url: str) -> dict:
    domain = urlparse(url).netloc.lower()
    rate_limit_domain(domain)

    session = get_session()
    start = time.monotonic()
    result = {
        "url": url,
        "status": "error",
        "http_code": None,
        "response_time_ms": None,
        "redirect_target": None,
        "error_detail": None,
    }

    try:
        # Try HEAD first
        resp = session.head(
            url, timeout=TIMEOUT, allow_redirects=False
        )
        method_used = "HEAD"

        # 405 Method Not Allowed → fall back to GET
        if resp.status_code == 405:
            resp = session.get(
                url, timeout=TIMEOUT, allow_redirects=False, stream=True
            )
            method_used = "GET (fallback)"
            # Close body immediately to avoid downloading large files
            resp.close()

    except requests.exceptions.SSLError as exc:
        result["error_detail"] = f"SSL error: {exc}"
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        return result
    except requests.exceptions.ConnectionError as exc:
        result["error_detail"] = f"Connection error: {exc}"
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        return result
    except requests.exceptions.Timeout:
        result["error_detail"] = "Timeout"
        result["status"] = "error"
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        return result
    except Exception as exc:
        result["error_detail"] = f"Unexpected error: {exc}"
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        return result

    elapsed_ms = int((time.monotonic() - start) * 1000)
    result["http_code"] = resp.status_code
    result["response_time_ms"] = elapsed_ms

    code = resp.status_code

    if code in (301, 302, 303, 307, 308):
        result["status"] = "redirect"
        result["redirect_target"] = resp.headers.get("Location")
    elif 200 <= code <= 299:
        if elapsed_ms > SLOW_THRESHOLD * 1000:
            result["status"] = "slow"
        else:
            result["status"] = "alive"
    elif code in (404, 410):
        result["status"] = "broken"
    else:
        # 4xx/5xx that are not 404/410 — treat as error
        result["status"] = "error"
        result["error_detail"] = f"HTTP {code}"

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    memorial_files = sorted(
        glob.glob(os.path.join(MEMORIALS_DIR, "*.json"))
    )
    print(f"Found {len(memorial_files)} memorial files")

    # -- Pass 1: collect all URLs, track which memorials/fields reference each --
    # url -> {"memorials": set of slugs, "field": str}
    url_index: dict[str, dict] = {}

    memorials_data: dict[str, dict] = {}

    for filepath in memorial_files:
        with open(filepath) as f:
            memorial = json.load(f)
        slug = memorial.get("id", os.path.basename(filepath).replace(".json", ""))
        memorials_data[slug] = {"data": memorial, "path": filepath}

        for url, field in extract_urls(memorial):
            if url not in url_index:
                url_index[url] = {"memorials": set(), "field": field}
            url_index[url]["memorials"].add(slug)
            # Keep the most "important" field designation
            # Priority: external_narratives > sources > website > squadron_badge_url
            priority = {
                "external_narratives": 0,
                "sources": 1,
                "website": 2,
                "squadron_badge_url": 3,
            }
            current_prio = priority.get(url_index[url]["field"], 99)
            new_prio = priority.get(field, 99)
            if new_prio < current_prio:
                url_index[url]["field"] = field

    unique_urls = list(url_index.keys())
    print(f"Unique URLs to verify: {len(unique_urls)}")
    print(f"Submitting up to {MAX_WORKERS} concurrent workers ...\n")

    # -- Pass 2: check all URLs in parallel --
    results_map: dict[str, dict] = {}
    checked = 0
    total = len(unique_urls)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(check_url, url): url for url in unique_urls
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "url": url,
                    "status": "error",
                    "http_code": None,
                    "response_time_ms": None,
                    "redirect_target": None,
                    "error_detail": str(exc),
                }
            results_map[url] = result
            checked += 1
            if checked % 25 == 0 or checked == total:
                print(f"  [{checked}/{total}] verified ...")

    print("\nAll URLs checked. Building report ...\n")

    # -- Pass 3: assemble full results list --
    results_list = []
    counters = defaultdict(int)

    for url, meta in url_index.items():
        r = results_map[url]
        entry = {
            "url": url,
            "status": r["status"],
            "http_code": r["http_code"],
            "response_time_ms": r["response_time_ms"],
            "redirect_target": r["redirect_target"],
            "error_detail": r["error_detail"],
            "memorials_using": sorted(meta["memorials"]),
            "field": meta["field"],
        }
        results_list.append(entry)
        counters[r["status"]] += 1

    # Sort: broken/error first, then by url
    priority_order = {"broken": 0, "error": 1, "slow": 2, "redirect": 3, "alive": 4}
    results_list.sort(key=lambda x: (priority_order.get(x["status"], 5), x["url"]))

    # -- Pass 4: update still_live in external_narratives --
    broken_or_error = {"broken", "error"}
    updates_made = 0

    for slug, obj in memorials_data.items():
        memorial = obj["data"]
        filepath = obj["path"]
        changed = False

        for entry in memorial.get("external_narratives", []):
            url = entry.get("original_url", "").strip()
            if not url:
                continue
            r = results_map.get(url)
            if r is None:
                continue
            new_still_live = r["status"] not in broken_or_error
            if entry.get("still_live") != new_still_live:
                entry["still_live"] = new_still_live
                changed = True

        if changed:
            with open(filepath, "w") as f:
                json.dump(memorial, f, indent=2, ensure_ascii=False)
                f.write("\n")
            updates_made += 1

    # -- Build output JSON --
    output = {
        "scan_date": str(date.today()),
        "total_urls": len(unique_urls),
        "alive": counters["alive"],
        "broken": counters["broken"],
        "redirect": counters["redirect"],
        "error": counters["error"],
        "slow": counters["slow"],
        "results": results_list,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # -- Print summary --
    print("=" * 60)
    print("LINK VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Scan date       : {output['scan_date']}")
    print(f"Memorial files  : {len(memorial_files)}")
    print(f"Unique URLs     : {output['total_urls']}")
    print(f"  alive         : {output['alive']}")
    print(f"  redirect      : {output['redirect']}")
    print(f"  broken        : {output['broken']}")
    print(f"  error         : {output['error']}")
    print(f"  slow          : {output['slow']}")
    print(f"Memorial files updated (still_live): {updates_made}")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("=" * 60)

    if counters["broken"] or counters["error"]:
        print(f"\nBROKEN / ERROR URLs ({counters['broken'] + counters['error']} total):")
        for entry in results_list:
            if entry["status"] in broken_or_error:
                slugs = ", ".join(entry["memorials_using"][:3])
                extra = f" (+{len(entry['memorials_using']) - 3} more)" if len(entry["memorials_using"]) > 3 else ""
                detail = entry.get("error_detail") or f"HTTP {entry.get('http_code')}"
                print(f"  [{entry['status'].upper()}] {entry['url']}")
                print(f"         detail={detail}  memorials=[{slugs}{extra}]")

    if counters["redirect"]:
        print(f"\nREDIRECTS ({counters['redirect']} total):")
        for entry in results_list:
            if entry["status"] == "redirect":
                print(f"  {entry['url']}")
                print(f"    -> {entry['redirect_target']}")

    if counters["slow"]:
        print(f"\nSLOW URLs (>{SLOW_THRESHOLD}s):")
        for entry in results_list:
            if entry["status"] == "slow":
                print(f"  {entry['url']}  ({entry['response_time_ms']}ms)")


if __name__ == "__main__":
    main()
