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
  return all.filter((m) => m.data_quality === 'Complete');
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
    completeEntries: all.filter((m) => m.data_quality === 'Complete').length,
  };
}
