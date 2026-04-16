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

// Stub regions: countries with genuine Bomber Command memorials that are
// squadron/general memorials (out of crash-site scope for v3.3.0).
// These stub pages are generated even when no active memorial data exists,
// so visitors reaching these URLs get a proper page not a 404.
const STUB_REGION_CODES: { code: string; name: string }[] = [
  { code: 'canada', name: 'Canada' },
  { code: 'france', name: 'France' },
  { code: 'new-zealand', name: 'New Zealand' },
  { code: 'belgium', name: 'Belgium' },
];

export function getCountryCodes(): { code: string; name: string; count: number }[] {
  const byCountry = getMemorialsByCountry();
  const activeCodes = Object.entries(byCountry)
    .map(([name, memorials]) => ({
      code: name.toLowerCase().replace(/\s+/g, '-'),
      name,
      count: memorials.length,
    }));

  // Merge stub regions — add any that aren't already present from active data
  const existingCodes = new Set(activeCodes.map((c) => c.code));
  for (const stub of STUB_REGION_CODES) {
    if (!existingCodes.has(stub.code)) {
      activeCodes.push({ code: stub.code, name: stub.name, count: 0 });
    }
  }

  return activeCodes.sort((a, b) => b.count - a.count);
}

export function getMemorialsByRegionCode(code: string): Memorial[] {
  const byCountry = getMemorialsByCountry();
  const entry = Object.entries(byCountry).find(
    ([name]) => name.toLowerCase().replace(/\s+/g, '-') === code
  );
  return entry ? entry[1] : [];
}

export function getRegionName(code: string): string {
  // Check active data first
  const byCountry = getMemorialsByCountry();
  const entry = Object.entries(byCountry).find(
    ([name]) => name.toLowerCase().replace(/\s+/g, '-') === code
  );
  if (entry) return entry[0];

  // Fall back to stub region names
  const stub = STUB_REGION_CODES.find((s) => s.code === code);
  if (stub) return stub.name;

  return code;
}

export function getFeaturedMemorials(): Memorial[] {
  const all = getAllMemorials();
  return all.filter((m) => m.data_quality === 'Comprehensive');
}

/**
 * Weekly rotating featured memorials: 5 per week (1-2 Complete, 2-3 Partial).
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
 * Haversine distance in kilometres between two lat/lng points.
 */
