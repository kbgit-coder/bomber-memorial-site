#!/usr/bin/env bun
/**
 * Quality Monitor — deterministic build/deploy gate.
 *
 * Catches, before any visitor sees them:
 *   1. Duplicate ids and titles across all three data dirs
 *   2. Schema violations (missing/empty required fields, bad tiers, id↔filename mismatch)
 *   3. Formatting errors (malformed dates, out-of-range coords, placeholder what3words,
 *      adjacent duplicated phrases)
 *   4. AI-slop phrasing in prose fields (inscriptions exempt — verbatim historical text)
 *   5. Tier-vs-content consistency (a "Comprehensive" record with no crew and no
 *      narrative is lying about itself)
 *
 * Exit 0 = clean. Exit 1 = violations (blocks build/deploy).
 * Usage: bun scripts/quality-monitor.ts [--warn-only]
 */

import { readdirSync, readFileSync } from "fs";
import { join, basename } from "path";

const REPO = join(import.meta.dir, "..");
const DATA_DIRS = [
  "public/data/memorials",
  "international-memorials",
  "ftr-memorials",
];

const VALID_TIERS = new Set(["Comprehensive", "Partial", "Stub"]);

// Prose fields scanned for slop. Inscriptions are verbatim historical text — never scanned.
const PROSE_FIELDS = [
  "narrative",
  "memorial_details",
  "community_connection",
  "crew_summary",
] as const;

// AI-slop and banned-provenance patterns. Tuned during triage — add, don't loosen.
const SLOP_PATTERNS: { re: RegExp; label: string }[] = [
  { re: /stands? as a (lasting |powerful |poignant )?testament/i, label: "slop: 'stands as a testament'" },
  { re: /serves? as a (poignant|stark|powerful|solemn|lasting) reminder/i, label: "slop: 'serves as a ... reminder'" },
  { re: /rich tapestry/i, label: "slop: 'rich tapestry'" },
  { re: /a rare immediacy/i, label: "slop: 'a rare immediacy'" },
  { re: /in the annals of/i, label: "slop: 'in the annals of'" },
  { re: /little did (they|he|she) know/i, label: "slop: 'little did they know'" },
  { re: /nestled (in|among|between|at)/i, label: "slop: 'nestled'" },
  { re: /\bdelve[sd]? into\b/i, label: "slop: 'delve into'" },
  { re: /paying homage to/i, label: "slop: 'paying homage to'" },
  { re: /Leitheiser/i, label: "banned provenance: 'Leitheiser'" },
  { re: /hackathon/i, label: "banned provenance: 'hackathon'" },
  { re: /\bplaceholder\b/i, label: "placeholder text" },
  { re: /research needed/i, label: "internal note: 'research needed'" },
  { re: /\bTBD\b/, label: "internal note: 'TBD'" },
  { re: /\blorem ipsum\b/i, label: "placeholder text: 'lorem ipsum'" },
];

// Adjacent duplicated phrase (5+ words repeated back-to-back), e.g.
// "Florennes Airbase & Spitfire Museum Florennes Airbase & Spitfire Museum ..."
const DUP_PHRASE = /\b([\w&'-]+(?: [\w&'-]+){4,}?)\s+\1\b/i;

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
// crash_date honest-imprecision forms for area/multi-crash memorials and
// records where only the month/year/era is verifiable: YYYY-MM, YYYY, YYYY-YYYY, WW2.
const CRASH_DATE_RE = /^(\d{4}-\d{2}-\d{2}|\d{4}-\d{2}|\d{4}(-\d{4})?|WW2)$/;
const W3W_RE = /^[a-z]+\.[a-z]+\.[a-z]+$/;
const W3W_PLACEHOLDERS = new Set(["unverified.approximate.location"]);

type Violation = { file: string; check: string; detail: string };
const violations: Violation[] = [];
const v = (file: string, check: string, detail: string) =>
  violations.push({ file, check, detail });

// ---------------------------------------------------------------------------
// Load
// ---------------------------------------------------------------------------
type Rec = Record<string, any>;
const records: { file: string; rec: Rec }[] = [];

for (const dir of DATA_DIRS) {
  const abs = join(REPO, dir);
  let names: string[];
  try {
    names = readdirSync(abs).filter((n) => n.endsWith(".json"));
  } catch {
    continue; // dir absent — fine
  }
  for (const name of names) {
    if (name.startsWith("_")) continue; // _ftr-summary.data.json etc.
    const file = join(dir, name);
    let rec: Rec;
    try {
      rec = JSON.parse(readFileSync(join(abs, name), "utf8"));
    } catch (e) {
      v(file, "json", `unparseable JSON: ${(e as Error).message}`);
      continue;
    }
    if (Array.isArray(rec)) continue; // summary arrays are not records
    records.push({ file, rec });
  }
}

