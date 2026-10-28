#!/usr/bin/env bun
/**
 * Research dossiers — the only route by which researched facts reach a memorial record.
 *
 * A dossier (research/dossiers/<memorial-id>.json) records what was searched, every source
 * used, each fact as a claim tied to its sources, and narrative paragraphs that cite claims.
 * This tool:
 *   validate   — shape checks; every claim cites known sources, every paragraph cites claims
 *   crosscheck — groups claims per field (per person for crew), marks each
 *                corroborated | single | conflict, counting independence by publisher
 *   apply      — writes accepted facts into public/data/memorials/<id>.json with their sources,
 *                and sets data_quality from what the dossier proves (never typed by hand)
 *   report     — conflicts and held-back facts across dossiers, for Keith's review
 *
 * Usage: bun scripts/research/dossier.ts <validate|crosscheck|apply|report> [id ...] [--dry-run]
 * With no ids, every dossier is processed. Exit 1 on any validation error.
 */
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";

export const REPO = join(import.meta.dir, "../..");
const DOSSIERS = join(REPO, "research/dossiers");
const MEMORIALS = join(REPO, "public/data/memorials");
const IMAGES = join(REPO, "public/images/memorials");

export type Tier = "official" | "institutional" | "researched" | "community" | "secondary";
export const TIER_RANK: Record<Tier, number> = { official: 5, institutional: 4, researched: 3, community: 2, secondary: 1 };

export interface Source {
  id: string; url: string; title: string; publisher: string; tier: Tier; retrieved: string;
  summary?: string; key_details?: string[];
}
export interface Claim { id: string; field: string; value: string | number; person?: string; sources: string[]; quote?: string }
export interface Paragraph { section: "narrative" | "community_connection"; text: string; cites: string[]; presents_conflict?: boolean }
export interface Photo { url: string; credit: string; caption: string; source_id: string }
export interface Dossier {
  memorial_id: string; researched_at: string;
  searches: { query: string; useful: boolean }[];
  sources: Source[]; claims: Claim[]; paragraphs: Paragraph[];
  photos?: Photo[];
  custodian_status: "known" | "unknown-confirmed" | "unknown";
  /** Existing record content no source supports or a source contradicts; apply removes it. */
  retractions?: { field: string; reason: string }[];
  notes?: string;
}

/** Record-level fields a claim may set, and crew fields keyed by person. */
export const RECORD_FIELDS = new Set([
  "crash_date", "serial_number", "aircraft_type", "squadron", "station", "operation_type", "operation_target",
  "cause_of_loss", "location_name", "county", "memorial_type", "memorial_name", "memorial_address",
  "dedication_date", "erected_by", "inscription", "names_on_memorial", "died_count", "condition",
  "maintainer.organisation", "maintainer.website", "maintainer.maintainer_type",
]);
export const CREW_FIELDS = new Set([
  "crew.name", "crew.rank", "crew.role", "crew.age", "crew.service_number", "crew.nationality", "crew.fate",
  "crew.burial_location", "crew.cwgc_url", "crew.ibcc_url", "crew.iwm_name_url", "crew.hometown", "crew.decorations",
]);
/** A narrative-only fact (a take-off time, who was on which aircraft): paragraphs may cite it, apply never writes it to a field. */
export const EVENT = "event";
/** Fields a retraction may clear. Crew are never retracted wholesale: a name stays until a human removes it. */
export const RETRACTABLE = new Set([...RECORD_FIELDS, "local_contacts", "community_connection", "narrative", "crew_summary", "memorial_details"]);
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const URL_FIELDS = new Set(["crew.cwgc_url", "crew.ibcc_url", "crew.iwm_name_url", "maintainer.website"]);

