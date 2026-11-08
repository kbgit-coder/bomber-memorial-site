import { test, expect } from "@playwright/test";

// Phone-width layout guard. Founding bug (8 Nov 2026): the header nav ran 663px wide on
// a 390px phone, so every page scrolled sideways and half the crew table was off-screen.
test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 3 });

const PAGES = [
  "/",
  "/memorial/halam-lancaster-ed823",
  "/memorial/hampden-p1294",
  "/region/united-kingdom",
  "/squadron",
  "/squadron/93rd-bomb-group",
  "/memorial/arenig-fawr-b-17-42-3124",
  "/search",
  "/stories",
  "/insights",
  "/about",
];

for (const path of PAGES) {
  test(`no sideways scroll at 390px: ${path}`, async ({ page }) => {
    await page.goto(path, { waitUntil: "networkidle" });
    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(scrollWidth, `${path} is ${scrollWidth}px wide on a ${clientWidth}px screen`).toBeLessThanOrEqual(clientWidth);
  });
}

test("menu button opens every nav link on a phone", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("header nav.hidden")).toBeHidden();
  await page.getByRole("button", { name: "Open menu" }).click();
  const menu = page.locator("#mobile-nav");
  for (const label of ["Home", "Regions", "Squadrons", "Search", "Stories", "Insights", "About"]) {
    await expect(menu.getByRole("link", { name: label })).toBeVisible();
  }
  await menu.getByRole("link", { name: "Stories" }).click();
  await expect(page).toHaveURL(/\/stories/);
});

test("crew shows as cards on a phone", async ({ page }) => {
  await page.goto("/memorial/hampden-p1294");
  await expect(page.locator("table").first()).toBeHidden();
  await expect(page.getByText("George Donald Kerr").first()).toBeVisible();
});