// ---------------------------------------------------------------------------
// 1. Duplicates
// ---------------------------------------------------------------------------
const byId = new Map<string, string[]>();
const byTitle = new Map<string, string[]>();
for (const { file, rec } of records) {
  if (rec.id) byId.set(rec.id, [...(byId.get(rec.id) ?? []), file]);
  if (rec.title) {
    const t = String(rec.title).trim().toLowerCase();
    byTitle.set(t, [...(byTitle.get(t) ?? []), file]);
  }
}
for (const [id, files] of byId)
  if (files.length > 1) v(files.join(" + "), "dup-id", `id "${id}" in ${files.length} files`);
for (const [title, files] of byTitle)
  if (files.length > 1) v(files.join(" + "), "dup-title", `title "${title}" in ${files.length} files`);

// ---------------------------------------------------------------------------
// 2–5. Per-record checks
// ---------------------------------------------------------------------------
for (const { file, rec } of records) {
  const expectId = basename(file, ".json");

  // Schema
  for (const req of ["id", "title", "country"])
    if (!rec[req] || String(rec[req]).trim() === "")
      v(file, "schema", `required field "${req}" missing or empty`);
  if (rec.id && rec.id !== expectId)
    v(file, "schema", `id "${rec.id}" does not match filename "${expectId}"`);
  if (!VALID_TIERS.has(rec.data_quality))
    v(file, "schema", `data_quality "${rec.data_quality}" not in Comprehensive/Partial/Stub`);
  if (!Array.isArray(rec.sources) || rec.sources.length === 0)
    v(file, "schema", "sources missing or empty — every record must cite at least one source");
  else
    for (const s of rec.sources)
      if (!s.title || String(s.title).trim() === "")
        v(file, "schema", "source entry with empty title");

  // Formatting: dates
  {
    const lu = rec.last_updated;
    if (lu !== undefined && lu !== "" && !DATE_RE.test(String(lu)))
      v(file, "format", `last_updated "${lu}" not YYYY-MM-DD`);
    const cd = rec.crash_date;
    if (cd !== undefined && cd !== "") {
      if (!CRASH_DATE_RE.test(String(cd)))
        v(file, "format", `crash_date "${cd}" not an accepted form (YYYY-MM-DD, YYYY-MM, YYYY, YYYY-YYYY, WW2)`);
      else if (/^\d{4}/.test(String(cd))) {
        const year = Number(String(cd).slice(0, 4));
        if (year < 1936 || year > 1947)
          v(file, "format", `crash_date "${cd}" outside plausible wartime range`);
      }
    }
  }

  // Formatting: coordinates
  for (const [cf, min, max] of [["latitude", -90, 90], ["longitude", -180, 180]] as const) {
    const val = rec[cf];
    if (val === undefined || val === null || val === "") continue;
    if (typeof val !== "number" || Number.isNaN(val) || val < min || val > max)
      v(file, "format", `${cf} "${val}" invalid`);
  }

  // Formatting: what3words
  const w3w = rec.what3words;
  if (typeof w3w === "string" && w3w !== "") {
    if (W3W_PLACEHOLDERS.has(w3w)) v(file, "format", `what3words is a placeholder: "${w3w}"`);
    else if (!W3W_RE.test(w3w)) v(file, "format", `what3words "${w3w}" malformed`);
  }

  // Prose: slop + duplicated phrases
  for (const pf of PROSE_FIELDS) {
    const text = rec[pf];
    if (typeof text !== "string" || text === "") continue;
    for (const { re, label } of SLOP_PATTERNS) {
      const m = text.match(re);
      if (m) v(file, "slop", `${label} in ${pf}: "...${m[0]}..."`);
    }
    const dup = text.match(DUP_PHRASE);
    if (dup) v(file, "format", `adjacent duplicated phrase in ${pf}: "${dup[1].slice(0, 60)}..."`);
  }

  // Tier consistency
  const narrLen = typeof rec.narrative === "string" ? rec.narrative.trim().length : 0;
  const crewLen = Array.isArray(rec.crew) ? rec.crew.length : 0;
  if (rec.data_quality === "Comprehensive" && narrLen < 200 && crewLen === 0)
    v(file, "tier", `Comprehensive but narrative ${narrLen} chars and no crew — overstated tier`);
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
const warnOnly = process.argv.includes("--warn-only");
console.log(`Quality monitor: ${records.length} records scanned across ${DATA_DIRS.length} dirs`);

if (violations.length === 0) {
  console.log("✓ clean — no violations");
  process.exit(0);
}

const byCheck = new Map<string, Violation[]>();
for (const viol of violations)
  byCheck.set(viol.check, [...(byCheck.get(viol.check) ?? []), viol]);

for (const [check, list] of [...byCheck.entries()].sort()) {
  console.log(`\n[${check}] ${list.length} violation(s):`);
  for (const { file, detail } of list) console.log(`  ${file}: ${detail}`);
}
console.log(`\n✗ ${violations.length} violation(s) in total`);
process.exit(warnOnly ? 0 : 1);
