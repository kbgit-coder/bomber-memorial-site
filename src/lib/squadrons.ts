import fs from 'fs';
import path from 'path';
import { getAllMemorials } from './data';
import { Memorial } from './types';

export type SquadronCategory = 'RAF Bomber Command' | 'USAAF Bomb Groups' | 'Training Units' | 'Other Units';

export interface SquadronHistory {
  formed?: string;
  disbanded?: string;
  group?: string;
  station?: string;
  nickname?: string;
  sub_units?: string[];
  total_sorties?: number;
  total_operations?: number;
  total_targets?: number;
  tons_dropped?: number;
  aircraft_lost?: number;
  killed?: number;
  pow?: number;
  commanding_officers?: { name: string; honours?: string; period?: string }[];
  aircraft_code?: string;
  summary?: string;
  notable_personnel?: { name: string; rank?: string; distinction: string; detail?: string }[];
  books?: { title: string; author: string; year?: string; isbn?: string; notes?: string }[];
  videos?: { url: string; title: string; source?: string }[];
  documents?: { title: string; url: string; description?: string }[];
  contact_email?: string;
  contact_name?: string;
  facebook_url?: string;
  committee?: { name: string; role: string }[];
  source_url?: string;
  source_name?: string;
}

export interface Squadron {
  slug: string;
  name: string;
  category: SquadronCategory;
  sort_number: number;
  badge_url?: string;
  motto?: string;
  stations: string[];
  association_url?: string;
  memorials: Memorial[];
  total_crew: number;
  aircraft_types: string[];
  history?: SquadronHistory;
}

// Known association URLs from Jack Sparrow heritage raid (7 Apr 2026)
const ASSOCIATION_URLS: Record<string, { url: string; name: string }> = {
  '578 Squadron': { url: 'https://578squadron.org.uk', name: '578 Squadron Association' },
  '100 Squadron': { url: 'https://100squadronassociation.org.uk', name: '100 Squadron Association' },
  '101 Squadron': { url: 'https://101squadronassociation.org.uk', name: '101 Squadron Association' },
  '103 Squadron': { url: 'https://elshamwolds.org.uk', name: 'Elsham Wolds Association' },
  '49 Squadron': { url: 'https://49squadron.co.uk', name: '49 Squadron Association' },
  '44 Squadron': { url: 'https://44sqn.com', name: '44 Squadron' },
  '44 (Rhodesia) Squadron': { url: 'https://44sqn.com', name: '44 Squadron' },
  '61 Squadron': { url: 'https://no-50-and-no-61-squadrons-association.co.uk', name: '50 & 61 Squadrons Association' },
  '50 Squadron': { url: 'https://no-50-and-no-61-squadrons-association.co.uk', name: '50 & 61 Squadrons Association' },
  '158 Squadron': { url: 'https://158squadron.co.uk', name: '158 Squadron' },
  '207 Squadron': { url: 'http://www.207squadron.rafinfo.org.uk', name: '207 Squadron' },
  '617 (Dambuster) Squadron': { url: 'https://617squadronassociation.org', name: '617 Squadron Association' },
  '12 Squadron': { url: 'https://wickenbymuseum.co.uk', name: 'Wickenby Museum' },
  '12 Sqdn.': { url: 'https://wickenbymuseum.co.uk', name: 'Wickenby Museum' },
  '156 Squadron': { url: 'https://156squadron.com', name: '156 Squadron' },
  '75 (NZ) Squadron': { url: 'https://75nzsquadron.wordpress.com', name: '75(NZ) Squadron' },
  '460 (RAAF) Squadron': { url: 'https://460squadronraaf.com', name: '460 Squadron RAAF' },
  '102 (Ceylon) Squadron': { url: 'https://102ceylonsquadronassociation.org', name: '102 Ceylon Squadron Association' },
  '582 PFF': { url: 'https://raf-pathfinders.com', name: 'RAF Pathfinders Archive' },
  '385th Bomb Group': { url: 'https://385thbga.com', name: '385th Bomb Group Association' },
  '385th Bombardment Group (Heavy), 8th USAAF': { url: 'https://385thbga.com', name: '385th Bomb Group Association' },
  '93rd Bomb Group': { url: 'https://93rd-bg-museum.org', name: '93rd Bomb Group Museum' },
  '389th Bomb Group': { url: 'https://389thbg.com', name: '389th Bomb Group' },
};

