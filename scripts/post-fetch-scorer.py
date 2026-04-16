#!/usr/bin/env python3
"""
BMR Post-Fetch Link Scorer — Stage 2

Takes links that scored ≥ 0.30 in pre-fetch scoring and refines their scores
using actual page content. Updates link_references with post_fetch_score and
refined tier assignment.

Data sources (checked in order):
1. scrape_log table (stored HTML — free, instant)
2. Live fetch with rate limiting (per-domain 2.5s between requests)

Post-fetch refinements:
- Dimension D (Content Substance): word count, primary source refs, images with captions
- Dimension E (Freshness): actual page dates, copyright year, update cadence
- scrape_status: detects paywall, login, rate limit from HTTP response

Usage:
    python3 scripts/post-fetch-scorer.py                    # All candidates
    python3 scripts/post-fetch-scorer.py --threshold 0.25   # Lower threshold
    python3 scripts/post-fetch-scorer.py --limit 20         # Small test batch
    python3 scripts/post-fetch-scorer.py --domain 97squadron.wordpress.com
    python3 scripts/post-fetch-scorer.py --dry-run
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
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from link_scorer import (
    PRIMARY_SOURCE_KEYWORDS, BOT_BLOCKED_DOMAINS,
)

# ─── Config ──────────────────────────────────────────────────────────

DB_CONTAINER = "bmr-research-db"
DB_USER = "bmr"
DB_NAME = "bmr_research"
RATE_LIMIT = 2.5  # seconds between requests to same domain
FETCH_TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; BomberMemorialResearch/1.0; +https://bombermemorial.co.uk)"

RESULTS_DIR = "/nas2/Projects/BomberMemorial/data-governance/link-graph"


# ─── DB access ───────────────────────────────────────────────────────

def db_query(sql: str) -> str:
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip()


def db_query_to_file(sql: str, tmp_file: str) -> bool:
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c",
         f"\\copy ({sql}) TO '{tmp_file}'"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return False
    subprocess.run(["docker", "cp", f"{DB_CONTAINER}:{tmp_file}", tmp_file],
                   capture_output=True, timeout=30)
    return os.path.exists(tmp_file)


def db_exec_file(sql_file: str) -> bool:
    subprocess.run(["docker", "cp", sql_file, f"{DB_CONTAINER}:/tmp/exec.sql"],
                   capture_output=True, timeout=30)
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-f", "/tmp/exec.sql"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  DB error: {result.stderr[:300]}")
        return False
    return True


def get_candidates(threshold: float, domain: str = None, limit: int = None) -> list[dict]:
    """Get all link_references rows that need post-fetch scoring."""
    where = f"pre_fetch_score >= {threshold} AND scrape_status != 'bot_blocked' AND post_fetch_score IS NULL"
    if domain:
        where += f" AND target_domain = '{domain}'"

    sql = f"""SELECT id, target_url, target_domain, anchor_text, link_context,
                     pre_fetch_score, score_components::text
              FROM link_references
              WHERE {where}
              ORDER BY pre_fetch_score DESC"""
    if limit:
        sql += f" LIMIT {limit}"

    tmp_file = f"/tmp/bmr_candidates_{os.getpid()}.tsv"
    ok = db_query_to_file(sql, tmp_file)
    if not ok:
        return []

    candidates = []
    with open(tmp_file) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            try:
                components = json.loads(parts[6].replace("\\\\", "\\"))
            except Exception:
                components = {}
            candidates.append({
                "id": int(parts[0]),
                "target_url": parts[1].replace("\\n", "\n"),
                "target_domain": parts[2],
                "anchor_text": parts[3].replace("\\n", "\n") if parts[3] else "",
                "link_context": parts[4].replace("\\n", "\n") if parts[4] else "",
                "pre_fetch_score": float(parts[5]),
                "pre_components": components,
            })
    os.unlink(tmp_file)
    return candidates


def get_stored_html_for_url(url: str) -> str | None:
    """Check if we already have this URL's HTML in scrape_log."""
    tmp_file = f"/tmp/bmr_stored_{os.getpid()}.txt"
    safe_url = url.replace("'", "''")
    sql = f"SELECT raw_content FROM scrape_log WHERE url = '{safe_url}' AND raw_content IS NOT NULL AND length(raw_content) > 500 LIMIT 1"
    ok = db_query_to_file(sql, tmp_file)
    if not ok or not os.path.exists(tmp_file):
        return None
    with open(tmp_file) as f:
        content = f.read().strip()
    os.unlink(tmp_file)
    content = content.replace("\\n", "\n").replace("\\\\", "\\")
    return content if len(content) > 100 else None


