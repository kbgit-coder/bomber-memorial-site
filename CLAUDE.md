# Bomber Memorial — Project Rules

## Purpose

The Bomber Command Memorial Register — a community heritage site cataloguing WW2 Bomber Command crash sites and memorials across the UK and internationally. Each record captures location, aircraft, crew, narrative, and the human story behind the memorial.

Live at [bombermemorial.co.uk](https://bombermemorial.co.uk). Non-commercial heritage research. Current record count: ~406 memorials.

## Owner

Keith Binley (KB). Holly (DA) builds and maintains. Shorthand: **BMR**.

## Stack

- **Next.js 14** — static export (`output: 'export'`). No server runtime; everything is SSG.
- **TypeScript 5** across all app code and scripts
- **MapLibre GL 5** — interactive map (`/map` route)
- **Pagefind** — client-side full-text search, built in `postbuild` against the `out/` HTML
- **Tailwind CSS 3** — styling
- **Recharts** — insights/analytics charts (`/insights`, `/qa-dashboard`)
- **PostHog** (EU cloud, `eu.i.posthog.com`) — page analytics, event tracking. Key hardcoded in `src/components/PostHogProvider.tsx` — this is intentional for a public static site.
- **Playwright** — all tests in `tests/`, targeting staging
- **Deploy:** `lftp` FTP mirror to WHUK cPanel (`django.ukhosted.net`). Script at `scripts/deploy.sh`. Credentials in `.env.deploy` (gitignored).

### Key file locations

| What | Where |
|------|-------|
| Memorial JSON records | `public/data/memorials/*.json` (406 files) |
| Squadron data | `public/data/squadrons/` |
| Governance data | `public/data/governance/` |
| Type definitions | `src/lib/types.ts` |
| Data access functions | `src/lib/data.ts` |
| Prebuild scripts | `scripts/` (Node.js + Python 3) |
| Playwright tests | `tests/staging-validation.spec.ts` |
| Playwright config | `playwright.config.ts` |

## Data Rules

- **All memorial data in `public/data/memorials/` is WW2 heritage research** — non-personal, non-commercial, publicly sourced (CWGC, IWM, Aircrew Remembered, local archives). It is safe to read and modify in dev.
- **Master data lives on NAS** at `/mnt/nas2/Projects/BomberMemorial/data/master/memorials/`. The repo copies are build inputs, not the source of truth for enrichment.
- **Personal contact data (PII) is stripped before build** by `scripts/strip-internal-fields.js`. The prebuild hook removes `contact_email`, `contact_phone`, `contact_name` from `local_contacts[]` and `maintainer` objects. Never add PII fields to repo JSON that bypasses this strip.
- **Internal audit fields** (`location_confidence.verification_notes`, `.sources`, `.score`) are also stripped by the same script. They may exist in master data but must not appear in the repo's `public/` copies.
- **Bomber verification gate (GATE 0):** Every memorial must be a genuine WW2 bomber crash memorial. Aircraft names (Halifax, Lancaster, Wellington, etc.) also occur as place names and surnames — the gate in `scripts/bomber-verification-gate.py` catches false positives. Run it manually if adding new records outside the normal ingest pipeline. False positives land in `rejected-memorials/`.
- Do not ingest data from non-heritage commercial sources without KB approval.

## Credentials

- **FTP deploy credentials** — `.env.deploy` in repo root (gitignored). Format: `FTP_HOST`, `FTP_PROD_USER`, `FTP_PROD_PASS`, `FTP_STAGING_USER`, `FTP_STAGING_PASS`. See `scripts/deploy.sh` header.
- **Staging HTTP auth** — hardcoded in `playwright.config.ts` (`keith` / `bmr-staging-2026`). Staging is intentionally open (no `.htpasswd` by default); the credentials are for Playwright's `httpCredentials` only.
- **PostHog key** — hardcoded in `PostHogProvider.tsx`. Public write-only key for a static site — this is correct. Do not treat it as a secret.
- **WHUK cPanel** — credentials in `~/.claude/.env` (`WHUK_*`) and `~/.claude/CREDENTIALS/cpanel.env`. See OPERATIONAL_RULES for WHUK cPanel gotchas: serial HTTPS-only requests with ≥2s spacing; never retry 401/403/429 (cPHulk will block the IP).
- Never call enrichment APIs (IWM, CWGC, What3Words, external scraping) without KB approval — these may be rate-limited, paid, or ethically sensitive for bulk use.

## Build Pipeline

The `npm run build` sequence matters — do not skip steps:

1. **`prebuild`** (auto-runs before `next build`):
   - `clean-narratives.js` — normalises narrative text
   - `filter-narrative-depth.js` — removes shallow narratives
   - `section-relevancy-scorer.py` — scores and trims irrelevant sections
   - `strip-internal-fields.js` — removes PII and internal audit fields (HARD GATE)
   - `generate-sitemap.js` — rebuilds `public/sitemap.xml`
   - `validate-consistency.js` — cross-checks data consistency
2. **`next build`** — static export to `out/`
3. **`postbuild`** — Pagefind indexes `out/**/*.html`

**For deploy**, always use `scripts/deploy.sh staging|production` — it runs the bomber verification gate, schema validator, section relevancy gate, crew cleanup, build, QA scan, and crew DB sync before FTP mirror.

The inscription validator (`scripts/inscription-validator.py`) is intentionally excluded from the deploy pipeline — it takes ~87 minutes. Run manually before major releases.

## Definition of Done

- All Playwright tests pass against staging: `npx playwright test`
- `npm run build` completes without errors (all prebuild gates pass)
- Bomber verification gate passes: `python3 scripts/bomber-verification-gate.py`
- JSON schema validation passes: `node scripts/validate-memorials.js`
- QA scan passes: `python3 scripts/qa-scan.py`
- Visual spot-check of affected memorial pages via Interceptor (real Chrome)
- PostHog events firing on page load and key interactions (check EU PostHog dashboard)
- No PII fields present in `out/` after build (verify with `scripts/strip-internal-fields.js --dry-run` if in doubt)

## Deploy

```bash
# Staging (safe — auto-deploys after tests)
./scripts/deploy.sh staging

# Production (prompts for git tag after success)
./scripts/deploy.sh production
```

Both require `.env.deploy` present. Production deploy creates a git release tag — always tag production releases.

## Escalation

If a rule blocks the task and there is no permitted alternative, stop and surface the conflict explicitly. Do not loop or guess. Specifically:

- If adding memorial records that may be false positives (town/surname ambiguity), stop and verify — do not bulk-add and rely on the gate to catch them.
- If an enrichment run would call a paid or rate-limited API (CWGC, IWM, W3W, AI generation), stop and confirm with KB first.
- If PII appears in source data, strip it before committing — do not commit contact details to the repo.

## Code Conventions

- **No server runtime** — this is a fully static site. All data loading uses `fs.readFileSync` at build time in `src/lib/data.ts`. Do not introduce API routes or server actions.
- **Memorial slugs** are the JSON filename without `.json` extension (e.g. `annesley-eh988`). The slug is also the `id` field inside the JSON.
- **Data quality field** — each memorial has `data_quality: "Partial" | "Good" | "Verified"`. The quality score (0–100) lives in a separate computed field. See `scripts/quality-scoring-algorithm.md` for the scoring logic.
- **Schema** — memorial JSON schema at `scripts/memorial-schema.json`. Validated by `scripts/validate-memorials.js`. Add new fields to the schema before using them in the app.
- **Prebuild scripts are idempotent** — all scripts must produce the same output when run multiple times. The deploy script verifies this for section-relevancy and crew-cleanup.
- **TypeScript** — strict mode. Types in `src/lib/types.ts`. Do not use `any` except where Playwright or third-party libraries force it.
- **Tailwind** — utility classes only, no custom CSS files beyond `globals.css`.
- **Naming** — kebab-case for JSON files and slugs; PascalCase for React components; camelCase for TypeScript functions and variables.
- **Routes**: `src/app/memorial/[slug]/`, `src/app/squadron/[slug]/`, `src/app/region/[country]/`, `src/app/map/`, `src/app/search/`, `src/app/insights/`, `src/app/qa-dashboard/`.
- **Sandcastle** — `.sandcastle/main.mts` is an AI-hero sandcastle runner. Do not modify without understanding the impact on the batch enrichment pipeline.