export function validate(d: Dossier): string[] {
  const e: string[] = [];
  const srcIds = new Set(d.sources.map(s => s.id));
  const claimIds = new Set(d.claims.map(c => c.id));
  if (!d.memorial_id) e.push("memorial_id missing");
  if (!ISO_DATE.test(d.researched_at ?? "")) e.push("researched_at must be YYYY-MM-DD");
  if (!["known", "unknown-confirmed", "unknown"].includes(d.custodian_status)) e.push("custodian_status invalid");
  if (srcIds.size !== d.sources.length) e.push("duplicate source ids");
  if (claimIds.size !== d.claims.length) e.push("duplicate claim ids");
  for (const s of d.sources) {
    if (!/^https:\/\//.test(s.url)) e.push(`source ${s.id}: url must be https`);
    if (!(s.tier in TIER_RANK)) e.push(`source ${s.id}: bad tier ${s.tier}`);
    if (!s.publisher?.trim()) e.push(`source ${s.id}: publisher missing`);
  }
  for (const c of d.claims) {
    if (!RECORD_FIELDS.has(c.field) && !CREW_FIELDS.has(c.field) && c.field !== EVENT) e.push(`claim ${c.id}: unknown field ${c.field}`);
    if (CREW_FIELDS.has(c.field) && !c.person) e.push(`claim ${c.id}: crew claim needs person`);
    if (!c.sources?.length) e.push(`claim ${c.id}: no sources`);
    for (const s of c.sources ?? []) if (!srcIds.has(s)) e.push(`claim ${c.id}: unknown source ${s}`);
    // Same honest-imprecision forms quality-monitor accepts: a month or year when the day isn't verifiable.
    if (/date/.test(c.field) && !/^\d{4}(-\d{2}(-\d{2})?)?$/.test(String(c.value))) e.push(`claim ${c.id}: ${c.field} must be YYYY-MM-DD (or YYYY-MM / YYYY)`);
    if (URL_FIELDS.has(c.field) && !/^https:\/\//.test(String(c.value))) e.push(`claim ${c.id}: ${c.field} must be https`);
    if (String(c.value).trim() === "") e.push(`claim ${c.id}: empty value`);
  }
  const groups = crosscheck(d);
  for (const [i, p] of d.paragraphs.entries()) {
    if (!p.cites?.length) e.push(`paragraph ${i}: cites no claims`);
    for (const c of p.cites ?? []) {
      if (!claimIds.has(c)) { e.push(`paragraph ${i}: unknown claim ${c}`); continue; }
      const g = groups.find(g => g.claims.some(x => x.id === c));
      if (g?.status === "conflict" && !p.presents_conflict) e.push(`paragraph ${i}: cites conflicted claim ${c} without presents_conflict`);
    }
  }
  for (const t of d.retractions ?? []) {
    if (!RETRACTABLE.has(t.field)) e.push(`retraction: field ${t.field} cannot be retracted`);
    if (!t.reason?.trim()) e.push(`retraction ${t.field}: reason missing`);
  }
  for (const p of d.photos ?? []) {
    if (!srcIds.has(p.source_id)) e.push(`photo ${p.url}: unknown source ${p.source_id}`);
    if (!p.credit?.trim()) e.push(`photo ${p.url}: credit missing`);
  }
  return e;
}

export function normalise(field: string, v: string | number): string {
  const s = String(v).toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  if (field === "crew.name") {
    // Agree on surname + first forename initial; middle names and initials vary between sources.
    const parts = s.split(" ").filter(Boolean);
    return parts.length > 1 ? `${parts[0][0]} ${parts[parts.length - 1]}` : s;
  }
  if (field === "crew.service_number") return s.replace(/ /g, "");
  return s;
}

export interface Group {
  field: string; person?: string; claims: Claim[];
  values: { value: string | number; publishers: string[]; topTier: Tier }[];
  status: "corroborated" | "single" | "conflict";
  accepted?: string | number;
}

export function crosscheck(d: Dossier): Group[] {
  const src = new Map(d.sources.map(s => [s.id, s]));
  const byKey = new Map<string, Claim[]>();
  for (const c of d.claims) {
    // Each event is its own fact; two different events are not a conflict.
    const k = c.field === EVENT ? `${EVENT}#${c.id}|` : `${c.field}|${c.person ?? ""}`;
    byKey.set(k, [...(byKey.get(k) ?? []), c]);
  }
  const out: Group[] = [];
  for (const [k, claims] of byKey) {
    const [rawField, person] = k.split("|");
    const field = rawField.startsWith(EVENT) ? EVENT : rawField;
    const vals = new Map<string, { value: string | number; publishers: Set<string>; topTier: Tier }>();
    for (const c of claims) {
      const n = normalise(field, c.value);
      const cur = vals.get(n) ?? { value: c.value, publishers: new Set<string>(), topTier: "secondary" as Tier };
      // Keep the fullest spelling of an agreeing value (e.g. "George Alexander Alexander" over "G. A. Alexander").
      if (String(c.value).length > String(cur.value).length) cur.value = c.value;
      for (const sid of c.sources) {
        const s = src.get(sid); if (!s) continue;
        cur.publishers.add(s.publisher.trim().toLowerCase());
        if (TIER_RANK[s.tier] > TIER_RANK[cur.topTier]) cur.topTier = s.tier;
      }
      vals.set(n, cur);
    }
    const values = [...vals.values()].map(v => ({ value: v.value, publishers: [...v.publishers], topTier: v.topTier }));
    let status: Group["status"];
    let accepted: string | number | undefined;
    if (values.length > 1) {
      status = "conflict";
      // A conflict resolves only when one value alone carries the highest tier present.
      const best = Math.max(...values.map(v => TIER_RANK[v.topTier]));
      const top = values.filter(v => TIER_RANK[v.topTier] === best);
      if (top.length === 1 && best >= TIER_RANK.institutional && field !== "cause_of_loss") accepted = top[0].value;
    } else {
      const v = values[0];
      status = v.publishers.length >= 2 ? "corroborated" : "single";
      // Single-source facts need a researched-or-better source; community and secondary sites only corroborate.
      if (status === "corroborated" || TIER_RANK[v.topTier] >= TIER_RANK.researched) accepted = v.value;
    }
    out.push({ field, person: person || undefined, claims, values, status, accepted });
  }
  return out;
}

/** Local path (under public/images/memorials/) a dossier photo is saved to. */
export function photoFile(memorialId: string, url: string): string {
  const base = decodeURIComponent(new URL(url).pathname.split("/").pop() ?? "photo.jpg").toLowerCase().replace(/[^a-z0-9._-]+/g, "-");
  return `${memorialId}/${base}`;
}

const roleOrder = ["pilot", "co-pilot", "second pilot", "navigator", "flight engineer", "bomb aimer", "wireless operator", "air gunner", "mid-upper gunner", "rear gunner"];

export interface Applied { record: any; held: Group[]; conflicts: Group[]; quality: string }

export function apply(d: Dossier, record: any): Applied {
  const groups = crosscheck(d);
  const r = structuredClone(record);
  const used = new Set<string>();

  // Retractions first, so a sourced fact for the same field still lands afterwards.
  for (const t of d.retractions ?? []) {
    if (t.field.startsWith("maintainer.")) { if (r.maintainer) delete r.maintainer[t.field.slice(11)]; if (r.maintainer && !Object.keys(r.maintainer).length) delete r.maintainer; }
    else if (t.field === "local_contacts") r.local_contacts = [];
    else delete r[t.field];
  }
  const markUsed = (g: Group) => g.claims.filter(c => normalise(g.field, c.value) === normalise(g.field, g.accepted!)).forEach(c => c.sources.forEach(s => used.add(s)));

  for (const g of groups.filter(g => g.accepted !== undefined && RECORD_FIELDS.has(g.field))) {
    if (g.field.startsWith("maintainer.")) { r.maintainer = { ...(r.maintainer ?? {}), [g.field.slice(11)]: g.accepted }; }
    else r[g.field] = g.accepted;
    markUsed(g);
  }

  // Crew: one entry per person whose name was accepted; other fields fill in where accepted.
  const people = [...new Set(groups.filter(g => g.person).map(g => g.person!))];
  const crew: any[] = [];
  for (const p of people) {
    const nameG = groups.find(g => g.person === p && g.field === "crew.name");
    if (!nameG || nameG.accepted === undefined) continue;
    markUsed(nameG);
    const existing = (r.crew ?? []).find((c: any) => normalise("crew.name", c.name ?? "") === normalise("crew.name", nameG.accepted!)) ?? {};
    const m: any = { ...existing, name: nameG.accepted };
    for (const g of groups.filter(g => g.person === p && g.field !== "crew.name" && g.accepted !== undefined)) {
      m[g.field.slice(5)] = g.field === "crew.age" ? Number(g.accepted) : g.accepted;
      markUsed(g);
    }
    crew.push(m);
  }
  if (crew.length) {
    // Keep any existing crew the dossier doesn't mention, so research never silently drops a name.
    const kept = (r.crew ?? []).filter((c: any) => !crew.some(m => normalise("crew.name", m.name) === normalise("crew.name", c.name ?? "")));
    r.crew = [...crew, ...kept].sort((a, b) => {
      const ia = roleOrder.findIndex(x => (a.role ?? "").toLowerCase().startsWith(x)), ib = roleOrder.findIndex(x => (b.role ?? "").toLowerCase().startsWith(x));
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
  }

  for (const section of ["narrative", "community_connection"] as const) {
    const paras = d.paragraphs.filter(p => p.section === section);
    if (paras.length) { r[section] = paras.map(p => p.text.trim()).join("\n\n"); paras.forEach(p => p.cites.forEach(cid => d.claims.find(c => c.id === cid)?.sources.forEach(s => used.add(s)))); }
  }

  if (d.photos?.length) {
    const have = new Set((r.photos ?? []).map((p: any) => p.source));
    r.photos = [...(r.photos ?? []), ...d.photos.filter(p => !have.has(p.url)).map(p => ({ filename: photoFile(d.memorial_id, p.url), caption: p.caption, credit: p.credit, source: p.url }))];
    d.photos.forEach(p => used.add(p.source_id));
  }

  // Sources and external narratives: everything the applied facts rest on.
  const srcById = new Map(d.sources.map(s => [s.id, s]));
  const have = new Set((r.sources ?? []).map((s: any) => s.url));
  for (const id of used) {
    const s = srcById.get(id)!;
    if (!have.has(s.url)) { (r.sources ??= []).push({ title: s.title, type: s.tier, url: s.url, date: s.retrieved }); have.add(s.url); }
    if (s.summary && !(r.external_narratives ?? []).some((e: any) => e.original_url === s.url)) {
      (r.external_narratives ??= []).push({ source_site: s.publisher, original_url: s.url, summary: s.summary, key_details: s.key_details ?? [], date_retrieved: s.retrieved, still_live: true });
    }
  }
  if (r.narrative_source === "generated-claude-sonnet" && d.paragraphs.some(p => p.section === "narrative")) r.narrative_source = "researched-dossier";
  r.last_updated = d.researched_at;
  r.last_validated = d.researched_at;
  r.data_quality = quality(r, d, groups);

  return { record: r, held: groups.filter(g => g.accepted === undefined && g.status !== "conflict"), conflicts: groups.filter(g => g.status === "conflict"), quality: r.data_quality };
}

/**
 * Comprehensive: crew present and every crew name corroborated or from an official/institutional
 * source; a sourced narrative; custodian known or confirmed unknown; a photo; 2+ independent publishers.
 * Partial: sourced crew or narrative. Stub: neither.
 */
export function quality(r: any, d: Dossier, groups = crosscheck(d)): "Comprehensive" | "Partial" | "Stub" {
  const nameGroups = groups.filter(g => g.field === "crew.name" && g.accepted !== undefined);
  const crewSolid = (r.crew ?? []).length > 0 && nameGroups.length > 0 &&
    nameGroups.every(g => g.status === "corroborated" || TIER_RANK[g.values[0].topTier] >= TIER_RANK.institutional);
  const narrative = d.paragraphs.some(p => p.section === "narrative");
  const custodian = d.custodian_status !== "unknown";
  const photo = (r.photos ?? []).length > 0;
  const publishers = new Set(d.sources.map(s => s.publisher.trim().toLowerCase()));
  if (crewSolid && narrative && custodian && photo && publishers.size >= 2) return "Comprehensive";
  if ((r.crew ?? []).length > 0 || narrative) return "Partial";
  return "Stub";
}

// ---------- CLI ----------
if (import.meta.main) {
  const [cmd, ...rest] = process.argv.slice(2);
  const dry = rest.includes("--dry-run");
  const ids = rest.filter(a => !a.startsWith("--"));
  if (!existsSync(DOSSIERS)) { console.error(`no dossiers dir: ${DOSSIERS}`); process.exit(1); }
  const all = readdirSync(DOSSIERS).filter(f => f.endsWith(".json")).map(f => f.slice(0, -5));
  const targets = ids.length ? ids : all;
  const load = (id: string): Dossier => JSON.parse(readFileSync(join(DOSSIERS, `${id}.json`), "utf8"));
  let failed = false;

  if (cmd === "validate") {
    for (const id of targets) {
      const errs = validate(load(id));
      if (!existsSync(join(MEMORIALS, `${id}.json`))) errs.push("no memorial record with this id");
      console.log(`${errs.length ? "FAIL" : "ok  "} ${id}${errs.length ? "\n  - " + errs.join("\n  - ") : ""}`);
      if (errs.length) failed = true;
    }
  } else if (cmd === "crosscheck") {
    for (const id of targets) {
      const g = crosscheck(load(id));
      const n = (s: string) => g.filter(x => x.status === s).length;
      console.log(`${id}: ${g.length} facts · ${n("corroborated")} corroborated · ${n("single")} single · ${n("conflict")} conflict · ${g.filter(x => x.accepted === undefined).length} held back`);
    }
  } else if (cmd === "apply") {
    for (const id of targets) {
      const d = load(id);
      const errs = validate(d);
      if (errs.length) { console.log(`SKIP ${id}: ${errs.length} validation errors`); failed = true; continue; }
      const path = join(MEMORIALS, `${id}.json`);
      const before = JSON.parse(readFileSync(path, "utf8"));
      const a = apply(d, before);
      console.log(`${dry ? "would apply" : "applied"} ${id}: crew ${(before.crew ?? []).length}→${(a.record.crew ?? []).length} · narrative ${(before.narrative ?? "").length}→${(a.record.narrative ?? "").length} chars · sources ${(before.sources ?? []).length}→${a.record.sources.length} · ${before.data_quality}→${a.quality} · ${a.conflicts.length} conflicts · ${a.held.length} held`);
      if (dry) continue;
      // Save any new photos locally first; a record never points at an image we don't hold.
      for (const p of (a.record.photos ?? []).filter((p: any) => p.source && !existsSync(join(IMAGES, p.filename)))) {
        const res = await fetch(p.source);
        if (!res.ok || !(res.headers.get("content-type") ?? "").startsWith("image/")) {
          console.log(`  photo not saved (${res.status}), dropped: ${p.source}`);
          a.record.photos = a.record.photos.filter((x: any) => x !== p);
          continue;
        }
        mkdirSync(dirname(join(IMAGES, p.filename)), { recursive: true });
        writeFileSync(join(IMAGES, p.filename), Buffer.from(await res.arrayBuffer()));
        await new Promise(r => setTimeout(r, 2000)); // polite pacing for IWM and other hosts
      }
      a.record.data_quality = quality(a.record, d); // a dropped photo can lower the tier
      writeFileSync(path, JSON.stringify(a.record, null, 2) + "\n");
    }
  } else if (cmd === "report") {
    const lines = ["# Research conflicts and held-back facts", "", `Generated ${new Date().toISOString().slice(0, 10)} by scripts/research/dossier.ts report. Conflicts are never resolved silently: each needs a human call or a better source.`, ""];
    for (const id of targets) {
      const d = load(id); const g = crosscheck(d);
      const src = new Map(d.sources.map(s => [s.id, s]));
      const bad = g.filter(x => x.status === "conflict" || x.accepted === undefined);
      if (!bad.length) continue;
      lines.push(`## ${id}`, "");
      for (const x of bad) {
        lines.push(`- **${x.field}${x.person ? ` (${x.person})` : ""}** — ${x.status}${x.accepted !== undefined ? `, resolved to "${x.accepted}" by source tier` : ", not applied"}`);
        for (const v of x.values) {
          const urls = x.claims.filter(c => normalise(x.field, c.value) === normalise(x.field, v.value)).flatMap(c => c.sources).map(s => src.get(s)?.url).filter(Boolean);
          lines.push(`  - "${v.value}" — ${v.publishers.join(", ")} (${v.topTier}) ${[...new Set(urls)].join(" ")}`);
        }
      }
      lines.push("");
    }
    const out = join(REPO, "research/CONFLICTS.md");
    writeFileSync(out, lines.join("\n"));
    console.log(`wrote ${out}`);
  } else {
    console.error("usage: dossier.ts <validate|crosscheck|apply|report> [id ...] [--dry-run]");
    process.exit(1);
  }
  process.exit(failed ? 1 : 0);
}