# ─── Live fetching ───────────────────────────────────────────────────

class FetchResult:
    def __init__(self):
        self.status = "pending"
        self.http_code = None
        self.html = None
        self.error = None
        self.final_url = None


def fetch_live(url: str) -> FetchResult:
    """Fetch a URL with HTTPS->HTTP fallback. Returns FetchResult."""
    result = FetchResult()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    urls_to_try = [url]
    if url.startswith("https://"):
        urls_to_try.append(url.replace("https://", "http://"))

    for try_url in urls_to_try:
        try:
            req = urllib.request.Request(try_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=FETCH_TIMEOUT, context=ctx)
            html = resp.read().decode("utf-8", errors="ignore")
            result.status = "ok"
            result.http_code = 200
            result.html = html
            result.final_url = resp.url
            return result
        except urllib.error.HTTPError as e:
            result.http_code = e.code
            if e.code == 401:
                result.status = "login_required"
                result.error = "HTTP 401 Unauthorized"
                return result
            elif e.code == 402:
                result.status = "paywalled"
                result.error = "HTTP 402 Payment Required"
                return result
            elif e.code == 403:
                result.status = "bot_blocked"
                result.error = "HTTP 403 Forbidden"
                return result
            elif e.code == 404:
                result.status = "not_found"
                result.error = "HTTP 404"
                return result
            elif e.code == 429:
                result.status = "rate_limited"
                result.error = "HTTP 429 Too Many Requests"
                return result
            result.error = f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            result.error = f"URL error: {e.reason}"
        except Exception as e:
            result.error = f"Fetch error: {e}"

    result.status = "failed"
    return result


# ─── Content analysis ────────────────────────────────────────────────

def detect_paywall_patterns(soup) -> tuple[bool, bool]:
    """
    Returns (is_paywalled, is_login_required) based on content analysis.
    """
    text = soup.get_text().lower()

    paywall_signals = [
        "subscribe to read", "subscribe for access", "paid subscription",
        "become a member to read", "members only", "unlock this content",
        "pay to read", "this article is for subscribers",
    ]

    login_signals = [
        "log in to view", "please log in", "sign in to continue",
        "login required", "register to read", "create an account to view",
    ]

    is_paywalled = any(s in text for s in paywall_signals)
    is_login = any(s in text for s in login_signals)

    return is_paywalled, is_login


