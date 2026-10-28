#!/usr/bin/env bun
/**
 * IWM memorial page capture — names, text and photos in one normal page load.
 *
 * IWM loads the names on a memorial client-side, so the page HTML never holds them.
 * We load the public page as a browser would and read the page's own name responses.
 * Never call IWM's JSON:API directly: their bot check refused it (28 Oct 2026).
 *
 * Usage: bun scripts/research/iwm-page.ts <iwmMemorialId>
 * Output: JSON { iwm_id, url, names: [{name_id, forename, surname, url}], text, photos }
 * Pacing: one page per call; callers must leave >= 5s between calls.
 */
import { chromium } from "@playwright/test";

const id = process.argv[2];
if (!/^\d+$/.test(id ?? "")) { console.error("usage: iwm-page.ts <iwmMemorialId>"); process.exit(1); }

const url = `https://memorials.iwm.org.uk/memorial/${id}`;
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const bodies: any[] = [];
  page.on("response", async r => {
    if (r.url().includes("jsonapi/node/name")) { try { bodies.push(await r.json()); } catch { /* not JSON */ } }
  });
  await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
  await page.waitForTimeout(2000);

  const seen = new Set<string>();
  const names = bodies.flatMap(b => b.data ?? []).map((n: any) => ({
    name_id: String(n.attributes?.field_name_id ?? n.field_name_id ?? ""),
    forename: n.attributes?.field_name_forename ?? n.field_name_forename ?? "",
    surname: n.attributes?.field_name_surname ?? n.field_name_surname ?? "",
  })).filter(n => n.name_id && !seen.has(n.name_id) && seen.add(n.name_id))
    .map(n => ({ ...n, url: `https://memorials.iwm.org.uk/name/${n.name_id}` }));

  const text = (await page.innerText("main").catch(() => page.innerText("body"))).slice(0, 12_000);
  // Thumbnails sit under /styles/thumbnail/public/; the full image drops that segment and the itok query.
  const thumbs = [...new Set(await page.$$eval("img", imgs =>
    imgs.map(i => (i as HTMLImageElement).src).filter(s => s.includes("wmr.iwm.org.uk/sites/default/files"))))];
  const photos = thumbs.map(t => ({ thumbnail: t, full: t.replace("/styles/thumbnail/public/", "/").replace(/\?.*$/, "") }));
  // Credits appear in page order as "Source: …"; IWM shows one per photo.
  const credits = [...text.matchAll(/^Source:\s*(.+)$/gm)].map(m => m[1].trim());

  console.log(JSON.stringify({ iwm_id: id, url, names, text, photos, photo_credits: credits }, null, 1));
} finally {
  await browser.close();
}
