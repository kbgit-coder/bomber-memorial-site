#!/usr/bin/env node
/**
 * Filter scraped narratives to keep only content that ADDS DEPTH
 * beyond what's already in the memorial's structured fields.
 *
 * Removes:
 * - Crew lists (already in crew table)
 * - Date/unit/aircraft/base/location fields (already in details section)
 * - Empty section headers
 * - Short fragments that aren't sentences
 * - Repeated operation summaries that match the existing narrative
 *
 * Keeps:
 * - Human stories, personal histories, operational detail
 * - Remembrance/anniversary accounts
 * - Footnotes and supplementary context
 * - Anything that reads as prose and isn't duplicated
 *
 * Runs after clean-narratives.js in the prebuild chain.
 * Usage: node scripts/filter-narrative-depth.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');

const MEMORIALS_DIR = path.resolve(__dirname, '../public/data/memorials');
const DRY_RUN = process.argv.includes('--dry-run');

// Lines matching these patterns are structured data already displayed elsewhere
const DUPLICATE_LINE_PATTERNS = [
  // Field: Value lines (crew roles, aircraft details, etc.)
  /^(?:Date|Unit|Type|Base|Location|Pilot|Co-?pilot|Flight Engineer|Navigator|Air Bomber|Bomb Aimer|Wireless Operator|Air Gunner|Rear Gunner|Mid-?upper Gunner|Badge|Operation|Target|Station|Aircraft|Serial|Squadron|Airfield|Cause of (?:loss|crash)):/i,
  // Short role prefixes used by Aircrew Remembered
  /^(?:Fl\/Eng|Nav|Air\/Bmr|Vis\.?\s*Air|W\/Op|Air\/Gnr|Fl\/Sgt|MU\/AG|R\/AG):/i,
  // Crew lines: Rank. Name ServiceNumber Force Age - Fate
  /^(?:F\/Sgt|P\/O|W\/O|F\/O|Fl\/Lt|Sgt|Cpl|LAC|AC[12]|Fg\/Off|Sqn\/Ldr|Wg\/Cdr|Gp\/Capt)\.\s+\S+.*\d{5,}.*(?:RAF|RAAF|RCAF|RNZAF|USAAF)/i,
  // Bare crew lines: Name ServiceNumber - Killed/Survived etc
  /^\S+\s+\S+.*\d{6,}\s+(?:RAFVR|RAAF|RCAF|RNZAF|RAF)\s+Age\s+\d/i,
  // Rank Name — no context, just a name + service number
  /^[A-Z][a-z]+\s+[A-Z][a-z]+\s+\d{6,}\s+(?:RAFVR|RAF|RAAF|RCAF)/,
];

// Headers that are empty / generic / just structural
const JUNK_HEADER_RE = /^#{1,4}\s+(INTRODUCTION|REASON FOR LOSS|BURIAL DETAILS|BIOGRAPHICAL DETAILS|CREW|THE CREW|AIRCRAFT|THE AIRCRAFT|OPERATION|THE OPERATION|DETAILS|BACKGROUND|REFERENCES?|SOURCES?|NOTES?|ACKNOWLEDGEMENTS?)\s*$/i;

// Lines that are just a date in isolation (already shown in details)
const BARE_DATE_RE = /^\d{1,2}[\/.]\d{1,2}[\/.]\d{2,4}\s*(?:No\.\s*No\.)?.*(?:Squadron|Lancaster|Halifax|Wellington|Stirling|Mosquito|Hampden|Whitley|Blenheim|Manchester|Liberator|Fortress)/i;

// Motto lines already shown in squadron section
const MOTTO_RE = /^(?:Motto|Badge):\s*["']?/i;

function isNarrativeLine(line, memorial) {
  const trimmed = line.trim();
  if (!trimmed) return false;

  // Empty or generic headers → skip
  if (JUNK_HEADER_RE.test(trimmed)) return false;

  // Meaningful headers (70th Anniversary, etc.) → keep
  if (/^#{1,4}\s+/.test(trimmed) && !JUNK_HEADER_RE.test(trimmed)) return true;

  // Structured data lines → skip
  for (const pattern of DUPLICATE_LINE_PATTERNS) {
    if (pattern.test(trimmed)) return false;
  }

  // Bare date + aircraft line → skip
  if (BARE_DATE_RE.test(trimmed)) return false;

  // Motto/badge lines → skip
  if (MOTTO_RE.test(trimmed)) return false;

  // Very short fragments (< 30 chars) that aren't sentences → skip
  if (trimmed.length < 30 && !trimmed.endsWith('.') && !trimmed.endsWith('?') && !trimmed.endsWith('!')) {
    return false;
  }

  // Everything else is narrative → keep
  return true;
}

function filterNarrative(text, memorial) {
  if (!text) return text;

  const lines = text.split('\n');
  const kept = [];
  let lastKept = '';

  for (const line of lines) {
    if (isNarrativeLine(line, memorial)) {
      kept.push(line);
      lastKept = line.trim();
    }
    // Keep blank lines between kept content (preserve paragraph breaks)
    else if (line.trim() === '' && kept.length > 0 && kept[kept.length - 1].trim() !== '') {
      kept.push('');
    }
  }

  // Trim trailing blank lines
  while (kept.length > 0 && kept[kept.length - 1].trim() === '') {
    kept.pop();
  }

  const result = kept.join('\n').trim();

  // If filtering removed everything meaningful (< 50 chars remaining), return null
  // This means the scrape had ONLY structured data, no added depth
  if (result.length < 50) return null;

  return result;
}

function processMemorials() {
  const files = fs.readdirSync(MEMORIALS_DIR).filter(f => f.endsWith('.json'));
  let modified = 0;
  let narrativesFiltered = 0;
  let narrativesRemoved = 0;
  let charsRemoved = 0;

  for (const file of files) {
    const filePath = path.join(MEMORIALS_DIR, file);
    const raw = fs.readFileSync(filePath, 'utf-8');
    const memorial = JSON.parse(raw);

    let changed = false;
    const narratives = memorial.external_narratives || [];

    for (const n of narratives) {
      if (!n.full_narrative) continue;

      const original = n.full_narrative;
      const filtered = filterNarrative(original, memorial);

      if (filtered === null) {
        // Nothing of depth — remove the full_narrative entirely
        if (!DRY_RUN) {
          delete n.full_narrative;
        }
        narrativesRemoved++;
        charsRemoved += original.length;
        changed = true;
      } else if (filtered !== original) {
        if (!DRY_RUN) {
          n.full_narrative = filtered;
        }
        narrativesFiltered++;
        charsRemoved += (original.length - filtered.length);
        changed = true;
      }
    }

    if (changed) {
      modified++;
      if (!DRY_RUN) {
        fs.writeFileSync(filePath, JSON.stringify(memorial, null, 2));
      }
    }
  }

  console.log(`[filter-depth] Scanned ${files.length} memorials`);
  console.log(`[filter-depth] Modified: ${modified} files`);
  console.log(`[filter-depth] Narratives filtered (depth kept): ${narrativesFiltered}`);
  console.log(`[filter-depth] Narratives removed (no depth): ${narrativesRemoved}`);
  console.log(`[filter-depth] Chars of duplicate data removed: ${charsRemoved}`);
  if (DRY_RUN) {
    console.log(`[filter-depth] --dry-run: no files written`);
  }
}

processMemorials();
