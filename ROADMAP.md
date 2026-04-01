# Bomber Command Memorial Register — Quarterly Release Roadmap

Releases every 3 months. Each drop includes new data, features, and outreach follow-ups accumulated since the last release.

---

## Q2 2026 — 1 July 2026

### Data Enrichment
- [ ] Extract structured crew arrays from remaining 48 memorials with full_narrative content
- [ ] Clean up 475 scraped photo captions (replace filename-derived captions with descriptive text)
- [ ] Migrate all photos to source/credit model (currently only Farnsfield + Elsham done)
- [ ] Remove duplicate Calverton entry (calverton-fairey-battle-l5499 vs l-5499)
- [ ] Fix 12 files using "WW2" instead of specific crash dates
- [ ] Standardise data_quality "Good" to "Complete"
- [ ] Add crew_summary to 5 Complete files missing it
- [ ] Process any new outreach responses (photos, corrections, local knowledge)

### New Features
- [ ] YouTube/video embed support — new `videos` field in schema, embed section on memorial page
- [ ] Kirkley memorial: embed Francis Guildea's YouTube film (youtu.be/parota2XbR0 at 15:36)
- [ ] War Memorials Online systematic photo scrape for remaining 127 memorials without photos
- [ ] Scrape additional heritage sources (IWM, RAF Museum) for photos where available

### Outreach
- [ ] Follow up on CWGC Director call (Rich Hills) — data partnership
- [ ] Follow up on Gransden Society (Martin Davies) response
- [ ] Follow up on Brigstock Historical Society response
- [ ] Process any material from Bob Collis (Lowestoft)
- [ ] Process any digital files from Martin Grocock (Blyth Historical Society)
- [ ] Second wave outreach to remaining 100+ parish councils not yet contacted

### Site Improvements
- [ ] Update featured memorials on homepage (refresh top 5 based on new enrichment)
- [ ] Review and improve About page with project stats
- [ ] Add "Recently Updated" section or badge to show active development

---

## Q3 2026 — 1 October 2026

### Data
- [ ] Target: 150+ memorials at Complete quality (currently 55)
- [ ] Target: 150+ memorials with photos (currently 81)
- [ ] International memorial enrichment (Charlie's 48 entries)
- [ ] CWGC data integration (if partnership agreed from Q2 call)

### Features
- [ ] County-level pages (e.g. /county/nottinghamshire) with map
- [ ] Interactive map on homepage showing all memorials
- [ ] Print-friendly memorial pages (for researchers, families)
- [ ] RSS feed for new/updated memorials

### Outreach
- [ ] Third wave outreach — target heritage societies directly (not just parish councils)
- [ ] Contact aircrewremembered.com about formal data partnership
- [ ] Contact RAF Museum about badge/crest usage permissions
- [ ] Approach local newspapers for coverage of the project

---

## Q4 2026 — 1 January 2027

### Data
- [ ] Target: 200+ memorials at Complete quality
- [ ] Target: 200+ memorials with photos
- [ ] Full crew data for every Complete memorial
- [ ] Historical context sections (squadron histories, operations)

### Features
- [ ] Search by crew name (find a relative's memorial)
- [ ] Search by date (what happened on this day)
- [ ] Memorial comparison (side-by-side records)
- [ ] Contributor leaderboard (acknowledge community contributions)

### Outreach
- [ ] Annual remembrance push (November timing)
- [ ] Social media presence (if warranted by content volume)
- [ ] Schools outreach pack (educational resource)

---

## Q1 2027 — 1 April 2027

### Review
- [ ] Full year review — what worked, what didn't
- [ ] Data quality audit (repeat of April 2026 audit)
- [ ] Site performance and SEO review
- [ ] Contributor feedback collection
- [ ] Roadmap refresh for 2027-28

---

## Release Process

Each quarterly drop:
1. Data enrichment and cleanup (weeks 1-10)
2. Feature development (weeks 1-10, parallel)
3. Full rebuild and test (week 11)
4. Deploy to production (week 12)
5. Update Outline wiki, commit to Gitea + GitHub
6. Send update email to active contributors
7. Update featured memorials on homepage
