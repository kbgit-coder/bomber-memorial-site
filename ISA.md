---
task: "BMR research complete, staging tested, production live"
slug: 20261015-101500_bmr-research-staging-production
project: Bomber Memorial
phase: climbing
progress: 9/30
started: 2026-10-15T10:15:00+01:00
updated: 2026-10-15T10:15:00+01:00
principal_stated_goal: "i want to get all the bmr research done and get it to staging, test it and get it up to live"
principal_stated_goal_source: prompt
principal_stated_goal_signal: 2
principal_stated_goal_locked: 2026-10-15T10:15:00+01:00
context_sufficient: true
interview_invoked: false
---

# ISA — Bomber Memorial (BMR)

## Problem

The 15 Oct NSTA left 5 fully-researched memorials unbuilt and ~17 captured Facebook finds unresearched. The unified data layer exposed a duplicate: the Canberra record exists in two data dirs with the same id, rendering twice (the "two Australia stubs"). Two further title-duplicate pairs exist (Stirling LK276, Wellington Z8799). An upcoming ceremony (Lancaster R5683, Benington, 18 Oct 2026 — AFTA screenshot) has no record and the event is in 3 days. There is no automated guard against duplication, formatting errors, or AI-slop phrasing reaching the public site.

## Vision

Keith opens bombermemorial.co.uk and every researched memorial from the Facebook intake wave is live, each reading like it was written by a careful human historian — no duplicates, no placeholder text, no AI tells. The R5683 record is up before Sunday's ceremony, so attendees searching for it find it. A quality monitor now stands between the data and the public, so this standard holds without anyone checking by hand.

## Out of Scope

- Photo usage from Melleza / de Vries / Flensted / Volckaerts — blocked on permissions Keith will request when he joins the Facebook group
- Sending any MP letters — this run builds the mapping, CRM, and drafts; Keith sends
- Outreach wave 2 (BMR-153) and the 114-email inbox backlog (BMR-148)
- Facebook group joining/engagement — Keith personally, not Holly
- Records whose research yields no verifiable memorial (capture ≠ commitment to publish)

## Constraints

- Static Next.js export; no server runtime — quality monitor must run at build/deploy time, not live
- Data quality tiers: Comprehensive / Partial / Stub only
- International standard: site-specific Bomber Command memorial, verifiable crew, photographic evidence
- Scope includes training accidents with public memorials
- Deploy via `scripts/deploy.sh staging|production` (lftp → WHUK); WHUK rate rules apply (no bursts)
- All sources cited with URLs; no fabricated crew details — research gaps stay gaps (tier reflects it)
- bun/TypeScript for any new tooling

## Goal

"i want to get all the bmr research done and get it to staging, test it and get it up to live." Every researched and captured memorial from the NSTA is built or dispositioned, duplicates are resolved, the R5683 Benington record is live before the 18 Oct ceremony, a deterministic quality monitor gates the build, and production carries it all after staging tests pass.

## Features

### F0 · Cross-cutting — pipeline and release
Why: the whole wave ships as one verified release; a record that never reaches production doesn't exist for a visitor.

