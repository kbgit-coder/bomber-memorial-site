#!/usr/bin/env bun
/**
 * mp-constituency-map.ts
 *
 * Produces a memorial → constituency → current MP lookup table for every UK
 * memorial record with coordinates.
 *
 * Output: mp-outreach/constituency-map.json
 *
 * Usage: bun scripts/mp-constituency-map.ts
 */

import { readdirSync, readFileSync, mkdirSync, writeFileSync } from "fs";
import { join, basename } from "path";

const REPO = join(import.meta.dir, "..");
const DATA_DIRS = [
  "public/data/memorials",
  "international-memorials",
  "ftr-memorials",
];
const OUTPUT_DIR = join(REPO, "mp-outreach");
const OUTPUT_FILE = join(OUTPUT_DIR, "constituency-map.json");

const UK_COUNTRIES = new Set([
  "United Kingdom",
  "UK",
  "England",
  "Scotland",
  "Wales",
  "Northern Ireland",
]);

// ─── Constituency name normalisation ─────────────────────────────────────────
// postcodes.io returns ASCII-stripped names for Welsh constituencies;
// Parliament API uses proper Welsh unicode characters. This map bridges known
// mismatches found in practice.
const CONSTITUENCY_NAME_FIXES: Record<string, string> = {
  "Montgomeryshire and Glyndwr": "Montgomeryshire and Glyndŵr",
  "Caerphilly": "Caerffili",
  // Add further mappings here if new mismatches are discovered
};

function normaliseConstituencyName(name: string): string {
  return CONSTITUENCY_NAME_FIXES[name] ?? name;
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface Memorial {
  id: string;
  title: string;
  county?: string;
  country?: string;
  latitude?: number | string | null;
  longitude?: number | string | null;
}

interface MemorialWithCoords extends Memorial {
  latitude: number;
  longitude: number;
}

interface PostcodesGeolocResult {
  parliamentary_constituency_2024?: string | null;
  parliamentary_constituency?: string | null;
}

interface PostcodesBulkResponseItem {
  query: { longitude: number; latitude: number };
  result: PostcodesGeolocResult[] | null;
}

interface ParliamentConstituency {
  id: number;
  name: string;
  currentRepresentation?: {
    member?: {
      value?: {
        id: number;
        nameDisplayAs: string;
        latestParty?: { name: string; abbreviation: string };
      };
    };
  };
}

interface MPInfo {
  mp_name: string;
  mp_party: string;
  mp_member_id: number;
  mp_parliamentary_email: string | null;
}

interface OutputRow {
  memorial_id: string;
  title: string;
  county: string | null;
  latitude: number;
  longitude: number;
  constituency: string | null;
  mp_name: string | null;
  mp_party: string | null;
  mp_member_id: number | null;
  mp_parliamentary_email: string | null;
}

interface Summary {
  total_uk_with_coords: number;
  mapped: number;
  unmapped: string[];
  distinct_constituency_count: number;
  ambiguous: string[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 3,
  delayMs = 1000
): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const res = await fetch(url, options);
    if (res.status === 429) {
      console.warn(`  [429] Rate limited on ${url.substring(0, 80)}... waiting 30s`);
      await sleep(30000);
      continue;
    }
    return res;
  }
  throw new Error(`Failed after ${retries} retries: ${url}`);
}

// ─── Step 1: Load memorial records ───────────────────────────────────────────

function loadUKMemorialsWithCoords(): MemorialWithCoords[] {
  const results: MemorialWithCoords[] = [];

  for (const dir of DATA_DIRS) {
    const dirPath = join(REPO, dir);
    let files: string[];
    try {
      files = readdirSync(dirPath);
    } catch {
      console.warn(`  [warn] Could not read dir: ${dirPath}`);
      continue;
    }

    for (const file of files) {
      if (!file.endsWith(".json")) continue;
      if (basename(file).startsWith("_")) continue;

      const filePath = join(dirPath, file);
      let record: Memorial;
      try {
        record = JSON.parse(readFileSync(filePath, "utf-8"));
      } catch {
        console.warn(`  [warn] Could not parse: ${filePath}`);
        continue;
      }

      // Filter: UK country
      if (!record.country || !UK_COUNTRIES.has(record.country)) continue;

      // Filter: numeric coordinates
      const lat = typeof record.latitude === "number"
        ? record.latitude
        : parseFloat(record.latitude as string);
      const lon = typeof record.longitude === "number"
        ? record.longitude
        : parseFloat(record.longitude as string);

      if (!isFinite(lat) || !isFinite(lon)) continue;
      if (lat === 0 && lon === 0) continue; // null island guard

      results.push({
        ...record,
        latitude: lat,
        longitude: lon,
      });
    }
  }

  return results;
}

