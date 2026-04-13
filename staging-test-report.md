# BMR Staging Test Report — 2026-04-13 06:15

**Site:** https://staging.bombermemorial.co.uk
**Duration:** 532s (8.9 min)
**Pages tested:** 434 memorials + 6 special pages

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total memorial pages** | 434 | 100% |
| **All checks passed** | 266 | 61.3% |
| **Some checks failed** | 168 | 38.7% |
| **Connection errors** | 0 | 0.0% |

## Special Pages

- ✅ **Homepage** — PASS
- ✅ **Insights Dashboard** — PASS
- ✅ **Quality Dashboard** — PASS
- ✅ **Contact** — PASS
- ✅ **FAQ** — PASS
- ❌ **Site Terms** — FAIL

## Per-Check Pass Rates

| Check | Passed | Failed | Rate |
|-------|--------|--------|------|
| content_length | 434 | 0 | 100.0% |
| has_h1 | 434 | 0 | 100.0% |
| has_location | 429 | 5 | 98.8% |
| has_sources | 434 | 0 | 100.0% |
| has_title_tag | 434 | 0 | 100.0% |
| inscription_section | 434 | 0 | 100.0% |
| memorial_type_shown | 272 | 162 | 62.7% |
| no_all_caps_inscription | 434 | 0 | 100.0% |
| no_error_text | 434 | 0 | 100.0% |
| shows_quality_badge | 427 | 7 | 98.4% |
| status_200 | 434 | 0 | 100.0% |
| the_memorial_section | 434 | 0 | 100.0% |

## Data Quality Distribution

| Quality Level | Count | Percentage |
|---------------|-------|------------|
| Good | 294 | 67.7% |
| Partial | 133 | 30.6% |

## Data Field Coverage

| Field | Has Data | Missing | Coverage |
|-------|----------|---------|----------|
| coordinates | 434 | 0 | 100.0% |
| county | 427 | 7 | 98.4% |
| crash_date | 396 | 38 | 91.2% |
| squadron | 301 | 133 | 69.4% |
| inscription | 278 | 156 | 64.1% |
| crew | 189 | 245 | 43.5% |
| narrative | 188 | 246 | 43.3% |
| photos | 78 | 356 | 18.0% |

## Enrichment Improvement (Before → After)

*Baseline: 218 production memorials + 335 bare stubs (coords/photos only)*

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Stubs at 'Stub' quality | 355 | 0 | **-355** |
| Pages at 'Good' quality | ~218 | 294 | **+76** |
| Pages with inscription | ~218 | 278 | **+60** |
| Pages with county | ~218 | 427 | **+209** |
| Pages with crash date | ~150 | 396 | **+246** |
| Pages with squadron | ~80 | 301 | **+221** |

## Failure Analysis

**Most common failure reasons:**

- `memorial_type_shown`: 162 pages
- `shows_quality_badge`: 7 pages
- `has_location`: 5 pages

**Failed pages (168):**