def analyse_content(html: str) -> dict:
    """
    Extract post-fetch signals from actual page content.
    Returns a dict of measurable signals used for Dimension D and E scoring.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return {"parse_error": True}

    # Remove chrome
    for tag in soup(["script", "style", "nav", "footer", "noscript", "aside", "header"]):
        tag.decompose()

    # Get main text content
    body = soup.find("body") or soup
    text = body.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    # Primary source references (scan full text)
    text_lower = text.lower()
    primary_sources_found = [kw for kw in PRIMARY_SOURCE_KEYWORDS if kw in text_lower]

    # Images with captions
    images_with_captions = 0
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        # Find adjacent figcaption
        has_figcaption = False
        parent = img.parent
        if parent and parent.name == "figure":
            if parent.find("figcaption"):
                has_figcaption = True
        # Descriptive alt text (not filler)
        if has_figcaption or (len(alt) > 15 and not any(
            x in alt.lower() for x in ["logo", "icon", "banner", "button", "avatar", "spacer"]
        )):
            images_with_captions += 1

    # Specific identifying details — dates, place-names, full names
    full_dates = re.findall(
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+19[3-4]\d\b",
        text,
    )
    numeric_dates = re.findall(r"\b\d{1,2}[./-]\d{1,2}[./-]19[3-4]\d\b", text)
    specific_places = re.findall(r"\bat\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", text)
    full_names = re.findall(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b", text)

    # Freshness signals
    current_year = datetime.now(timezone.utc).year
    recent_years = [str(current_year), str(current_year - 1)]
    five_year_window = [str(y) for y in range(current_year - 5, current_year + 1)]

    # Copyright year — look for © [year] patterns
    copyright_matches = re.findall(r"(?:©|\(c\)|copyright)\s*(\d{4})", text, re.IGNORECASE)
    copyright_years = [int(y) for y in copyright_matches if 1990 <= int(y) <= current_year + 1]
    latest_copyright = max(copyright_years) if copyright_years else None

    # Post dates — look for common formats
    post_date_matches = re.findall(
        r"(?:posted|published|updated|date[d]?)\s*[:\s]\s*([\w\s,]+20\d{2})",
        text, re.IGNORECASE,
    )

    # Any year 2010+ in text
    any_recent_year = re.findall(r"\b(20[1-2]\d)\b", text)
    recent_years_in_text = sorted(set(int(y) for y in any_recent_year if 2010 <= int(y) <= current_year + 1))

    has_recent_12mo = latest_copyright and latest_copyright >= current_year - 1
    if not has_recent_12mo and recent_years_in_text:
        has_recent_12mo = recent_years_in_text[-1] >= current_year - 1

    has_recent_5y = latest_copyright and latest_copyright >= current_year - 5
    if not has_recent_5y and recent_years_in_text:
        has_recent_5y = recent_years_in_text[-1] >= current_year - 5

    has_any_dates = bool(copyright_years or recent_years_in_text or full_dates or numeric_dates or post_date_matches)

    # Paywall/login detection
    is_paywalled, is_login = detect_paywall_patterns(soup)

    return {
        "parse_error": False,
        "word_count": word_count,
        "primary_sources_found": primary_sources_found,
        "images_with_captions": images_with_captions,
        "full_dates_count": len(full_dates) + len(numeric_dates),
        "place_mentions_count": len(specific_places),
        "named_persons_count": len(set(full_names)),
        "latest_copyright_year": latest_copyright,
        "recent_years_in_text": recent_years_in_text[-5:] if recent_years_in_text else [],
        "has_recent_12mo": has_recent_12mo,
        "has_recent_5y": has_recent_5y,
        "has_any_dates": has_any_dates,
        "is_paywalled": is_paywalled,
        "is_login_required": is_login,
    }


# ─── Post-fetch scoring ──────────────────────────────────────────────

def score_dimension_d_post(signals: dict) -> tuple[float, dict]:
    """Dimension D Content Substance — post-fetch (0-15 points)."""
    components = {}
    total = 0.0

    if signals.get("word_count", 0) > 500:
        components["substantive_prose"] = 5
        total += 5

    if signals.get("primary_sources_found"):
        components["primary_source_refs"] = 4
        components["primary_sources_matched"] = signals["primary_sources_found"]
        total += 4

    if signals.get("images_with_captions", 0) >= 2:
        components["captioned_images"] = 3
        total += 3

    # Specific identifying details — combined signal
    details_count = (
        signals.get("full_dates_count", 0)
        + signals.get("place_mentions_count", 0) // 3
        + signals.get("named_persons_count", 0) // 5
    )
    if details_count >= 3:
        components["specific_details"] = 3
        total += 3

    return min(total, 15.0), components


def score_dimension_e_post(signals: dict) -> tuple[float, dict]:
    """Dimension E Freshness — post-fetch (-3 to +10 points)."""
    components = {}
    total = 0.0
    awarded_recency = False

    if signals.get("has_recent_12mo"):
        components["active_12mo"] = 5
        total += 5
        awarded_recency = True

    if not awarded_recency and signals.get("has_recent_5y"):
        components["active_5y"] = 3
        total += 3
        awarded_recency = True

    if signals.get("has_any_dates"):
        components["has_discoverable_dates"] = 2
        total += 2

    if signals.get("latest_copyright_year"):
        components["has_copyright"] = 2
        total += 2

    # Penalties
    shallow = signals.get("word_count", 0) < 500
    no_primary = not signals.get("primary_sources_found")
    no_dates = not signals.get("has_any_dates")

    if no_dates and shallow:
        components["penalty_no_dates_shallow"] = -2
        total -= 2

    # >10 years dormant penalty
    current_year = datetime.now(timezone.utc).year
    copyright_year = signals.get("latest_copyright_year")
    very_stale = copyright_year and (current_year - copyright_year) > 10
    recent_years = signals.get("recent_years_in_text", [])
    very_stale_content = very_stale or (not recent_years or max(recent_years) < current_year - 10)

    if very_stale_content and shallow and no_primary:
        components["penalty_very_stale_shallow"] = -3
        total -= 3

    return total, components


def refine_score(candidate: dict, signals: dict) -> dict:
    """
    Compute the post-fetch score by refining Dimensions D and E against real content.
    Dimensions A, B, C remain from pre-fetch.
    Returns a dict with post_fetch_score, components, and new tier.
    """
    pre = candidate["pre_components"]
    pre_dims = pre.get("dimensions", {}) if isinstance(pre, dict) else {}

    # Retain A, B, C from pre-fetch
    dim_a = pre_dims.get("A", 0)
    dim_b = pre_dims.get("B", 0)
    dim_c = pre_dims.get("C", 0)

    # Recompute D and E from content
    dim_d, d_components = score_dimension_d_post(signals)
    dim_e, e_components = score_dimension_e_post(signals)

    raw_total = dim_a + dim_b + dim_c + dim_d + dim_e
    clamped = max(raw_total, 0.0)
    normalised = min(clamped / 95.0, 1.0)

    # Assign tier using ORIGINAL thresholds (Keith wants to see what happens with proper post-fetch)
    if normalised >= 0.75:
        tier = "PRIMARY"
    elif normalised >= 0.50:
        tier = "SECONDARY"
    elif normalised >= 0.25:
        tier = "TERTIARY"
    elif normalised >= 0.10:
        tier = "BACKGROUND"
    else:
        tier = "NOISE"

    return {
        "post_fetch_score": round(normalised, 4),
        "post_fetch_raw": round(raw_total, 2),
        "tier": tier,
        "dimension_d_post": dim_d,
        "dimension_e_post": dim_e,
        "d_components": d_components,
        "e_components": e_components,
        "dim_a_pre": dim_a,
        "dim_b_pre": dim_b,
        "dim_c_pre": dim_c,
    }


# ─── Update DB ───────────────────────────────────────────────────────

def escape_sql(s: str) -> str:
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"


def update_link_ref(row_id: int, refined: dict, signals: dict, scrape_status: str,
                     unscrapable_reason: str = None, outreach_candidate: bool = False,
                     source_components: dict = None) -> bool:
    """Update a link_references row with post-fetch results."""

    # Merge components
    combined_components = source_components if source_components else {}
    combined_components["post_fetch"] = {
        "raw_total": refined["post_fetch_raw"],
        "normalised": refined["post_fetch_score"],
        "dimensions": {
            "A": refined["dim_a_pre"],
            "B": refined["dim_b_pre"],
            "C": refined["dim_c_pre"],
            "D": refined["dimension_d_post"],
            "E": refined["dimension_e_post"],
        },
        "d_components": refined["d_components"],
        "e_components": refined["e_components"],
        "content_signals": {
            "word_count": signals.get("word_count", 0),
            "primary_sources": signals.get("primary_sources_found", []),
            "images_with_captions": signals.get("images_with_captions", 0),
            "latest_copyright": signals.get("latest_copyright_year"),
            "recent_years": signals.get("recent_years_in_text", []),
            "is_paywalled": signals.get("is_paywalled", False),
            "is_login_required": signals.get("is_login_required", False),
        },
        "analysed_at": datetime.now(timezone.utc).isoformat(),
    }

    components_json = json.dumps(combined_components)
    reason_sql = escape_sql(unscrapable_reason) if unscrapable_reason else "NULL"
    outreach_sql = "TRUE" if outreach_candidate else "FALSE"

    sql = f"""UPDATE link_references
              SET post_fetch_score = {refined['post_fetch_score']},
                  tier = '{refined['tier']}',
                  score_components = {escape_sql(components_json)},
                  scrape_status = '{scrape_status}',
                  unscrapable_reason = {reason_sql},
                  outreach_candidate = {outreach_sql},
                  last_rescored_at = NOW()
              WHERE id = {row_id};"""

    tmp_sql = f"/tmp/bmr_update_{os.getpid()}.sql"
    with open(tmp_sql, "w") as f:
        f.write(sql)
    ok = db_exec_file(tmp_sql)
    os.unlink(tmp_sql)
    return ok


def mark_unfetchable(row_id: int, status: str, reason: str, outreach: bool = False) -> bool:
    """Mark a link as unfetchable without refining score."""
    outreach_sql = "TRUE" if outreach else "FALSE"
    sql = f"""UPDATE link_references
              SET scrape_status = '{status}',
                  unscrapable_reason = {escape_sql(reason)},
                  outreach_candidate = {outreach_sql},
                  last_rescored_at = NOW()
              WHERE id = {row_id};"""
    tmp_sql = f"/tmp/bmr_mark_{os.getpid()}.sql"
    with open(tmp_sql, "w") as f:
        f.write(sql)
    ok = db_exec_file(tmp_sql)
    os.unlink(tmp_sql)
    return ok


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BMR Post-Fetch Link Scorer")
    parser.add_argument("--threshold", type=float, default=0.30,
                        help="Pre-fetch score threshold (default 0.30)")
    parser.add_argument("--domain", help="Process only this target domain")
    parser.add_argument("--limit", type=int, help="Limit candidates")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without processing")
    args = parser.parse_args()

    print("=" * 70)
    print("BMR Post-Fetch Link Scorer — Stage 2")
    print("=" * 70)

    candidates = get_candidates(args.threshold, args.domain, args.limit)
    print(f"\nCandidates: {len(candidates)} links with pre_fetch_score >= {args.threshold}")

    if not candidates:
        print("No candidates to process.")
        return

    # Group by domain
    by_domain = defaultdict(list)
    for c in candidates:
        by_domain[c["target_domain"]].append(c)

    print(f"Unique domains: {len(by_domain)}")

    if args.dry_run:
        print("\nDomain breakdown:")
        for d, items in sorted(by_domain.items(), key=lambda x: -len(x[1])):
            print(f"  {d}: {len(items)}")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    stats = {
        "total": len(candidates),
        "from_cache": 0,
        "fetched_live": 0,
        "failed": 0,
        "scrapable": 0,
        "paywalled": 0,
        "login_required": 0,
        "bot_blocked_runtime": 0,
        "rate_limited": 0,
        "not_found": 0,
        "tier_changes": defaultdict(int),
        "new_primary": [],
        "new_secondary": [],
    }

    domain_last_fetch = {}
    processed = 0

    for domain in sorted(by_domain.keys()):
        domain_candidates = by_domain[domain]
        print(f"\n[{domain}] {len(domain_candidates)} links")

        for c in domain_candidates:
            processed += 1
            url = c["target_url"]
            print(f"  [{processed}/{stats['total']}] {url[:80]}", end=" ", flush=True)

            # Try stored HTML first
            html = get_stored_html_for_url(url)
            used_cache = bool(html)

            # If not cached, fetch live
            fetch_result = None
            if not html:
                # Rate limit per domain
                last = domain_last_fetch.get(domain, 0)
                wait = RATE_LIMIT - (time.time() - last)
                if wait > 0:
                    time.sleep(wait)
                domain_last_fetch[domain] = time.time()

                fetch_result = fetch_live(url)

                if fetch_result.status == "ok":
                    html = fetch_result.html
                    stats["fetched_live"] += 1
                else:
                    # Mark with appropriate status
                    if fetch_result.status in ("paywalled", "login_required"):
                        outreach = True
                        stats["paywalled" if fetch_result.status == "paywalled" else "login_required"] += 1
                    elif fetch_result.status == "bot_blocked":
                        outreach = False
                        stats["bot_blocked_runtime"] += 1
                    elif fetch_result.status == "rate_limited":
                        outreach = False
                        stats["rate_limited"] += 1
                    elif fetch_result.status == "not_found":
                        outreach = False
                        stats["not_found"] += 1
                    else:
                        outreach = False
                        stats["failed"] += 1

                    mark_unfetchable(c["id"], fetch_result.status, fetch_result.error or "", outreach)
                    print(f"  → {fetch_result.status.upper()}")
                    continue
            else:
                stats["from_cache"] += 1

            # Analyse content
            signals = analyse_content(html)
            if signals.get("parse_error"):
                stats["failed"] += 1
                mark_unfetchable(c["id"], "failed", "HTML parse error")
                print("  → PARSE ERROR")
                continue

            # Check for paywall/login patterns in content
            scrape_status = "scrapable"
            unscrapable_reason = None
            outreach = False

            if signals.get("is_paywalled"):
                scrape_status = "paywalled"
                unscrapable_reason = "Paywall patterns detected in content"
                outreach = True
                stats["paywalled"] += 1
            elif signals.get("is_login_required"):
                scrape_status = "login_required"
                unscrapable_reason = "Login required patterns detected"
                outreach = True
                stats["login_required"] += 1
            else:
                stats["scrapable"] += 1

            # Refine score
            refined = refine_score(c, signals)

            # Wrap pre-fetch components under "pre_fetch" key for clarity
            source_components = {"pre_fetch": c["pre_components"]}

            update_link_ref(
                c["id"], refined, signals, scrape_status,
                unscrapable_reason, outreach, source_components,
            )

            # Track tier changes
            old_tier = "BACKGROUND" if c["pre_fetch_score"] < 0.25 else "TERTIARY"
            if c["pre_fetch_score"] >= 0.50:
                old_tier = "SECONDARY"
            new_tier = refined["tier"]
            if old_tier != new_tier:
                stats["tier_changes"][f"{old_tier}→{new_tier}"] += 1

            if new_tier == "PRIMARY":
                stats["new_primary"].append({
                    "url": url,
                    "anchor": c["anchor_text"][:80],
                    "score": refined["post_fetch_score"],
                })
            elif new_tier == "SECONDARY" and old_tier != "SECONDARY":
                stats["new_secondary"].append({
                    "url": url,
                    "anchor": c["anchor_text"][:80],
                    "score": refined["post_fetch_score"],
                })

            src = "cache" if used_cache else "live"
            print(f"  {src} {refined['post_fetch_score']:.3f} {refined['tier']}")

    # Summary
    print(f"\n{'=' * 70}")
    print("POST-FETCH SCORING COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total candidates: {stats['total']}")
    print(f"  From cache: {stats['from_cache']}")
    print(f"  Fetched live: {stats['fetched_live']}")
    print(f"  Failed: {stats['failed']}")
    print(f"\n  Scrape status results:")
    print(f"    scrapable: {stats['scrapable']}")
    print(f"    paywalled: {stats['paywalled']} (outreach candidates)")
    print(f"    login_required: {stats['login_required']} (outreach candidates)")
    print(f"    bot_blocked (runtime): {stats['bot_blocked_runtime']}")
    print(f"    rate_limited: {stats['rate_limited']}")
    print(f"    not_found: {stats['not_found']}")
    print(f"\n  Tier movements:")
    for change, count in sorted(stats["tier_changes"].items(), key=lambda x: -x[1]):
        print(f"    {change}: {count}")
    print(f"\n  New PRIMARY tier: {len(stats['new_primary'])}")
    print(f"  New SECONDARY tier: {len(stats['new_secondary'])}")

    # Save summary
    summary_file = os.path.join(RESULTS_DIR, f"post_fetch_run_{run_id}.json")
    with open(summary_file, "w") as f:
        json.dump({
            "run_id": run_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "threshold": args.threshold,
            "stats": {
                **{k: v for k, v in stats.items() if k not in ("tier_changes", "new_primary", "new_secondary")},
                "tier_changes": dict(stats["tier_changes"]),
                "new_primary": stats["new_primary"],
                "new_secondary": stats["new_secondary"],
            },
        }, f, indent=2, ensure_ascii=False)
    os.chmod(summary_file, 0o666)
    print(f"\n  Summary: {summary_file}")


if __name__ == "__main__":
    main()
