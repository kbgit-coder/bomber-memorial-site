# Memorial research brief

The brief every research pass follows, human or agent. The output is one dossier per memorial at `research/dossiers/<memorial-id>.json`. Nothing reaches the site except through a dossier (`bun scripts/research/dossier.ts`).

## What done looks like

- Every person named on the memorial is identified, and for each airman: rank, role, age, service number, nationality, fate, burial place, plus CWGC / IBCC / IWM name links where they exist.
- The story is told from sources: the flight (unit, base, purpose, time), what happened, who died and who survived, and what happened after (inquiry findings, families, recovery).
- The memorial is told from sources too: who built it, when it was dedicated, who looks after it now (the custodian), and what the community still does there.
- Every fact is a claim tied to the sources that state it. Facts found in two independent sources are worth far more than facts in one. Search for a second source on purpose.
- Where sources disagree, both versions are recorded. Never pick one quietly.
- What you searched for is logged, including searches that found nothing. "Searched, nothing found" is a result.

## Dossier format

```json
{
  "memorial_id": "short-stirling-r9329",
  "researched_at": "2026-10-28",
  "searches": [{ "query": "Stirling R9329 Cornwood memorial", "useful": true }],
  "sources": [
    { "id": "S1", "url": "https://…", "title": "…", "publisher": "Dartmoor Explorations", "tier": "researched",
      "retrieved": "2026-10-28", "summary": "Two or three sentences in your own words.", "key_details": ["short", "facts"] }
  ],
  "claims": [
    { "id": "C1", "field": "crew.name", "person": "smith-j", "value": "John Albert Smith", "sources": ["S1", "S2"], "quote": "≤25 words from the source" },
    { "id": "C2", "field": "squadron", "value": "149 Squadron", "sources": ["S1"] }
  ],
  "paragraphs": [
    { "section": "narrative", "text": "Plain prose.", "cites": ["C1", "C2"] },
    { "section": "memorial_details", "text": "What the memorial is and where it stands.", "cites": ["C5"] },
    { "section": "community_connection", "text": "…", "cites": ["C9"] }
  ],
  "photos": [{ "url": "https://wmr.iwm.org.uk/sites/default/files/images/…jpg", "credit": "Name, via IWM War Memorials Register", "caption": "…", "source_id": "S3" }],
  "custodian_status": "known | unknown-confirmed | unknown",
  "notes": "Anything a human should know: dead links, doubts, leads not followed."
}
```

- **Fields:** record-level `crash_date, serial_number, aircraft_type, squadron, station, operation_type, operation_target, cause_of_loss, location_name, county, memorial_type, memorial_name, memorial_address, dedication_date, erected_by, inscription, names_on_memorial, died_count, condition, maintainer.organisation, maintainer.website, maintainer.maintainer_type`; per airman (needs `person`, a stable key like `smith-j`) `crew.name, crew.rank, crew.role, crew.age, crew.service_number, crew.nationality, crew.fate, crew.burial_location, crew.cwgc_url, crew.ibcc_url, crew.iwm_name_url, crew.hometown, crew.decorations`.
- **One claim per source group.** If IBCC and CWGC both give an age, either one claim citing both, or two claims (one each). If they differ, two claims; the tool will flag the conflict.
- **Dates** `YYYY-MM-DD`, or `YYYY-MM` / `YYYY` when the day isn't verifiable. **Links** https only.
- **Paragraphs cite claims.** Every sentence must be backed by a cited claim. A paragraph citing a conflicted claim must say so in the text (both versions, attributed) and set `"presents_conflict": true`.
- **Retractions:** where our existing record states something no source supports, or a source contradicts, add `"retractions": [{ "field": "maintainer.organisation", "reason": "…" }]`. Retractable: record-level fields, `local_contacts`, `narrative`, `community_connection`, `crew_summary`, `memorial_details`. Crew names are never retracted; raise doubts in `notes`.
- **Story-only facts:** a fact with no record field (a take-off time, which aircraft each man was on, how the survivor escaped) is a claim with `"field": "event"`. Paragraphs cite it; it never lands in a record field. Never put such a fact in an unrelated field such as `operation_target`.
- **Civilians** killed by the crash are not crew: tell their story in the narrative, citing claims on record fields or the inscription.

## Source tiers

Independence is counted by **publisher**: two pages on one site are one source. A site that copies IWM text is not independent of IWM; say so in `notes` and don't count it as corroboration.

| Tier | Publishers | Use |
|---|---|---|
| official | CWGC, RAF Air Historical Branch, National Archives, London Gazette, Library and Archives Canada service files | Accepted alone |
| institutional | IWM War Memorials Register (incl. our capture in `research/iwm/`), IBCC Losses Database, county rolls of honour, Canadian Virtual War Memorial, Australian War Memorial, Auckland Museum Cenotaph, RAF Museum | Accepted alone; win conflicts against lower tiers |
| researched | War Memorials Online (War Memorials Trust: curated, photographed; best for the memorial itself), dedicated memorial/committee sites, local history societies, regional crash researchers (yorkshire-aircraft.co.uk, aircrashsites, Peak District Air Accident Research, Dartmoor Explorations), Aircrew Remembered, Aviation Safety Network, squadron associations, published books | Accepted alone, best with a second source |
| community | Traces of War, Find a Grave, Geograph, forums, parish newsletters | Corroboration only; never alone |
| secondary | Wikipedia, news articles | Corroboration only; follow their references to the primary |

## Search method

1. Start from what we hold: our record (`public/data/memorials/<id>.json`) and the IWM capture (`research/iwm/<id>.json`, which holds the names on the stone and photos). If the record's IWM link is dead, find the right IWM entry by search.
2. Search the serial, place and "memorial", then the serial with "crash", then each airman's surname with the serial. Look up each airman on IBCC (`losses.internationalbcc.co.uk`) and CWGC.
3. Look for the memorial's custodian: names on the stone ("erected by…"), the parish council, a local society, a church. Moordown (JP137) had its own website, jp137.com, which no register linked to.
4. Read a site's sub-pages, not just its homepage. The story is usually one or two clicks in.
5. Stop when the five points under "What done looks like" are covered, or when two more searches add nothing new.

## Hard rules

- **Never write a fact you didn't read in a source.** No filling gaps from general knowledge, no "likely", no invented human detail. Gaps stay gaps.
- **Never call IWM's JSON:API or any API directly.** Ordinary page fetches only, a few per memorial. The IWM capture is already done for you.
- **No Facebook.** Keith handles that by hand.
- **Quote sparingly** (≤25 words per quote) and summarise in your own words. Local researchers' work is credited and linked, never copied wholesale.
- **Photos:** only IWM photos from the capture (credit the photographer as shown on IWM, "via IWM War Memorials Register"), or Geograph photos (CC BY-SA; credit the photographer and licence). Nothing else.
- **Plain British English.** No "stands as a testament", "serves as a poignant reminder", "nestled", "delve", "rich tapestry", "in the annals of", "little did they know", "paying homage". The build fails on these.
- **Living people:** name committee members or relatives only where a published source names them in that role; never give contact details for private individuals.