// ─── Step 2: Reverse-geocode via postcodes.io bulk endpoint ──────────────────

async function geocodeBatch(
  batch: MemorialWithCoords[],
  radius: number
): Promise<Map<string, string | null>> {
  // Returns memorial_id → constituency (or null)
  const body = {
    geolocations: batch.map((m) => ({
      longitude: m.longitude,
      latitude: m.latitude,
      limit: 1,
      radius,
    })),
  };

  const res = await fetchWithRetry(
    "https://api.postcodes.io/postcodes",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );

  if (!res.ok) {
    console.warn(`  [warn] postcodes.io returned ${res.status}`);
    return new Map(batch.map((m) => [m.id, null]));
  }

  const data = await res.json() as { status: number; result: PostcodesBulkResponseItem[] };

  if (!Array.isArray(data.result)) {
    console.warn(`  [warn] Unexpected postcodes.io response shape`);
    return new Map(batch.map((m) => [m.id, null]));
  }

  const out = new Map<string, string | null>();
  for (let i = 0; i < batch.length; i++) {
    const memorial = batch[i];
    const item = data.result[i];
    if (!item || !item.result || item.result.length === 0) {
      out.set(memorial.id, null);
      continue;
    }
    const postcode = item.result[0];
    // Prefer 2024 boundary, fall back to legacy; normalise Welsh unicode names
    const rawConstituency =
      postcode.parliamentary_constituency_2024 ||
      postcode.parliamentary_constituency ||
      null;
    const constituency = rawConstituency ? normaliseConstituencyName(rawConstituency) : null;
    out.set(memorial.id, constituency);
  }
  return out;
}

async function reverseGeocodeAll(
  memorials: MemorialWithCoords[]
): Promise<Map<string, string | null>> {
  const BATCH_SIZE = 100;
  const results = new Map<string, string | null>();

  // First pass at 2000m
  const batches: MemorialWithCoords[][] = [];
  for (let i = 0; i < memorials.length; i += BATCH_SIZE) {
    batches.push(memorials.slice(i, i + BATCH_SIZE));
  }

  console.log(`  Geocoding ${memorials.length} memorials in ${batches.length} batches (radius 2000m)...`);
  for (let bi = 0; bi < batches.length; bi++) {
    const batch = batches[bi];
    console.log(`    Batch ${bi + 1}/${batches.length} (${batch.length} records)...`);
    const batchResults = await geocodeBatch(batch, 2000);
    for (const [id, constituency] of batchResults) {
      results.set(id, constituency);
    }
    if (bi < batches.length - 1) await sleep(200);
  }

  // Second pass: retry misses with radius 20000
  const misses = memorials.filter((m) => !results.get(m.id));
  if (misses.length > 0) {
    console.log(`  Retrying ${misses.length} misses with radius 20000m...`);
    const retryBatches: MemorialWithCoords[][] = [];
    for (let i = 0; i < misses.length; i += BATCH_SIZE) {
      retryBatches.push(misses.slice(i, i + BATCH_SIZE));
    }
    for (let bi = 0; bi < retryBatches.length; bi++) {
      const batch = retryBatches[bi];
      console.log(`    Retry batch ${bi + 1}/${retryBatches.length} (${batch.length} records)...`);
      const batchResults = await geocodeBatch(batch, 20000);
      for (const [id, constituency] of batchResults) {
        if (constituency) results.set(id, constituency);
      }
      if (bi < retryBatches.length - 1) await sleep(200);
    }
  }

  return results;
}

// ─── Step 3: Fetch MP for each constituency ───────────────────────────────────

