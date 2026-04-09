#!/usr/bin/env node
/**
 * strip-internal-fields.js
 *
 * Pre-build script: removes internal audit fields and personal contact data
 * from all memorial JSON files under public/data/memorials/.
 *
 * INTERNAL FIELDS removed from location_confidence:
 *   - verification_notes, sources, score
 *
 * PERSONAL DATA removed (GDPR/privacy — HARD GATE):
 *   - local_contacts[].contact_email
 *   - local_contacts[].contact_phone
 *   - local_contacts[].contact_name
 *   - maintainer.contact_email
 *   - maintainer.contact_phone
 *
 * The NAS master at /nas2/Projects/BomberMemorial/data/master/memorials/
 * retains the full data. This script operates only on the repo build copies.
 *
 * Idempotent — running it multiple times produces the same result.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const MEMORIALS_DIR = path.join(__dirname, '..', 'public', 'data', 'memorials');

const LC_INTERNAL_FIELDS = ['verification_notes', 'sources', 'score'];
const CONTACT_PII_FIELDS = ['contact_email', 'contact_phone', 'contact_name'];
const MAINTAINER_PII_FIELDS = ['contact_email', 'contact_phone'];

function processFile(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(raw);
  let changed = false;
  const removals = [];

  // Strip location_confidence internal fields
  if (data.location_confidence && typeof data.location_confidence === 'object') {
    for (const field of LC_INTERNAL_FIELDS) {
      if (Object.prototype.hasOwnProperty.call(data.location_confidence, field)) {
        delete data.location_confidence[field];
        changed = true;
        removals.push(`location_confidence.${field}`);
      }
    }
  }

  // Strip personal data from local_contacts
  if (Array.isArray(data.local_contacts)) {
    for (let i = 0; i < data.local_contacts.length; i++) {
      const contact = data.local_contacts[i];
      for (const field of CONTACT_PII_FIELDS) {
        if (contact[field]) {
          delete contact[field];
          changed = true;
          removals.push(`local_contacts[${i}].${field}`);
        }
      }
    }
  }

  // Strip personal data from maintainer
  if (data.maintainer && typeof data.maintainer === 'object') {
    for (const field of MAINTAINER_PII_FIELDS) {
      if (data.maintainer[field]) {
        delete data.maintainer[field];
        changed = true;
        removals.push(`maintainer.${field}`);
      }
    }
  }

  if (changed) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  }

  return { changed, removals };
}

function main() {
  if (!fs.existsSync(MEMORIALS_DIR)) {
    console.error(`ERROR: memorials directory not found: ${MEMORIALS_DIR}`);
    process.exit(1);
  }

  const files = fs.readdirSync(MEMORIALS_DIR)
    .filter(f => f.endsWith('.json'))
    .sort();

  let processed = 0;
  let stripped = 0;

  for (const file of files) {
    const filePath = path.join(MEMORIALS_DIR, file);
    try {
      const result = processFile(filePath);
      processed++;
      if (result.changed) {
        stripped++;
        console.log(`  stripped: ${file} — ${result.removals.join(', ')}`);
      }
    } catch (err) {
      console.error(`  ERROR processing ${file}: ${err.message}`);
      process.exit(1);
    }
  }

  console.log(`\nstrip-internal-fields: ${processed} files processed, ${stripped} had fields stripped.`);
}

main();
