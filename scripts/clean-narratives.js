#!/usr/bin/env node
/**
 * Clean scraped narrative text: strip boilerplate, fix HTML entities,
 * remove site chrome, clean empty headers, trim footnote markers.
 *
 * Runs at prebuild (before strip-internal-fields.js).
 * Safe to re-run — idempotent.
 *
 * Usage: node scripts/clean-narratives.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');
const glob = require('path');

const MEMORIALS_DIR = path.resolve(__dirname, '../public/data/memorials');
const DRY_RUN = process.argv.includes('--dry-run');

// Boilerplate blocks to remove entirely (order matters — longest first)
const REMOVE_BLOCKS = [
  // Aircrew Remembered site navigation dump (pre and post entity conversion)
  /[•&]bull;\s*Kracker Archive\s*[•&]bull;.*?(?:Searchable Lists|RNZAF|USA)[.\s]*/gs,
  /\u2022\s*Kracker Archive\s*\u2022.*?(?:Searchable Lists|RNZAF|USA)[.\s]*/gs,
  // Partial nav remnants after other cleaning
  /[•\u2022]\s*(?:USA|RNZAF|RAAF|RCAF|Paradie Canadian|Archiwum Polish|Allied Losses|Kracker Archive)\s*[•\u2022]?\s*/g,
  /[•\u2022]?\s*Searchable Lists[.\s]*/gi,
  // Boilerplate CTAs
  /We appeal to anyone with further information and\/or photographs to please contact us via (?:our |the )?HELPDESK\.?\s*/gi,
  /We seek additional information and photographs\.\s*Please contact us via the Helpdesk\.?\s*/gi,
  /Add to or correct this story with a few clicks\.?\s*/gi,
  /Check our [Rr]esearch databases?:?\s*[Dd]atabase [Ll]ist\.?\s*/gi,
  /Archive [Rr]eport:\s*Allied [Ff]orces\s*/gi,
  /Compiled from official National Archive and Service sources,\s*contemporary press reports,\s*personal logbooks,\s*diaries and correspondence,\s*reference books,\s*other sources,\s*and interviews\.?\s*/gi,
  /please contact us via (?:our |the )?helpdesk\.?\s*/gi,
  // Empty markdown headers (## HEADING followed by nothing useful)
  /^## [A-Z ]+\n\s*\n(?=## )/gm,
  // Standalone empty headers at the start of text
  /^(?:## [A-Z ]+\n\s*\n)+(?=\S)/gm,
];

// HTML entities to convert
const ENTITY_MAP = {
  '&bull;': '•',
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&quot;': '"',
  '&#39;': "'",
  '&nbsp;': ' ',
  '&ndash;': '–',
  '&mdash;': '—',
  '&hellip;': '…',
};

// Lines to strip entirely if they match
const STRIP_LINES = [
  /^[•\u2022\s]+$/,                          // Lines that are just bullets
  /^\s*Searchable Lists\s*$/i,
  /^\s*Database List\s*$/i,
  /^\s*HELPDESK\s*$/i,
  /^\s*Click here\s*$/i,
  /^\s*Share this:?\s*$/i,
  /^\s*Like this:?\s*$/i,
  /^\s*Related\s*$/i,
  /^\s*Loading\.\.\.\s*$/i,
  /^\s*Comments are closed\.?\s*$/i,
  /^\s*Leave a [Rr]eply\s*$/i,
  /^\s*Skip to (?:main )?content\s*$/i,
];

function cleanNarrative(text) {
  if (!text) return text;

  let cleaned = text;

  // Replace HTML entities
  for (const [entity, replacement] of Object.entries(ENTITY_MAP)) {
    cleaned = cleaned.split(entity).join(replacement);
  }

  // Remove boilerplate blocks
  for (const pattern of REMOVE_BLOCKS) {
    cleaned = cleaned.replace(pattern, '');
  }

  // Strip junk lines
  cleaned = cleaned
    .split('\n')
    .filter(line => !STRIP_LINES.some(p => p.test(line)))
    .join('\n');

  // Fix words that ran together after stripping (e.g. "HEADING23.06" → "HEADING\n\n23.06")
  cleaned = cleaned.replace(/([A-Za-z])(\d{2}\.\d{2}\.\d{4})/g, '$1\n\n$2');

  // Clean up excessive whitespace (3+ newlines → 2)
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  // Trim
  cleaned = cleaned.trim();

  return cleaned;
}

function processMemorials() {
  const files = fs.readdirSync(MEMORIALS_DIR).filter(f => f.endsWith('.json'));
  let modified = 0;
  let narrativesCleaned = 0;
  let totalRemoved = 0;

  for (const file of files) {
    const filePath = path.join(MEMORIALS_DIR, file);
    const raw = fs.readFileSync(filePath, 'utf-8');
    const memorial = JSON.parse(raw);

    let changed = false;
    const narratives = memorial.external_narratives || [];

    for (const n of narratives) {
      if (!n.full_narrative) continue;

      const original = n.full_narrative;
      const cleaned = cleanNarrative(original);

      if (cleaned !== original) {
        const removed = original.length - cleaned.length;
        totalRemoved += removed;
        narrativesCleaned++;

        if (!DRY_RUN) {
          n.full_narrative = cleaned;
        }
        changed = true;
      }
    }

    // Also clean the main narrative field if present
    if (memorial.narrative) {
      const cleaned = cleanNarrative(memorial.narrative);
      if (cleaned !== memorial.narrative) {
        if (!DRY_RUN) {
          memorial.narrative = cleaned;
        }
        changed = true;
        narrativesCleaned++;
      }
    }

    if (changed) {
      modified++;
      if (!DRY_RUN) {
        fs.writeFileSync(filePath, JSON.stringify(memorial, null, 2));
      }
    }
  }

  console.log(`[clean-narratives] Scanned ${files.length} memorials`);
  console.log(`[clean-narratives] Modified: ${modified} files, ${narrativesCleaned} narratives`);
  console.log(`[clean-narratives] Removed: ${totalRemoved} chars of boilerplate`);
  if (DRY_RUN) {
    console.log(`[clean-narratives] --dry-run: no files written`);
  }
}

processMemorials();
