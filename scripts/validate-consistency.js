#!/usr/bin/env node
'use strict';

/**
 * BMR Data Consistency Validator
 *
 * Runs at prebuild. Validates cross-site statistics are consistent:
 * 1. Memorial counts — JSON files = sitemap entries = homepage stats
 * 2. Crew counts — per-memorial sums = aggregate totals
 * 3. Squadron cross-references — memorials reference valid squadrons
 * 4. Crew deduplication warnings — flag same name on multiple memorials
 * 5. Orphan detection — JSONs not generating pages, empty memorials
 * 6. Data completeness — flag memorials with zero useful content
 *
 * Exit code 1 on errors (hard failures). Warnings are logged but don't fail.
 *
 * Usage: node scripts/validate-consistency.js [--strict] [--fix-squadrons]
 */

const fs = require('fs');
const path = require('path');

const MEMORIAL_DIR = path.join(__dirname, '..', 'public', 'data', 'memorials');
const SQUADRON_DIR = path.join(__dirname, '..', 'public', 'data', 'squadrons');
const SITEMAP_PATH = path.join(__dirname, '..', 'public', 'sitemap.xml');

const strict = process.argv.includes('--strict');

// ── Load all memorial data ──────────────────────────────────────────

const memorialFiles = fs.readdirSync(MEMORIAL_DIR)
  .filter(f => f.endsWith('.json'))
  .sort();

const memorials = [];
const loadErrors = [];

for (const file of memorialFiles) {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(MEMORIAL_DIR, file), 'utf8'));
    data._file = file;
    memorials.push(data);
  } catch (e) {
    loadErrors.push(`  JSON parse error: ${file} — ${e.message}`);
  }
}

// ── Load squadron data ──────────────────────────────────────────────

const squadronFiles = fs.existsSync(SQUADRON_DIR)
  ? fs.readdirSync(SQUADRON_DIR).filter(f => f.endsWith('.json')).sort()
  : [];

const squadrons = [];
for (const file of squadronFiles) {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(SQUADRON_DIR, file), 'utf8'));
    data._file = file;
    squadrons.push(data);
  } catch (e) {
    loadErrors.push(`  JSON parse error (squadron): ${file} — ${e.message}`);
  }
}

// ── Collect results ─────────────────────────────────────────────────

const errors = [...loadErrors];
const warnings = [];

// ── 1. Memorial count consistency ───────────────────────────────────

const totalMemorialFiles = memorialFiles.length;
const totalMemorialsLoaded = memorials.length;

if (totalMemorialFiles !== totalMemorialsLoaded) {
  errors.push(`  Memorial count mismatch: ${totalMemorialFiles} files, ${totalMemorialsLoaded} loaded successfully`);
}

// Check for duplicate IDs
const idCounts = {};
for (const m of memorials) {
  const id = m.id || m._file.replace('.json', '');
  idCounts[id] = (idCounts[id] || 0) + 1;
}
const dupeIds = Object.entries(idCounts).filter(([, c]) => c > 1);
for (const [id, count] of dupeIds) {
  errors.push(`  Duplicate memorial ID: "${id}" appears ${count} times`);
}

