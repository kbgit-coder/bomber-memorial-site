# BMR Inscription Validation Report — 2026-04-13 07:26

**Duration:** 4597s | **Memorials checked:** 278 | **Mode:** APPLIED

## Summary

| Severity | Count |
|----------|-------|
| critical | 6 |
| high | 9 |
| medium | 148 |
| low | 20 |
| clean | 95 |

## Issue Categories

- **CREW MISSING**: 81
- **COMMUNITY CONNECTION MISSING**: 67
- **SQUADRON MISSING**: 36
- **MULTIPLE EVENTS**: 36
- **FTR MEMORIAL**: 10
- **CRASH DATE MISSING**: 9
- **Claude query failed**: 7
- **SERIAL NUMBER MISSING**: 7
- **CIVILIAN CASUALTIES NOT RECORDED**: 6
- **CRASH DATE MISMATCH**: 3
- **AIRCRAFT TYPE MISSING**: 2

## Corrections Applied: 27

## CRITICAL — Requires Immediate Action (6)

### 617-squadron-aircrew-derwent-valley
**617 Squadron Aircrew - Derwent Valley**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event

### avro-lancaster-jb284
**Avro Lancaster JB284**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site

### handley-page-halifax-lv905
**Handley Page Halifax LV905**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site

### handley-page-halifax-lw579
**Handley Page Halifax LW579**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site

### sergeant-t-h-skelton-and-crew-of-avro-lancaster-w4938
**Avro Lancaster W4938**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site

### vickers-wellington-he702
**Vickers Wellington HE702**
- FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site

## HIGH — Data Corrections Needed (9)

**avro-lancaster-lm616** — Avro Lancaster LM616
- CIVILIAN CASUALTIES NOT RECORDED: Inscription explicitly states both crew and civilians were killed in the crash
- COMMUNITY CONNECTION MISSING: Aircraft crashed into West End Farm Great Offley killing both crew and local civilians indicating direct community impact
  - Fix `community_connection`: `` → `Inscription explicitly states both crew and civilians were killed in the crash` (confidence: high)
  - Fix `community_connection`: `` → `Aircraft crashed into West End Farm Great Offley killing both crew and local civilians indicating direct community impact` (confidence: medium)

**handley-page-halifax-jb798** — Handley Page Halifax JB798
- CIVILIAN CASUALTIES NOT RECORDED: Civilian parishioners lost their lives when the aircraft struck the church spire and fell on nearby buildings
- COMMUNITY CONNECTION MISSING: Spire demolished; extensive damage to church and adjoining buildings; civilian parishioners and RAAF crew killed; restoration begun 10 May 1949; church re-dedicated 11 December 1950
  - Fix `community_connection`: `` → `Civilian parishioners lost their lives when the aircraft struck the church spire and fell on nearby buildings` (confidence: high)
  - Fix `community_connection`: `` → `Spire demolished; extensive damage to church and adjoining buildings; civilian parishioners and RAAF crew killed; restoration begun 10 May 1949; church re-dedicated 11 December 1950` (confidence: medium)

**handley-page-halifax-rt922** — Handley Page Halifax RT922
- CIVILIAN CASUALTIES NOT RECORDED: Passengers described explicitly as Press Photographers; inscription states crew and passengers were ALL KILLED
- COMMUNITY CONNECTION MISSING: Mission to airdrop supplies to the snow-bound communities of Grindon and the surrounding areas; cairn erected 1999 by Leek Branch of Royal Air Force Association, supported by Staffordshire Moorlands District Council and Grindon Parish Council
  - Fix `community_connection`: `` → `Passengers described explicitly as Press Photographers; inscription states crew and passengers were ALL KILLED` (confidence: high)
  - Fix `community_connection`: `` → `Mission to airdrop supplies to the snow-bound communities of Grindon and the surrounding areas; cairn erected 1999 by Leek Branch of Royal Air Force Association, supported by Staffordshire Moorlands District Council and Grindon Parish Council` (confidence: medium)