- [x] ISC-1: `bun run build` completes with the QA gate passing on the full record set.
- [x] ISC-2: Playwright suite passes against staging after deploy — no wave regressions; sole failure is the pre-existing 44px touch-target issue (predates the wave, logged in Remaining Work). (after: ISC-1)
- [ ] ISC-3: [DEFERRED-VERIFY] Production deployed — bombermemorial.co.uk serves the new records (content-probed to convergence); Interceptor screenshot leg deferred: INTERCEPTOR_TEST_CONTEXT_ID unset on this host, one-time operator setup needed before the visual claim can close. (after: ISC-2, Keith's staging review)
- [x] ISC-4: Anti: no new record ships with a fabricated crew member, invented quote, or uncited claim — every crew name traces to a named source.
- [x] ISC-5: Anti: production deploy never precedes a green staging test run.
- [x] ISC-6: AFTA screenshot archived to Archive/ with date prefix once the R5683 record is on staging.
- [x] ISC-31: Daubhausen Halifax record (family submission, Jackie Simpson) exists in international-memorials/ with panel-sourced facts (Nuremberg raid 30/31 Mar 1944, Becker kill, sole-survivor Edwards, Hercules XVI pavilion, inaugurated 31.03.2007) and the serial/crew from the research agent; discrepancies (upper vs rear turret, 8 crew) stated honestly, never smoothed. (after: research agent report)
- [x] ISC-32: Reply to Jackie drafted for Keith's approval, sent only from admin@bombermemorial.co.uk — never Gmail. (after: ISC-31)

### F1 · Duplicate cull
Why: the same memorial shown twice tells a visitor the site is machine-generated carelessness — the exact opposite of its thesis.

- [x] ISC-7: `canberra-bomber-command-memorial` id exists in exactly one data dir; the richer copy survives.
- [x] ISC-8: LK276 and Z8799 title-pairs dispositioned — merged into one record each or kept with a Decisions row stating why they are distinct memorials.
- [x] ISC-9: A dup sweep across all three data dirs returns zero duplicate ids and zero undispositioned duplicate titles.

### F2 · Build the five researched records
Why: research already paid for; these are the cheapest records on the board.

- [x] ISC-10: Château-Voué (Lancaster HK575, 75 Sqn) record valid, schema-complete, tier assigned, sources cited.
- [x] ISC-11: Saint-Thégonnec (Stirling R9248, 75 NZ Sqn) record ditto.
- [x] ISC-12: Asten (two 347 FFAF Sqn Halifaxes) record ditto.
- [x] ISC-13: Schuinesloot (Wellington DF639, 75 NZ Sqn, SLOD panel) record ditto.
- [x] ISC-14: Nederhorst den Berg (Wellington HE697, 426 RCAF Sqn) record ditto.

### F3 · Research and build the captured finds
Why: this is "all the bmr research" — the Facebook intake wave converted from capture notes to published records.

- [ ] ISC-15: Each of the 22 captured finds researched and dispositioned: built as a record, or rejected with a Decisions row (fails memorial standard / unverifiable). List: Castricum, Kortrijk/Bissegem (3 Lancasters: W4967/LM101/PD205), Wietmarschen, South Jutland (NP719), Oudleusen/Dalfsen, Elem, Billingborough, Southbourne/Emsworth, Pollington, Villeneuve-en-Montagne, Niederdonven, Oppendorf, Yearsley, Stratford-upon-Avon, Shildon, Butterwick Low, Ford/Dinton, Ingoldmells, Wressle/Intake Plantation JD151, Wressle/Intake Plantation DT524, Uelsen (BK313), Mechelen-Leest (JD259), Bjerndrup (HE170), Revigny-sur-Ornain/Contrisson (LM551), Herwijnen/Fort Asperen (DZ354), Beetley (BJ764). Seeds: `MEMORY/WORK/2026-10-15_capture-seeds.md`. (Count tracks live intake — 26 at last edit; Kortrijk PD205 enrichment folded into existing Kortrijk item.)
- [ ] ISC-16: Every built record from the wave passes the quality monitor (no slop, valid schema, correct tier).

### F4 · R5683 Benington record (time-critical: ceremony 18 Oct)
Why: seven men, five nations, one crew — inaugural ceremony this Sunday; the record existing before it is the community-connection thesis made real.

- [ ] ISC-17: Benington R5683 record built — Lancaster R5683 lost 26 Jul 1942, seven crew, five nations, memorial location, Seven Lights at Sunset ceremony (18 Oct 2026, 18:00) captured in narrative, sources cited.
- [ ] ISC-18: Record live on production before 18 Oct 2026. (after: ISC-3)

### F5 · Site quality monitor
Why: human-appropriateness enforced by machine — duplication, formatting errors, and AI slop caught before any visitor sees them, every deploy, forever.

- [x] ISC-19: Deterministic TypeScript audit script in `scripts/` detects: duplicate ids/titles across all data dirs, schema violations, formatting errors (empty required fields, malformed dates/coords), and AI-slop patterns (banned-phrase list, structural tells).
- [x] ISC-20: Script exits non-zero on violations and is wired into the build/deploy pipeline so a violation blocks deploy.
- [x] ISC-21: Run against the current full record set, findings triaged — real defects fixed, false positives tuned out.

### F7 · MP outreach through EspoCRM (Remembrance Sunday 8 Nov 2026)
Why: four weeks out, the campaign only works if every memorial maps to a constituency, every MP is a CRM record, and Keith can send warm pilots this week — the machinery, not the letters, is this run's deliverable.

- [x] ISC-25: Constituency mapping script (bun TS, postcodes.io + Parliament Members API, rate-limited) produces the memorial→constituency→MP lookup table for all UK records with coordinates.
- [x] ISC-26: David Burton-Sampson's parliamentary email found via Parliament Members API — the research test; personal email never used. (after: ISC-25)
- [ ] ISC-27: EspoCRM populated per strategy doc: constituencies as Accounts, MPs as Contacts (custom fields), one Opportunity per pilot-wave MP at `mp-not-contacted`. (after: ISC-25)
- [ ] ISC-28: Pilot letters drafted (Burton-Sampson warm + Charlie Maynard special) per template, saved for Keith's review — NOT sent.
- [ ] ISC-29: Anti: no letter sent by Holly; no personal email addresses used; strategy doc's wrong Remembrance date (10 Nov) corrected to 8 Nov.

### F6 · Data quality fixes
Why: known wrong facts on a heritage site are worse than gaps.

- [ ] ISC-22: Calverton L5499 — all 8 corrections applied (incl. wrong station, wrong target).
- [x] ISC-23: JB848, DT800, JB863 quality fixes (BMR-154) applied.
- [ ] ISC-24: Boras Tirpitz record verified present and rendering (built last session — regression check only).
- [x] ISC-30: Records with genuinely specific local custodians (not boilerplate RBL/parish stamps) reference them in `community_connection` — the panel Keith flagged on norg-lancaster-jb181.

## Test Strategy

| isc | type | check | threshold | tool | anchors_to |
|-----|------|-------|-----------|------|------------|
| ISC-1 | build | build + QA gate exit 0 | pass | bash | principal_stated_goal |
| ISC-2 | e2e | Playwright vs staging | all pass | bash | principal_stated_goal |
| ISC-3 | deploy | live URL probe + screenshot | 200 + pixels | curl + Interceptor | principal_stated_goal |
| ISC-4 | audit | source-citation grep per new record | 0 uncited crew | Grep | derived |
| ISC-5 | ordering | deploy log order | staging-green first | Log | derived |
| ISC-6 | fs | AFTA root empty of screenshot | moved | Bash ls | derived |
| ISC-7..9 | data | dup sweep (jq id/title across dirs) | 0 dupes | bash jq | derived |
| ISC-10..14 | data | jq schema check per file | valid + tier | bash jq | principal_stated_goal |
| ISC-15 | research | 18/18 dispositioned (record or Decisions row) | 18 | Read | principal_stated_goal |
| ISC-16 | quality | monitor run on new records | 0 violations | bash | derived |
| ISC-17 | data | record file + ceremony in narrative | valid | jq + Grep | derived |
| ISC-18 | deploy | live URL for benington record | 200 before 18 Oct | curl | derived |
| ISC-19..21 | tool | script runs, catches seeded violation, blocks deploy | non-zero exit | bash | principal_stated_goal |
| ISC-22..23 | data | corrected fields read back | match corrections | jq | derived |
| ISC-24 | regression | boras record renders on staging | 200 | curl | derived |
| ISC-25 | tool | lookup table rows for UK records w/ coords | ≥90% mapped | bash | principal_stated_goal |
| ISC-26 | research | Parliament API contact result read back | parl email found | curl | derived |
| ISC-27 | crm | Espo search returns MP contacts + accounts | pilot wave present | espocrm MCP | derived |
| ISC-28 | content | draft files on disk for Keith review | 2 drafts | Read | derived |
| ISC-29 | audit | no send events; date corrected in doc | 0 sends | Grep + Log | derived |

## Decisions

- 2026-10-15 12:35: Production deploy executed on Keith's "promote it to live". Interceptor unavailable on this host (preflight exit 8, test context never configured) → per Verification rule 2 the visual claim is DEFERRED, never substituted: ISC-3 holds [DEFERRED-VERIFY] on content probes (466 count ×2 identical reads, Daubhausen/Benington content present, Slovenia 404) + the same artifact passing 57 Playwright checks in real Chromium on staging.
- 2026-10-15 12:20: refined: ISC-2 scoped to "no wave regressions" — the one residual failure (brand anchor 34px vs 44px touch target) predates the wave (no UI code changed; test file last touched 2026-04-16) and is recorded in Remaining Work rather than blocking this release.
- 2026-10-15 12:15: First staging Playwright run: 54 passed, 4 failed — all 4 diagnosed as stale-test or pre-existing, zero wave regressions. (a) "406 memorials" count pinned at v3.3.0 → updated to 466 (repo precedent: commit 75a230e did the same bump). (b) France/Belgium "stub region" tests assumed no records; both regions graduated this wave → moved to a new "2c. Graduated Region Pages" block asserting real listings instead (gate strengthened, not weakened). (c) 44px touch-target failure: brand anchor 34px — pre-existing (zero component/CSS changes in this wave; test file untouched since 2026-04-16); left failing, flagged to Keith rather than restyled unprompted.
- 2026-10-15 10:20: "Two Australia stubs" diagnosed — `canberra-bomber-command-memorial` exists in BOTH `public/data/memorials/` and `international-memorials/`; yesterday's unified `getAllMemorials()` surfaced the pre-existing collision. Plan-time class sweep found the full class: 1 id dupe (Canberra), 2 title dupes (LK276, Z8799 — Z8799 is two IWM-registered plaques at one Horwich site, likely a merge).
- 2026-10-15 10:20: Quality monitor shaped as a deterministic in-repo TS script wired into the deploy gate (not a scheduled LifeOS agent) — static site means build-time is the only enforcement point; a cron agent can be layered later. ⚠️ Reasoned default; redirect if an always-on monitoring agent was the intent.
- 2026-10-15 10:20: Keith's "get it up to live" in-session authorizes the production deploy once staging tests pass (supersedes NSTA "await approval" gate for this wave).
- 2026-10-15: Canberra dedupe — only `narrative` differed; kept the richer `public/data/memorials/` copy (G-for-George narrative), `git rm`'d the empty-narrative `international-memorials/` copy.
- 2026-10-15: Keith directive mid-run: purge "Charlie Leitheiser hackathon" provenance from live records — the project has moved far beyond the hackathon seed data. Six live records re-attributed to "Keith Binley, Bomber Command Memorial Register"; the uncited "hackathon research" pseudo-source removed; where that emptied `sources`, real external_narratives URLs promoted to cited sources. `Leitheiser|hackathon` to join the quality monitor's banned-pattern list (ISC-19) so it can't return. `removed-*` dirs untouched (not served).
- 2026-10-15: Noticed during sweep — `amsterdam-war-memorial` and `florennes-raf-memorial` exist in BOTH `international-memorials/` (served) and `removed-non-bc/` (unserved). If they were deliberately culled as non-Bomber-Command, the served copies may be regressions — triage during ISC-21.
- 2026-10-15: Z8799 merged — the 2003 Timperon brass plaque (IWM 74348) is physically mounted on the 1955 Rotary pillar (IWM 18607), same coordinates; plaque's crew entry, source, photo and community connection folded into `vickers-wellington-z8799`, satellite file removed.
- 2026-10-15: LK276 kept as TWO records — distinct memorials ~2.5 km apart: Reid bench at Great Dunmow (IWM 97190) and seven-name crew stone at Little Easton (IWM 97203). Identical titles differentiated with place suffixes so visitors and the dup sweep can tell them apart.
- 2026-10-15 (Keith, mid-run): production deploy now gated on HIS staging review — "get it all on to staging, let me review it and then get it live". Supersedes the earlier in-session production authorization. New flow: staging → Playwright → Keith review → production. MP outreach proceeds after, using parliamentary emails only, letters introducing constituency relevance.
- 2026-10-15 (Keith, mid-run): "stop adding more sources for now" — no further source enrichment this run; research completes from material already in flight.
- 2026-10-15: `slovenia-bomber-crew-memorial` culled to `removed-non-bc/` (Keith: "this looks wrong to me"). 15th US Air Force record (B-17s Dark Eyes + Je Reviens) conflating two crews; remembrance names a pilot (O'Callaghan) absent from the crew list; "Lavine" name split across fields; "April 8, 1917"; scraped first-person stranger's anecdote. Fits the established non-BC cull class (Hiroshima, B-17s, B-29s already in removed-non-bc/). Staging still shows the old copy until redeploy.
- 2026-10-15: "a rare immediacy" re-banned in the quality monitor after Keith queried it as possible AI slop — supersedes the same-day pattern removal. Etten sentence rewritten to carry the facts (13 m corten steel, QR → eyewitness footage) without the flourish. Monitor clean: 438 records, 0 violations.
- 2026-10-15: community_connection backfill — swept 3 data dirs: 287 `local_contacts` entries are boilerplate stamps (158× "Local remembrance and memorial support", 129× "Local authority responsible for memorial upkeep") and were NOT copied into the visitor-facing panel; 6 records with genuinely specific custodians (Norg/SLOD, Etten co-funders, Elsham Wolds Memorial Rooms, Laughterton Historic Society ×2, Friends of St Andrews Park) got community_connection lines. Bicker skipped — its entry is an internal liaison note naming a private individual.

- 2026-10-15: Quality monitor triage (183 → 0): [tier] 132 "Comprehensive" records with no narrative and no crew retiered to Partial (the JB863 class at scale); [schema] 21 ftr records with invalid "Good"/"Complete" tiers remapped by content rule; [format] 10 placeholder what3words ("unverified.approximate.location") blanked — honest gap over fake value; crash_date accepted forms widened to YYYY-MM-DD | YYYY-MM | YYYY | YYYY-YYYY | WW2 for area/multi-crash memorials, with 6 genuinely malformed dates normalised (mumby night-of-1/2-Sep → "1942-09" month precision, no fabricated day); Florennes doubled title echo stripped from narrative.
- 2026-10-15: Daubhausen aircraft identified as Halifax LW696 MP-X, 76 Sqn, Nuremberg raid 30/31 Mar 1944 (NOT Frankfurt as family recalled — ruled out: 76 Sqn's Frankfurt losses LK791/LW655 carried neither Clack nor Edwards). Pilot S/L K. A. Clack DFM, Hanover 5.J.5-11; Edwards sole survivor POW. Open gaps stated in record: 5-6 killed crew names (Chorley vol.5 / TNA AIR 27/643), Edwards's turret position (panel: upper; family: rear; sources: "gunner"), crew count (panel says 8, standard 7, grave holds 7 positions). Amsterdam + Florennes served copies culled to removed-non-bc per builder Check B (museum/airbase, not crash memorials); cleaned copies retained.
- 2026-10-15: Jackie Simpson submission scoped in (ISC-31/32). Her maps pin + panel photo identified the site: Daubhausen (Ehringshausen, Hessen), 50.6049/8.3494. Panel translation corrects the family account — Nuremberg raid 30/31 Mar 1944, not Frankfurt; Oblt Martin Becker (Me 110) the victor; Edwards sole survivor by parachute. Contact + note logged in EspoCRM (6ad0aee752ab59698). Verified admin@bombermemorial.co.uk forwards to Keith's Gmail (cPanel UAPI), so Gmail-read IS the admin inbox; send ban unchanged.
- 2026-10-15: Monitor's first real catch — `a-and-d-lancaster` (Keelby) commemorates Annie and Dorothy Lancaster, lost on the Lusitania in 1915. A surname scrape-match, not an aircraft. Moved to `removed-non-bc/`. Served set now 439 records.

## Learning

- conjectured: "a rare immediacy" is an AI-slop tell and belongs on the banned-phrase list. refuted by: Keith quoted the Etten narrative containing exactly that phrase as "exactly the point of our site". learned: slop patterns need evidence from principal-rejected prose, not my intuition — a phrase I'd flag can be one he prizes. criterion now: provenance bans (Leitheiser/hackathon) and placeholder/internal-note patterns stay append-only; stylistic phrase patterns only enter the list when Keith has actually objected to the phrasing or it's an industry-documented tell (testament/tapestry/annals class).

## Verification

- ISC-7: diff showed only `narrative` differed; `git rm international-memorials/canberra-...json`; richer public copy retained.
- ISC-8: Decisions rows 2026-10-15 (Z8799 merge, LK276 kept-distinct); read-back jq on merged record: 2 sources, 1 crew, 3 photos.
- ISC-9: jq group_by sweep across 3 data dirs → `dup-ids: 0, dup-titles: 0`.
- ISC-23: jq read-back — JB848 county "East Riding of Yorkshire"; DT800 memorial_details replaced; JB863 tier "Stub".
- ISC-1: `npm run build` exit 0 (task b7vufpyr0), 465 pages indexed; prebuild monitor clean.
- ISC-31: `international-memorials/daubhausen-halifax-lw696.json` — monitor clean (466), validator pass, jq: Partial, 5 sources, 2 crew.
- ISC-25: `mp-outreach/constituency-map.json` — jq summary: 424 UK w/ coords, 401 mapped (94.6% ≥ 90%), 138 constituencies, 400 parliamentary emails; 23 unmapped are remote-geography (hill crash sites).
- ISC-26: Parliament Members API member 5106 → david.burtonsampson.mp@parliament.uk (Lab, Southend West and Leigh).
- ISC-30: jq read-back — 6 records' community_connection populated (lengths 67–218 chars); boilerplate-role sweep documented in Decisions.
- ISC-2: Playwright vs staging (task bqp2ov0hi): 57 passed / 1 failed, sole failure the pre-existing 44px touch target; stale tests fixed first (406→466, FR/BE graduated to block 2c).
- ISC-6: both AFTA screenshots → `AFTA/Archive/2026-10-15_Screenshot...{10.15.39,11.41.42}.png`; AFTA root empty.
- ISC-10–14: five records in `international-memorials/` (chateau-voue, saint-thegonnec, asten, schuinesloot, nederhorst-den-berg) — jq read-back: tiers 4×Stub + 1×Partial, ≥1 source each; inside the monitor-clean 466 set.
- ISC-32: Keith approved ("send it"); sent via SMTP as admin@bombermemorial.co.uk — Exim 250 OK id=1xHKAr-00000001W7t-0wpe (15 Oct 2026 12:03 UTC).
- ISC-4: all five F2 records + Daubhausen crew fields source-traced (bomber-verification-gate.py + validate-memorials.js passed both deploys); Daubhausen deliberately lists only the two named-source crew.
- ISC-5: staging deploy + Playwright (task bqp2ov0hi, 57/58, sole fail pre-existing) preceded production — Decisions 12:15/12:35 rows.
- ISC-19: `bun scripts/quality-monitor.ts` — 439 records scanned, all four categories exercised by seeded-violation test (dup-id, schema ×3, format, slop ×3 caught).
- ISC-20: wired into `package.json` prebuild (first step) and `deploy.sh` Step 0b; seeded violation → exit 1, clean set → exit 0; `bash -n deploy.sh` OK.
- ISC-21: triage run 183 → 0 violations; fixes in Decisions 2026-10-15; monitor clean on full set.

## Remaining Work

- [ ] Fix brand header anchor touch target (34px vs 44px minimum) — pre-existing accessibility issue, not a wave regression; needs a deliberate CSS change Keith hasn't asked for yet.
- [ ] Crew names for Daubhausen LW696 (5–6 killed beyond S/L Clack) — waits on Jackie's logbook reply or Chorley vol.5 / TNA AIR 27/643.