// Normalize messy squadron names to canonical display names
function normalizeSquadronName(raw: string): string {
  // Skip generic entries
  if (['Various', 'Unknown', 'RAF', 'USAAF', 'Bomber Command', 'RAF Bomber Command',
       'Bomber/Coastal Command', 'OTU', 'Bomber Command (test flight)',
       'General Bomber Command memorial'].includes(raw)) {
    return raw;
  }

  // Normalize "Sqdn." / "Sqdn" → "Squadron" (remove trailing period too)
  let name = raw.replace(/\bSqdn\.?\s*/g, 'Squadron ').replace(/Squadron\s*\./g, 'Squadron').trim();

  // Normalize "BG" → "Bomb Group" for USAAF (with correct ordinal)
  name = name.replace(/\b(\d+)(?:th|st|nd|rd)\s+BG\b/, (_, num) => {
    const n = parseInt(num);
    const suffix = (n % 10 === 1 && n !== 11) ? 'st' : (n % 10 === 2 && n !== 12) ? 'nd' : (n % 10 === 3 && n !== 13) ? 'rd' : 'th';
    return `${n}${suffix} Bomb Group`;
  });

  // Normalize HCU
  name = name.replace(/\b(\d+)\s+HCU\b/, '$1 Heavy Conversion Unit');

  // Normalize OTU
  name = name.replace(/\b(\d+)\s+OTU\b/, '$1 Operational Training Unit');

  // Normalize LFS
  name = name.replace(/\b(\d+)\s+LFS\b/, '$1 Lancaster Finishing School');

  return name;
}

function categorizeSquadron(name: string): { category: SquadronCategory; sort_number: number } {
  const numMatch = name.match(/^(\d+)/);
  const num = numMatch ? parseInt(numMatch[1]) : 9999;

  if (/Bomb Group|Bombardment/i.test(name) || /USAAF/i.test(name)) {
    return { category: 'USAAF Bomb Groups', sort_number: num };
  }
  if (/Operational Training Unit|Heavy Conversion Unit|Lancaster Finishing School|Bomber Command$|RAF Bomber Command/i.test(name)) {
    return { category: 'Training Units', sort_number: num };
  }
  if (/Squadron/i.test(name)) {
    return { category: 'RAF Bomber Command', sort_number: num };
  }
  return { category: 'Other Units', sort_number: num };
}

function squadronSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[().,]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export function getAllSquadrons(): Squadron[] {
  const memorials = getAllMemorials();
  const grouped: Record<string, Memorial[]> = {};

  // Generic entries that aren't real squadrons
  const SKIP = new Set(['Various', 'Unknown', 'Bomber Command', 'RAF Bomber Command',
    'Bomber/Coastal Command', 'OTU', 'Bomber Command (test flight)',
    'General Bomber Command memorial', 'RAF', 'USAAF', 'RAF Lindholme',
    'RAF Finningley', 'RAF Pershore', 'RAF Silverstone', 'RAF Longtown',
    'Based at Elvington', 'Various squadrons based at East Moor']);

  for (const m of memorials) {
    if (!m.squadron || SKIP.has(m.squadron)) continue;
    // Normalize before grouping — merges "97 Sqdn." and "97 Squadron"
    const canonical = normalizeSquadronName(m.squadron);
    if (!grouped[canonical]) grouped[canonical] = [];
    grouped[canonical].push(m);
  }

  return Object.entries(grouped)
    .filter(([, mems]) => mems.length >= 2)
    .map(([name, mems]) => {
      const stations = Array.from(new Set(mems.map(m => m.station).filter((s): s is string => !!s)));
      const aircraftTypes = Array.from(new Set(mems.map(m => m.aircraft_type).filter((s): s is string => !!s)));
      const totalCrew = mems.reduce((sum, m) => sum + (m.crew?.length || 0), 0);
      const assoc = ASSOCIATION_URLS[name];
      const { category, sort_number } = categorizeSquadron(name);

      // Load enriched data if available
      const slug = squadronSlug(name);
      const enrichedPath = path.join(process.cwd(), 'public/data/squadrons', `${slug}.json`);
      let history: SquadronHistory | undefined;
      if (fs.existsSync(enrichedPath)) {
        try {
          const enriched = JSON.parse(fs.readFileSync(enrichedPath, 'utf8'));
          history = enriched.history;
        } catch { /* ignore malformed files */ }
      }

      return {
        slug,
        name,
        category,
        sort_number,
        badge_url: mems[0].squadron_badge_url,
        motto: mems[0].squadron_motto,
        stations,
        association_url: assoc?.url,
        memorials: mems.sort((a, b) => a.title.localeCompare(b.title)),
        total_crew: totalCrew,
        aircraft_types: aircraftTypes,
        history,
      };
    })
    .sort((a, b) => {
      // Sort by category order, then numerically within category
      const catOrder: Record<SquadronCategory, number> = {
        'RAF Bomber Command': 1,
        'USAAF Bomb Groups': 2,
        'Training Units': 3,
        'Other Units': 4,
      };
      const catDiff = catOrder[a.category] - catOrder[b.category];
      if (catDiff !== 0) return catDiff;
      return a.sort_number - b.sort_number;
    });
}

export function getSquadronBySlug(slug: string): Squadron | undefined {
  return getAllSquadrons().find(s => s.slug === slug);
}

export function getSquadronSlugs(): string[] {
  return getAllSquadrons().map(s => s.slug);
}

export function getSquadronSlugForName(name: string): string | undefined {
  const all = getAllSquadrons();
  const normalized = normalizeSquadronName(name);
  const match = all.find(s => s.name === normalized);
  return match?.slug;
}
