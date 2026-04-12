#!/usr/bin/env node
/**
 * Deep content quality audit for every memorial page.
 *
 * Scores each memorial 0-100 across five dimensions:
 *   1. Content quality     — is text well-formed prose, not raw data dumps?
 *   2. Formatting          — proper paragraphs, no ALL CAPS walls, no slash-delimited inscriptions?
 *   3. Relevancy           — does each section contain section-appropriate content?
 *   4. Repetition          — is the same info repeated across sections?
 *   5. Completeness        — how many sections have meaningful content?
 *
 * Outputs: JSON report + summary to stdout.
 * Usage: node scripts/audit-content-quality.js [--verbose] [--json report.json] [--slug memorial-slug]
 */

const fs = require('fs');
const path = require('path');

const MEMORIALS_DIR = path.resolve(__dirname, '../public/data/memorials');
const VERBOSE = process.argv.includes('--verbose');
const SINGLE_SLUG = (() => {
  const idx = process.argv.indexOf('--slug');
  return idx >= 0 ? process.argv[idx + 1] : null;
})();
const JSON_OUT = (() => {
  const idx = process.argv.indexOf('--json');
  return idx >= 0 ? process.argv[idx + 1] : null;
})();

// ---- Detectors ----

function isAllCapsWall(text) {
  if (!text || text.length < 50) return false;
  const upper = text.replace(/[^A-Za-z]/g, '');
  const upperCount = (upper.match(/[A-Z]/g) || []).length;
  return upperCount / upper.length > 0.7;
}

