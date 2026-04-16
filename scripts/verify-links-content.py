#!/usr/bin/env python3
"""
BMR-107 — Content-Verified Link Checker (Minion Worker)

Each invocation processes a batch of memorials. For each memorial:
1. Fetch every external URL (GET, not just HEAD)
2. Check HTTP status
3. Content verification — does the page contain at least ONE memorial identifier?
   (aircraft serial, squadron, location, crew surname)
4. Cross-reference CWGC/Find A Grave URLs against specific crew/memorial data
5. Output structured verification result per link

Usage:
  python3 verify-links-content.py --batch 0 --batch-size 5
  python3 verify-links-content.py --all  (process everything sequentially)
"""

import json
import os
import re
import sys
import time
import argparse
import urllib.request
import urllib.error
import ssl
from html.parser import HTMLParser

CONTEXTS_FILE = '/tmp/bmr107-memorial-contexts.json'
OUTPUT_DIR = '/tmp/bmr107-results'
MEMORIALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'data', 'memorials')

# Domains known to block automated requests — skip content check, mark as bot-blocked
BOT_BLOCKERS = {
    'www.tracesofwar.com', 'tracesofwar.com',
    'www.americanairmuseum.com', 'americanairmuseum.com',
    'www.peakdistrict.gov.uk', 'peakdistrict.gov.uk',
    'www.dartmoor.gov.uk', 'dartmoor.gov.uk',
    'www.raf.mod.uk', 'raf.mod.uk',
}

# Rate limiting per domain
domain_last_request = {}
RATE_LIMIT_SECONDS = 1.5


class TextExtractor(HTMLParser):
    """Extract visible text from HTML."""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False
        self._skip_tags = {'script', 'style', 'noscript', 'header', 'nav', 'footer'}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def extract_domain(url):
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    except Exception:
        return ''


def rate_limit(domain):
    """Wait if we've hit this domain recently."""
    now = time.time()
    last = domain_last_request.get(domain, 0)
    elapsed = now - last
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    domain_last_request[domain] = time.time()


def fetch_url(url, timeout=15):
    """Fetch URL content. Returns (status_code, body_text, final_url, error)."""
    domain = extract_domain(url)

    if domain in BOT_BLOCKERS:
        return (None, '', url, 'bot-blocked')

    rate_limit(domain)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Bomber Memorial Heritage Project link checker)',
            'Accept': 'text/html,application/xhtml+xml,*/*',
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = resp.status
            final_url = resp.url
            content_type = resp.headers.get('Content-Type', '')

            # Only parse HTML content
            if 'text/html' in content_type or 'xhtml' in content_type:
                raw = resp.read(200_000)  # Read up to 200KB
                charset = 'utf-8'
                ct_parts = content_type.split('charset=')
                if len(ct_parts) > 1:
                    charset = ct_parts[1].strip().split(';')[0]
                try:
                    html = raw.decode(charset, errors='replace')
                except (LookupError, UnicodeDecodeError):
                    html = raw.decode('utf-8', errors='replace')

                extractor = TextExtractor()
                extractor.feed(html)
                body_text = extractor.get_text()
            elif 'image/' in content_type:
                body_text = '[IMAGE]'
            else:
                body_text = ''

            return (status, body_text, final_url, None)

    except urllib.error.HTTPError as e:
        return (e.code, '', url, f'HTTP {e.code}')
    except urllib.error.URLError as e:
        return (None, '', url, f'URLError: {e.reason}')
    except TimeoutError:
        return (None, '', url, 'Timeout')
    except Exception as e:
        return (None, '', url, str(e)[:200])


def verify_content(body_text, memorial_ctx, url_info):
    """
    Check if page content matches the memorial.
    Returns (verified: bool, match_type: str, detail: str)
    """
    if not body_text or body_text == '[IMAGE]':
        return (None, 'no_content', 'Non-HTML or empty response')

    text_lower = body_text.lower()
    matches = []

    # Check serial number
    serial = memorial_ctx.get('serial_number', '').strip()
    if serial and len(serial) >= 3:
        # Try exact and common formats: ED393, ED 393, ED-393
        serial_variants = [
            serial.lower(),
            re.sub(r'^([a-z]+)(\d)', r'\1 \2', serial.lower()),
            re.sub(r'^([a-z]+)(\d)', r'\1-\2', serial.lower()),
        ]
        for sv in serial_variants:
            if sv in text_lower:
                matches.append(f'serial:{serial}')
                break

    # Check squadron
    squadron = memorial_ctx.get('squadron', '').strip()
    if squadron and len(squadron) >= 3:
        sq_lower = squadron.lower()
        # Match "61 Squadron", "No. 61", "61 Sqn", etc.
        sq_num = re.search(r'\d+', sq_lower)
        if sq_num and sq_num.group() in text_lower:
            # Require the number near "squadron" or "sqn" or "sqdn"
            num = sq_num.group()
            patterns = [f'{num} squadron', f'{num} sqn', f'no.{num}', f'no. {num}', f'#{num}']
            for p in patterns:
                if p in text_lower:
                    matches.append(f'squadron:{squadron}')
                    break

    # Check location
    location = memorial_ctx.get('location_name', '').strip()
    if location and len(location) >= 3:
        if location.lower() in text_lower:
            matches.append(f'location:{location}')

    county = memorial_ctx.get('county', '').strip()
    if county and len(county) >= 3:
        if county.lower() in text_lower:
            matches.append(f'county:{county}')

    # Check crew surnames
    for surname in memorial_ctx.get('crew_surnames', []):
        if surname and len(surname) >= 3:
            if surname.lower() in text_lower:
                matches.append(f'crew:{surname}')
                break  # One crew match is enough

    # Special handling for CWGC URLs — verify specific crew member name
    if url_info.get('field', '').startswith('crew[') and url_info.get('crew_name'):
        crew_name = url_info['crew_name']
        name_parts = [p.strip() for p in re.split(r'[,\s]+', crew_name) if len(p.strip()) >= 3]
        cwgc_match = any(p.lower() in text_lower for p in name_parts)
        if cwgc_match:
            matches.append(f'cwgc_name_match:{crew_name}')
        else:
            return (False, 'mismatch', f'CWGC page does not mention crew member: {crew_name}')

    # Special handling for Find A Grave URLs
    if 'findagrave.com' in url_info.get('url', '').lower():
        # Must match at least one crew surname or the memorial title
        title_words = [w for w in memorial_ctx.get('title', '').split() if len(w) >= 4]
        fag_match = any(w.lower() in text_lower for w in title_words)
        surname_match = any(s.lower() in text_lower for s in memorial_ctx.get('crew_surnames', []) if len(s) >= 3)
        if fag_match or surname_match:
            matches.append('findagrave_verified')
        else:
            return (False, 'mismatch', f'Find A Grave page does not match memorial identifiers')

    if matches:
        return (True, 'verified', '; '.join(matches))
    else:
        # No identifiers found — could be a general reference site (Wikipedia, Legion, etc.)
        # Don't flag as mismatch if it's a maintainer/contact website
        if url_info.get('field', '') in ('maintainer.website', 'squadron_badge_url') or \
           url_info.get('field', '').startswith('local_contacts'):
            return (None, 'not_applicable', 'Contact/badge URL — content verification not applicable')

        return (False, 'unverified', 'No memorial identifiers found in page content')


