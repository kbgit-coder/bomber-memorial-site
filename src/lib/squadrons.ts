import { getAllMemorials } from './data';
import { Memorial } from './types';

export interface Squadron {
  slug: string;
  name: string;
  badge_url?: string;
  motto?: string;
  stations: string[];
  association_url?: string;
  memorials: Memorial[];
  total_crew: number;
  aircraft_types: string[];
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

  for (const m of memorials) {
    if (!m.squadron || m.squadron === 'Various' || m.squadron === 'Unknown') continue;
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

      return {
        slug: squadronSlug(name),
        name,
        badge_url: mems[0].squadron_badge_url,
        motto: mems[0].squadron_motto,
        stations,
        association_url: assoc?.url,
        memorials: mems.sort((a, b) => a.title.localeCompare(b.title)),
        total_crew: totalCrew,
        aircraft_types: aircraftTypes,
      };
    })
    .sort((a, b) => b.memorials.length - a.memorials.length);
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
