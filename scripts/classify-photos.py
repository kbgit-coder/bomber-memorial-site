#!/usr/bin/env python3
"""
Classify usable photos in photo_claims using Granite 8B via Ollama.

For each photo: sends caption + source domain + parent URL + memorial title
to Granite, asks for one of 11 categories (10 real + 'junk').

Then computes quality_score and is_hero_eligible.

Usage:
  python3 scripts/classify-photos.py [--limit N] [--dry-run] [--reclassify]
"""

import argparse
import json
import os
import sys
import time

import psycopg2
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAULT_FILE = "/root/.claude/PAI/USER/CREDENTIALS/bmr-research-db.env"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite4:3b"

CATEGORIES = [
    "memorial-exterior",       # the physical memorial stone/plaque/monument
    "memorial-detail",         # close-up of inscription, names, badge
    "crew-portrait",           # individual portrait of crew member
    "crew-group",              # group/squadron photograph
    "crash-site",              # wreckage, crash location then or now
    "landscape-setting",       # contextual geography, village, airfield
    "remembrance-ceremony",    # dedication, wreath, service, anniversary
    "condition-maintenance",   # repair, restoration, condition photo
    "historical-document",     # logbook, letter, newspaper, official record
    "related-building",        # church, museum, school associated with memorial
    "junk",                    # gambling ad, unrelated stock photo, site chrome
]

# Source tier scoring for quality
SOURCE_TIER_SCORE = {
    "iwm.org.uk": 100, "cwgc.org": 100, "mod.uk": 100, "rafmuseum.org.uk": 100,
    "nationalarchives.gov.uk": 100, "abmc.gov": 100,
    "bbc.co.uk": 80, "bbc.com": 80, "warmemorialsonline.org.uk": 80,
    "geograph.org.uk": 75, "americanairmuseum.com": 80,
    "nationalww2museum.org": 80, "forces.net": 70,
    "wikipedia.org": 60, "flickr.com": 50,
}
SQUADRON_PATTERN_SCORE = 65  # squadron associations

PROMPT_TEMPLATE = """Classify this photograph from a WW2 Bomber Command memorial website.

Memorial: {memorial_title}
Photo caption: {caption}
Source website: {source_domain}
Source page URL: {parent_url}

Choose exactly ONE category from this list:
- memorial-exterior (the physical memorial stone, plaque, or monument)
- memorial-detail (close-up showing inscription, engraved names, badge)
- crew-portrait (individual portrait of a crew member)
- crew-group (group or squadron photograph of multiple crew)
- crash-site (wreckage or crash location, historical or modern)
- landscape-setting (surrounding geography, village, airfield)
- remembrance-ceremony (dedication service, wreath laying, anniversary event)
- condition-maintenance (restoration work, condition report photo)
- historical-document (logbook page, letter, newspaper cutting, official record)
- related-building (church, museum, school associated with the memorial)
- junk (gambling advertisement, unrelated stock photo, website decoration, navigation element, casino banner, slot game, betting promotion)

Respond with ONLY a JSON object: {{"category": "...", "confidence": 0.0-1.0, "reason": "brief reason"}}
Do not include any other text."""


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def load_db_env():
    with open(VAULT_FILE) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

def connect():
    load_db_env()
    return psycopg2.connect(
        host=os.environ["BMR_DB_HOST"],
        port=int(os.environ["BMR_DB_PORT"]),
        dbname=os.environ["BMR_DB_NAME"],
        user=os.environ["BMR_DB_USER"],
        password=os.environ["BMR_DB_PASSWORD"],
    )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_photo(caption, source_domain, parent_url, memorial_title):
    """Call Granite 8B to classify a single photo. Returns (category, confidence, reason)."""
    prompt = PROMPT_TEMPLATE.format(
        memorial_title=memorial_title or "Unknown",
        caption=caption or "No caption",
        source_domain=source_domain or "unknown",
        parent_url=parent_url or "unknown",
    )

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 150},
        }, timeout=30)

        if resp.status_code != 200:
            return "unknown", 0.0, f"HTTP {resp.status_code}"

        text = resp.json().get("response", "").strip()

        # Parse JSON from response — handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            cat = parsed.get("category", "unknown").strip().lower()
            conf = float(parsed.get("confidence", 0.5))
            reason = parsed.get("reason", "")

            if cat not in CATEGORIES:
                # Fuzzy match
                for c in CATEGORIES:
                    if c.startswith(cat.split("-")[0]):
                        cat = c
                        break
                else:
                    cat = "unknown"

            return cat, min(1.0, max(0.0, conf)), reason

        return "unknown", 0.0, f"Unparseable: {text[:100]}"

    except requests.Timeout:
        return "unknown", 0.0, "timeout"
    except Exception as e:
        return "unknown", 0.0, str(e)[:100]


