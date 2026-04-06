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
  const memorial = JSON.parse(fileContents) as Memorial;
  // Strip personal contact details — never expose email/phone publicly
  if (memorial.maintainer) {
    delete (memorial.maintainer as Record<string, unknown>).contact_email;
    delete (memorial.maintainer as Record<string, unknown>).contact_phone;
  }
  if (memorial.local_contacts) {
    memorial.local_contacts = memorial.local_contacts.map((c) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { contact_email, contact_phone, ...safe } = c;
      return safe as typeof c;
    });
  }
  return memorial;
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

/**
 * Weekly rotating featured memorials: 5 per week (1-2 Complete, 2-3 Partial).
 * Deterministic based on ISO week number so it's consistent during SSG.
 * All 208 memorials appear at least once per year (208/5 = ~42 weeks < 52).
 */
export function getWeeklyFeaturedMemorials(): Memorial[] {
  const all = getAllMemorials();
  const complete = all.filter((m) => m.data_quality === 'Complete');
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

  // Pick 2 Complete + 3 Partial (= 5 total)
  // If not enough Complete, fill with more Partial
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

/**
 * Haversine distance between two lat/lng points in km
 */
function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Returns up to `count` nearest memorials to the given coordinates,
 * excluding the memorial with the given id.
 * Calculated at build time — no client-side computation needed.
 */
export function getNearbyMemorials(
  id: string,
  lat: number,
  lng: number,
  count = 5
): (Memorial & { distance_km: number })[] {
  const all = getAllMemorials();
  return all
    .filter((m) => m.id !== id && m.latitude != null && m.longitude != null)
    .map((m) => ({
      ...m,
      distance_km: haversineKm(lat, lng, m.latitude!, m.longitude!),
    }))
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, count);
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
