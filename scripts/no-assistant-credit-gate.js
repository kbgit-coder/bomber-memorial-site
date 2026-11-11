#!/usr/bin/env node
// Prebuild gate: the Register is Keith's project. The AI assistant that helps build it
// is never credited in public data. Matches the assistant's own credit strings only,
// so a genuine contributor called Holly is unaffected.
const fs = require('fs');
const path = require('path');

const DIRS = ['public/data/memorials', 'international-memorials', 'ftr-memorials'];
const PATTERN = /\bLifeOS\b|\bPAI\b|Holly \((?:PAI|LifeOS)/;

const hits = [];
for (const dir of DIRS) {
  const abs = path.resolve(__dirname, '..', dir);
  if (!fs.existsSync(abs)) continue;
  for (const f of fs.readdirSync(abs).filter((n) => n.endsWith('.json'))) {
    const text = fs.readFileSync(path.join(abs, f), 'utf8');
    const m = text.match(PATTERN);
    if (m) hits.push(`${dir}/${f}: "${m[0]}"`);
  }
}

if (hits.length) {
  console.error(`✗ Assistant credit found in ${hits.length} record(s):\n  ${hits.join('\n  ')}`);
  process.exit(1);
}
console.log('✓ No assistant credits in public data');