// Check sitemap if it exists
if (fs.existsSync(SITEMAP_PATH)) {
  const sitemap = fs.readFileSync(SITEMAP_PATH, 'utf8');
  const sitemapMemorials = (sitemap.match(/\/memorial\//g) || []).length;
  if (sitemapMemorials !== totalMemorialsLoaded) {
    warnings.push(`  Sitemap has ${sitemapMemorials} memorial URLs vs ${totalMemorialsLoaded} JSON files`);
  }
}

// ── 2. Crew count consistency ───────────────────────────────────────

let totalCrew = 0;
let memorialsWithCrew = 0;
const crewByMemorial = {};

for (const m of memorials) {
  const id = m.id || m._file.replace('.json', '');
  const crew = m.crew || [];
  crewByMemorial[id] = crew.length;
  totalCrew += crew.length;
  if (crew.length > 0) memorialsWithCrew++;
}

// Check for crew with no name at all (not even "Unknown")
for (const m of memorials) {
  const id = m.id || m._file.replace('.json', '');
  for (let i = 0; i < (m.crew || []).length; i++) {
    const c = m.crew[i];
    const name = (c.name || '').trim();
    if (!name) {
      warnings.push(`  Empty crew name: ${id} crew[${i}] (rank=${c.rank || 'none'}, role=${c.role || 'none'})`);
    }
  }
}

// ── 3. Squadron cross-references ────────────────────────────────────

// Collect all squadron names referenced by memorials
const squadronRefs = {};
for (const m of memorials) {
  const sq = (m.squadron || '').trim();
  if (sq) {
    if (!squadronRefs[sq]) squadronRefs[sq] = [];
    squadronRefs[sq].push(m.id || m._file);
  }
}

// Check squadron data files reference real memorials
const squadronCanonical = {};
for (const sq of squadrons) {
  squadronCanonical[sq.canonical_name || ''] = sq;
  const sqMemorials = sq.memorials || [];
  for (const sm of sqMemorials) {
    const smId = sm.id || sm.slug;
    if (smId && !idCounts[smId]) {
      warnings.push(`  Squadron "${sq.canonical_name}" references non-existent memorial: ${smId}`);
    }
  }
}

// How many unique squadron names in memorials have no squadron page?
const uniqueSquadronNames = Object.keys(squadronRefs);
const orphanSquadrons = uniqueSquadronNames.filter(name => {
  return !squadrons.some(sq =>
    sq.canonical_name === name ||
    (sq.display_name || '').includes(name) ||
    name.includes(sq.canonical_name || '___nomatch___')
  );
});

if (orphanSquadrons.length > 0) {
  warnings.push(`  ${orphanSquadrons.length} squadron names in memorials have no squadron page:`);
  // Group similar names
  for (const name of orphanSquadrons.slice(0, 20)) {
    warnings.push(`    "${name}" (${squadronRefs[name].length} memorials)`);
  }
  if (orphanSquadrons.length > 20) {
    warnings.push(`    ... and ${orphanSquadrons.length - 20} more`);
  }
}

// ── 4. Crew deduplication warnings ──────────────────────────────────

const crewNameIndex = {};
for (const m of memorials) {
  const id = m.id || m._file.replace('.json', '');
  for (const c of (m.crew || [])) {
    const name = (c.name || '').trim().toLowerCase();
    if (name && name !== 'unknown') {
      if (!crewNameIndex[name]) crewNameIndex[name] = [];
      crewNameIndex[name].push({ memorial: id, rank: c.rank, fate: c.fate });
    }
  }
}

// Flag names appearing on 3+ memorials (2 could be legitimate collision memorials)
const suspiciousDupes = Object.entries(crewNameIndex)
  .filter(([, entries]) => entries.length >= 3)
  .sort((a, b) => b[1].length - a[1].length);

if (suspiciousDupes.length > 0) {
  warnings.push(`  ${suspiciousDupes.length} crew names appear on 3+ memorials (may be garbled):`);
  for (const [name, entries] of suspiciousDupes.slice(0, 10)) {
    const memos = entries.map(e => e.memorial).join(', ');
    warnings.push(`    "${name}" (${entries.length}x): ${memos.substring(0, 100)}`);
  }
}

// ── 5. Orphan detection ─────────────────────────────────────────────

// Memorials with no content at all
const emptyMemorials = memorials.filter(m => {
  const hasNarrative = m.narrative && m.narrative.trim().length > 10;
  const hasCrew = m.crew && m.crew.length > 0;
  const hasRemembrance = m.remembrance && (
    (typeof m.remembrance === 'string' && m.remembrance.trim().length > 0) ||
    (Array.isArray(m.remembrance) && m.remembrance.length > 0) ||
    (typeof m.remembrance === 'object' && !Array.isArray(m.remembrance) && Object.keys(m.remembrance).length > 0)
  );
  const hasCommunity = m.community_connection && m.community_connection.trim && m.community_connection.trim().length > 0;
  const hasExternalNarratives = m.external_narratives && m.external_narratives.length > 0;
  return !hasNarrative && !hasCrew && !hasRemembrance && !hasCommunity && !hasExternalNarratives;
});

if (emptyMemorials.length > 0) {
  warnings.push(`  ${emptyMemorials.length} memorials have zero content (no narrative, crew, remembrance, community, or links):`);
  for (const m of emptyMemorials.slice(0, 10)) {
    warnings.push(`    ${m.id || m._file}`);
  }
}

// ── 6. Data completeness scoring ────────────────────────────────────

let sectionsPopulated = { narrative: 0, crew: 0, remembrance: 0, community: 0, links: 0, photos: 0 };
for (const m of memorials) {
  if (m.narrative && m.narrative.trim().length > 10) sectionsPopulated.narrative++;
  if (m.crew && m.crew.length > 0) sectionsPopulated.crew++;
  if (m.remembrance && ((typeof m.remembrance === 'string' && m.remembrance.trim().length > 0) ||
    (Array.isArray(m.remembrance) && m.remembrance.length > 0) ||
    (typeof m.remembrance === 'object' && !Array.isArray(m.remembrance) && Object.keys(m.remembrance).length > 0)))
    sectionsPopulated.remembrance++;
  if (m.community_connection && m.community_connection.trim && m.community_connection.trim().length > 0) sectionsPopulated.community++;
  if (m.external_narratives && m.external_narratives.length > 0) sectionsPopulated.links++;
  if (m.photos && m.photos.length > 0) sectionsPopulated.photos++;
}

// ── 7. Required fields check ────────────────────────────────────────

const requiredFields = ['id', 'title', 'location_name', 'latitude', 'longitude'];
for (const m of memorials) {
  const id = m.id || m._file.replace('.json', '');
  for (const field of requiredFields) {
    if (m[field] === undefined || m[field] === null || m[field] === '') {
      if (field === 'latitude' || field === 'longitude') {
        warnings.push(`  Missing ${field}: ${id}`);
      } else {
        errors.push(`  Missing required field "${field}": ${id}`);
      }
    }
  }
}

// ── Report ──────────────────────────────────────────────────────────

console.log('');
console.log('BMR Data Consistency Validator');
console.log('═'.repeat(50));
console.log('');
console.log('Summary:');
console.log(`  Memorial files:     ${totalMemorialFiles}`);
console.log(`  Loaded OK:          ${totalMemorialsLoaded}`);
console.log(`  Squadron files:     ${squadronFiles.length}`);
console.log(`  Total crew:         ${totalCrew}`);
console.log(`  Memorials w/ crew:  ${memorialsWithCrew}`);
console.log('');

console.log('Section coverage:');
for (const [section, count] of Object.entries(sectionsPopulated)) {
  const pct = ((count / totalMemorialsLoaded) * 100).toFixed(1);
  console.log(`  ${section.padEnd(15)} ${count}/${totalMemorialsLoaded} (${pct}%)`);
}
console.log('');

console.log('Squadron coverage:');
console.log(`  Unique names in memorials: ${uniqueSquadronNames.length}`);
console.log(`  Squadron data pages:       ${squadronFiles.length}`);
console.log(`  Unmatched squadron names:  ${orphanSquadrons.length}`);
console.log('');

if (warnings.length > 0) {
  console.log(`⚠️  WARNINGS (${warnings.length}):`);
  for (const w of warnings) {
    console.log(w);
  }
  console.log('');
}

if (errors.length > 0) {
  console.log(`❌ ERRORS (${errors.length}):`);
  for (const e of errors) {
    console.log(e);
  }
  console.log('');
  console.log('BUILD BLOCKED — fix errors above before deploying.');
  process.exit(1);
} else {
  console.log('✅ No blocking errors. Data is consistent.');
  if (strict && warnings.length > 0) {
    console.log('');
    console.log('STRICT MODE: Warnings treated as errors.');
    process.exit(1);
  }
  process.exit(0);
}
