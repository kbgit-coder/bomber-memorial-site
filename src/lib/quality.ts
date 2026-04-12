import { Memorial } from './types';

export interface SectionScore {
  section: string;
  score: number;  // 0-100
  issues: string[];
}

export interface MemorialQuality {
  slug: string;
  title: string;
  overallScore: number;  // 0-100
  dataQuality: string;
  sections: SectionScore[];
  capsRatio: number;
  bracketCount: number;
  slashCount: number;
  hasInscription: boolean;
  hasNarrative: boolean;
  hasCrew: boolean;
  hasCoordinates: boolean;
  hasPhotos: boolean;
  crewCount: number;
  crewWithRank: number;
  crewWithAge: number;
  crewWithNationality: number;
  lastUpdated: string;
}

function scoreSection(name: string, content: string): SectionScore {
  const issues: string[] = [];
  let score = 100;

  if (!content || content.trim().length === 0) {
    return { section: name, score: 0, issues: ['Section empty'] };
  }

  const len = content.length;

  // Caps ratio (per section)
  const letters = content.replace(/[^a-zA-Z]/g, '');
  if (letters.length > 20) {
    const capsRatio = (letters.replace(/[a-z]/g, '').length) / letters.length;
    if (capsRatio > 0.7) {
      score -= 20;
      issues.push(`${Math.round(capsRatio * 100)}% uppercase`);
    }
  }

  // Brackets and placeholders
  const brackets = (content.match(/[\[\](){}]/g) || []).length;
  if (brackets > 6) {
    score -= 10;
    issues.push(`${brackets} brackets/parens`);
  }

  // Raw placeholders
  if (/\(NAMES?\)/i.test(content)) { score -= 25; issues.push('Raw (NAMES) placeholder'); }
  if (/undefined|null/i.test(content) && !/\bnull and\b/i.test(content)) {
    score -= 15; issues.push('undefined/null text');
  }

  // AI refusal text
  if (/does not explicitly|as an ai|the text does not/i.test(content)) {
    score -= 30; issues.push('AI refusal text');
  }

  // Very short content
  if (len < 20) { score -= 10; issues.push('Very short'); }

  // Article dump markers
  if (/---\n|ARTICLE DUMP:|SOURCE URL:/i.test(content)) {
    score -= 20; issues.push('Article dump markers');
  }

  return { section: name, score: Math.max(0, score), issues };
}

export function scoreMemorial(m: Memorial): MemorialQuality {
  const slug = m.id;
  const sections: SectionScore[] = [];

  // Score each section
  sections.push(scoreSection('Narrative', m.narrative || ''));
  sections.push(scoreSection('Inscription', m.inscription || ''));
  sections.push(scoreSection('Community Connection', m.community_connection || ''));
  sections.push(scoreSection('Memorial Details', m.memorial_details || ''));

  // Crew section scoring
  const crew = m.crew || [];
  let crewScore = 0;
  const crewIssues: string[] = [];
  if (crew.length > 0) {
    crewScore = 50; // Base for having crew
    const withRank = crew.filter(c => c.rank && c.rank !== 'Unknown' && c.rank !== '—').length;
    const withAge = crew.filter(c => c.age).length;
    const withNat = crew.filter(c => c.nationality).length;
    const withRole = crew.filter(c => c.role && c.role !== 'unknown').length;
    crewScore += (withRank / crew.length) * 15;
    crewScore += (withAge / crew.length) * 10;
    crewScore += (withNat / crew.length) * 10;
    crewScore += (withRole / crew.length) * 15;
    // Check for duplicates
    const names = crew.map(c => (c.name || '').toLowerCase());
    const dupes = names.filter((n, i) => n && names.indexOf(n) !== i);
    if (dupes.length > 0) { crewScore -= 20; crewIssues.push(`${dupes.length} duplicate names`); }
    // Check for junk
    for (const c of crew) {
      if (/regiment|infantry|fusilier|society|school/i.test(c.name || '')) {
        crewScore -= 15;
        crewIssues.push(`Non-person: ${c.name}`);
        break;
      }
    }
  }
  sections.push({ section: 'Crew', score: Math.max(0, Math.min(100, Math.round(crewScore))), issues: crewIssues });

  // Overall all-text analysis
  const allText = [m.narrative, m.inscription, m.community_connection, m.memorial_details].filter(Boolean).join(' ');
  const allLetters = allText.replace(/[^a-zA-Z]/g, '');
  const capsRatio = allLetters.length > 0 ? allLetters.replace(/[a-z]/g, '').length / allLetters.length : 0;
  const bracketCount = (allText.match(/[\[\](){}]/g) || []).length;
  const slashCount = (allText.match(/\//g) || []).length;

  // Overall score: weighted average of sections + completeness bonus
  const sectionAvg = sections.length > 0
    ? sections.reduce((s, sec) => s + sec.score, 0) / sections.length
    : 0;

  let completeness = 0;
  if (m.narrative) completeness += 20;
  if (m.inscription) completeness += 10;
  if (m.crew && m.crew.length > 0) completeness += 20;
  if (m.latitude != null) completeness += 10;
  if (m.crash_date) completeness += 10;
  if (m.aircraft_type) completeness += 10;
  if (m.squadron) completeness += 5;
  if (m.county) completeness += 5;
  if (m.community_connection) completeness += 5;
  if (m.photos && m.photos.length > 0) completeness += 5;

  const overallScore = Math.round(sectionAvg * 0.6 + completeness * 0.4);

  return {
    slug,
    title: m.title,
    overallScore,
    dataQuality: m.data_quality || 'Unknown',
    sections,
    capsRatio: Math.round(capsRatio * 100),
    bracketCount,
    slashCount,
    hasInscription: !!m.inscription,
    hasNarrative: !!m.narrative,
    hasCrew: !!(m.crew && m.crew.length > 0),
    hasCoordinates: m.latitude != null,
    hasPhotos: !!(m.photos && m.photos.length > 0),
    crewCount: crew.length,
    crewWithRank: crew.filter(c => c.rank && c.rank !== 'Unknown' && c.rank !== '—').length,
    crewWithAge: crew.filter(c => c.age).length,
    crewWithNationality: crew.filter(c => c.nationality).length,
    lastUpdated: m.last_updated || '',
  };
}
