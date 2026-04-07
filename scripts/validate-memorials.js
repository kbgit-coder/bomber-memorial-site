#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');

const ajv = new Ajv({ allErrors: true });

const schemaPath = path.join(__dirname, 'memorial-schema.json');
const dataDir = path.join(__dirname, '..', 'public', 'data', 'memorials');

if (!fs.existsSync(schemaPath)) {
  console.error('ERROR: Schema not found at', schemaPath);
  process.exit(1);
}

if (!fs.existsSync(dataDir)) {
  console.error('ERROR: Memorial data directory not found at', dataDir);
  process.exit(1);
}

const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
const validate = ajv.compile(schema);

const files = fs.readdirSync(dataDir)
  .filter(f => f.endsWith('.json'))
  .sort();

let passed = 0;
let failed = 0;
const failures = [];

for (const filename of files) {
  const filepath = path.join(dataDir, filename);
  let data;

  try {
    data = JSON.parse(fs.readFileSync(filepath, 'utf8'));
  } catch (e) {
    failed++;
    failures.push({ file: filename, errors: [`JSON parse error: ${e.message}`] });
    continue;
  }

  const valid = validate(data);
  if (valid) {
    passed++;
  } else {
    failed++;
    const errors = validate.errors.map(err => {
      const field = err.instancePath || err.schemaPath;
      return `${field}: ${err.message}${err.params ? ' (' + JSON.stringify(err.params) + ')' : ''}`;
    });
    failures.push({ file: filename, errors });
  }
}

const total = passed + failed;

console.log('');
console.log('Bomber Memorial Schema Validation');
console.log('==================================');
console.log(`Total files:  ${total}`);
console.log(`Passed:       ${passed}`);
console.log(`Failed:       ${failed}`);
console.log('');

if (failures.length > 0) {
  console.log('FAILURES:');
  console.log('---------');
  for (const failure of failures) {
    console.log(`\n  ${failure.file}`);
    for (const err of failure.errors) {
      console.log(`    - ${err}`);
    }
  }
  console.log('');
  process.exit(1);
} else {
  console.log('All files passed validation.');
  console.log('');
  process.exit(0);
}
