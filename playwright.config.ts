import { defineConfig, devices } from "@playwright/test";

// Staging HTTP basic auth credentials embedded in the origin URL
const STAGING_URL = "https://keith:bmr-staging-2026@staging.bombermemorial.co.uk";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: "list",
  outputDir: "test-results/",
  use: {
    baseURL: STAGING_URL,
    // Basic auth passed via URL — also set httpCredentials for Playwright's
    // built-in basic-auth handling so navigation and fetch both authenticate.
    httpCredentials: {
      username: "keith",
      password: "bmr-staging-2026",
    },
    screenshot: "only-on-failure",
    trace: "off",
    ignoreHTTPSErrors: false,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