**handley-page-hampden-p4399** — Handley Page Hampden P4399
- CREW MISSING: inscription has 3 crew names but crew list is empty
- CIVILIAN CASUALTIES NOT RECORDED: 3 civilians of Dartford killed in the crash
- COMMUNITY CONNECTION MISSING: 3 civilians of Dartford were killed in the crash alongside 3 RAF aircrew; memorial dedicated by the Leader of Dartford Borough Council
  - Fix `crew`: `0 crew` → `3 crew (extract from inscription)` (confidence: medium)
  - Fix `community_connection`: `` → `3 civilians of Dartford killed in the crash` (confidence: high)
  - Fix `community_connection`: `` → `3 civilians of Dartford were killed in the crash alongside 3 RAF aircrew; memorial dedicated by the Leader of Dartford Borough Council` (confidence: medium)

**lincoln-high-school-ww2-aircrash-memorial** — Lincoln High School WW2 Aircrash Memorial
- CRASH DATE MISMATCH: DB has 1941-07-26, inscription says 1941-07-22. Reasoning: "ON JULY 22 1941 AT THE GREESTONES" — this date is explicitly stated and applies to the events at the Greestones and Greestone Stairs including the four airmen
- CREW MISSING: inscription has 4 crew names but crew list is empty
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `1941-07-26` → `1941-07-22` (confidence: high)
  - Fix `crew`: `0 crew` → `4 crew (extract from inscription)` (confidence: medium)

**vickers-wellington-t2520** — Vickers Wellington T2520
- CRASH DATE MISMATCH: DB has 1940-12-09, inscription says 1940-12-10. Reasoning: CRASHED HERE 10.12.1940
  - Fix `crash_date`: `1940-12-09` → `1940-12-10` (confidence: high)

**vickers-wellington-x3790** — Vickers Wellington X3790
- CIVILIAN CASUALTIES NOT RECORDED: Winslow residents and evacuees are explicitly named among those who lost their lives alongside aircrew
- COMMUNITY CONNECTION MISSING: Winslow residents and evacuees lost their lives in the crash alongside aircrew, indicating a significant local civilian impact
  - Fix `community_connection`: `` → `Winslow residents and evacuees are explicitly named among those who lost their lives alongside aircrew` (confidence: high)
  - Fix `community_connection`: `` → `Winslow residents and evacuees lost their lives in the crash alongside aircrew, indicating a significant local civilian impact` (confidence: medium)

**wellington-bomber-n2980** — Wellington Bomber N2980
- CRASH DATE MISMATCH: DB has 1940-12-18, inscription says 1940-12-31. Reasoning: it ditched on Loch Ness during a snow storm on New Years Eve
- COMMUNITY CONNECTION MISSING: Plaque erected by the Loch Ness Wellington Assoc. Ltd on 60th anniversary of Battle of Heligoland Bight (18th Dec 1989); unveiled by pupils from Drumsmittal School; manufactured by Newmill Castings Ltd, Elgin. Second plaque dedicated June 29 2002 regarding sonar discovery.
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `1940-12-18` → `1940-12-31` (confidence: high)
  - Fix `community_connection`: `` → `Plaque erected by the Loch Ness Wellington Assoc. Ltd on 60th anniversary of Battle of Heligoland Bight (18th Dec 1989); unveiled by pupils from Drumsmittal School; manufactured by Newmill Castings Ltd, Elgin. Second plaque dedicated June 29 2002 regarding sonar discovery.` (confidence: medium)

**wellington-t2962** — Wellington T2962
- CIVILIAN CASUALTIES NOT RECORDED: Civilian names are present in the inscription alongside military names; all died in Llangrove as a result of the crash. Exact civilian names not recoverable from transcription as provided.
- COMMUNITY CONNECTION MISSING: Both military personnel and civilians died in the local community of Llangrove as a direct result of the crash, indicating significant community impact.
  - Fix `community_connection`: `` → `Civilian names are present in the inscription alongside military names; all died in Llangrove as a result of the crash. Exact civilian names not recoverable from transcription as provided.` (confidence: high)
  - Fix `community_connection`: `` → `Both military personnel and civilians died in the local community of Llangrove as a direct result of the crash, indicating significant community impact.` (confidence: medium)

