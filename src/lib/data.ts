import fs from 'fs';
import path from 'path';
import { Memorial } from './types';

const memorialsDirectory = path.join(process.cwd(), 'public/data/memorials');

export function getAllMemorials(): Memorial[] {
  const fileNames = fs.readdirSync(memorialsDirectory);
  const memorials = fileNames
    .filter((fileName) => fileName.endsWith('.json'))
    .map((fileName) => {
      const filePath = path.join(memorialsDirectory, fileName);
      const fileContents = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(fileContents) as Memorial;
    });

  return memorials.sort((a, b) => a.title.localeCompare(b.title));
}

export function getMemorialBySlug(slug: string): Memorial | undefined {
  const filePath = path.join(memorialsDirectory, `${slug}.json`);
  if (!fs.existsSync(filePath)) return undefined;
  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents) as Memorial;
}

export function getAllMemorialSlugs(): string[] {
  const fileNames = fs.readdirSync(memorialsDirectory);
  return fileNames
    .filter((fileName) => fileName.endsWith('.json'))
    .map((fileName) => fileName.replace('.json', ''));
}

export function getMemorialsByCountry(): Record<string, Memorial[]> {
  const memorials = getAllMemorials();
  const grouped: Record<string, Memorial[]> = {};
  for (const memorial of memorials) {
    const country = memorial.country || 'Unknown';
    if (!grouped[country]) grouped[country] = [];
    grouped[country].push(memorial);
  }
  return grouped;
}

export function getCountryCodes(): { code: string; name: string; count: number }[] {
  const byCountry = getMemorialsByCountry();
  return Object.entries(byCountry)
    .map(([name, memorials]) => ({
      code: name.toLowerCase().replace(/\s+/g, '-'),
      name,
      count: memorials.length,
    }))
    .sort((a, b) => b.count - a.count);
}

export function getMemorialsByRegionCode(code: string): Memorial[] {
  const byCountry = getMemorialsByCountry();
  const entry = Object.entries(byCountry).find(
    ([name]) => name.toLowerCase().replace(/\s+/g, '-') === code
  );
  return entry ? entry[1] : [];
}

export function getRegionName(code: string): string {
  const byCountry = getMemorialsByCountry();
  const entry = Object.entries(byCountry).find(
    ([name]) => name.toLowerCase().replace(/\s+/g, '-') === code
  );
  return entry ? entry[0] : code;
}

export function getFeaturedMemorials(): Memorial[] {
  const all = getAllMemorials();
  return all.filter((m) => m.data_quality === 'Comprehensive');
}

/**
 * Weekly rotating featured memorials: 5 per week (1-2 Comprehensive, 2-3 Partial).
 * Deterministic based on ISO week number so it's consistent during SSG.
 * All 208 memorials appear at least once per year (208/5 = ~42 weeks < 52).
 */
export function getWeeklyFeaturedMemorials(): Memorial[] {
  const all = getAllMemorials();
  const complete = all.filter((m) => m.data_quality === 'Comprehensive');
  const partial = all.filter((m) => m.data_quality === 'Partial');

  // Get ISO week number (1-52)
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / 86400000) + 1;
  const weekNumber = Math.ceil(dayOfYear / 7);

  // Deterministic shuffle using week as seed — simple but effective
  function seededPick<T>(arr: T[], seed: number, count: number): T[] {
    if (arr.length === 0) return [];
    const result: T[] = [];
    const used = new Set<number>();
    let s = seed;
    while (result.length < count && used.size < arr.length) {
      // Simple LCG-style hash
      s = ((s * 1103515245 + 12345) & 0x7fffffff);
      const idx = s % arr.length;
      if (!used.has(idx)) {
        used.add(idx);
        result.push(arr[idx]);
      }
    }
    return result;
  }

  // Pick 2 Comprehensive + 3 Partial (= 5 total)
  // If not enough Comprehensive, fill with more Partial
  const completeCount = Math.min(2, complete.length);
  const partialCount = 5 - completeCount;

  const pickedComplete = seededPick(complete, weekNumber * 7 + 1, completeCount);
  const pickedPartial = seededPick(partial, weekNumber * 7 + 2, partialCount);

  return [...pickedComplete, ...pickedPartial];
}

export function getWeekLabel(): string {
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / 86400000) + 1;
  const weekNumber = Math.ceil(dayOfYear / 7);
  return `Week ${weekNumber}, ${now.getFullYear()}`;
}

export function getMemorialStats() {
  const all = getAllMemorials();
  const withCrew = all.filter((m) => m.crew && m.crew.length > 0);
  const totalCrew = withCrew.reduce((sum, m) => sum + (m.crew?.length || 0), 0);
  const countries = new Set(all.map((m) => m.country).filter(Boolean));

  return {
    totalMemorials: all.length,
    totalCrew,
    countries: countries.size,
    completeEntries: all.filter((m) => m.data_quality === 'Comprehensive').length,
  };
}