function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function getNearbyMemorials(
  lat: number,
  lng: number,
  excludeSlug: string,
  limit = 5,
  maxDistanceKm = 50
): Array<Memorial & { distanceMiles: number }> {
  const all = getAllMemorials();
  return all
    .filter(
      (m) =>
        m.id !== excludeSlug &&
        m.latitude != null &&
        m.longitude != null
    )
    .map((m) => ({
      ...m,
      distanceMiles: haversineKm(lat, lng, m.latitude!, m.longitude!) * 0.621371,
    }))
    .filter((m) => m.distanceMiles <= maxDistanceKm * 0.621371)
    .sort((a, b) => a.distanceMiles - b.distanceMiles)
    .slice(0, limit);
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

// Cross-linked memorials: same incident, separate memorial pages
const CROSS_LINKS: Record<string, { slug: string; reason: string }[]> = {
  'cloot-drove-nd981-and-lancaster-me625-mid-air-collision-': [
    { slug: 'crowland-mid-air-collision-me265-lancaster-nd981', reason: 'Same mid-air collision, 23 June 1944 — two Lancasters collided over the Fens' },
  ],
  'crowland-mid-air-collision-me265-lancaster-nd981': [
    { slug: 'cloot-drove-nd981-and-lancaster-me625-mid-air-collision-', reason: 'Same mid-air collision, 23 June 1944 — two Lancasters collided over the Fens' },
  ],
  'bleasby-3-lancaster-r-5698': [
    { slug: 'bleasby-4-jb132', reason: 'Mid-air collision at Bleasby, 1 September 1943' },
  ],
  'bleasby-4-jb132': [
    { slug: 'bleasby-3-lancaster-r-5698', reason: 'Mid-air collision at Bleasby, 1 September 1943' },
  ],
  'brocklesby-me442': [
    { slug: 'east-stockwith-me323', reason: 'Same night, 4 March 1945 — Lincolnshire' },
    { slug: 'ulceby-cross-pb476', reason: 'Same night, 4 March 1945 — Lincolnshire' },
  ],
  'east-stockwith-me323': [
    { slug: 'brocklesby-me442', reason: 'Same night, 4 March 1945 — Lincolnshire' },
    { slug: 'ulceby-cross-pb476', reason: 'Same night, 4 March 1945 — Lincolnshire' },
  ],
  'ulceby-cross-pb476': [
    { slug: 'brocklesby-me442', reason: 'Same night, 4 March 1945 — Lincolnshire' },
    { slug: 'east-stockwith-me323', reason: 'Same night, 4 March 1945 — Lincolnshire' },
  ],
  'hatcliffe-top-jb596': [
    { slug: 'waithe-lancaster-mid-air-collision', reason: 'Same night, 17 December 1943 — returning from Berlin' },
  ],
  'waithe-lancaster-mid-air-collision': [
    { slug: 'hatcliffe-top-jb596', reason: 'Same night, 17 December 1943 — returning from Berlin' },
  ],
};

export function getRelatedMemorials(slug: string) {
  const links = CROSS_LINKS[slug] || [];
  return links.map(link => {
    const memorial = getMemorialBySlug(link.slug);
    return memorial ? { ...link, title: memorial.title, aircraft_type: memorial.aircraft_type } : null;
  }).filter(Boolean) as { slug: string; reason: string; title: string; aircraft_type?: string }[];
}

export function getQualityDashboardData() {
  // Dynamic import to avoid circular dependency
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { scoreMemorial } = require('./quality');
  const all = getAllMemorials();
  return all.map((m: Memorial) => scoreMemorial(m));
}

export function getInsightsData() {
  const all = getAllMemorials();

  // Crashes by year
  const yearCounts: Record<string, number> = {};
  for (const m of all) {
    if (m.crash_date) {
      const y = m.crash_date.slice(0, 4);
      if (/^\d{4}$/.test(y)) yearCounts[y] = (yearCounts[y] || 0) + 1;
    }
  }
  const crashesByYear = Object.entries(yearCounts)
    .map(([year, count]) => ({ year, count }))
    .sort((a, b) => a.year.localeCompare(b.year));

  // Crash categories
  const catCounts: Record<string, number> = {};
  for (const m of all) {
    const cat = m.crash_category || 'unknown';
    catCounts[cat] = (catCounts[cat] || 0) + 1;
  }
  const crashCategories = Object.entries(catCounts)
    .map(([category, count]) => ({
      category: category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      count,
    }))
    .sort((a, b) => b.count - a.count);

  // Aircraft types (normalise common variants)
  const aircraftMap: Record<string, string> = {
    'Avro Lancaster': 'Lancaster', 'Lancaster III': 'Lancaster', 'Lancaster I': 'Lancaster',
    'Short Stirling': 'Stirling', 'Stirling III': 'Stirling',
    'Wellington Mk.IC': 'Wellington', 'Wellington Mk.X': 'Wellington', 'Wellington Ic': 'Wellington',
    'Wellington II': 'Wellington', 'Wellington III': 'Wellington',
    'Halifax III': 'Halifax', 'Halifax II': 'Halifax',
  };
  const acCounts: Record<string, number> = {};
  for (const m of all) {
    if (m.aircraft_type) {
      const norm = aircraftMap[m.aircraft_type] || m.aircraft_type;
      acCounts[norm] = (acCounts[norm] || 0) + 1;
    }
  }
  const aircraftTypes = Object.entries(acCounts)
    .map(([aircraft, count]) => ({ aircraft, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Crew stats
  const ages: number[] = [];
  const natCounts: Record<string, number> = {};
  let totalCrew = 0;
  let killedCount = 0;
  let survivedCount = 0;
  for (const m of all) {
    for (const c of m.crew || []) {
      totalCrew++;
      if (c.age) {
        const a = parseInt(String(c.age), 10);
        if (!isNaN(a) && a >= 15 && a <= 60) ages.push(a);
      }
      if (c.nationality) {
        natCounts[c.nationality] = (natCounts[c.nationality] || 0) + 1;
      }
      const fate = (c.fate || '').toLowerCase();
      if (fate.includes('survived') || fate.includes('pow') || fate.includes('evaded')) {
        survivedCount++;
      } else if (fate.includes('killed') || fate.includes('died') || fate.includes('lost')) {
        killedCount++;
      }
    }
  }

  const nationalities = Object.entries(natCounts)
    .map(([nationality, count]) => ({ nationality, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Age distribution (bucketed)
  const ageBuckets: Record<string, number> = {};
  for (const a of ages) {
    const bucket = a < 20 ? '18-19' : a < 22 ? '20-21' : a < 24 ? '22-23' : a < 26 ? '24-25' : a < 28 ? '26-27' : a < 30 ? '28-29' : '30+';
    ageBuckets[bucket] = (ageBuckets[bucket] || 0) + 1;
  }
  const ageDistribution = ['18-19', '20-21', '22-23', '24-25', '26-27', '28-29', '30+']
    .map(range => ({ range, count: ageBuckets[range] || 0 }));

  const meanAge = ages.length > 0 ? Math.round((ages.reduce((s, a) => s + a, 0) / ages.length) * 10) / 10 : 0;

  // Data quality
  const qualCounts: Record<string, number> = {};
  for (const m of all) {
    const q = m.data_quality || 'Unknown';
    qualCounts[q] = (qualCounts[q] || 0) + 1;
  }
  const qualityOrder = ['Complete', 'Partial', 'Stub', 'Unknown'];
  const dataQuality = Object.entries(qualCounts)
    .map(([quality, count]) => ({ quality, count }))
    .sort((a, b) => qualityOrder.indexOf(a.quality) - qualityOrder.indexOf(b.quality));

  return {
    totalMemorials: all.length,
    totalCrew,
    meanAge,
    killedCount,
    survivedCount,
    crewWithAge: ages.length,
    crashesByYear,
    crashCategories,
    aircraftTypes,
    nationalities,
    ageDistribution,
    dataQuality,
  };
}