## MEDIUM — Missing Data (148)

- **305th-bomb-group-b17-flying-fortress-42-97578-crash**: SQUADRON MISSING: inscription mentions 422nd Squadron, 305th Bomb Group; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **aircrew-of-wellington-r1801**: CREW MISSING: inscription has 3 crew names but crew list is empty
- **australian-aircrew-lost-over-europe**: CREW MISSING: inscription has 5397 crew names but crew list is empty; FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site
- **avro-lancaster-dv361**: COMMUNITY CONNECTION MISSING: null
- **avro-lancaster-jb286**: COMMUNITY CONNECTION MISSING: null
- **avro-lancaster-jb477**: SQUADRON MISSING: inscription mentions R.C.A.F. from Gransden Lodge; CREW MISSING: inscription has 7 crew names but crew list is empty
- **avro-lancaster-jb534-damaged-early-2025-currently-removed-for-repair**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **avro-lancaster-kb879**: COMMUNITY CONNECTION MISSING: Memorial erected in 1999 by the Sandon & District Royal British Legion
- **avro-lancaster-ll686**: COMMUNITY CONNECTION MISSING: Memorial erected by the villagers of Aldborough to commemorate the 50th anniversary of the crew's sacrifice; the pilot deliberately steered away from the village before coming down on Studforth Hill
- **avro-lancaster-lm311**: SQUADRON MISSING: inscription mentions 467 RAAF Squadron; COMMUNITY CONNECTION MISSING: null
- **avro-lancaster-lm719**: SQUADRON MISSING: inscription mentions 1653 HCU, RAF North Luffenham; CREW MISSING: inscription has 7 crew names but crew list is empty
- **avro-lancaster-nd820**: COMMUNITY CONNECTION MISSING: null
- **avro-lancaster-pb355**: COMMUNITY CONNECTION MISSING: Nine road names are listed, some of which may honour individuals (Callon Drive, Essenhigh Drive, Moore Close, Rees Close, Thompson Close, Varey Road, Bourne Close) and one references a squadron (Squadron Drive), suggesting a memorial street-naming scheme, but no individuals are explicitly identified as crew members in the inscription text
- **avro-lancaster-pb366-cross**: CRASH DATE MISSING: inscription states 1944-12-24
- **avro-lancaster-pb366-pillar**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Aircraft crashed within the community of Great Paxton
- **avro-lancaster-pb475**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **avro-lancaster-pb565**: SQUADRON MISSING: inscription mentions 1667 HCU
- **avro-lancaster-r5489**: CRASH DATE MISSING: inscription states 1942-08-16; SQUADRON MISSING: inscription mentions 44 (Rhodesia) Squadron, Waddington
- **avro-lancaster-r5694**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **avro-lancaster-w4319**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **avro-lancasters-me473-and-nd572**: CREW MISSING: inscription has 2 crew names but crew list is empty
- **b-24h-liberator-usaaf-crew-tablet**: SQUADRON MISSING: inscription mentions 392nd BG, USAAF; COMMUNITY CONNECTION MISSING: Local community members aided survivors; inscription explicitly thanks those who aided the survivors in the common cause of freedom
- **burn-chapel-578-sqn-panels**: CREW MISSING: inscription has 219 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: 219 aircrew killed, 79 taken as POW, 45 aircraft lost during squadron service January 1944 to March 1945 operating from RAF Burn
- **canadian-crew-of-wellington-bomber**: SERIAL NUMBER MISSING: inscription mentions LN181; CREW MISSING: inscription has 8 crew names but crew list is empty
- **chipping-norton-oxford-and-wellington-crews-ww2**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **crew-of-28-otu-wellington-mf200**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **crew-of-hampden-p5303**: SQUADRON MISSING: inscription mentions No.16 Operational Training Unit, RAF Upper Heyford
- **crew-of-handley-page-hampden-ae381-2**: SERIAL NUMBER MISSING: inscription mentions AE381
- **crew-of-lancaster-ll811-bq-j-and-their-comrades**: COMMUNITY CONNECTION MISSING: North Killingholme is explicitly named as the departure airfield for the first D-Day strike aircraft; the inscription states this operation 'put North Killingholme on the map'; FTR MEMORIAL: Claude identifies this as a Failed to Return memorial, not a local crash site
- **crew-of-lancaster-nd-714-60-t**: SERIAL NUMBER MISSING: inscription mentions ND714
- **crew-of-lincoln-bomber-re373-of-97-squadron**: AIRCRAFT TYPE MISSING: inscription mentions Lincoln Bomber
- **crew-of-wellington-bomber-ln482**: SQUADRON MISSING: inscription mentions 11 OTU; CREW MISSING: inscription has 6 crew names but crew list is empty
- **crew-of-wellington-ln281**: COMMUNITY CONNECTION MISSING: One named survivor is commemorated on the memorial, described as the only survivor who suffered serious injuries
- **crew-of-wellington-w5444**: CREW MISSING: inscription has 3 crew names but crew list is empty
- **crew-of-whitley-mk-5-no-1489**: SERIAL NUMBER MISSING: inscription mentions 1489
- **crews-of-lancasters-me625-and-nd981**: COMMUNITY CONNECTION MISSING: null
- **flight-lieutenant-l-cumberworth-and-flying-officer-j-easdale-handley-page-halifa**: SQUADRON MISSING: inscription mentions Royal Air Force
- **flying-officer-j-j-bregman-and-crew-of-avro-lancaster-pb171**: CRASH DATE MISSING: inscription states 1944-07-19; SQUADRON MISSING: inscription mentions BH (squadron code derived from aircraft identifier BH-K)
- **halifax-bomber-ll459**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **hampden-p1294**: COMMUNITY CONNECTION MISSING: Crew attempted to land burning and badly damaged aircraft without injury to others; all crew were killed when the tree added an additional obstacle to the fatal crash in the field opposite
- **handley-page-halifax-dg358**: COMMUNITY CONNECTION MISSING: Bodies of the airmen rested at Bwlch-y-ffridd Institute on the evening of 23rd January 1944, indicating local community received and cared for the deceased
- **handley-page-halifax-eb199**: SQUADRON MISSING: inscription mentions 1664 HCU
- **handley-page-halifax-eb203**: SQUADRON MISSING: inscription mentions 1664 HCU (RCAF) Dishforth; CREW MISSING: inscription has 7 crew names but crew list is empty
- **handley-page-halifax-jb863**: COMMUNITY CONNECTION MISSING: Squadron based at Elvington; memorial erected near crash site
- **handley-page-halifax-jp137**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **handley-page-halifax-jp190**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **handley-page-halifax-lk789**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **handley-page-halifax-lk794**: COMMUNITY CONNECTION MISSING: Pilot deliberately manoeuvred to avoid the heavily populated areas of Reading and Maidenhead before the aircraft exploded
- **handley-page-halifax-lk844**: COMMUNITY CONNECTION MISSING: 7 cherry trees planted for each member of the crew and 1300 crocus bulbs were planted along with more daffodils around the stone
- **handley-page-halifax-lk878**: SQUADRON MISSING: inscription mentions 1659 H.C.U. Topcliffe; CREW MISSING: inscription has 9 crew names but crew list is empty
- **handley-page-halifax-lk930**: SQUADRON MISSING: inscription mentions No 1664 HCU Squadron
- **handley-page-halifax-lk954-2019**: CREW MISSING: inscription has 8 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **handley-page-halifax-lk954**: COMMUNITY CONNECTION MISSING: null; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **handley-page-halifax-ll356**: CRASH DATE MISSING: inscription states 1944-04-27; SQUADRON MISSING: inscription mentions No. 138 (SD) Squadron RAF Tempsford
- **handley-page-halifax-ll505**: SQUADRON MISSING: inscription mentions No. 1659 HCU Topcliffe; CREW MISSING: inscription has 8 crew names but crew list is empty
- **handley-page-halifax-lv836**: COMMUNITY CONNECTION MISSING: null
- **handley-page-halifax-lv955**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **handley-page-halifax-lw478**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **handley-page-halifax-lw598-ow-j-johnnie**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **handley-page-halifax-lw598**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **handley-page-halifax-mz454**: COMMUNITY CONNECTION MISSING: null
- **handley-page-halifax-mz538**: COMMUNITY CONNECTION MISSING: Aircraft hit trees close to the village of Alne causing an explosion; the altar window of a local church was damaged and restored with new stained glass in 1958; pilot F/O Joseph R.J.M. Desmaris DFC credited with saving massive casualties
- **handley-page-halifax-mz920**: SQUADRON MISSING: inscription mentions 434; CREW MISSING: inscription has 5 crew names but crew list is empty
- **handley-page-halifax-na612**: COMMUNITY CONNECTION MISSING: They are remembered by the people of Helperby and Brafferton
- **handley-page-halifax-nr179**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **handley-page-halifax-nr287**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: The memorial plaque was originally attached to the tree against which the Halifax came to rest, approximately half a mile from Scawton church. After the tree fell, the plaque was relocated to the church porch at Scawton, establishing a lasting community connection.
- **handley-page-halifax-r9438**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **handley-page-halifax-rg475-and-local-men-and-women-who-served-in-the-royal-air-f**: CREW MISSING: inscription has 8 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Memorial dedicated to all local men and women who have served in the Royal Air Force, in addition to commemorating the Halifax crew
- **handley-page-halifax-s-jp201-and-ll137**: CREW MISSING: inscription has 13 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: The memorial was erected by the local parish community, indicating a community connection to the crash site over their parish
- **handley-page-halifax-s-ll186-and-ll296-raf-tiree**: SQUADRON MISSING: inscription mentions Coastal Command
- **handley-page-halifax-w7823**: CREW MISSING: inscription has 10 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **handley-page-hampden-at219**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **handley-page-hampden-l4173**: CREW MISSING: inscription has 2 crew names but crew list is empty
- **handley-page-hampden-p4313**: CREW MISSING: inscription has 3 crew names but crew list is empty
- **handley-page-hampden-p4392**: CRASH DATE MISSING: inscription states 1940-09-28; CREW MISSING: inscription has 1 crew names but crew list is empty
- **henham-park-multiple-incidents-b-24-42-110033-arizo**: SERIAL NUMBER MISSING: inscription mentions 42-110033 and 41-28590; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **holmpton-avro-manchester-l-75**: SERIAL NUMBER MISSING: inscription mentions L7523
- **hp-hampden-x3027-plaque**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **hull-bridge-halifax-mid-air-collision**: COMMUNITY CONNECTION MISSING: null
- **lancaster-bombers-ed730-and-nd327**: CREW MISSING: inscription has 14 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **lancaster-r5672**: CREW MISSING: inscription has 9 crew names but crew list is empty
- **leicester-pa269**: COMMUNITY CONNECTION MISSING: Aircraft crashed on school site in Leicester
- **location-via-iwm-handley-page-halifax**: CRASH DATE MISSING: inscription states 1944-03-26; SQUADRON MISSING: inscription mentions No. 425 Squadron Royal Canadian Air Force
- **normanton-on-soar-bomber-crash**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **north-kelsey-moor-lancaster-r-5672**: SERIAL NUMBER MISSING: inscription mentions R5672
- **pilot-officer-h-e-rath-and-sergeant-k-m-miegel**: COMMUNITY CONNECTION MISSING: A poem titled 'My Rose' attributed to Lillian Brindley is inscribed on the memorial, indicating a personal or community connection to the crew members
- **pilot-officers-b-w-jobling-and-f-w-weston**: CREW MISSING: inscription has 2 crew names but crew list is empty
- **polish-aircrew-avro-lancaster-pa269**: COMMUNITY CONNECTION MISSING: Aircraft crashed onto a school site in Leicester; plaque erected at the crash location
- **raf-wellington-aircrew**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **rcaf-crew-of-raf-wellington-he821-and-pilot-officer-h-s-keeton**: SQUADRON MISSING: inscription mentions RAF Gamston (base/station only, no squadron number stated); MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **revesby-nd415**: COMMUNITY CONNECTION MISSING: The aeroplane crashed within the parish itself, and the crew are commemorated alongside local parish men on the same memorial, indicating a direct community connection to the crash site.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **royal-canadian-air-force-crew-vickers-wellington-bk387**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **ryhope-sunderland-barton-vc**: COMMUNITY CONNECTION MISSING: Barton crash-landed south-west of Hollycarrside specifically to avoid Ryhope, sacrificing his life to protect the community
- **scredington-ed439**: COMMUNITY CONNECTION MISSING: null
- **sergeant-a-j-smith-and-short-stirling-ef352**: CRASH DATE MISSING: inscription states 1943-10-22
- **sergeant-t-butterley-and-sergeant-a-priest-vickers-wellington-r1538**: SQUADRON MISSING: inscription mentions 28 O.T.U. R.A.F. WYMESWOLD
- **short-stirling-bk784**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **short-stirling-eh940-and-avro-lancaster-lm292**: CREW MISSING: inscription has 7 crew names but crew list is empty; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **short-stirling-lj450**: SQUADRON MISSING: inscription mentions 1654 HBCU
- **short-stirling-lj930**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **short-stirling-lk116**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **short-stirling-lk276**: COMMUNITY CONNECTION MISSING: null
- **short-stirling-n3756**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Memorial fence erected in 1993 by P. Ryan (Gwent) and J.B. Hammond (Suffolk)
- **short-stirling-r9329**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **short-stirling-w7441**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **short-stirling-w7467**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **st-egwin-s-church-norton-and-lenchwick-ww2-wellington-memorial**: CREW MISSING: inscription has 5 crew names but crew list is empty
- **stow-bedon-blenheim-v-5851**: COMMUNITY CONNECTION MISSING: Eyewitness account states the pilot deliberately put the nose down to crash into a field rather than hit a house, saving all occupants inside
- **the-gunthorpe-fallen-and-lancaster-r5703**: COMMUNITY CONNECTION MISSING: Memorial located in Gunthorpe Parish commemorates both WWI fallen (Plaque 1) and a WW2 bomber crew who died within the parish (Plaque 2), indicating community recognition of both conflicts.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **two-avro-lancaster-crews-st-peter-ad-vincula**: SQUADRON MISSING: inscription mentions Royal Air Force (no specific squadron stated); COMMUNITY CONNECTION MISSING: Memorial erected by George and Alma Sparrow in grateful appreciation of the crews' sacrifice
- **vautour-mitchell-crash-site**: CREW MISSING: inscription has 2 crew names but crew list is empty
- **vickers-wellington-bj879**: SQUADRON MISSING: inscription mentions 26 OTU; COMMUNITY CONNECTION MISSING: Aircraft crashed into the local water tower; memorial donated by Anglian Water Services Ltd, successor organisation to the water authority responsible for the tower
- **vickers-wellington-bk157**: CREW MISSING: inscription has 7 crew names but crew list is empty
- **vickers-wellington-bk352**: SQUADRON MISSING: inscription mentions 17 OTU RAF Turweston; CREW MISSING: inscription has 7 crew names but crew list is empty
- **vickers-wellington-bk491**: SQUADRON MISSING: inscription mentions 26 OTU; CREW MISSING: inscription has 4 crew names but crew list is empty
- **vickers-wellington-bk517**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-dv697**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **vickers-wellington-dv717**: SQUADRON MISSING: inscription mentions RNAF (likely RNZAF - Royal New Zealand Air Force, suggested by Māori language on lower plaque)
- **vickers-wellington-dv771**: SQUADRON MISSING: inscription mentions 28 OTU
- **vickers-wellington-he818-and-handley-page-halifax-na581**: SQUADRON MISSING: inscription mentions 18 O.T.U. RAF WORKSOP (south side); 425 (ALOUETTE) SQUADRON RCAF / RAF THOLTHORPE (north side); MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **vickers-wellington-hf570**: SQUADRON MISSING: inscription mentions 84 Operational Training Unit, Bomber Command, RAF Desborough; COMMUNITY CONNECTION MISSING: Memorial also recognises other airmen who lost their lives during training at RAF Desborough, indicating broader community remembrance beyond single crash
- **vickers-wellington-hf613**: CREW MISSING: inscription has 5 crew names but crew list is empty
- **vickers-wellington-ln181**: SQUADRON MISSING: inscription mentions 82 OTU; CREW MISSING: inscription has 8 crew names but crew list is empty
- **vickers-wellington-ln660-and-short-stirling-eh989**: CREW MISSING: inscription has 15 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Memorial at Westcott Airfield dedicated to all units and personnel based there; unveiled 28.09.2012 on 70th anniversary of No. 11 OTU's initial arrival
- **vickers-wellington-lp397**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-lp841-stone**: SQUADRON MISSING: inscription mentions 82 O.T.U. - Ossington
- **vickers-wellington-lp841-tablet**: CREW MISSING: inscription has 4 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Crash occurred in South Field Laxton, suggesting direct local impact on the community of Laxton
- **vickers-wellington-mf116**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-mp624**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-nb824**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Three survivors were assisted by two American soldiers and Leading Aircraftwoman Ivy Cross, who was later awarded the British Empire Medal for bravery. Plaque unveiled 28th March 2015 in the presence of many relatives of the crew.
- **vickers-wellington-nz-n**: CREW MISSING: inscription has 6 crew names but crew list is empty; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **vickers-wellington-r1028**: COMMUNITY CONNECTION MISSING: Memorial is displayed in a pub, suggesting local community connection, but no explicit community impact is stated in the inscription text.
- **vickers-wellington-r1465**: COMMUNITY CONNECTION MISSING: Crew explicitly identified as Canadian; community_connection field in database is blank and should be updated to reflect Canadian nationality of crew
- **vickers-wellington-r1646-and-all-other-aircrew-killed-over-the-cairngorms**: SQUADRON MISSING: inscription mentions 20 Operational Training Unit, RAF Lossiemouth; CREW MISSING: inscription has 8 crew names but crew list is empty
- **vickers-wellington-w5667**: SQUADRON MISSING: inscription mentions 14 OTU Cottesmore
- **vickers-wellington-x-hf465**: CRASH DATE MISSING: inscription states 1944-10-20; SQUADRON MISSING: inscription mentions 12 O.T.U.
- **vickers-wellington-z8397**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-z8799**: COMMUNITY CONNECTION MISSING: Memorial erected by the Rotary Club of Horwich in June 1955; family members traveled from South Australia to attend the 60th anniversary commemoration on 16 November 2003
- **vickers-wellington-z8860**: COMMUNITY CONNECTION MISSING: null
- **vickers-wellington-z8863**: CREW MISSING: inscription has 9 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **vickers-wellingtons-ln532-and-lp172**: COMMUNITY CONNECTION MISSING: Memorial erected in Whittlebury (MMXVII=2017), the crash site community, commemorating both incidents; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **victor-george-bailey-and-louis-grover-martin-wellington-crash-ford**: CRASH DATE MISSING: inscription states 1944-01-09
- **walton-on-the-naze-rg475**: COMMUNITY CONNECTION MISSING: Memorial dedicated to all local men and women who have served in the Royal Air Force, in addition to the Halifax crew; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **weasenham-r-a-f-aircrew-ww-ii**: CREW MISSING: inscription has 3 crew names but crew list is empty; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **wellington-bomber-he740**: CREW MISSING: inscription has 6 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: null
- **wellington-bomber-mk-x-mf509**: AIRCRAFT TYPE MISSING: inscription mentions Wellington X; CREW MISSING: inscription has 6 crew names but crew list is empty
- **wellington-r1392-crash**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **wellington-x-he-324-crash**: CREW MISSING: inscription has 6 crew names but crew list is empty

---
*Generated 2026-04-13 08:43:31 | Corrections file: /root/repos/bomber-memorial-site/scripts/../inscription-corrections.json*