def compute_quality_score(width, height, file_size, has_caption, source_domain):
    """Compute 0-100 quality score."""
    # Source tier (40%)
    domain = (source_domain or "").lower()
    tier_score = SOURCE_TIER_SCORE.get(domain, 0)
    if tier_score == 0:
        # Check squadron pattern
        squadron_kw = ("squadron", "bombercommand", "aviation", "aircrew", "raf",
                       "memorial", "yorkshireaircraft", "peakdistrict", "warmemorial")
        if any(p in domain for p in squadron_kw):
            tier_score = SQUADRON_PATTERN_SCORE
        else:
            tier_score = 20  # generic unverified

    # Dimension (30%)
    long_edge = max(width or 0, height or 0)
    if long_edge >= 1200:
        dim_score = 100
    elif long_edge <= 400:
        dim_score = 0
    else:
        dim_score = ((long_edge - 400) / 800) * 100

    # Caption (20%)
    cap_score = 100 if has_caption else 0

    # Density (10%)
    pixels = (width or 1) * (height or 1)
    bpp = (file_size or 0) / pixels if pixels > 0 else 0
    if bpp < 0.05:
        den_score = 20
    elif bpp > 0.5:
        den_score = 100
    else:
        den_score = (bpp / 0.5) * 100

    score = (tier_score * 0.40 + dim_score * 0.30 + cap_score * 0.20 + den_score * 0.10)
    return round(min(100, max(0, score)))


def is_hero_eligible(category, quality_score):
    return quality_score >= 60 and category in (
        "memorial-exterior", "memorial-detail", "crash-site",
        "crew-group", "remembrance-ceremony"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--reclassify", action="store_true", help="Re-classify already-classified photos")
    args = p.parse_args()

    conn = connect()
    cur = conn.cursor()

    # Fetch usable photos
    where = "fetch_status='ok' AND NOT is_icon AND NOT is_duplicate"
    if not args.reclassify:
        where += " AND category='unknown'"

    cur.execute(f"""
        SELECT pc.id, pc.caption, pc.credit, pc.parent_url, pc.original_url,
               pc.width, pc.height, pc.file_size,
               m.slug, m.title
        FROM photo_claims pc
        JOIN memorials m ON m.id=pc.memorial_id
        WHERE {where}
        ORDER BY pc.id
        {"LIMIT " + str(args.limit) if args.limit else ""}
    """)
    photos = cur.fetchall()
    cur.close()

    print(f"[classify] {len(photos)} photos to classify")

    if args.dry_run:
        print("[classify] --dry-run: would classify, exiting")
        return

    from collections import Counter
    stats = Counter()
    start = time.time()

    for i, (pc_id, caption, credit, parent_url, orig_url,
            width, height, file_size, slug, title) in enumerate(photos):

        cat, conf, reason = classify_photo(caption, credit, parent_url, title)
        q_score = compute_quality_score(width, height, file_size,
                                        bool(caption and len(caption) > 10), credit)
        hero = is_hero_eligible(cat, q_score)

        # Junk photos get display_excluded
        excluded = (cat == "junk")

        upd = conn.cursor()
        upd.execute("""
            UPDATE photo_claims SET
                category = %s,
                classification_confidence = %s,
                quality_score = %s,
                is_hero_eligible = %s,
                display_excluded = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (cat, conf, q_score, hero, excluded, pc_id))
        upd.close()
        conn.commit()

        stats[cat] += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            eta = (len(photos) - i - 1) / rate if rate > 0 else 0
            print(f"[classify] {i+1}/{len(photos)} ({rate:.1f}/s, ETA {eta:.0f}s) "
                  f"dist: {dict(stats.most_common(5))}")

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print("CLASSIFICATION COMPLETE")
    print("=" * 60)
    print(f"  Photos classified: {sum(stats.values())}")
    print(f"  Elapsed: {elapsed:.0f}s ({sum(stats.values())/elapsed:.1f}/s)")
    print(f"  Distribution:")
    for cat, n in stats.most_common():
        pct = n / sum(stats.values()) * 100
        print(f"    {cat:30} {n:5} ({pct:.1f}%)")

    # Summary query
    cur = conn.cursor()
    cur.execute("""
        SELECT category, COUNT(*),
               COUNT(*) FILTER (WHERE is_hero_eligible),
               COUNT(*) FILTER (WHERE display_excluded),
               ROUND(AVG(quality_score))
        FROM photo_claims
        WHERE fetch_status='ok' AND NOT is_icon AND NOT is_duplicate
        GROUP BY category ORDER BY 2 DESC
    """)
    print(f"\n  DB summary (all usable photos):")
    print(f"  {'Category':30} {'Count':>6} {'Hero':>6} {'Excl':>6} {'AvgQ':>6}")
    for r in cur.fetchall():
        print(f"  {r[0]:30} {r[1]:6} {r[2]:6} {r[3]:6} {r[4]:6}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