function isSlashDelimited(text) {
  if (!text) return false;
  const slashes = (text.match(/\//g) || []).length;
  const lines = text.split('\n').length;
  return slashes > 5 && slashes > lines;
}

function isPlainInscription(text) {
  if (!text) return false;
  return isAllCapsWall(text) || isSlashDelimited(text);
}

function containsThanksBoilerplate(text) {
  if (!text) return false;
  const t = text.toLowerCase();
  return (
    (t.includes('wishes to place on record') && t.includes('appreciation')) ||
    (t.includes('cooperation') && t.includes('financial assistance')) ||
    (t.includes('thanks') && t.includes('providing this site')) ||
    (t.includes('grateful thanks') && t.includes('erect')) ||
    (t.includes('appreciation') && t.includes('contributed'))
  );
}

function containsCommunityContent(text) {
  if (!text) return false;
  const t = text.toLowerCase();
  return (
    t.includes('unveiled') || t.includes('dedication') || t.includes('ceremony') ||
    t.includes('community') || t.includes('local') || t.includes('parish') ||
    t.includes('association') || t.includes('funded') || t.includes('erected by') ||
    t.includes('thanks') || t.includes('cooperation') || t.includes('donated')
  );
}

function hasExcessiveRepetition(narrative, crew, squadron, crashDate) {
  if (!narrative) return 0;
  let score = 0;
  const t = narrative.toLowerCase();

  // Check if crew names from crew array appear in narrative
  if (crew && crew.length > 0) {
    let crewMentions = 0;
    for (const c of crew) {
      if (c.name) {
        const surname = c.name.split(' ').pop().toLowerCase();
        if (surname && surname.length > 3 && t.includes(surname)) crewMentions++;
      }
    }
    // If >50% of crew are mentioned by name, that's repetitive
    if (crew.length > 2 && crewMentions / crew.length > 0.5) score += 20;
  }

  // Check if squadron is mentioned (already displayed)
  if (squadron && t.includes(squadron.toLowerCase())) score += 5;

  return Math.min(score, 30);
}

function isFormattedProse(text) {
  if (!text || text.length < 30) return 0;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 10);
  const paragraphs = text.split(/\n\n+/).filter(p => p.trim().length > 20);
  // Good prose: multiple sentences, some paragraphs, mixed case
  const sentenceScore = Math.min(sentences.length * 10, 40);
  const paraScore = Math.min(paragraphs.length * 15, 30);
  const caseScore = isAllCapsWall(text) ? 0 : 30;
  return Math.min(sentenceScore + paraScore + caseScore, 100);
}

function detectServiceNumberDump(text) {
  if (!text) return false;
  // Lines with service numbers like "1622745 RAFVR" or "Aus/415220"
  const serviceLines = (text.match(/\d{5,}\s+(?:RAFVR?|RAAF|RCAF|RNZAF)/g) || []).length;
  return serviceLines >= 3;
}

function hasHTMLEntities(text) {
  if (!text) return false;
  return /&(?:bull|amp|lt|gt|nbsp|ndash|mdash|hellip|quot);/.test(text);
}

// ---- Audit a single memorial ----

function auditMemorial(memorial, slug) {
  const issues = [];
  const scores = {
    content: 100,
    formatting: 100,
    relevancy: 100,
    repetition: 100,
    completeness: 0,
  };

  const narrative = memorial.narrative || '';
  const crew = memorial.crew || [];
  const community = memorial.community_connection || '';
  const narratives = memorial.external_narratives || [];
  const fullNarratives = narratives.filter(n => n.full_narrative);

  // ---- 1. Content Quality ----

  // Narrative is a raw inscription
  if (narrative && isPlainInscription(narrative)) {
    scores.content -= 30;
    issues.push({ field: 'narrative', issue: 'raw-inscription', severity: 'high',
      detail: 'What Happened section contains raw plaque inscription text (ALL CAPS / slash-delimited)' });
  }

  // Narrative contains service number dumps
  if (narrative && detectServiceNumberDump(narrative)) {
    scores.content -= 20;
    issues.push({ field: 'narrative', issue: 'service-number-dump', severity: 'medium',
      detail: 'What Happened section contains crew data with service numbers (belongs in crew table)' });
  }

  // Full narratives with service number dumps
  for (const n of fullNarratives) {
    if (detectServiceNumberDump(n.full_narrative)) {
      scores.content -= 10;
      issues.push({ field: 'full_narrative', issue: 'service-number-dump', severity: 'medium',
        source: n.source_site,
        detail: 'Detailed Record contains crew data with service numbers (duplicate of crew table)' });
    }
  }

  // HTML entities in any text
  for (const [field, text] of [['narrative', narrative], ['community_connection', community]]) {
    if (hasHTMLEntities(text)) {
      scores.content -= 10;
      issues.push({ field, issue: 'html-entities', severity: 'low',
        detail: 'Text contains unrendered HTML entities (&bull; etc.)' });
    }
  }

  // ---- 2. Formatting ----

  // ALL CAPS wall
  if (narrative && isAllCapsWall(narrative)) {
    scores.formatting -= 35;
    issues.push({ field: 'narrative', issue: 'all-caps-wall', severity: 'high',
      detail: 'What Happened text is >70% uppercase — reads as shouting' });
  }

  // Slash-delimited inscription format
  if (narrative && isSlashDelimited(narrative)) {
    scores.formatting -= 25;
    issues.push({ field: 'narrative', issue: 'slash-delimited', severity: 'high',
      detail: 'Text uses / as line separators (raw inscription format)' });
  }

  // Poor prose quality in narrative
  if (narrative) {
    const proseScore = isFormattedProse(narrative);
    if (proseScore < 40) {
      scores.formatting -= (40 - proseScore);
      issues.push({ field: 'narrative', issue: 'poor-prose', severity: 'medium',
        detail: `Prose quality score ${proseScore}/100 — may lack sentences or paragraph structure` });
    }
  }

  // ---- 3. Relevancy ----

  // Thanks/appreciation content in What Happened (belongs in Community Connection)
  if (narrative && containsThanksBoilerplate(narrative)) {
    scores.relevancy -= 25;
    issues.push({ field: 'narrative', issue: 'thanks-in-narrative', severity: 'high',
      detail: 'What Happened contains thank-you/appreciation text — belongs in Community Connection' });
  }

  // Community content misplaced in narrative
  if (narrative && !community && containsCommunityContent(narrative)) {
    scores.relevancy -= 10;
    issues.push({ field: 'narrative', issue: 'community-in-narrative', severity: 'low',
      detail: 'What Happened contains community/dedication content that could populate Community Connection' });
  }

  // Crew list in narrative (already in crew table)
  if (narrative && crew.length > 0) {
    const rep = hasExcessiveRepetition(narrative, crew, memorial.squadron, memorial.crash_date);
    if (rep > 15) {
      scores.relevancy -= rep;
      issues.push({ field: 'narrative', issue: 'crew-in-narrative', severity: 'medium',
        detail: 'What Happened repeats crew names already in the Crew table' });
    }
  }

  // ---- 4. Repetition ----

  // Same info in narrative and full_narrative
  if (narrative && fullNarratives.length > 0) {
    for (const n of fullNarratives) {
      // Check for significant text overlap (>30% of shorter text appears in longer)
      const shorter = narrative.length < n.full_narrative.length ? narrative : n.full_narrative;
      const longer = narrative.length < n.full_narrative.length ? n.full_narrative : narrative;
      const words = shorter.toLowerCase().split(/\s+/).filter(w => w.length > 5);
      const overlap = words.filter(w => longer.toLowerCase().includes(w)).length;
      if (words.length > 5 && overlap / words.length > 0.4) {
        scores.repetition -= 25;
        issues.push({ field: 'narrative+full_narrative', issue: 'text-overlap', severity: 'medium',
          source: n.source_site,
          detail: `${Math.round(overlap / words.length * 100)}% word overlap between What Happened and Detailed Record` });
        break;
      }
    }
  }

  // Narrative repeats structured data
  const rep = hasExcessiveRepetition(narrative, crew, memorial.squadron, memorial.crash_date);
  if (rep > 0) scores.repetition -= rep;

  // ---- 5. Completeness ----

  let filled = 0;
  const total = 7;
  if (narrative && narrative.length > 30) filled++;
  if (crew.length > 0) filled++;
  if (community && community.length > 20) filled++;
  if (memorial.remembrance && (memorial.remembrance.annual_service || (memorial.remembrance.events && memorial.remembrance.events.length > 0))) filled++;
  if (memorial.photos && memorial.photos.length > 0) filled++;
  if (narratives.length > 0) filled++;
  if (memorial.latitude != null) filled++;
  scores.completeness = Math.round(filled / total * 100);

  // Clamp scores
  for (const key of ['content', 'formatting', 'relevancy', 'repetition']) {
    scores[key] = Math.max(0, Math.min(100, scores[key]));
  }

  // Overall weighted score
  const overall = Math.round(
    scores.content * 0.25 +
    scores.formatting * 0.20 +
    scores.relevancy * 0.25 +
    scores.repetition * 0.15 +
    scores.completeness * 0.15
  );

  return {
    slug,
    title: memorial.title,
    overall,
    scores,
    issues,
    dataQuality: memorial.data_quality || 'Unknown',
  };
}

// ---- Main ----

function main() {
  const files = fs.readdirSync(MEMORIALS_DIR).filter(f => f.endsWith('.json'));
  const results = [];

  for (const file of files) {
    const slug = file.replace('.json', '');
    if (SINGLE_SLUG && slug !== SINGLE_SLUG) continue;

    const memorial = JSON.parse(fs.readFileSync(path.join(MEMORIALS_DIR, file), 'utf-8'));
    const result = auditMemorial(memorial, slug);
    results.push(result);
  }

  // Sort by score (worst first)
  results.sort((a, b) => a.overall - b.overall);

  // Summary
  const avgScore = Math.round(results.reduce((s, r) => s + r.overall, 0) / results.length);
  const issueCount = results.reduce((s, r) => s + r.issues.length, 0);
  const buckets = { excellent: 0, good: 0, fair: 0, poor: 0 };
  for (const r of results) {
    if (r.overall >= 80) buckets.excellent++;
    else if (r.overall >= 60) buckets.good++;
    else if (r.overall >= 40) buckets.fair++;
    else buckets.poor++;
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`CONTENT QUALITY AUDIT — ${results.length} memorials`);
  console.log(`${'='.repeat(60)}`);
  console.log(`  Average score: ${avgScore}/100`);
  console.log(`  Total issues:  ${issueCount}`);
  console.log(`  Excellent (80+): ${buckets.excellent}`);
  console.log(`  Good (60-79):    ${buckets.good}`);
  console.log(`  Fair (40-59):    ${buckets.fair}`);
  console.log(`  Poor (<40):      ${buckets.poor}`);

  // Issue frequency
  const issueCounts = {};
  for (const r of results) {
    for (const i of r.issues) {
      issueCounts[i.issue] = (issueCounts[i.issue] || 0) + 1;
    }
  }
  console.log(`\n  Issue frequency:`);
  for (const [issue, count] of Object.entries(issueCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`    ${issue.padEnd(30)} ${count}`);
  }

  // Worst 20
  console.log(`\n  Bottom 20 memorials:`);
  for (const r of results.slice(0, 20)) {
    const issueLabels = r.issues.map(i => i.issue).join(', ');
    console.log(`    ${r.overall.toString().padStart(3)}/100  ${r.slug.substring(0, 50).padEnd(52)} ${issueLabels}`);
  }

  if (VERBOSE || SINGLE_SLUG) {
    console.log(`\n  Detailed issues:`);
    for (const r of results.filter(r => r.issues.length > 0).slice(0, SINGLE_SLUG ? 100 : 30)) {
      console.log(`\n  ${r.slug} (${r.overall}/100):`);
      console.log(`    Content: ${r.scores.content}  Format: ${r.scores.formatting}  Relevancy: ${r.scores.relevancy}  Repetition: ${r.scores.repetition}  Complete: ${r.scores.completeness}`);
      for (const i of r.issues) {
        console.log(`    [${i.severity}] ${i.issue}: ${i.detail}`);
      }
    }
  }

  if (JSON_OUT) {
    fs.writeFileSync(JSON_OUT, JSON.stringify({ summary: { avgScore, issueCount, buckets }, results }, null, 2));
    console.log(`\n  Full report: ${JSON_OUT}`);
  }
}

main();