- `amsterdam-war-memorial`: shows_quality_badge
- `annesley-eh988`: memorial_type_shown
- `ardleigh-dt800`: memorial_type_shown
- `bacton-hudson-v-9097`: memorial_type_shown
- `balkholme-halifax-mid-air-collision`: memorial_type_shown
- `bassingham-fen-eh977`: memorial_type_shown
- `bawdeswell-kb364`: memorial_type_shown
- `beetley-bj764`: memorial_type_shown
- `bellingdon-pb475`: memorial_type_shown
- `bicker-nd820`: memorial_type_shown
- `blankney-mid-air-collision-lm130`: memorial_type_shown
- `bleasby-1-lancaster-r-5703`: memorial_type_shown
- `bleasby-2-lancaster-w-4232`: memorial_type_shown
- `bleasby-3-lancaster-r-5698`: memorial_type_shown
- `bleasby-4-jb132`: memorial_type_shown
- `bleasby-5-wellington-r-1014`: memorial_type_shown
- `bleasby-6-wellington-r-1212`: memorial_type_shown
- `blyth-green-1-he818`: memorial_type_shown
- `blyth-green-2-na581`: memorial_type_shown
- `blythburgh-liberator-42-110007-`: memorial_type_shown
- `bodicote-bk517`: memorial_type_shown
- `bransby-at129`: memorial_type_shown
- `bressingham-bk770`: memorial_type_shown
- `brettenham-stirling-n-3756`: memorial_type_shown
- `brigstock-dv361`: memorial_type_shown
- `brisley-blenheim-v-5455`: memorial_type_shown
- `briston-wellington-w-5444`: memorial_type_shown
- `brocklesby-me442`: memorial_type_shown
- `buckden-pike-wellington-n-2848`: memorial_type_shown
- `bunny-church-hj767`: memorial_type_shown
- `burn-chapel-578-sqn-panels`: memorial_type_shown
- `bury-lv971`: memorial_type_shown
- `california-gap-wellington-z-8397`: memorial_type_shown
- `calverton-fairey-battle-l5499`: memorial_type_shown
- `canberra-bomber-command-memorial`: has_location, shows_quality_badge
- `carleton-rode-b-24-mid-air-collision`: memorial_type_shown
- `carreg-goch-wellington-r1465-r1465`: memorial_type_shown
- `cawston-1-hampden-p-4405`: memorial_type_shown
- `caythorpe-heath-lj450`: memorial_type_shown
- `caythorpe-station-pb812`: memorial_type_shown
- `chediston-dv930`: memorial_type_shown
- `cheviot-hills-memorial-multiple-aircraft-co`: memorial_type_shown
- `cheviot-hills-wellington-z1078-z1078`: memorial_type_shown
- `chippenham-bk784`: memorial_type_shown
- `chipping-warden-1-lp286`: memorial_type_shown
- `chipping-warden-2-wellington-r-1037`: memorial_type_shown
- `clenchwarton-multi-crash-memorial-hr832-mosquito-dd717-blenheim-z-7278`: memorial_type_shown
- `colchester-dv177`: memorial_type_shown
- `colsterdale-jb926`: memorial_type_shown
- `cotgrave-place-wellington-w-5365`: memorial_type_shown
- `coveney-double-lancaster-crash-ll667-and-lancaster-ll867`: memorial_type_shown
- `crews-of-lancasters-jb678-and-jb674`: memorial_type_shown
- `crowland-mid-air-collision-me265-lancaster-nd981`: memorial_type_shown
- `desborough-an534`: memorial_type_shown
- `dry-doddington-pb432`: memorial_type_shown
- `earith-mid-air-collision-w7467-and-hurricane-v6865`: memorial_type_shown
- `easby-moor-hudson-n-7294`: memorial_type_shown
- `east-stockwith-me323`: memorial_type_shown
- `elsham-wolds-jd386`: memorial_type_shown
- `elvetham-consolidated-liberat`: memorial_type_shown
- `farnsfield-halifax-mz519`: memorial_type_shown
- `felixstowe-docks-hampden-p-1340`: memorial_type_shown
- `felixstowe-lm258`: memorial_type_shown
- `florennes-raf-memorial`: has_location, shows_quality_badge
- `foulsham-mid-air-collision-beaufighter-v-8715-a`: memorial_type_shown
- `garrowby-hill-area-various-bomber-comma`: memorial_type_shown, shows_quality_badge
- `garvestone-b-24-liberator-42-95`: memorial_type_shown
- `godmanchester-n3703`: memorial_type_shown
- `gonalston-lancaster-l7578`: memorial_type_shown
- `great-ashfield-385th-bomb-group`: memorial_type_shown
- `great-carrs-ll505-s-for-sugar-`: memorial_type_shown
- `great-dun-fell-blea-crag-bb310`: memorial_type_shown
- `great-gransden-hayley-wood-jb219`: memorial_type_shown
- `great-rissington-lamb-inn-r1028`: memorial_type_shown
- `great-whernside-dt578`: memorial_type_shown
- `greensted-juxta-ongar-pb512`: memorial_type_shown
- `grimston-hill-wellington-ms471`: memorial_type_shown
- `halam-lancaster-ed823`: memorial_type_shown
- `halifax-area-dk192`: memorial_type_shown
- `hamburg-bombing-memorial`: has_location, shows_quality_badge
- `hameldown-x3054`: memorial_type_shown
- `hatcliffe-top-jb596`: memorial_type_shown
- `hempnall-dz587`: memorial_type_shown
- `henham-park-multiple-incidents-b-24-42-110033-arizo`: memorial_type_shown
- `high-ercall-area-various-mosquito-wel`: memorial_type_shown
- `higher-shelf-stones-boeing-rb-29a-superf`: memorial_type_shown
- `hindolveston-bk440`: memorial_type_shown
- `hiroshima-peace-memorial`: has_location, shows_quality_badge
- `holmpton-avro-manchester-l-75`: memorial_type_shown
- `honeybourne-area-z2639`: memorial_type_shown
- `houghton-st-martin-pb351`: memorial_type_shown
- `hoveringham-1-jb125`: memorial_type_shown
- `hoveringham-2-lm308`: memorial_type_shown
- `hull-bridge-halifax-mid-air-collision`: memorial_type_shown
- `kessingland-b-24-liberator-41-28`: memorial_type_shown
- `kinder-scout-1-w5719`: memorial_type_shown
- `kinder-scout-2-aircraft-polish-crew`: memorial_type_shown
- `laughterton-1-eh940`: memorial_type_shown
- `laughterton-2-lm292`: memorial_type_shown
- `laxton-lp841`: memorial_type_shown
- `leicester-pa269`: memorial_type_shown
- `little-atwick-hx351`: memorial_type_shown
- `little-yeldham-hf471`: memorial_type_shown
- `long-bennington-lm311`: memorial_type_shown
- `low-bradley-hz251`: memorial_type_shown
- `manea-lk789`: memorial_type_shown
- `marchington-wellington-mk-x`: memorial_type_shown
- `melton-mowbray-ln281`: memorial_type_shown
- `moordown-jp137`: memorial_type_shown
- `mumby-bb216`: memorial_type_shown
- `mundford-mk773`: memorial_type_shown
- `nailstone-b-17-fortress-43-377`: memorial_type_shown
- `near-sheldon-village-w5795`: memorial_type_shown
- `north-kelsey-moor-lancaster-r-5672`: memorial_type_shown
- `north-lopham-mid-air-collision-b-17-44-6137-the-abo`: memorial_type_shown
- `north-rauceby-wellington-t-2834`: memorial_type_shown
- `north-thoresby-ed583`: memorial_type_shown
- `old-leake-wellington-w-5667`: memorial_type_shown
- `pidley-dk300`: memorial_type_shown
- `plungar-ed549`: memorial_type_shown
- `pocklington-ed393`: memorial_type_shown
- `redenhall-two-b-24-crashes-b-24-42-50790-little`: memorial_type_shown
- `reedham-mid-air-collision-b-17-42-37963-and-b-`: memorial_type_shown
- `reigate-hill-b-17-flying-fortress`: memorial_type_shown
- `revesby-nd415`: memorial_type_shown
- `rumburgh-b-24-liberator-42-51`: memorial_type_shown
- `rushup-edge-hampden-mk-i`: memorial_type_shown
- `ryhope-sunderland-barton-vc`: memorial_type_shown
- `salford-pb304`: memorial_type_shown
- `salthouse-lm720`: memorial_type_shown
- `scallows-hall-dv270`: memorial_type_shown
- `scawton-near-helmsley-halifax-free-french-`: memorial_type_shown
- `scredington-ed439`: memorial_type_shown
- `screveton-1-wellington-w-4103`: memorial_type_shown
- `sheffield-b-17-flying-fortress`: memorial_type_shown
- `sibsey-lancaster-details-on`: memorial_type_shown
- `skegness-x3027`: memorial_type_shown
- `somersham-x3811`: memorial_type_shown
- `south-cove-b-24-liberator-42-51`: memorial_type_shown
- `south-kyme-lk954`: memorial_type_shown
- `southrepps-hampden-x-3023`: memorial_type_shown
- `staunton-in-the-vale-wellington-w-4270`: memorial_type_shown
- `stoke-holy-cross-blenheim-z-7304`: memorial_type_shown
- `stoke-rochford-hall-lm719`: memorial_type_shown
- `stow-bedon-blenheim-v-5851`: memorial_type_shown
- `sturton-by-stow-lancaster-r-5676`: memorial_type_shown
- `tattershall-1-w4175`: memorial_type_shown
- `tattershall-2-pb422`: memorial_type_shown
- `thorpe-morieux-1-b-17-42-3108`: memorial_type_shown
- `thorpe-morieux-2-b-17-42-38085`: memorial_type_shown
- `three-barrows-ln775`: memorial_type_shown
- `tigers-marsh-b-17-flying-fortress`: memorial_type_shown
- `timberlands-fen-jb534`: memorial_type_shown
- `tinian-north-field-memorial`: has_location, shows_quality_badge
- `tintwistle-knarr-pa411`: memorial_type_shown
- `ulceby-cross-pb476`: memorial_type_shown
- `ulceby-lancaster-mid-air-collision`: memorial_type_shown
- `upwaltham-dv382`: memorial_type_shown
- `vautour-mitchell-crash-site`: memorial_type_shown
- `waithe-lancaster-mid-air-collision`: memorial_type_shown
- `walton-on-the-naze-rg475`: memorial_type_shown
- `weasenham-st-peter-three-crashes-commemorated-fl206-boston-al285`: memorial_type_shown
- `west-okement-valley-pb4y-1-liberator-639`: memorial_type_shown
- `westborough-lm619`: memorial_type_shown
- `withcall-hk194`: memorial_type_shown
- `wollaston-l7380`: memorial_type_shown
- `wrangle-b-24j-liberator-42-9`: memorial_type_shown
- `yelling-jb477`: memorial_type_shown

---
*Generated 2026-04-13 06:23:58 by BMR staging-full-test.py*