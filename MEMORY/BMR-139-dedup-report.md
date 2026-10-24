# BMR-139 Crew Deduplication Audit

**Run date:** 2026-10-23
**Memorial files scanned:** 416
**Total crew records (non-placeholder):** 1182
**Total duplicate pairs found:** 23

## Summary

| Category | Pairs |
|----------|-------|
| Same service number + matching name (clear duplicate) | 1 |
| Same service number, name differs (SN collision / data error) | 1 |
| Same normalised name, different SN or no SN | 12 |
| Fuzzy name match (≥85% similarity) | 9 |
| **Total** | **23** |

### Interpretation

- **Clear duplicates** (same SN + matching name on different memorials) are the most likely real-world cases of one person commemorated on multiple memorials — flag for human review, do not auto-remove.
- **SN collision** pairs need individual inspection: service numbers were occasionally reused across air forces, or transcription errors occurred.
- **Exact name / fuzzy name** matches without a corroborating SN are lower-confidence — common names (John Smith, William Jones) will generate false positives.

## Clear Duplicates — Same SN + Matching Name

_These are most likely the same person commemorated on multiple memorials. Flag for review._

| Confidence | SN | Name Similarity | Memorial A | Name A | Rank A | Memorial B | Name B | Rank B |
|------------|----|-----------------|------------|--------|--------|------------|--------|--------|
| 0.95 | R/79246 | 1.000 | beetley-bj764 | Raymond Rogers Foltz | F/Sgt | beetley-wellington-bj764 | Raymond Rogers Foltz | F/Sgt |

## Same Service Number, Name Mismatch

_Low name similarity despite matching SN. Could be transcription error, SN reuse, or same person under different name forms._

| Confidence | SN | Name Similarity | Memorial A | Name A | Memorial B | Name B |
|------------|----|-----------------|------------|--------|------------|--------|
| 0.80 | R/119711 | 0.579 | beetley-bj764 | J.R.A. Pambrun | beetley-wellington-bj764 | Joseph Raoul Armand Pambrun |

## Same Normalised Name, Different Memorial

_Matched on name alone. May be coincidental for common names._

| Confidence | Name Sim | Memorial A | Name A | SN A | Memorial B | Name B | SN B |
|------------|----------|------------|--------|------|------------|--------|------|
| 0.80 | 1.000 | balkholme-halifax-mid-air-collision | JOHN SMITH |  | great-rissington-lamb-inn-r1028 | John Smith |  |
| 0.80 | 1.000 | beetley-bj764 | Joseph Albert Delorme | RCAF | beetley-wellington-bj764 | Joseph Albert Delorme | R/101687 |
| 0.80 | 1.000 | brisley-blenheim-v-5455 | John Graham |  | stow-bedon-blenheim-v-5851 | John Graham |  |
| 0.80 | 1.000 | brisley-blenheim-v-5455 | Michael Beaufoy |  | stow-bedon-blenheim-v-5851 | Michael Beaufoy |  |
| 0.80 | 1.000 | brisley-blenheim-v-5455 | Leslie Harrowell |  | stow-bedon-blenheim-v-5851 | Leslie Harrowell |  |
| 0.80 | 1.000 | hatcliffe-top-jb596 | Edward Platt |  | hull-bridge-halifax-mid-air-collision | Edward Platt |  |
| 0.80 | 1.000 | henham-park-multiple-incidents-b-24-42-110033-arizo | Max E. Dailey |  | south-cove-b-24-liberator-42-51 | Max E. Dailey |  |
| 0.80 | 1.000 | mynydd-mawr-aircraft-type-varies | Ernest Andrew Hoagg |  | pen-yr-ole-wen-n9855 | Ernest Andrew Hoagg |  |
| 0.80 | 1.000 | mynydd-mawr-aircraft-type-varies | John Hedgley Lewis |  | pen-yr-ole-wen-n9855 | John Hedgley Lewis |  |
| 0.80 | 1.000 | mynydd-mawr-aircraft-type-varies | Leslie John Hill |  | pen-yr-ole-wen-n9855 | Leslie John Hill |  |
| 0.80 | 1.000 | vickers-wellington-he320 | VICTOR GEORGE BAILEY |  | victor-george-bailey-and-louis-grover-martin-wellington-crash-ford | Victor George Bailey | 1585910 |
| 0.80 | 1.000 | vickers-wellington-he320 | LOUIS GROVER MARTIN |  | victor-george-bailey-and-louis-grover-martin-wellington-crash-ford | Louis Grover Martin | R/182617 |

## Fuzzy Name Matches (≥85% similarity)

_Probable spelling variants, abbreviations, or transcription differences._

| Confidence | Name Sim | Memorial A | Name A | SN A | Memorial B | Name B | SN B |
|------------|----------|------------|--------|------|------------|--------|------|
| 0.70 | 0.933 | cloot-drove-nd981-and-lancaster-me625-mid-air-collision- | Henry Stewart "Jim" Van Raalte | Aus/415220 RAAF | crowland-mid-air-collision-me265-lancaster-nd981 | Henry Stewart (Aus Jim) Van Raalte |  |
| 0.70 | 0.919 | north-rauceby-wellington-t-2834 | Douglas J. Roberts |  | pen-yr-ole-wen-n9855 | Douglas John Roberts |  |
| 0.70 | 0.897 | mynydd-mawr-aircraft-type-varies | Leslie John Hill |  | north-rauceby-wellington-t-2834 | Leslie J. Hill |  |
| 0.70 | 0.897 | north-rauceby-wellington-t-2834 | Leslie J. Hill |  | pen-yr-ole-wen-n9855 | Leslie John Hill |  |
| 0.70 | 0.889 | cheviot-hills-memorial-multiple-aircraft-co | E. L. Brown |  | hindolveston-bk440 | E. W. Brown |  |
| 0.70 | 0.880 | nailstone-b-17-fortress-43-377 | Ralph W. Franke |  | tattershall-1-w4175 | Ralph Frank |  |
| 0.70 | 0.857 | balkholme-halifax-mid-air-collision | William Davidon |  | pen-yr-ole-wen-n9855 | William Gavin |  |
| 0.70 | 0.857 | mynydd-mawr-aircraft-type-varies | R. Davies |  | waithe-lancaster-mid-air-collision | Davies |  |
| 0.70 | 0.850 | bacton-hudson-v-9097 | John MacGillivray |  | colsterdale-jb926 | John James MacGillivray | R/143002 |

---
_Generated by scripts/crew-dedup-audit.py — BMR-139_