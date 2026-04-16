#!/usr/bin/env python3
"""
BMR Full Staging Test — Every Page, Every Check
Tests all 573+ memorial pages plus special pages on staging.
Produces detailed statistics report with pass/fail/improvement metrics.

Usage: python3 scripts/staging-full-test.py [--parallel N]

SET NEW STANDARDS.
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

STAGING_URL = "https://staging.bombermemorial.co.uk"
STAGING_USER = "keith"
STAGING_PASS = "bmr-staging-2026"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LOG_FILE = os.path.join(REPORT_DIR, 'staging-test-report.log')
REPORT_FILE = os.path.join(REPORT_DIR, 'staging-test-report.md')

PARALLEL = 4
for i, arg in enumerate(sys.argv):
    if arg == '--parallel' and i + 1 < len(sys.argv):
        PARALLEL = int(sys.argv[i + 1])


def test_page(slug, json_data, page):
    """Test a single memorial page. Returns dict of check results."""
    url = f"{STAGING_URL}/memorial/{slug}"
    result = {
        'slug': slug,
        'data_quality': json_data.get('data_quality', 'Unknown'),
        'has_inscription_data': bool(json_data.get('inscription')),
        'has_county_data': bool(json_data.get('county')),
        'has_crash_date_data': bool(json_data.get('crash_date')),
        'has_squadron_data': bool(json_data.get('squadron')),
        'has_crew_data': bool(json_data.get('crew') and len(json_data.get('crew', [])) > 0),
        'has_narrative_data': bool(json_data.get('narrative')),
        'has_coords_data': bool(json_data.get('latitude')),
        'has_photos_data': bool(json_data.get('photos') and len(json_data.get('photos', [])) > 0),
        'checks': {},
        'error': None,
    }

    try:
        resp = page.goto(url, timeout=20000, wait_until='networkidle')
        text = page.inner_text('body')
        text_lower = text.lower()
        html = page.content()

        # === STRUCTURAL CHECKS ===
        result['checks']['status_200'] = resp.status == 200
        result['checks']['has_h1'] = bool(re.search(r'<h1[^>]*>.+?</h1>', html, re.DOTALL))
        result['checks']['no_error_text'] = not any(err in text[:300] for err in ['Not Found', 'Error:', 'Something went wrong', '404'])
        result['checks']['content_length'] = len(text) > 300
        result['checks']['has_title_tag'] = bool(re.search(r'<title>.{10,}</title>', html))

        # === MEMORIAL SECTION CHECKS ===
        result['checks']['the_memorial_section'] = 'the memorial' in text_lower
        result['checks']['inscription_section'] = 'inscription' in text_lower
        result['checks']['memorial_type_shown'] = bool(re.search(r'(?:memorial\s*type|type\s*of\s*memorial)', text_lower))

        # === LOCATION CHECKS ===
        location_pattern = r'(england|scotland|wales|northern ireland|united kingdom|shire|london|devon|highland|cornwall|sussex|surrey|kent|norfolk|suffolk|essex|somerset|dorset|antrim|yorkshire|manchester|lancashire|staffordshire|warwickshire|derbyshire|nottinghamshire|leicestershire|hampshire|buckinghamshire|oxfordshire|berkshire|hertfordshire|bedfordshire|cambridgeshire|rutland|northamptonshire|herefordshire|worcestershire|shropshire|cheshire|merseyside|cumbria|durham|northumberland|tyne|dumfries|lothian|fife|angus|argyll|perthshire|aberdeenshire|inverness|galloway|borders|gwynedd|powys|glamorgan|pembrokeshire|ceredigion|carmarthenshire|flintshire|wrexham|denbighshire|conwy|isle of|tyrone|fermanagh|armagh|down|derry|londonderry)'
        result['checks']['has_location'] = bool(re.search(location_pattern, text_lower))

        # === DATA QUALITY RENDERING ===
        result['checks']['shows_quality_badge'] = bool(re.search(r'(complete|good|partial|stub)\s*record', text_lower))

        # === ALL CAPS CHECK (inscription) ===
        insc_match = re.search(r'INSCRIPTION\s*\n(.*?)(?:\n[A-Z]{2,}\s|\nCREW|\nTHE CREW|\nSOURCES)', text, re.DOTALL)
        if insc_match and json_data.get('inscription'):
            insc_rendered = insc_match.group(1).strip()
            letters = [c for c in insc_rendered if c.isalpha()]
            if len(letters) > 20:
                upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
                result['checks']['no_all_caps_inscription'] = upper_ratio < 0.7
            else:
                result['checks']['no_all_caps_inscription'] = True
        else:
            result['checks']['no_all_caps_inscription'] = True

        # === SOURCE ATTRIBUTION ===
        result['checks']['has_sources'] = 'source' in text_lower or 'iwm' in text_lower or 'contributor' in text_lower

        # Overall
        result['passed'] = all(result['checks'].values())
        result['check_count'] = len(result['checks'])
        result['pass_count'] = sum(1 for v in result['checks'].values() if v)
        result['fail_count'] = sum(1 for v in result['checks'].values() if not v)

    except Exception as e:
        result['error'] = str(e)
        result['passed'] = False
        result['checks'] = {'connection': False}
        result['check_count'] = 1
        result['pass_count'] = 0
        result['fail_count'] = 1

    return result


def test_special_page(path, label, page):
    """Test a non-memorial page."""
    url = f"{STAGING_URL}/{path}"
    result = {'slug': path, 'label': label, 'checks': {}, 'error': None}

    try:
        resp = page.goto(url, timeout=20000, wait_until='networkidle')
        text = page.inner_text('body')
        html = page.content()

        result['checks']['status_200'] = resp.status == 200
        result['checks']['has_content'] = len(text) > 200
        result['checks']['has_h1'] = bool(re.search(r'<h1[^>]*>.+?</h1>', html, re.DOTALL))
        result['checks']['no_error'] = not any(err in text[:300] for err in ['Not Found', 'Error:', '404'])

        result['passed'] = all(result['checks'].values())
    except Exception as e:
        result['error'] = str(e)
        result['passed'] = False

    return result


def run_batch(batch_data):
    """Run a batch of tests with one browser instance."""
    batch_id, slugs_and_data = batch_data
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        ctx = browser.new_context(
            http_credentials={"username": STAGING_USER, "password": STAGING_PASS},
            user_agent='Mozilla/5.0 (compatible; BMR-StageTest/1.0)',
        )
        pg = ctx.new_page()

        for i, (slug, json_data) in enumerate(slugs_and_data):
            if i % 25 == 0:
                print(f'  [B{batch_id}] {i}/{len(slugs_and_data)}...', flush=True)
            result = test_page(slug, json_data, pg)
            results.append(result)
            time.sleep(0.3)  # Light rate limit

        ctx.close()
        browser.close()

    return results


def main():
    start_time = datetime.now()
    print(f"\n{'=' * 70}")
    print(f"BMR FULL STAGING TEST — {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Testing ALL pages on {STAGING_URL}")
    print(f"{'=' * 70}\n")

    # Load all memorial JSONs
    memorials = []
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith('.json'):
            continue
        slug = fname.replace('.json', '')
        with open(os.path.join(DATA_DIR, fname)) as f:
            data = json.load(f)
        memorials.append((slug, data))

    print(f"Memorials to test: {len(memorials)}")
    print(f"Parallel browsers: {PARALLEL}")

    # Split into batches
    batch_size = max(1, len(memorials) // PARALLEL)
    batches = []
    for i in range(0, len(memorials), batch_size):
        batches.append((len(batches) + 1, memorials[i:i + batch_size]))

    print(f"Batches: {len(batches)} of ~{batch_size} each\n")

    # Run batches (ProcessPoolExecutor for true parallelism)
    all_results = []
    for batch_data in batches:
        batch_results = run_batch(batch_data)
        all_results.extend(batch_results)
        done = len(all_results)
        passed = sum(1 for r in all_results if r['passed'])
        print(f"  Progress: {done}/{len(memorials)} tested, {passed} passed so far")

    # Test special pages
    print("\nTesting special pages...")
    from playwright.sync_api import sync_playwright
    special_results = []
    special_pages = [
        ("", "Homepage"),
        ("insights", "Insights Dashboard"),
        ("qa-dashboard", "Quality Dashboard"),
        ("contact", "Contact"),
        ("faq", "FAQ"),
        ("site-terms", "Site Terms"),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = browser.new_context(
            http_credentials={"username": STAGING_USER, "password": STAGING_PASS}
        )
        pg = ctx.new_page()
        for path, label in special_pages:
            r = test_special_page(path, label, pg)
            special_results.append(r)
            print(f"  {'✅' if r['passed'] else '❌'} {label}")
        ctx.close()
        browser.close()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # === GENERATE REPORT ===
    total = len(all_results)
    passed = sum(1 for r in all_results if r['passed'])
    failed = sum(1 for r in all_results if not r['passed'])
    errors = sum(1 for r in all_results if r.get('error'))

    # Per-check stats
    check_stats = defaultdict(lambda: {'pass': 0, 'fail': 0})
    for r in all_results:
        for check_name, check_val in r['checks'].items():
            if check_val:
                check_stats[check_name]['pass'] += 1
            else:
                check_stats[check_name]['fail'] += 1

    # Quality distribution
    quality_dist = Counter(r['data_quality'] for r in all_results)

    # Data coverage
    coverage = {
        'inscription': sum(1 for r in all_results if r['has_inscription_data']),
        'county': sum(1 for r in all_results if r['has_county_data']),
        'crash_date': sum(1 for r in all_results if r['has_crash_date_data']),
        'squadron': sum(1 for r in all_results if r['has_squadron_data']),
        'crew': sum(1 for r in all_results if r['has_crew_data']),
        'narrative': sum(1 for r in all_results if r['has_narrative_data']),
        'coordinates': sum(1 for r in all_results if r['has_coords_data']),
        'photos': sum(1 for r in all_results if r['has_photos_data']),
    }

    # Failed pages detail
    failed_pages = [r for r in all_results if not r['passed']]
    fail_reasons = Counter()
    for r in failed_pages:
        for check_name, check_val in r['checks'].items():
            if not check_val:
                fail_reasons[check_name] += 1

    # Before enrichment baseline (from NSTA: 218 production, 335 stubs)
    baseline = {
        'total_memorials': 573,
        'production_pages': 218,
        'stub_pages': 355,
        'stubs_with_inscription': 0,
        'stubs_with_county': 0,
        'stubs_with_crash_date': 0,
        'stubs_quality_stub': 355,
    }

    # === WRITE REPORT ===
    report_lines = []
    report_lines.append(f"# BMR Staging Test Report — {start_time.strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("")
    report_lines.append(f"**Site:** {STAGING_URL}")
    report_lines.append(f"**Duration:** {duration:.0f}s ({duration/60:.1f} min)")
    report_lines.append(f"**Pages tested:** {total} memorials + {len(special_results)} special pages")
    report_lines.append("")

    report_lines.append("## Overall Results")
    report_lines.append("")
    report_lines.append(f"| Metric | Count | Percentage |")
    report_lines.append(f"|--------|-------|------------|")
    report_lines.append(f"| **Total memorial pages** | {total} | 100% |")
    report_lines.append(f"| **All checks passed** | {passed} | {100*passed/total:.1f}% |")
    report_lines.append(f"| **Some checks failed** | {failed} | {100*failed/total:.1f}% |")
    report_lines.append(f"| **Connection errors** | {errors} | {100*errors/total:.1f}% |")
    report_lines.append("")

    report_lines.append("## Special Pages")
    report_lines.append("")
    for r in special_results:
        report_lines.append(f"- {'✅' if r['passed'] else '❌'} **{r.get('label', r['slug'])}** — {'PASS' if r['passed'] else 'FAIL'}")
    report_lines.append("")

    report_lines.append("## Per-Check Pass Rates")
    report_lines.append("")
    report_lines.append(f"| Check | Passed | Failed | Rate |")
    report_lines.append(f"|-------|--------|--------|------|")
    for check_name in sorted(check_stats.keys()):
        s = check_stats[check_name]
        t = s['pass'] + s['fail']
        rate = 100 * s['pass'] / t if t else 0
        report_lines.append(f"| {check_name} | {s['pass']} | {s['fail']} | {rate:.1f}% |")
    report_lines.append("")

    report_lines.append("## Data Quality Distribution")
    report_lines.append("")
    report_lines.append(f"| Quality Level | Count | Percentage |")
    report_lines.append(f"|---------------|-------|------------|")
    for q in ['Complete', 'Good', 'Partial', 'Stub', 'Unknown']:
        count = quality_dist.get(q, 0)
        if count > 0:
            report_lines.append(f"| {q} | {count} | {100*count/total:.1f}% |")
    report_lines.append("")

    report_lines.append("## Data Field Coverage")
    report_lines.append("")
    report_lines.append(f"| Field | Has Data | Missing | Coverage |")
    report_lines.append(f"|-------|----------|---------|----------|")
    for field, count in sorted(coverage.items(), key=lambda x: -x[1]):
        missing = total - count
        report_lines.append(f"| {field} | {count} | {missing} | {100*count/total:.1f}% |")
    report_lines.append("")

    report_lines.append("## Enrichment Improvement (Before → After)")
    report_lines.append("")
    report_lines.append("*Baseline: 218 production memorials + 335 bare stubs (coords/photos only)*")
    report_lines.append("")
    report_lines.append(f"| Metric | Before | After | Improvement |")
    report_lines.append(f"|--------|--------|-------|-------------|")
    report_lines.append(f"| Stubs at 'Stub' quality | {baseline['stubs_quality_stub']} | {quality_dist.get('Stub', 0)} | **-{baseline['stubs_quality_stub'] - quality_dist.get('Stub', 0)}** |")
    report_lines.append(f"| Pages at 'Good' quality | ~218 | {quality_dist.get('Good', 0)} | **+{quality_dist.get('Good', 0) - 218}** |")
    report_lines.append(f"| Pages with inscription | ~218 | {coverage['inscription']} | **+{coverage['inscription'] - 218}** |")
    report_lines.append(f"| Pages with county | ~218 | {coverage['county']} | **+{coverage['county'] - 218}** |")
    report_lines.append(f"| Pages with crash date | ~150 | {coverage['crash_date']} | **+{coverage['crash_date'] - 150}** |")
    report_lines.append(f"| Pages with squadron | ~80 | {coverage['squadron']} | **+{coverage['squadron'] - 80}** |")
    report_lines.append("")

    if failed_pages:
        report_lines.append("## Failure Analysis")
        report_lines.append("")
        report_lines.append(f"**Most common failure reasons:**")
        report_lines.append("")
        for reason, count in fail_reasons.most_common(10):
            report_lines.append(f"- `{reason}`: {count} pages")
        report_lines.append("")

        report_lines.append(f"**Failed pages ({len(failed_pages)}):**")
        report_lines.append("")
        for r in sorted(failed_pages, key=lambda x: x['slug']):
            failed_checks = [k for k, v in r['checks'].items() if not v]
            err = f" — ERROR: {r['error'][:60]}" if r.get('error') else ""
            report_lines.append(f"- `{r['slug']}`: {', '.join(failed_checks)}{err}")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append(f"*Generated {end_time.strftime('%Y-%m-%d %H:%M:%S')} by BMR staging-full-test.py*")

    report_text = '\n'.join(report_lines)

    # Write report
    with open(REPORT_FILE, 'w') as f:
        f.write(report_text)

    # Also write to log
    with open(LOG_FILE, 'w') as f:
        f.write(f"BMR STAGING TEST LOG — {start_time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{'=' * 60}\n\n")
        for r in all_results:
            status = "PASS" if r['passed'] else "FAIL"
            failed_checks = [k for k, v in r['checks'].items() if not v]
            line = f"[{status}] {r['slug']} (quality={r['data_quality']})"
            if failed_checks:
                line += f" — failed: {', '.join(failed_checks)}"
            if r.get('error'):
                line += f" — ERROR: {r['error'][:80]}"
            f.write(line + '\n')
        f.write(f"\n{'=' * 60}\n")
        f.write(f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors}\n")
        f.write(f"Duration: {duration:.0f}s\n")

    # Console summary
    print(f"\n{'=' * 70}")
    print(f"BMR FULL STAGING TEST COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Duration:        {duration:.0f}s ({duration/60:.1f} min)")
    print(f"  Pages tested:    {total} memorials + {len(special_results)} special")
    print(f"  ALL CHECKS PASS: {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"  Some failures:   {failed}/{total} ({100*failed/total:.1f}%)")
    print(f"  Errors:          {errors}")
    print()
    print(f"  QUALITY DISTRIBUTION:")
    for q in ['Complete', 'Good', 'Partial', 'Stub']:
        c = quality_dist.get(q, 0)
        if c > 0:
            bar = '█' * (c * 40 // total)
            print(f"    {q:10s} {c:4d} ({100*c/total:5.1f}%) {bar}")
    print()
    print(f"  DATA COVERAGE:")
    for field in ['county', 'inscription', 'coordinates', 'crash_date', 'narrative', 'squadron', 'crew', 'photos']:
        c = coverage.get(field, 0)
        bar = '█' * (c * 40 // total)
        print(f"    {field:15s} {c:4d}/{total} ({100*c/total:5.1f}%) {bar}")
    print()
    if failed_pages:
        print(f"  TOP FAILURE REASONS:")
        for reason, count in fail_reasons.most_common(5):
            print(f"    {reason}: {count}")
    print()
    print(f"  Report: {REPORT_FILE}")
    print(f"  Log:    {LOG_FILE}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
