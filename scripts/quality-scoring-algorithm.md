# BMR Quality Scoring Algorithm v1.0

Baseline scoring algorithm for the quality dashboard CSV.
Every score is 0-100 unless otherwise stated.

---

## 1. OVERALL SCORE (0-100)

```
overall = (section_avg * 0.40) + (completeness * 0.35) + (crew_score * 0.15) + (link_score_norm * 0.10)
```

Where:
- `section_avg` = average of narrative, inscription, community, memorial_details content scores
- `completeness` = sum of presence weights (see §5)
- `crew_score` = crew data quality score (see §4)
- `link_score_norm` = normalised link quality (see §6)

---

## 2. SECTION CONTENT SCORES (0-100 each)

Applies to: `narrative`, `inscription`, `community_connection`, `memorial_details`, `crew_summary`

Start at 100, deduct for issues:

| Check | Deduction | Condition |
|-------|-----------|-----------|
| Empty | → 0 | No content or whitespace only |
| Very short | -30 | < 20 characters |
| Short | -15 | 20-49 characters |
| All caps | -20 | > 70% uppercase letters (min 20 letters to check) |
| Excessive brackets | -10 | > 6 bracket/paren characters |
| Raw placeholder | -25 | Contains `(NAME)` or `(NAMES)` |
| Null/undefined text | -15 | Contains literal "undefined" or "null" (not "null and") |
| AI refusal text | -30 | Contains "does not explicitly", "as an ai", "the text does not", "I cannot" |
| Article dump | -20 | Contains `---\n`, `ARTICLE DUMP:`, or `SOURCE URL:` |

Floor: 0. Deductions are cumulative.

---

## 3. SECTION RELEVANCY SCORES (0-100 each)

Applies to: `narrative`, `inscription`, `community_connection`

Measures whether content is actually about THIS specific memorial.

| Check | Points | Condition |
|-------|--------|-----------|
| Base | 50 | Content exists and is non-empty |
| Serial number match | +15 | Content mentions the memorial's serial number |
| Aircraft type match | +10 | Content mentions the aircraft type |
| Location match | +10 | Content mentions any word (>3 chars) from location_name first segment |
| Crew name matches | +5 each, max +15 | Content mentions crew member names |

Cap: 100.

---

## 4. CREW SCORE (0-100)

| Check | Points | Condition |
|-------|--------|-----------|
| No crew | → 0 | Empty crew array |
| Base | 50 | Crew array has entries |
| Rank completeness | + (with_rank / total) * 15 | Crew with rank not "Unknown" or "—" |
| Age completeness | + (with_age / total) * 10 | Crew with age field populated |
| Nationality completeness | + (with_nationality / total) * 10 | Crew with nationality field |
| Role completeness | + (with_role / total) * 10 | Crew with role not "unknown" or empty |
| Service number | + (with_service_no / total) * 5 | Crew with service_number field |
| Duplicate names | -20 | Any duplicate names in crew list |
| Non-person entries | -15 | Names matching regiment/infantry/fusilier/society/school |

Floor: 0. Cap: 100.

---

## 5. COMPLETENESS SCORE (0-100)

Binary presence checks, weighted by importance:

| Field | Weight | Condition |
|-------|--------|-----------|
| narrative | 15 | Non-empty |
| inscription | 10 | Non-empty |
| crew | 15 | Array has entries |
| crash_date | 10 | Non-empty |
| aircraft_type | 10 | Non-empty |
| squadron | 5 | Non-empty |
| serial_number | 5 | Non-empty |
| community_connection | 5 | Non-empty |
| photos (local) | 5 | Array has entries |
| external_links | 5 | external_narratives array has entries |
| station | 5 | Non-empty |
| cause_of_loss | 5 | Non-empty |
| operation_target | 5 | Non-empty |

Sum of weights = 100.

---

## 6. LINK QUALITY SCORE (0-5 per link, normalised to 0-100)

Per-link scoring (0-5 scale from QA standard Gate 9):

| Score | Label | Criteria |
|-------|-------|----------|
| 0 | Dead | HTTP error or domain gone |
| 1 | Problematic | Live but wrong incident, irrelevant, or broken content |
| 2 | Weak | Live, vaguely relevant, no detail |
| 3 | Valid | Live, about this crash, basic info |
| 4 | Strong | Live, about this crash, detailed narrative or key details |
| 5 | Authoritative | Primary source (CWGC, IWM, official archive) with rich detail |

Automated approximation (used in CSV until manual review):

| Check | Points | Condition |
|-------|--------|-----------|
| Base | 2 | Link exists |
| Confirmed live | +1 | `still_live` = true |
| Has summary | +1 | `summary` field > 50 chars |
| Has key details | +1 | `key_details` array non-empty |

Normalisation to 0-100 for overall score:
```
link_score_norm = (avg_link_score / 5) * 100    # if links exist
link_score_norm = 0                               # if no links
```

---

## 7. PHOTO SCORING (counts only, no quality score yet)

Reported as raw counts per category:

| Column | Source |
|--------|--------|
| `photos_local` | `photos` array length — images we host |
| `photos_iwm` | `iwm_photo_urls` array length — IWM images available to download |
| `photo_sources` | Breakdown by `credit`/`source` field (e.g., "Tony Hibberd / War Memorials Online") |

Future: photo quality scoring (resolution, relevance, caption quality).

---

## 8. COMMUNITY CONTENT FLAGS

| Column | Source |
|--------|--------|
| `community_submitted` | "Yes" if `decision_log` or `additional_contributors` exists |
| `additional_contributors` | Semicolon-separated names from `additional_contributors[].name` |

---

## 9. CSV COLUMN ORDER

1. slug, title, data_quality, overall_score
2. Section scores: narrative_score, narrative_issues, narrative_relevancy, inscription_score, inscription_issues, inscription_relevancy, community_score, community_issues, community_relevancy, memorial_details_score, memorial_details_issues, crew_summary_score
3. Photos: photos_local, photos_iwm, photo_sources
4. Crew: crew_total, crew_killed, crew_survived, crew_unknown_fate, crew_with_rank, crew_with_age, crew_with_nationality, crew_with_role, crew_with_service_no, crew_score
5. Links: external_links, source_refs, avg_link_score, dead_links, links_with_summary, links_with_details, link_scores, link_score_norm
6. Completeness: completeness_score, has_narrative, has_inscription, has_crew, has_crash_date, has_aircraft, has_squadron, has_serial, has_station, has_cause, has_operation, has_community_conn
7. Community: community_submitted, additional_contributors
8. Meta: squadron, aircraft_type, county, last_updated

Sorted by overall_score ascending (worst first = highest scraping priority).