def process_memorial(memorial_ctx):
    """Process all URLs for one memorial. Returns list of results."""
    slug = memorial_ctx['slug']
    results = []

    for url_info in memorial_ctx['urls']:
        url = url_info['url']
        status_code, body_text, final_url, error = fetch_url(url)

        result = {
            'url': url,
            'field': url_info.get('field', ''),
            'http_status': status_code,
            'final_url': final_url if final_url != url else None,
            'error': error,
        }

        if error == 'bot-blocked':
            result['verification'] = 'bot-blocked'
            result['detail'] = f'Domain blocks automated requests'
        elif error:
            result['verification'] = 'unreachable'
            result['detail'] = error
        elif status_code and 200 <= status_code < 300:
            verified, match_type, detail = verify_content(body_text, memorial_ctx, url_info)
            result['verification'] = match_type
            result['detail'] = detail
        elif status_code and 300 <= status_code < 400:
            result['verification'] = 'redirect'
            result['detail'] = f'Redirected to {final_url}'
        elif status_code == 404 or status_code == 410:
            result['verification'] = 'broken'
            result['detail'] = f'HTTP {status_code}'
        else:
            result['verification'] = 'error'
            result['detail'] = f'HTTP {status_code}'

        results.append(result)

    return {
        'slug': slug,
        'title': memorial_ctx['title'],
        'serial_number': memorial_ctx.get('serial_number', ''),
        'urls_checked': len(results),
        'results': results,
    }


def main():
    parser = argparse.ArgumentParser(description='BMR-107 Content-Verified Link Checker')
    parser.add_argument('--batch', type=int, help='Batch number (0-indexed)')
    parser.add_argument('--batch-size', type=int, default=5, help='Memorials per batch')
    parser.add_argument('--all', action='store_true', help='Process all memorials')
    args = parser.parse_args()

    with open(CONTEXTS_FILE) as f:
        all_contexts = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.all:
        contexts = all_contexts
    elif args.batch is not None:
        start = args.batch * args.batch_size
        end = start + args.batch_size
        contexts = all_contexts[start:end]
    else:
        parser.error('Specify --all or --batch N')

    print(f'Processing {len(contexts)} memorials ({sum(len(c["urls"]) for c in contexts)} URLs)')

    all_results = []
    for i, ctx in enumerate(contexts):
        slug = ctx['slug']
        n_urls = len(ctx['urls'])
        print(f'  [{i+1}/{len(contexts)}] {slug} ({n_urls} URLs)')

        result = process_memorial(ctx)
        all_results.append(result)

        # Write per-memorial result
        outpath = os.path.join(OUTPUT_DIR, f'{slug}.json')
        with open(outpath, 'w') as f:
            json.dump(result, f, indent=2)

    # Summary
    total = sum(r['urls_checked'] for r in all_results)
    verified = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'verified')
    unverified = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'unverified')
    mismatch = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'mismatch')
    broken = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'broken')
    unreachable = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'unreachable')
    bot_blocked = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'bot-blocked')
    not_applicable = sum(1 for r in all_results for u in r['results'] if u['verification'] == 'not_applicable')

    summary = {
        'scan_date': '2026-04-09',
        'memorials_processed': len(all_results),
        'total_urls': total,
        'verified': verified,
        'unverified': unverified,
        'mismatch': mismatch,
        'broken': broken,
        'unreachable': unreachable,
        'bot_blocked': bot_blocked,
        'not_applicable': not_applicable,
    }

    print(f'\n=== SUMMARY ===')
    for k, v in summary.items():
        print(f'  {k}: {v}')

    # Write batch summary
    batch_id = f'batch-{args.batch}' if args.batch is not None else 'all'
    summary_path = os.path.join(OUTPUT_DIR, f'summary-{batch_id}.json')
    summary['results'] = all_results
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nResults written to {summary_path}')


if __name__ == '__main__':
    main()
