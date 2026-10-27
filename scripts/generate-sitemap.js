#!/usr/bin/env node
/**
 * Generate sitemap.xml from all static, story, memorial, squadron, and region pages.
 * Run at build time (prebuild step) so sitemap always matches deployed pages.
 *
 * Usage: node scripts/generate-sitemap.js
 */

const fs = require('fs');
const path = require('path');

const SITE_URL = 'https://bombermemorial.co.uk';
const DATA_DIR = path.resolve(__dirname, '../public/data');
const MEMORIALS_DIR = path.join(DATA_DIR, 'memorials');
const SQUADRONS_DIR = path.join(DATA_DIR, 'squadrons');
const OUTPUT = path.resolve(__dirname, '../public/sitemap.xml');

const today = new Date().toISOString().split('T')[0];

function getMemorialSlugs() {
  return fs.readdirSync(MEMORIALS_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => f.replace('.json', ''))
    .sort();
}

function getSquadronSlugs() {
  // Squadron pages are generated from memorials that share squadron names
  // with 2+ memorials. Rather than duplicating that logic, read the built
  // squadron data files if they exist, or fall back to extracting from memorials.
  if (fs.existsSync(SQUADRONS_DIR)) {
    return fs.readdirSync(SQUADRONS_DIR)
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace('.json', ''))
      .sort();
  }

  // Fallback: extract unique squadron names from memorials
  const squadrons = new Map();
  for (const slug of getMemorialSlugs()) {
    try {
      const m = JSON.parse(fs.readFileSync(path.join(MEMORIALS_DIR, `${slug}.json`), 'utf-8'));
      if (m.squadron) {
        const sqSlug = m.squadron.toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
        squadrons.set(sqSlug, (squadrons.get(sqSlug) || 0) + 1);
      }
    } catch {}
  }
  return [...squadrons.entries()]
    .filter(([, count]) => count >= 2)
    .map(([slug]) => slug)
    .sort();
}

// Stub region codes: countries with genuine BC memorials (squadron/general type)
// that are out of crash-site scope. Pages are generated so external links
// don't 404 — they show a research-in-progress stub with contribution CTA.
const STUB_REGION_CODES = ['belgium', 'canada', 'france', 'new-zealand'];

function getRegionCodes() {
  const countries = new Map();
  for (const slug of getMemorialSlugs()) {
    try {
      const m = JSON.parse(fs.readFileSync(path.join(MEMORIALS_DIR, `${slug}.json`), 'utf-8'));
      if (m.country) {
        const code = m.country.toLowerCase().replace(/\s+/g, '-');
        countries.set(code, (countries.get(code) || 0) + 1);
      }
    } catch {}
  }
  // Add stub regions that aren't already present from active memorial data
  for (const code of STUB_REGION_CODES) {
    if (!countries.has(code)) {
      countries.set(code, 0);
    }
  }
  return [...countries.keys()].sort();
}

function url(loc, priority, lastmod) {
  return `  <url>
    <loc>${SITE_URL}${loc}</loc>
    <lastmod>${lastmod || today}</lastmod>
    <priority>${priority}</priority>
  </url>`;
}

// Build sitemap
const urls = [];

// Static pages
urls.push(url('/', '1.0'));
urls.push(url('/map', '0.8'));
urls.push(url('/about', '0.6'));
urls.push(url('/search', '0.5'));
urls.push(url('/squadron', '0.7'));
urls.push(url('/insights', '0.5'));
urls.push(url('/faq', '0.4'));
urls.push(url('/contact', '0.4'));
urls.push(url('/terms', '0.2'));
// /stories 301s to /stories/ on the host; list the canonical form.
urls.push(url('/stories/', '0.7'));
const STATIC_COUNT = urls.length;

// Story pages
const STORIES_DIR = path.join(DATA_DIR, 'stories');
const storySlugs = fs.existsSync(STORIES_DIR)
  ? fs.readdirSync(STORIES_DIR).filter(f => f.endsWith('.md')).map(f => f.replace('.md', '')).sort()
  : [];
for (const slug of storySlugs) {
  const lastmod = fs.statSync(path.join(STORIES_DIR, `${slug}.md`)).mtime.toISOString().split('T')[0];
  urls.push(url(`/stories/${slug}`, '0.8', lastmod));
}

// Memorial pages
const memorialSlugs = getMemorialSlugs();
for (const slug of memorialSlugs) {
  // Try to get lastmod from file mtime
  const filePath = path.join(MEMORIALS_DIR, `${slug}.json`);
  let lastmod = today;
  try {
    const stat = fs.statSync(filePath);
    lastmod = stat.mtime.toISOString().split('T')[0];
  } catch {}
  urls.push(url(`/memorial/${slug}`, '0.8', lastmod));
}

// Squadron pages
const squadronSlugs = getSquadronSlugs();
for (const slug of squadronSlugs) {
  urls.push(url(`/squadron/${slug}`, '0.7'));
}

// Region pages
const regionCodes = getRegionCodes();
for (const code of regionCodes) {
  urls.push(url(`/region/${code}`, '0.6'));
}

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>
`;

fs.writeFileSync(OUTPUT, sitemap);

const totalPages = urls.length;
console.log(`[sitemap] Generated ${OUTPUT}`);
console.log(`[sitemap] Total URLs: ${totalPages}`);
console.log(`[sitemap]   Static: ${STATIC_COUNT}`);
console.log(`[sitemap]   Stories: ${storySlugs.length}`);
console.log(`[sitemap]   Memorials: ${memorialSlugs.length}`);
console.log(`[sitemap]   Squadrons: ${squadronSlugs.length}`);
console.log(`[sitemap]   Regions: ${regionCodes.length}`);
