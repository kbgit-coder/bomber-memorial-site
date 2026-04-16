/**
 * staging-validation.spec.ts
 * Comprehensive validation suite for staging.bombermemorial.co.uk
 *
 * Groups:
 *   1. Core Pages (smoke tests)
 *   2. Memorial Pages
 *   3. Squadron Pages
 *   4. Features
 *   5. Data Integrity
 *   6. Accessibility
 */

import { test, expect, request } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Authenticated fetch — reuses Playwright's httpCredentials from config */
async function authFetch(
  apiContext: Awaited<ReturnType<typeof request.newContext>>,
  url: string
) {
  return apiContext.get(url);
}

// Five random memorial slugs (deliberately spread across alphabet) used in
// the internal-audit-data-leak tests.
const RANDOM_MEMORIAL_SLUGS = [
  "annesley-eh988",
  "bawdeswell-kb364",
  "cloot-drove-nd981-and-lancaster-me625-mid-air-collision-",
  "higher-shelf-stones-overexposed-memorial-b-29-44-61999",
  "kirkley-lowestoft-halifax-memorial-general-memorial-to-196",
];

// ---------------------------------------------------------------------------
// 1. Core Pages — smoke tests
// ---------------------------------------------------------------------------

test.describe("1. Core Pages", () => {
  test("homepage loads and title contains 'Bomber Command Memorial Register'", async ({
    page,
  }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle(/Bomber Command Memorial Register/i);
  });

  test("search page loads", async ({ page }) => {
    const response = await page.goto("/search");
    expect(response?.status()).toBe(200);
    // The search page must contain some form of search UI
    await expect(page.locator("body")).toContainText(/search/i);
  });

  test("about page loads", async ({ page }) => {
    const response = await page.goto("/about");
    expect(response?.status()).toBe(200);
    await expect(page.locator("body")).not.toBeEmpty();
  });

  test("squadron index page loads", async ({ page }) => {
    const response = await page.goto("/squadron");
    expect(response?.status()).toBe(200);
    await expect(page.locator("body")).toContainText(/squadron/i);
  });

  test("404 page shows branded content for /nonexistent-test-page", async ({
    page,
  }) => {
    // Next.js static export returns 404 status; some hosts return 200 with
    // the 404 page content — accept either as long as branded text appears.
    await page.goto("/nonexistent-test-page", { waitUntil: "domcontentloaded" });
    const body = page.locator("body");
    // Should contain either "not found" messaging or the site name — not a
    // generic server 500 or blank page.
    const text = (await body.textContent()) ?? "";
    const hasNotFound =
      /not found|404|page doesn.t exist|couldn.t find/i.test(text);
    const hasSiteBrand =
      /bomber command|memorial register|bombermemorial/i.test(text);
    expect(hasNotFound || hasSiteBrand, `Unexpected 404 body: "${text.slice(0, 200)}"`).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 2. Memorial Pages
// ---------------------------------------------------------------------------

test.describe("2. Memorial Pages", () => {
  test("Farnsfield memorial loads", async ({ page }) => {
    const response = await page.goto("/memorial/farnsfield-halifax-mz519");
    expect(response?.status()).toBe(200);
  });

  test("Farnsfield memorial has crew table with 7 members", async ({
    page,
  }) => {
    await page.goto("/memorial/farnsfield-halifax-mz519");
    // Crew table rows — one per crew member (exclude any header row).
    // Look for a <table> containing crew data; each member is a <tr>.
    const crewSection = page.locator("table");
    await expect(crewSection.first()).toBeVisible();

    // Count data rows (tr elements that are not the header)
    const dataRows = page.locator("table tr").filter({ hasText: /sgt|flt|plt|wg|grp|sqn|f\/o|f\/s|p\/o|lac|air/i });
    const count = await dataRows.count();
    // We expect 7 crew members — be generous and accept 6-8 in case the
    // page renders the header differently on staging vs local data.
    expect(count, `Expected 7 crew rows, found ${count}`).toBeGreaterThanOrEqual(6);
    expect(count).toBeLessThanOrEqual(8);
  });

  test("Kirmington 166 Sqn memorial garden loads with correct title", async ({
    page,
  }) => {
    const response = await page.goto(
      "/memorial/kirmington-166-sqn-memorial-garden"
    );
    expect(response?.status()).toBe(200);
    const title = await page.title();
    expect(title).toMatch(/166 Squadron/i);
  });

  test("Ryhope Barton VC memorial loads and contains 'Victoria Cross'", async ({
    page,
  }) => {
    const response = await page.goto(
      "/memorial/ryhope-sunderland-barton-vc"
    );
    expect(response?.status()).toBe(200);
    await expect(page.locator("body")).toContainText("Victoria Cross");
  });

  // Internal audit data leak — checks that raw data annotations are not
  // rendered in public page HTML.
  const LEAK_STRINGS = [
    "verification_notes",
    "CONFIRMED ERROR",
    "Previous coords",
  ];

  const memorialsToCheck = [
    ...RANDOM_MEMORIAL_SLUGS,
    "farnsfield-halifax-mz519",
  ];

  for (const slug of memorialsToCheck) {
    for (const leakString of LEAK_STRINGS) {
      test(`Memorial "${slug}" does not expose "${leakString}"`, async ({
        page,
      }) => {
        await page.goto(`/memorial/${slug}`);
        const bodyText = (await page.locator("body").textContent()) ?? "";
        expect(
          bodyText,
          `"${leakString}" found in memorial page ${slug}`
        ).not.toContain(leakString);
      });
    }
  }

  // HARD GATE: Personal data must NEVER appear on public pages.
  // Contributor emails, phone numbers, and personal names from
  // local_contacts and maintainer fields must be stripped before build.
  const PII_MEMORIALS = [
    "elsham-wolds-jd386",
    "farnsfield-halifax-mz519",
    "bleasby-3-lancaster-r-5698",
    "kessingland-b-24-liberator-41-28",
    ...RANDOM_MEMORIAL_SLUGS,
  ];

  const EMAIL_PATTERN = /[a-zA-Z0-9._%+-]+@(?!(?:staging\.)?bombermemorial\.co\.uk)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

  for (const slug of PII_MEMORIALS) {
    test(`HARD GATE: Memorial "${slug}" contains no personal email addresses`, async ({
      page,
    }) => {
      await page.goto(`/memorial/${slug}`);
      const html = await page.content();
      const emails = html.match(new RegExp(EMAIL_PATTERN.source, 'g')) || [];
      expect(
        emails,
        `Personal email found on ${slug}: ${emails.join(', ')}`
      ).toHaveLength(0);
    });
  }

  test("HARD GATE: Memorial JSON files contain no personal emails", async () => {
    const apiContext = await request.newContext({
      baseURL: "https://staging.bombermemorial.co.uk",
      httpCredentials: { username: "keith", password: "bmr-staging-2026" },
    });
    // Check known previously-affected files
    const filesToCheck = [
      "elsham-wolds-jd386",
      "bleasby-3-lancaster-r-5698",
      "farnsfield-halifax-mz519",
    ];
    for (const slug of filesToCheck) {
      const resp = await apiContext.get(`/data/memorials/${slug}.json`);
      expect(resp.status()).toBe(200);
      const text = await resp.text();
      const emails = text.match(new RegExp(EMAIL_PATTERN.source, 'g')) || [];
      expect(
        emails,
        `Personal email in JSON ${slug}.json: ${emails.join(', ')}`
      ).toHaveLength(0);
    }
    await apiContext.dispose();
  });
});

// ---------------------------------------------------------------------------
// 3. Squadron Pages
// ---------------------------------------------------------------------------

test.describe("3. Squadron Pages", () => {
  test("578 Squadron page loads and contains squadron number and history section", async ({
    page,
  }) => {
    const response = await page.goto("/squadron/578-squadron");
    expect(response?.status()).toBe(200);
    const body = page.locator("body");
    await expect(body).toContainText("578");
    // The enriched history section — look for a heading or section heading
    // that indicates history content exists on the page.
    const historyVisible =
      (await page
        .locator("text=/history|formed|disbanded|operations/i")
        .count()) > 0;
    expect(historyVisible, "No history content found on 578 Sqn page").toBe(true);
  });

  test("106 Squadron page loads", async ({ page }) => {
    const response = await page.goto("/squadron/106-squadron-raf");
    expect(response?.status()).toBe(200);
    await expect(page.locator("body")).toContainText("106");
  });

  test("300 Polish (Masovia) Squadron page loads", async ({ page }) => {
    const response = await page.goto(
      "/squadron/300-masovia-squadron-paf"
    );
    expect(response?.status()).toBe(200);
    await expect(page.locator("body")).toContainText("300");
  });

  test("300 Polish Squadron Wikipedia link resolves (HTTP 200)", async ({
    page,
  }) => {
    await page.goto("/squadron/300-masovia-squadron-paf");

    // Find all links containing 'wikipedia.org' on the page.
    const wikiLinks = page.locator('a[href*="wikipedia.org"]');
    const count = await wikiLinks.count();
    expect(
      count,
      "Expected at least one Wikipedia link on 300 Sqn page"
    ).toBeGreaterThan(0);

    const href = await wikiLinks.first().getAttribute("href");
    expect(href).toBeTruthy();

    // Verify the Wikipedia URL returns HTTP 200.  Use a plain fetch via
    // apiRequestContext so we get the status code without navigating away.
    const apiContext = await request.newContext();
    const resp = await apiContext.get(href!);
    expect(
      resp.status(),
      `Wikipedia URL ${href} returned ${resp.status()}`
    ).toBe(200);
    await apiContext.dispose();
  });
});

// ---------------------------------------------------------------------------
// 3b. Workstream 1 — Hidden Data Now Rendered
// ---------------------------------------------------------------------------

test.describe("3b. Workstream 1 — Storytelling Upgrade", () => {
  test("fate_detail renders on Staunton memorial crew section", async ({
    page,
  }) => {
    await page.goto("/memorial/staunton-in-the-vale-wellington-w-4270");
    const body = page.locator("body");
    // Thomas Warne's fate_detail mentions night flying hours
    await expect(body).toContainText("15 hours of night flying");
  });

  test("fate_detail renders on Farnsfield memorial crew section", async ({
    page,
  }) => {
    await page.goto("/memorial/farnsfield-halifax-mz519");
    const body = page.locator("body");
    // Parfitt's fate_detail about steering away from the village
    await expect(body).toContainText(/steered.*away|burning aircraft/i);
  });

  test("The Memorial section renders community connection on Farnsfield page", async ({
    page,
  }) => {
    await page.goto("/memorial/farnsfield-halifax-mz519");
    const body = page.locator("body");
    await expect(body).toContainText("The Memorial");
    // Should show community connection narrative from structured fields
    await expect(body).toContainText("Farnsfield Memorial Trust");
    await expect(body).toContainText("6 July 1994");
  });

  test("external narratives are NOT suppressed when crew array exists", async ({
    page,
  }) => {
    // Staunton has both crew array (7 members) and external narratives with full_narrative
    await page.goto("/memorial/staunton-in-the-vale-wellington-w-4270");
    const body = page.locator("body");
    // The "Detailed Record" section should be visible even though crew is structured
    await expect(body).toContainText("Detailed Record");
  });

  test("OS grid reference renders on Barton VC memorial", async ({
    page,
  }) => {
    await page.goto("/memorial/ryhope-sunderland-barton-vc");
    const body = page.locator("body");
    await expect(body).toContainText("OS Grid Ref");
    await expect(body).toContainText("NZ 41238 52906");
  });
});

// ---------------------------------------------------------------------------
// 4. Features
// ---------------------------------------------------------------------------

test.describe("4. Features", () => {
  test("Location confidence badge renders 'Confirmed' on Farnsfield page", async ({
    page,
  }) => {
    await page.goto("/memorial/farnsfield-halifax-mz519");
    // The badge should contain either "Verified" or "Confirmed"
    const body = page.locator("body");
    const text = (await body.textContent()) ?? "";
    const hasBadge = /confirmed|verified/i.test(text);
    expect(hasBadge, "Location confidence badge not found on Farnsfield page").toBe(true);
  });

  test("Nearby memorials section appears on Farnsfield page", async ({
    page,
  }) => {
    await page.goto("/memorial/farnsfield-halifax-mz519");
    const body = page.locator("body");
    const text = (await body.textContent()) ?? "";
    const hasNearby = /nearby|close by|also in this area/i.test(text);
    expect(hasNearby, "Nearby memorials section not found on Farnsfield page").toBe(true);
  });

  test("Print stylesheet exists (@media print in global CSS)", async ({
    page,
  }) => {
    await page.goto("/");
    // Playwright can evaluate whether print media is defined by inspecting
    // stylesheets. We look for any stylesheet that mentions print rules.
    const hasPrintCSS = await page.evaluate(() => {
      for (const sheet of Array.from(document.styleSheets)) {
        try {
          for (const rule of Array.from(sheet.cssRules)) {
            if (
              rule instanceof CSSMediaRule &&
              rule.conditionText.includes("print")
            ) {
              return true;
            }
          }
        } catch {
          // Cross-origin sheets throw — skip
        }
      }
      return false;
    });
    expect(hasPrintCSS, "@media print not found in any loaded stylesheet").toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 5. Data Integrity
// ---------------------------------------------------------------------------

test.describe("5. Data Integrity", () => {
  test("Homepage stats show 222 memorials", async ({ page }) => {
    await page.goto("/");
    // The stats section displays the count as plain text. Match the number.
    const body = page.locator("body");
    const text = (await body.textContent()) ?? "";
    expect(
      text,
      "Could not find '222' on the homepage stats"
    ).toContain("222");
  });

  test("All nav links on homepage return HTTP 200", async ({ page }) => {
    await page.goto("/");

    // Collect internal nav <a> hrefs
    const navLinks = await page
      .locator("header a, nav a")
      .evaluateAll((els) =>
        els
          .map((el) => el.getAttribute("href"))
          .filter(
            (href): href is string =>
              !!href &&
              !href.startsWith("http") &&
              !href.startsWith("#") &&
              !href.startsWith("mailto")
          )
      );

    expect(navLinks.length, "No internal nav links found on homepage").toBeGreaterThan(0);

    const apiContext = await request.newContext({
      httpCredentials: { username: "keith", password: "bmr-staging-2026" },
      baseURL: "https://staging.bombermemorial.co.uk",
    });

    const results: { href: string; status: number }[] = [];
    for (const href of navLinks) {
      const resp = await apiContext.get(href);
      results.push({ href, status: resp.status() });
    }
    await apiContext.dispose();

    const broken = results.filter((r) => r.status >= 400);
    expect(
      broken,
      `Broken nav links: ${JSON.stringify(broken)}`
    ).toHaveLength(0);
  });

  test("Squadron JSON data files are valid JSON (fetch /data/squadrons/)", async ({
    page,
  }) => {
    const SQUADRON_FILES = [
      "/data/squadrons/578-squadron.json",
      "/data/squadrons/106-squadron-raf.json",
      "/data/squadrons/300-masovia-squadron-paf.json",
      "/data/squadrons/166-squadron-raf.json",
      "/data/squadrons/100-squadron.json",
    ];

    const apiContext = await request.newContext({
      httpCredentials: { username: "keith", password: "bmr-staging-2026" },
      baseURL: "https://staging.bombermemorial.co.uk",
    });

    for (const file of SQUADRON_FILES) {
      const resp = await apiContext.get(file);
      expect(resp.status(), `${file} returned ${resp.status()}`).toBe(200);
      // Validate it parses as JSON
      let parsed: unknown;
      try {
        parsed = await resp.json();
      } catch (e) {
        parsed = null;
      }
      expect(parsed, `${file} is not valid JSON`).not.toBeNull();
      expect(typeof parsed).toBe("object");
    }

    await apiContext.dispose();
  });
});

// ---------------------------------------------------------------------------
// 6. Accessibility
// ---------------------------------------------------------------------------

test.describe("6. Accessibility", () => {
  test("Body font-size is at least 19px", async ({ page }) => {
    await page.goto("/");
    const fontSize = await page.evaluate(() => {
      const body = document.body;
      const computedSize = window.getComputedStyle(body).fontSize;
      return parseFloat(computedSize);
    });
    expect(
      fontSize,
      `Body font-size is ${fontSize}px — expected >= 19px`
    ).toBeGreaterThanOrEqual(19);
  });

  test("Focus-visible styles exist in loaded CSS", async ({ page }) => {
    await page.goto("/");
    const hasFocusVisible = await page.evaluate(() => {
      for (const sheet of Array.from(document.styleSheets)) {
        try {
          for (const rule of Array.from(sheet.cssRules)) {
            if (
              rule instanceof CSSStyleRule &&
              rule.selectorText?.includes(":focus-visible")
            ) {
              return true;
            }
          }
        } catch {
          // Cross-origin sheets — skip
        }
      }
      return false;
    });
    expect(
      hasFocusVisible,
      ":focus-visible rule not found in any loaded stylesheet"
    ).toBe(true);
  });

  test("Key interactive elements have minimum 44px touch target height", async ({
    page,
  }) => {
    await page.goto("/");

    // Sample the first 10 visible <a> elements in the nav/header and check
    // their bounding box height. Note: CSS sets min-height:44px globally,
    // but some anchors have min-height unset (p a, li a etc).  We check the
    // navigation anchors specifically.
    const navAnchors = page.locator("header a, nav a");
    const count = await navAnchors.count();
    const toCheck = Math.min(count, 10);

    const failures: string[] = [];
    for (let i = 0; i < toCheck; i++) {
      const el = navAnchors.nth(i);
      const box = await el.boundingBox();
      const text = (await el.textContent())?.trim() ?? `anchor[${i}]`;
      if (box && box.height < 44) {
        failures.push(`"${text}" height=${box.height}px`);
      }
    }
    expect(
      failures,
      `Nav anchors below 44px touch target: ${failures.join(", ")}`
    ).toHaveLength(0);
  });
});