async function fetchConstituencyMP(
  constituency: string,
  cache: Map<string, MPInfo | null>,
  ambiguous: string[]
): Promise<MPInfo | null> {
  if (cache.has(constituency)) return cache.get(constituency)!;

  // Search constituency
  const searchUrl = `https://members-api.parliament.uk/api/Location/Constituency/Search?searchText=${encodeURIComponent(constituency)}&skip=0&take=5`;
  await sleep(300); // rate limit spacing

  const searchRes = await fetchWithRetry(searchUrl, {
    headers: { Accept: "application/json" },
  });

  if (!searchRes.ok) {
    console.warn(`  [warn] Parliament API returned ${searchRes.status} for: ${constituency}`);
    cache.set(constituency, null);
    return null;
  }

  const searchData = await searchRes.json() as {
    items: { value: ParliamentConstituency }[];
    totalResults: number;
  };

  if (!searchData.items || searchData.items.length === 0) {
    console.warn(`  [warn] No constituency found for: ${constituency}`);
    cache.set(constituency, null);
    return null;
  }

  // Check for exact name match first
  const exactMatch = searchData.items.find(
    (item) => item.value.name.toLowerCase() === constituency.toLowerCase()
  );

  let constituencyData: ParliamentConstituency;
  if (exactMatch) {
    constituencyData = exactMatch.value;
  } else if (searchData.items.length === 1) {
    constituencyData = searchData.items[0].value;
  } else {
    // Multiple matches, not exact — report ambiguous
    const names = searchData.items.map((i) => i.value.name).join(", ");
    console.warn(`  [ambiguous] "${constituency}" → multiple: ${names}`);
    ambiguous.push(`${constituency} → candidates: ${names}`);
    // Use first result as best guess
    constituencyData = searchData.items[0].value;
  }

  const member = constituencyData.currentRepresentation?.member?.value;
  if (!member) {
    console.warn(`  [warn] No current MP for constituency: ${constituency}`);
    cache.set(constituency, null);
    return null;
  }

  const mpInfo: MPInfo = {
    mp_name: member.nameDisplayAs,
    mp_party: member.latestParty?.name ?? "Unknown",
    mp_member_id: member.id,
    mp_parliamentary_email: null,
  };

  // Fetch contact email
  await sleep(300);
  const contactUrl = `https://members-api.parliament.uk/api/Members/${member.id}/Contact`;
  const contactRes = await fetchWithRetry(contactUrl, {
    headers: { Accept: "application/json" },
  });

  if (contactRes.ok) {
    const contactData = await contactRes.json() as {
      value: { type: string; email: string | null }[];
    };
    const parlOffice = (contactData.value ?? []).find(
      (c) => c.type === "Parliamentary office" && c.email
    );
    if (parlOffice?.email) {
      mpInfo.mp_parliamentary_email = parlOffice.email;
    }
  }

  cache.set(constituency, mpInfo);
  return mpInfo;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=== MP Constituency Map ===\n");

  // Ensure output dir exists
  mkdirSync(OUTPUT_DIR, { recursive: true });

  // Step 1: Load memorials
  console.log("Loading UK memorials with coordinates...");
  const memorials = loadUKMemorialsWithCoords();
  console.log(`  Found ${memorials.length} UK memorials with coordinates\n`);

  // Step 2: Reverse-geocode
  console.log("Reverse-geocoding via postcodes.io...");
  const constituencyMap = await reverseGeocodeAll(memorials);
  console.log();

  // Step 3: Gather distinct constituencies
  const allConstituencies = new Set<string>();
  for (const [, constituency] of constituencyMap) {
    if (constituency) allConstituencies.add(constituency);
  }
  console.log(`Found ${allConstituencies.size} distinct constituencies\n`);

  // Step 4: Fetch MPs
  console.log("Fetching MP data from Parliament API...");
  const mpCache = new Map<string, MPInfo | null>();
  const ambiguous: string[] = [];
  const sortedConstituencies = Array.from(allConstituencies).sort();

  for (let i = 0; i < sortedConstituencies.length; i++) {
    const constituency = sortedConstituencies[i];
    if (i % 10 === 0) {
      console.log(`  Progress: ${i}/${sortedConstituencies.length} constituencies...`);
    }
    await fetchConstituencyMP(constituency, mpCache, ambiguous);
  }
  console.log(`  Done: ${sortedConstituencies.length}/${sortedConstituencies.length} constituencies\n`);

  // Step 5: Build output rows
  const rows: OutputRow[] = [];
  const unmapped: string[] = [];

  for (const memorial of memorials) {
    const constituency = constituencyMap.get(memorial.id) ?? null;
    const mpInfo = constituency ? mpCache.get(constituency) ?? null : null;

    rows.push({
      memorial_id: memorial.id,
      title: memorial.title,
      county: memorial.county ?? null,
      latitude: memorial.latitude,
      longitude: memorial.longitude,
      constituency: constituency,
      mp_name: mpInfo?.mp_name ?? null,
      mp_party: mpInfo?.mp_party ?? null,
      mp_member_id: mpInfo?.mp_member_id ?? null,
      mp_parliamentary_email: mpInfo?.mp_parliamentary_email ?? null,
    });

    if (!constituency) {
      unmapped.push(memorial.id);
    }
  }

  const mapped = memorials.length - unmapped.length;
  const mappedPct = memorials.length > 0
    ? ((mapped / memorials.length) * 100).toFixed(1)
    : "0";

  const summary: Summary = {
    total_uk_with_coords: memorials.length,
    mapped,
    unmapped,
    distinct_constituency_count: allConstituencies.size,
    ambiguous,
  };

  // Step 6: Write output
  const output = { records: rows, summary };
  writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log(`Output written to: ${OUTPUT_FILE}\n`);

  // Step 7: Print summary to stdout
  console.log("=== SUMMARY ===");
  console.log(`Total UK memorials with coordinates: ${summary.total_uk_with_coords}`);
  console.log(`Mapped to constituency:              ${summary.mapped} (${mappedPct}%)`);
  console.log(`Unmapped:                            ${summary.unmapped.length}`);
  console.log(`Distinct constituencies:             ${summary.distinct_constituency_count}`);
  console.log(`Ambiguous constituency lookups:      ${summary.ambiguous.length}`);

  if (summary.unmapped.length > 0) {
    console.log(`\nUnmapped IDs:`);
    for (const id of summary.unmapped) {
      const m = memorials.find((x) => x.id === id)!;
      console.log(`  - ${id} (${m.latitude}, ${m.longitude})`);
    }
  }

  if (summary.ambiguous.length > 0) {
    console.log(`\nAmbiguous cases:`);
    for (const a of summary.ambiguous) {
      console.log(`  - ${a}`);
    }
  }

  // Threshold check
  const pct = memorials.length > 0 ? mapped / memorials.length : 0;
  if (pct < 0.90) {
    console.log(`\n[WARN] Mapping rate ${mappedPct}% is below the 90% threshold. Review unmapped records.`);
  }

  // Step 8: Print 5 sample rows
  console.log("\n=== 5 SAMPLE ROWS ===");
  const samples = rows.filter((r) => r.constituency).slice(0, 5);
  for (const row of samples) {
    console.log(`  ${row.memorial_id}`);
    console.log(`    Constituency: ${row.constituency}`);
    console.log(`    MP:           ${row.mp_name ?? "n/a"} (${row.mp_party ?? "n/a"})`);
    console.log(`    Email:        ${row.mp_parliamentary_email ?? "n/a"}`);
    console.log(`    Coords:       ${row.latitude}, ${row.longitude}`);
    console.log();
  }

  // Step 9: Known-good checks
  console.log("=== KNOWN-GOOD CHECKS ===");
  // Check Southend West and Leigh if any memorial maps there
  const southendRow = rows.find((r) => r.constituency === "Southend West and Leigh");
  if (southendRow) {
    const pass = southendRow.mp_member_id === 5106 &&
      southendRow.mp_name === "David Burton-Sampson" &&
      southendRow.mp_parliamentary_email === "david.burtonsampson.mp@parliament.uk";
    console.log(`  Southend West and Leigh: ${pass ? "PASS" : "FAIL"}`);
    console.log(`    MP: ${southendRow.mp_name} (${southendRow.mp_member_id}), email: ${southendRow.mp_parliamentary_email}`);
  } else {
    console.log("  Southend West and Leigh: no memorial maps there (cannot verify)");
  }

  // Spot-check: any Lincolnshire memorials should map to Lincolnshire constituencies
  const lincolnshireRows = rows.filter(
    (r) => r.county && r.county.toLowerCase().includes("lincolnshire") && r.constituency
  );
  if (lincolnshireRows.length > 0) {
    const lincolnshireOK = lincolnshireRows.every(
      (r) => r.constituency && r.constituency.toLowerCase().includes("lincoln")
        || r.constituency && /stamford|gainsborough|sleaford|grantham|louth|brigg|cleethorpes|grimsby|skegness|boston|spalding|horncastle|market rasen|scunthorpe|immingham|mablethorpe/i.test(r.constituency ?? "")
    );
    const sample3 = lincolnshireRows.slice(0, 3);
    console.log(`\n  Lincolnshire spot-checks (${lincolnshireRows.length} records):`);
    for (const r of sample3) {
      console.log(`    ${r.memorial_id} → ${r.constituency} [county: ${r.county}]`);
    }
  } else {
    console.log("  No Lincolnshire memorials found with county field to spot-check");
    // Print any rows with constituency containing 'Lincoln' anyway
    const lincolnConstRows = rows.filter((r) => r.constituency?.toLowerCase().includes("lincoln"));
    if (lincolnConstRows.length > 0) {
      console.log(`  (${lincolnConstRows.length} records map to Lincolnshire-area constituencies — sample):`);
      for (const r of lincolnConstRows.slice(0, 3)) {
        console.log(`    ${r.memorial_id} → ${r.constituency} (lat ${r.latitude}, lon ${r.longitude})`);
      }
    }
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
