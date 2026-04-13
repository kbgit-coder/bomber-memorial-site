# BMR Inscription Validation Report — 2026-04-12 23:27

**Duration:** 5201s | **Memorials checked:** 277 | **Mode:** APPLIED

## Summary

| Severity | Count |
|----------|-------|
| critical | 0 |
| high | 48 |
| medium | 169 |
| low | 31 |
| clean | 29 |

## Issue Categories

- **COMMUNITY CONNECTION MISSING**: 197
- **CIVILIAN CASUALTIES NOT RECORDED**: 41
- **MULTIPLE EVENTS**: 37
- **SQUADRON MISSING**: 34
- **CREW MISSING**: 32
- **CRASH DATE MISSING**: 29
- **Granite query failed**: 25
- **CRASH DATE MISMATCH**: 8
- **SERIAL NUMBER MISSING**: 7
- **AIRCRAFT TYPE MISSING**: 2
- **FTR MEMORIAL**: 2

## Corrections Applied: 77

## HIGH — Data Corrections Needed (48)

**305th-bomb-group-b17-flying-fortress-42-97578-crash** — 305th Bomb Group - B17 Flying Fortress (42-97578) Crash
- CRASH DATE MISMATCH: DB has 1943-08-24, inscription says 1944-03-24. Reasoning: exact quote from inscription with the crash date
- CIVILIAN CASUALTIES NOT RECORDED: (CHILD'S NAME), AGED 14 YEARS. (CHILD'S NAME), AGED 4 YEARS
- COMMUNITY CONNECTION MISSING: of Yelden
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `1943-08-24` → `1944-03-24` (confidence: high)
  - Fix `community_connection`: `` → `(CHILD'S NAME), AGED 14 YEARS. (CHILD'S NAME), AGED 4 YEARS` (confidence: high)
  - Fix `community_connection`: `` → `of Yelden` (confidence: medium)

**61-squadron-handley-page-hampden-crew** — 61 Squadron Handley Page Hampden Crew
- CIVILIAN CASUALTIES NOT RECORDED: killing all the aircrew
- COMMUNITY CONNECTION MISSING: Bluestone plantation, community connection mentioned through www.cawstonheritage.co.uk
  - Fix `community_connection`: `` → `killing all the aircrew` (confidence: high)
  - Fix `community_connection`: `` → `Bluestone plantation, community connection mentioned through www.cawstonheritage.co.uk` (confidence: medium)

**617-squadron-aircrew-derwent-valley** — 617 Squadron Aircrew - Derwent Valley
- CRASH DATE MISSING: inscription states 16th May 1943
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Also REMEMBERED HERE ARE THE/ 204 617 SQD. AIRCREW WHO LAID DOWN/ THEIR LIVES BETWEEN 1943 - 1945
  - Fix `crash_date`: `` → `16th May 1943` (confidence: high)
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Also REMEMBERED HERE ARE THE/ 204 617 SQD. AIRCREW WHO LAID DOWN/ THEIR LIVES BETWEEN 1943 - 1945` (confidence: medium)

**a-and-d-lancaster** — A and D Lancaster
- CRASH DATE MISSING: inscription states 1915-05-07
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions 'Keelby Manor', indicating a local connection.
  - Fix `crash_date`: `` → `1915-05-07` (confidence: high)
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions 'Keelby Manor', indicating a local connection.` (confidence: medium)

**aircrew-of-lancaster-pb512** — Aircrew of Lancaster  PB512
- CIVILIAN CASUALTIES NOT RECORDED: A CRASH NEAR THIS CHURCH
- COMMUNITY CONNECTION MISSING: This CHURCH
  - Fix `community_connection`: `` → `A CRASH NEAR THIS CHURCH` (confidence: high)
  - Fix `community_connection`: `` → `This CHURCH` (confidence: medium)

**aircrew-of-wellington-r1801** — Aircrew of Wellington R1801
- CIVILIAN CASUALTIES NOT RECORDED: workmen from Beaumanor, passengers from a passing bus and villagers
- COMMUNITY CONNECTION MISSING: IN GREATFUL REMEMBRANCE FROM LOCAL PEOPLE; WENT THE DAY WELL? WE DIED AND NEVER KNEW, BUT, WELL OR ILL, FREEDOM, WE DIED FOR YOU
  - Fix `community_connection`: `` → `workmen from Beaumanor, passengers from a passing bus and villagers` (confidence: high)
  - Fix `community_connection`: `` → `IN GREATFUL REMEMBRANCE FROM LOCAL PEOPLE; WENT THE DAY WELL? WE DIED AND NEVER KNEW, BUT, WELL OR ILL, FREEDOM, WE DIED FOR YOU` (confidence: medium)

**avro-lancaster-biii-ja915** — Avro Lancaster BIII JA915
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Green Farm, Kenninghall
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Green Farm, Kenninghall` (confidence: medium)

**avro-lancaster-ll686** — Avro Lancaster LL686
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: This memorial was erected by the villagers of Aldborough to commemorate the 50th anniversary of their noble sacrifice.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `This memorial was erected by the villagers of Aldborough to commemorate the 50th anniversary of their noble sacrifice.` (confidence: medium)

**avro-lancaster-lm616** — Avro Lancaster LM616
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Their names will live for ever more
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Their names will live for ever more` (confidence: medium)

**avro-lancaster-pb304** — Avro Lancaster PB304
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: community affected by the crash, local people erected it
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `community affected by the crash, local people erected it` (confidence: medium)

**avro-lancaster-w4319** — Avro Lancaster W4319
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions the crash occurred off the North German coast, indicating a connection to local communities.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions the crash occurred off the North German coast, indicating a connection to local communities.` (confidence: medium)

**avro-lancasters-me473-and-nd572** — Avro Lancasters ME473 and ND572
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The memorial is in Cambridge City Cemetery, indicating a local connection.
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The memorial is in Cambridge City Cemetery, indicating a local connection.` (confidence: medium)

**bellingdon-pb475** — Bellingdon Lancaster Memorial
- CRASH DATE MISMATCH: DB has WW2, inscription says 1945-03-06. Reasoning: Six young airmen died at this spot on 6 March 1945.
  - Fix `crash_date`: `WW2` → `1945-03-06` (confidence: high)

**cairnsmore-of-fleet-ww2-crashes-1-post-war-commemorated-** — Cairnsmore of Fleet Memorial (7 Wartime Crashes)
- CRASH DATE MISMATCH: DB has WW2, inscription says 1940-08-08. Reasoning: First Crash: LEUTNANT A ZEISS AGE 25 UNTEROFFIZIER G T VON TURCKHEIM AGE 31 UNTEROFFIZIER W HAJESCH AGE 21 UNTEROFFIZIER W MECHSNER AGE 23 FROM NG 1 STAFFEL OF KAMPFGESCHWADER 4 SOESTERBURG AIR BASE HOLLAND THE AIRCRAFT A HEINKEL III H4 CRASHED ON 8TH AUGUST 1940
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `WW2` → `1940-08-08` (confidence: high)

**caythorpe-heath-lj450** — Caythorpe Heath Stirling Memorial
- CRASH DATE MISMATCH: DB has 1944-04-12, inscription says 1944-04-01. Reasoning: The inscription states 'SHOT DOWN AT 0125 HRS ON 1 APRIL 1944'
  - Fix `crash_date`: `1944-04-12` → `1944-04-01` (confidence: high)

**cheviot-hills-memorial-multiple-aircraft-co** — Cheviot Hills Memorial commemorated Memorial
- CRASH DATE MISMATCH: DB has WW2, inscription says 1939-1945. Reasoning: PER ARDUA AD ASTRA After 2015 refurbishment: DEDICATED TO THE MEMORY OF THE AIRMEN WHO LOST THEIR LIVES ON THE CHEVIOT HILLS AS A RESULT OF THE SECOND WORLD WAR
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `WW2` → `1939-1945` (confidence: high)

**flight-sergeant-l-lissette-and-crew-of-avro-lancaster-nd556** — Avro Lancaster ND556
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: This tree commemorates the crew members and indicates a local connection, suggesting it was erected by community members affected.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `This tree commemorates the crew members and indicates a local connection, suggesting it was erected by community members affected.` (confidence: medium)

**halifax-bomber-ll459** — Halifax Bomber LL459
- CRASH DATE MISSING: inscription states 1944-06-08
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The memorial is located opposite this church, indicating a strong community connection.
  - Fix `crash_date`: `` → `1944-06-08` (confidence: high)
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The memorial is located opposite this church, indicating a strong community connection.` (confidence: medium)

**hampden-p1294** — Hampden P1294
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions the crash site is opposite a field, indicating it was likely in a local area. The community connection implies local people were affected by this event.
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions the crash site is opposite a field, indicating it was likely in a local area. The community connection implies local people were affected by this event.` (confidence: medium)

**handley-page-halifax-dg358** — Handley Page Halifax DG358
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Their bodies rested at Bwlch-y--ffridd Institute on the evening of the 23rd.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Their bodies rested at Bwlch-y--ffridd Institute on the evening of the 23rd.` (confidence: medium)

**handley-page-halifax-dg412** — Handley Page Halifax DG412
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: This stone is to the memory of these brave men who died so young. The community connection implies a local impact.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `This stone is to the memory of these brave men who died so young. The community connection implies a local impact.` (confidence: medium)

**handley-page-halifax-dk192** — Handley Page Halifax DK192
- CIVILIAN CASUALTIES NOT RECORDED: A MILK LORRY WHO WAS PASSING ALONG THIS ROAD WERE KILLED
- COMMUNITY CONNECTION MISSING: ERECTED BY THEIR COMRADE (Name)
  - Fix `community_connection`: `` → `A MILK LORRY WHO WAS PASSING ALONG THIS ROAD WERE KILLED` (confidence: high)
  - Fix `community_connection`: `` → `ERECTED BY THEIR COMRADE (Name)` (confidence: medium)

**handley-page-halifax-hx181** — Handley Page Halifax HX181
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: RAF MELBOURNE, YORKS
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `RAF MELBOURNE, YORKS` (confidence: medium)

**handley-page-halifax-jb798** — Handley Page Halifax JB798
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The names of those who then lost their lives are inscribed below. RESTORATION/ OF THE BUILDING WAS BEGUN ON 10TH MAY. 1949 AND THE CHURCH/ WAS RE-DEDICATED ON 11TH DECEMBER .1950
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The names of those who then lost their lives are inscribed below. RESTORATION/ OF THE BUILDING WAS BEGUN ON 10TH MAY. 1949 AND THE CHURCH/ WAS RE-DEDICATED ON 11TH DECEMBER .1950` (confidence: medium)

**handley-page-halifax-jp137** — Handley Page Halifax JP137
- CIVILIAN CASUALTIES NOT RECORDED: Two local residents lost their lives.
- COMMUNITY CONNECTION MISSING: Organised by the Moortown 2010 Committee as a contribution to the Bicentenary of Bournemouth.
  - Fix `community_connection`: `` → `Two local residents lost their lives.` (confidence: high)
  - Fix `community_connection`: `` → `Organised by the Moortown 2010 Committee as a contribution to the Bicentenary of Bournemouth.` (confidence: medium)

**handley-page-halifax-lk794** — Handley Page Halifax LK794
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions 'MIRACULOUSLY THE CANADIAN REAR GUNNER MANAGED TO PARACHUTE TO SAFETY BUT THE REST OF THE CREW WERE LOST WITHOUT TRACE' and refers to the area as 'THIS IS HALLOWED GROUND', indicating a local connection.
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions 'MIRACULOUSLY THE CANADIAN REAR GUNNER MANAGED TO PARACHUTE TO SAFETY BUT THE REST OF THE CREW WERE LOST WITHOUT TRACE' and refers to the area as 'THIS IS HALLOWED GROUND', indicating a local connection.` (confidence: medium)

**handley-page-halifax-lw115** — Handley Page Halifax LW115
- CIVILIAN CASUALTIES NOT RECORDED: {'ages': None, 'relationship_to_community': "A CHILD was fatally injured when some wreckage fell on a house 'HOKANG' Pinfold Hill."}
- COMMUNITY CONNECTION MISSING: The memorial is for the community of Pinfold Hill where a child was fatally injured by wreckage from the crashed aircraft.
  - Fix `community_connection`: `` → `{'ages': None, 'relationship_to_community': "A CHILD was fatally injured when some wreckage fell on a house 'HOKANG' Pinfold Hill."}` (confidence: high)
  - Fix `community_connection`: `` → `The memorial is for the community of Pinfold Hill where a child was fatally injured by wreckage from the crashed aircraft.` (confidence: medium)

**handley-page-halifax-mz538** — Handley Page Halifax MZ538
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: THE EXPLOSION CAUSED THE LOSS OF ALL EIGHT CREW MEMBERS. IT WAS BY THE SKILL OF THE PILOT F/O JOSEPH R.J.M. DESMARIS DFC THAT MASSIVE CASUALTIES WERE SAVED./ THE ALTAR WINDOW WAS DAMAGED AND WAS RESTORED WITH NEW STAINED GLASS IN 1958. THE CANADIAN CREW ARE BURIED SIDE BY SIDE IN THE COMMONWEALTH WAR GRAVES COMMISSION'S PLOT AT STONEFALL CEMETERY, HARROGATE.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `THE EXPLOSION CAUSED THE LOSS OF ALL EIGHT CREW MEMBERS. IT WAS BY THE SKILL OF THE PILOT F/O JOSEPH R.J.M. DESMARIS DFC THAT MASSIVE CASUALTIES WERE SAVED./ THE ALTAR WINDOW WAS DAMAGED AND WAS RESTORED WITH NEW STAINED GLASS IN 1958. THE CANADIAN CREW ARE BURIED SIDE BY SIDE IN THE COMMONWEALTH WAR GRAVES COMMISSION'S PLOT AT STONEFALL CEMETERY, HARROGATE.` (confidence: medium)

**handley-page-halifax-nr179** — Handley Page Halifax NR179
- CRASH DATE MISMATCH: DB has 1945-03-03, inscription says 1945-03-04. Reasoning: On return to Base, while waiting to land, they were hit by gunfire from a Luftwaffe JU-88 night fighter. NR179 caught fire and crashed at 0110 hrs on 4th March 1945.
- CREW MISSING: inscription has 7 crew names but crew list is empty
  - Fix `crash_date`: `1945-03-03` → `1945-03-04` (confidence: high)
  - Fix `crew`: `0 crew` → `7 crew (extract from inscription)` (confidence: medium)

**handley-page-halifax-rt922** — Handley Page Halifax RT922
- CIVILIAN CASUALTIES NOT RECORDED: The inscription mentions the crash was during a mission to airdrop supplies to the snow-bound communities of Grindon and the surrounding areas.
- COMMUNITY CONNECTION MISSING: The crash site is adjacent to this cairn, erected by the Leek Branch of The Royal Air Force Association as a result of a project led by them. It was supported by Mount Harry Beecroft (landowner), Staffordshire Moorlands District Council & Grindon Parish Council.
  - Fix `community_connection`: `` → `The inscription mentions the crash was during a mission to airdrop supplies to the snow-bound communities of Grindon and the surrounding areas.` (confidence: high)
  - Fix `community_connection`: `` → `The crash site is adjacent to this cairn, erected by the Leek Branch of The Royal Air Force Association as a result of a project led by them. It was supported by Mount Harry Beecroft (landowner), Staffordshire Moorlands District Council & Grindon Parish Council.` (confidence: medium)

**handley-page-hampden-l4173** — Handley Page Hampden L4173
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions the community connection, but specific details are not provided.
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions the community connection, but specific details are not provided.` (confidence: medium)

**handley-page-hampden-p4399** — Handley Page Hampden P4399
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Dartford Borough Council, Councillor Jeremy Kite
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Dartford Borough Council, Councillor Jeremy Kite` (confidence: medium)

**leicester-pa269** — Leicester Lancaster Memorial
- CRASH DATE MISMATCH: DB has 04/02/1946 (post-war), inscription says 1946-02-04. Reasoning: OVER LEICESTER ON 4th FEBRUARY 1946
- COMMUNITY CONNECTION MISSING: This plaque has been erected in memory of the Airmen
  - Fix `crash_date`: `04/02/1946 (post-war)` → `1946-02-04` (confidence: high)
  - Fix `community_connection`: `` → `This plaque has been erected in memory of the Airmen` (confidence: medium)

**reigate-hill-b-17-flying-fortress** — Reigate Hill Fortress Memorial
- CRASH DATE MISMATCH: DB has WW2, inscription says 1945. Reasoning: INSCRIPTION TEXT: ... IN MEMORY OF THE NINE U.S. AIRMEN WHO DIED HERE IN 1945
  - Fix `crash_date`: `WW2` → `1945` (confidence: high)

**ryhope-sunderland-barton-vc** — Ryhope, Sunderland — Cyril Joe Barton VC Memorial
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: sacrificed his life to save others
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `sacrificed his life to save others` (confidence: medium)

**sergeant-a-j-smith-and-short-stirling-ef352** — Short Stirling EF352
- CRASH DATE MISSING: inscription states 22nd OCTOBER 1943
- CIVILIAN CASUALTIES NOT RECORDED: VILLAGE AT PRESTON WYNNE HEREFORD
- COMMUNITY CONNECTION MISSING: LEAVING A WIDOW AND THREE SONS IN HEDGE END. COMMUNITY CONNECTION: OF HEDGE END
  - Fix `crash_date`: `` → `22nd OCTOBER 1943` (confidence: high)
  - Fix `community_connection`: `` → `VILLAGE AT PRESTON WYNNE HEREFORD` (confidence: high)
  - Fix `community_connection`: `` → `LEAVING A WIDOW AND THREE SONS IN HEDGE END. COMMUNITY CONNECTION: OF HEDGE END` (confidence: medium)

**the-gunthorpe-fallen-and-lancaster-r5703** — The Gunthorpe Fallen and Lancaster R5703
- CIVILIAN CASUALTIES NOT RECORDED: 
- COMMUNITY CONNECTION MISSING: In Memory of the Bomber Crew who died in the Parish of Gunthorpe
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `In Memory of the Bomber Crew who died in the Parish of Gunthorpe` (confidence: medium)

**vickers-wellington-bj879** — Vickers Wellington BJ879
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: Donated by ANGLIAN WATER SERVICES LTD
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `Donated by ANGLIAN WATER SERVICES LTD` (confidence: medium)

**vickers-wellington-dv717** — Vickers Wellington DV717
- CIVILIAN CASUALTIES NOT RECORDED: Sgt McCord in Argadh, Ireland
- COMMUNITY CONNECTION MISSING: erected by community connection (Ollerton Cemetery)
  - Fix `community_connection`: `` → `Sgt McCord in Argadh, Ireland` (confidence: high)
  - Fix `community_connection`: `` → `erected by community connection (Ollerton Cemetery)` (confidence: medium)

**vickers-wellington-n2848** — Vickers Wellington N2848
- CIVILIAN CASUALTIES NOT RECORDED: null
- COMMUNITY CONNECTION MISSING: The PARKER FAMILY AND LOCAL PEOPLE
  - Fix `community_connection`: `` → `null` (confidence: high)
  - Fix `community_connection`: `` → `The PARKER FAMILY AND LOCAL PEOPLE` (confidence: medium)

**vickers-wellington-r1461** — Vickers Wellington R1461
- CIVILIAN CASUALTIES NOT RECORDED: {'names': ['EDWIN WILLIAMS', 'his wife ANNIE JANE'], 'relationship_to_community': None}
- COMMUNITY CONNECTION MISSING: {'erected_by': None, 'local_organisations': None}
  - Fix `community_connection`: `` → `{'names': ['EDWIN WILLIAMS', 'his wife ANNIE JANE'], 'relationship_to_community': None}` (confidence: high)
  - Fix `community_connection`: `` → `{'erected_by': None, 'local_organisations': None}` (confidence: medium)

**vickers-wellington-r1474** — Vickers Wellington R1474
- CIVILIAN CASUALTIES NOT RECORDED: Mr & Mrs Titmarsh SURVIVED.
- COMMUNITY CONNECTION MISSING: The occupants were Mr & Mrs Titmarsh, indicating a local connection.
  - Fix `community_connection`: `` → `Mr & Mrs Titmarsh SURVIVED.` (confidence: high)
  - Fix `community_connection`: `` → `The occupants were Mr & Mrs Titmarsh, indicating a local connection.` (confidence: medium)

**vickers-wellington-x3707** — Vickers Wellington X3707
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: at Craiglockhart View
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `at Craiglockhart View` (confidence: medium)

**vickers-wellington-x3790** — Vickers Wellington X3790
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: To the memory of those Winslow residents, evacuees and aircrew
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `To the memory of those Winslow residents, evacuees and aircrew` (confidence: medium)

**vickers-wellington-z8799** — Vickers Wellington Z8799
- CRASH DATE MISSING: inscription states 1943-11-12
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: ERECTED BY THE ROTARY CLUB OF HORWICH
  - Fix `crash_date`: `` → `1943-11-12` (confidence: high)
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `ERECTED BY THE ROTARY CLUB OF HORWICH` (confidence: medium)

**walton-on-the-naze-rg475** — Walton-on-the-Naze VII Memorial
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions: 'THIS MEMORIAL WAS ERECTED IN 1979 BY THE FRINTON AND WALTON ROYAL AIR FORCES ASSOCIATION TO COMMEMORATE THE 60TH ANNIVERSARY OF THE FORMATION OF THE ROYAL AIR FORCE AND THE 30th OF THE BRANCH.'
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions: 'THIS MEMORIAL WAS ERECTED IN 1979 BY THE FRINTON AND WALTON ROYAL AIR FORCES ASSOCIATION TO COMMEMORATE THE 60TH ANNIVERSARY OF THE FORMATION OF THE ROYAL AIR FORCE AND THE 30th OF THE BRANCH.'` (confidence: medium)

**wellington-bomber-n2980** — Wellington Bomber N2980
- CRASH DATE MISSING: inscription states 1940-12-18
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: The inscription mentions that the memorial was erected by the Loch Ness Wellington Association, Ltd. and unveiled by pupils from Drumsna School.
- MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
  - Fix `crash_date`: `` → `1940-12-18` (confidence: high)
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `The inscription mentions that the memorial was erected by the Loch Ness Wellington Association, Ltd. and unveiled by pupils from Drumsna School.` (confidence: medium)

**wellington-t2962** — Wellington T2962
- CIVILIAN CASUALTIES NOT RECORDED: None
- COMMUNITY CONNECTION MISSING: DIED IN LLANGROVE
  - Fix `community_connection`: `` → `Civilian casualties mentioned in inscription` (confidence: high)
  - Fix `community_connection`: `` → `DIED IN LLANGROVE` (confidence: medium)

## MEDIUM — Missing Data (169)

- **aircrew-1939-1945**: COMMUNITY CONNECTION MISSING: Dedicated by the Aircrew Association, Norwich and District Branch to honour all comrades who gave their lives.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **australian-aircrew-lost-over-europe**: COMMUNITY CONNECTION MISSING: Unveiled by Group Captain Roxley McNellan, Air Force Adviser of the Australian High Commission, London on 16th May 1995. Donated by Joan (...) Bannenberg, a niece of the late Squadron Leader, B.A. Grace (DFC), RAAF.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **avro-lancaster-dv334**: COMMUNITY CONNECTION MISSING: Memorial data indicates local connection, but specific community impact details are not provided.
- **avro-lancaster-dv361**: COMMUNITY CONNECTION MISSING: The memorial was dedicated on 16-09-98, suggesting a connection to the local community or possibly commemorating the event in a significant way.
- **avro-lancaster-dv382**: SQUADRON MISSING: inscription mentions 617/ ROYAL AIR FORCE; COMMUNITY CONNECTION MISSING: This is the site where a Lancaster bomber crashed, implying it was in a location significant to those involved or their community.
- **avro-lancaster-hk773**: SQUADRON MISSING: inscription mentions XV SQUADRON; COMMUNITY CONNECTION MISSING: The memorial is for the crew of XV SQUADRON, indicating a strong connection to local military community.
- **avro-lancaster-jb284**: COMMUNITY CONNECTION MISSING: Honouring the Memory of MY GRANDFATHER AND HIS CREW
- **avro-lancaster-jb477**: COMMUNITY CONNECTION MISSING: We will remember them. Community connection mentioned as being buried at Cambridge City Cemetery.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **avro-lancaster-jb534-damaged-early-2025-currently-removed-for-repair**: COMMUNITY CONNECTION MISSING: Erected and Maintained by Friends of Metheringham Airfield - metheringhamairfield.com
- **avro-lancaster-kb879**: COMMUNITY CONNECTION MISSING: The memorial was erected by the Sandon & District Royal British Legion, indicating a local connection.
- **avro-lancaster-lm619**: SQUADRON MISSING: inscription mentions 1668 HCU; COMMUNITY CONNECTION MISSING: no specific community connection mentioned
- **avro-lancaster-lm719**: CREW MISSING: inscription has 7 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Who perished near this place
- **avro-lancaster-lm720**: COMMUNITY CONNECTION MISSING: Dedicated to the MEMORY OF THE CREW OF THE ABOVE AIRCRAFT WHO DIED
- **avro-lancaster-nd820**: COMMUNITY CONNECTION MISSING: This memorial was commissioned by the Lincolnshire Aircraft Recovery Group.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **avro-lancaster-pb355**: COMMUNITY CONNECTION MISSING: Memorial for crew members of Lancaster aircraft PB355, likely from a local community.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **avro-lancaster-pb366-pillar**: CRASH DATE MISSING: inscription states 1944-12-24; COMMUNITY CONNECTION MISSING: The memorial is in Great Paxton, indicating a local connection.
- **avro-lancaster-pb432**: CRASH DATE MISSING: inscription states 1944-11-26
- **avro-lancaster-pb475**: COMMUNITY CONNECTION MISSING: Great lives cut short. Royal Air Force (3 Names). Royal Australian Air Force (3 Names). Community connection to the airmen.
- **avro-lancaster-pb565**: COMMUNITY CONNECTION MISSING: RAF SANDTOFT, IN MEMORY OF THE CREW
- **avro-lancaster-pd431**: SQUADRON MISSING: inscription mentions 1653 HCU; COMMUNITY CONNECTION MISSING: The inscription is located in a community setting, indicating local significance.
- **avro-lancaster-r5676**: COMMUNITY CONNECTION MISSING: This farm
- **b-17-flying-fortress-z9a-no-519-squadron-raf**: COMMUNITY CONNECTION MISSING: local people affected, who erected it: WE SHALL REMEMBER THEM AND THEIR COMRADES OF 519 MET RECCE. SQUADRON, ROYAL AIR FORCE, WICK.
- **b-24h-liberator-usaaf-crew-tablet**: COMMUNITY CONNECTION MISSING: in the common cause of freedom
- **burn-chapel-578-sqn-panels**: CREW MISSING: inscription has 219 crew names but crew list is empty
- **cairnsmore-of-fleet-local-air-crashes**: CREW MISSING: inscription has 1 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: The memorial is erected by NG 1 Staffel of Kampfgeschwader 4, indicating a strong connection to the local community and their defense efforts.
- **canadian-crew-of-wellington-bomber**: SQUADRON MISSING: inscription mentions 82 OTU; CREW MISSING: inscription has 8 crew names but crew list is empty
- **canberra-bomber-crash-tiverton**: CRASH DATE MISSING: inscription states 1961-11-21; COMMUNITY CONNECTION MISSING: We will remember them
- **chipping-norton-oxford-and-wellington-crews-ww2**: CREW MISSING: inscription has 8 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: The inscription mentions 'IN MEMORY OF THE AIRCREWS', indicating a community connection, likely local people affected or those who erected the memorial.
- **crew-of-28-otu-wellington-mf200**: COMMUNITY CONNECTION MISSING: Normanton on Soar
- **crew-of-handley-page-hampden-ae381-2**: CRASH DATE MISSING: inscription states 1942-01-21; COMMUNITY CONNECTION MISSING: The inscription does not specify the community impact.
- **crew-of-lancaster-aircraft-serial-mk-442**: COMMUNITY CONNECTION MISSING: The inscription mentions 'THE ENTIRE CREW OF THE LANCASTER PERISHED' and the community connection is implied by the memorial being erected for those who died.
- **crew-of-lancaster-bomber-lm258**: CRASH DATE MISSING: inscription states 1944-08-25; SQUADRON MISSING: inscription mentions HA-Q
- **crew-of-lancaster-ll811-bq-j-and-their-comrades**: COMMUNITY CONNECTION MISSING: The inscription mentions 'FOR THE BRAVE YOUNG LADS OF THAT CREW, SHOWN BELOW, AND FOR ALL THEIR COMRADES WHO DID NOT RETURN WE DEDICATE THIS SIMPLE PLAQUE.' and the community connection is shown as 'THIS HISTORIC OPERATION PUT NORTH KILLINGHOLME ON THE MAP'.
- **crew-of-lancaster-nd-714-60-t**: COMMUNITY CONNECTION MISSING: The memorial is for a local community, as indicated by the connection to the squadron and aircraft type.
- **crew-of-lancaster-pb476-12-squadron-raf**: COMMUNITY CONNECTION MISSING: This memorial is placed here, on/ the 50th anniversary of the crash,/ to commemorate the crew members/ who died.
- **crew-of-wellington-bomber-ln482**: CREW MISSING: inscription has 6 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: The inscription mentions a church nearby, indicating the crash site's connection to the local community.
- **crew-of-wellington-w5557**: COMMUNITY CONNECTION MISSING: Soldiers of Poland
- **crew-of-whitley-mk-5-no-1489**: COMMUNITY CONNECTION MISSING: Silsden Moor
- **crews-of-lancaster-4103-and-oxford-lb415**: SQUADRON MISSING: inscription mentions No 5 Lancaster finishing school./ No 5 Group/ Royal Air Force Bomber Command; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **crews-of-lancasters-jb678-and-jb674**: AIRCRAFT TYPE MISSING: inscription mentions Lancaster Bomber; COMMUNITY CONNECTION MISSING: Over GRAINSBY
- **crews-of-lancasters-me625-and-nd981**: COMMUNITY CONNECTION MISSING: The inscription mentions 'UNVEILED BY THE RELATIVES FOR THE 70TH ANNIVERSARY' and the plaque origin information panel states it is an identical copy unveiled near the crash site at Cloot House Farm Crowland.
- **crews-of-two-wellington-bombers**: CRASH DATE MISSING: inscription states 1943-10-12; SQUADRON MISSING: inscription mentions 82 OTU
- **flight-lieutenant-l-cumberworth-and-flying-officer-j-easdale-handley-page-halifa**: COMMUNITY CONNECTION MISSING: IN SWANLAND IN A HALIFAX BOMBER
- **flight-sergeant-j-timperon-r-a-a-f-and-vickers-wellington-z8799**: CRASH DATE MISSING: inscription states 2003-11-16; COMMUNITY CONNECTION MISSING: Sister Mary, Sister-in-law Shirley, and family members in South Australia
- **flying-fortress-lucky-strike-crew-and-emergency-services**: CRASH DATE MISSING: inscription states 1944-01-05; SERIAL NUMBER MISSING: inscription mentions 29923
- **flying-officer-j-j-bregman-and-crew-of-avro-lancaster-pb171**: CRASH DATE MISSING: inscription states 19.7.1944; COMMUNITY CONNECTION MISSING: The inscription mentions 'the family he never knew', indicating a local connection and impact.
- **great-rissington-lamb-inn-r1028**: COMMUNITY CONNECTION MISSING: THE AIRCRAFT CRASHED IN THE BACK GARDEN OF THE LAMB INN. THIS PLAQUE INSTALLED WITH THE KIND PERMISSION OF THE LAMB INN OWNER, MR CLEVERLEY.
- **handley-page-halifax-bb216**: COMMUNITY CONNECTION MISSING: from Topcliffe
- **handley-page-halifax-bb320**: COMMUNITY CONNECTION MISSING: Community connection mentioned as Royal Air Force Volunteer Reserve and Royal Canadian Air Force
- **handley-page-halifax-dk253**: COMMUNITY CONNECTION MISSING: This memorial is to all those who served in 427 Squadron and in 6 BOMBER GROUP RCAF.
- **handley-page-halifax-dt669**: COMMUNITY CONNECTION MISSING: Names
- **handley-page-halifax-dt696**: COMMUNITY CONNECTION MISSING: Their names LIVETH FOR EVERMORE.
- **handley-page-halifax-eb199**: COMMUNITY CONNECTION MISSING: ATLEY HILL, SOUTH COWTON/ YORKSHIRE
- **handley-page-halifax-eb203**: CRASH DATE MISSING: inscription states 1944-04-15; CREW MISSING: inscription has 7 crew names but crew list is empty
- **handley-page-halifax-hx351**: COMMUNITY CONNECTION MISSING: No specific community connection mentioned.
- **handley-page-halifax-jb863**: COMMUNITY CONNECTION MISSING: The memorial is erected by the community of Elvington, indicating a strong local connection.
- **handley-page-halifax-jd105-and-f86-sabre-xd733**: COMMUNITY CONNECTION MISSING: memorial to the AIRCREWS OF ALL ALLIED NATIONS; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **handley-page-halifax-jp190**: CREW MISSING: inscription has 8 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Erected 1st April 1994 by Nos. 2465 (Currie & Balarno) Squ./ 1007 (Duns) Squ. Air Training Corps, and the Forestry Commission.
- **handley-page-halifax-lk789**: COMMUNITY CONNECTION MISSING: This plaque is a memorial to the crew of RAF Halifax LK789/ of 76 Squadron Holme-on-Spalding Moor
- **handley-page-halifax-lk839**: COMMUNITY CONNECTION MISSING: names of crew members listed, indicating local connection
- **handley-page-halifax-lk844**: COMMUNITY CONNECTION MISSING: The inscription mentions cherry trees for each member of the crew, indicating a strong community connection.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **handley-page-halifax-lk878**: COMMUNITY CONNECTION MISSING: local people affected, who erected it
- **handley-page-halifax-lk954-2019**: SQUADRON MISSING: inscription mentions 428 (GHOST) Squadron Royal Canadian Air Force; CREW MISSING: inscription has 8 crew names but crew list is empty
- **handley-page-halifax-ll505**: COMMUNITY CONNECTION MISSING: From No. 1659 HCU Topcliffe; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **handley-page-halifax-lv836**: SQUADRON MISSING: inscription mentions 427 LION SQN RCAF/ROYAL CANADIAN AIR FORCE; COMMUNITY CONNECTION MISSING: This memorial is also dedicated to all members of BOMBER COMMAND who gave their lives in the defence of freedom 1939 - 1945
- **handley-page-halifax-lv905**: COMMUNITY CONNECTION MISSING: DEDICATED TO ALL WHO SERVED AT THIS AIRFIELD AND GAVE THEIR LIVES
- **handley-page-halifax-lv955**: COMMUNITY CONNECTION MISSING: community_connection
- **handley-page-halifax-lw478**: SQUADRON MISSING: inscription mentions 578 / Squadron Royal Air Force; COMMUNITY CONNECTION MISSING: The memorial is located in North Yorkshire, indicating a local connection to the community affected by the disaster.
- **handley-page-halifax-lw579**: CRASH DATE MISSING: inscription states 1944-03-31
- **handley-page-halifax-lw598-ow-j-johnnie**: SQUADRON MISSING: inscription mentions 426 (CANADIAN) SQUADRON; COMMUNITY CONNECTION MISSING: Who erected it: NAMES (6) MEMBERS OF 426 (CANADIAN) SQUADRON
- **handley-page-halifax-lw598**: CRASH DATE MISSING: inscription states 1944-06-09; SQUADRON MISSING: inscription mentions 426 (CANADIAN) SQUADRON
- **handley-page-halifax-mz454**: COMMUNITY CONNECTION MISSING: No specific community connection mentioned.
- **handley-page-halifax-mz519**: SQUADRON MISSING: inscription mentions NO. 578/ SQUADRON OF THE ROYAL AIR FORCE; COMMUNITY CONNECTION MISSING: the village of Farnsfield where the crash occurred
- **handley-page-halifax-mz920**: CREW MISSING: inscription has 5 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: in the Parish of Dunchurch
- **handley-page-halifax-nr287**: SQUADRON MISSING: inscription mentions 347 (Tunisie) Sqn; COMMUNITY CONNECTION MISSING: The inscription mentions the plaque was attached to a tree against which the Halifax came to rest until it fell and the plaque was moved to the church porch here in Scawton.
- **handley-page-halifax-rg475-and-local-men-and-women-who-served-in-the-royal-air-f**: CRASH DATE MISSING: inscription states 1945-03-05; COMMUNITY CONNECTION MISSING: The memorial was erected by the Frinton and Walton Royal Air Forces Association to commemorate the formation of the RAF and the branch, dedicated to all local men and women who have served in the RAF.
- **handley-page-halifax-s-bb373-and-jb874**: COMMUNITY CONNECTION MISSING: local people affected, HULL BRIDGE, TICKTON
- **handley-page-halifax-s-jp201-and-ll137**: CREW MISSING: inscription has 5 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: This memorial was erected to their honour on November 6th 1994
- **handley-page-halifax-w1228**: COMMUNITY CONNECTION MISSING: The inscription mentions the crew of Halifax W1228 from 76 Squadron, indicating a connection to local community or unit.
- **handley-page-halifax-w7823**: SQUADRON MISSING: inscription mentions No 8 Group PFF NTU / RAF Upwood; CREW MISSING: inscription has 10 crew names but crew list is empty
- **handley-page-hampden-ad783**: COMMUNITY CONNECTION MISSING: The crew of R.A.A.F. (Royal Australian Air Force)
- **handley-page-hampden-at110**: COMMUNITY CONNECTION MISSING: TANGMERE MILITARY AVIATION MUSEUM; FELPHAM PARISH COUNCIL; SNOOKS CORNER COMMUNITY CENTRE; ANONYMOUS DONOR; RAF ASSOCIATION - BOGNOR REGIS BRANCH
- **handley-page-hampden-at219**: SQUADRON MISSING: inscription mentions RCAF SQUADRON 420; COMMUNITY CONNECTION MISSING: The memorial is located at RAF Waddington, which suggests a strong connection to the local community and its military presence.
- **handley-page-hampden-p4313**: CREW MISSING: inscription has 4 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: Erected by THE MANX AVIATION PRESERVATION SOCIETY
- **hp-hampden-p1206**: CRASH DATE MISSING: inscription states 1941-11-08; COMMUNITY CONNECTION MISSING: The remains were donated by the Royal Netherlands Air Force
- **hp-hampden-x3027-plaque**: CREW MISSING: inscription has 4 crew names but crew list is empty
- **international-mosquito-air-and-ground-crew-memorial**: COMMUNITY CONNECTION MISSING: The memorial is for Allied Mosquito Air and Ground Crews who served on worldwide operations during and after World War II. It was sponsored by the Mosquito Aircrew Association.
- **lancaster-bomber-nd958**: SQUADRON MISSING: inscription mentions 3 LFS; COMMUNITY CONNECTION MISSING: names / IN MEMEMRY OF THE CREW WHO DIED
- **lancaster-bombers-ed730-and-nd327**: CREW MISSING: inscription has 14 crew names but crew list is empty
- **lancaster-r5672**: CREW MISSING: inscription has 9 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: This plaque has been donated by Caistor and District Lions
- **lancasters-jb670-and-lm332**: COMMUNITY CONNECTION MISSING: in the parish of Ulceby
- **lancasters-me625-and-nd981**: COMMUNITY CONNECTION MISSING: unveiled by the relatives for the 70th anniversary
- **laughterton-1-eh940**: COMMUNITY CONNECTION MISSING: integrated into the community_connection field; FTR MEMORIAL: Granite identifies this as a Failed to Return memorial, not a local crash site
- **lincoln-high-school-ww2-aircrash-memorial**: CREW MISSING: inscription has 4 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: GREESTONES
- **moordown-jp137**: COMMUNITY CONNECTION MISSING: Organised by the Moortown 2010 Committee as a contribution to the Bicentenary of Bournemouth.
- **normanton-on-soar-bomber-crash**: COMMUNITY CONNECTION MISSING: Normanton on Soar
- **north-lopham-mid-air-collision-b-17-44-6137-the-abo**: SERIAL NUMBER MISSING: inscription mentions 44-6137, 43-38746; COMMUNITY CONNECTION MISSING: SNETTERTON HEATH
- **pilot-officer-h-e-rath-and-sergeant-k-m-miegel**: COMMUNITY CONNECTION MISSING: The memorial was erected by Lillian Brindley, indicating a local connection and impact.
- **pilot-officers-b-w-jobling-and-f-w-weston**: COMMUNITY CONNECTION MISSING: REMEMBERED WITH PRIDE BY THEIR SONS AND FAMILIES.
- **polish-aircrew-1943-dunmoor-hill**: SERIAL NUMBER MISSING: inscription mentions R1535; SQUADRON MISSING: inscription mentions 301 POMERANIAN SQN.
- **polish-aircrew-avro-lancaster-pa269**: COMMUNITY CONNECTION MISSING: This plaque has been erected in memory of the Airmen
- **raf-bomber-a-w-whitley-z6639-and-crew**: SQUADRON MISSING: inscription mentions No 24 O.T.U; COMMUNITY CONNECTION MISSING: R.A.F HONEYBOURNE WORCS
- **raf-wellington-aircrew**: COMMUNITY CONNECTION MISSING: WITHINGTON / ON
- **rcaf-crew-of-raf-wellington-he821-and-pilot-officer-h-s-keeton**: COMMUNITY CONNECTION MISSING: This memorial was donated by Mr. Joseph Arthur Plant/ IN MEMORY OF HIS CLOSE FRIEND - RAF PILOT OFFICER/ HERBERT SYDNEY KEETON OF CRESWELL/
- **royal-canadian-air-force-crew-vickers-wellington-bk387**: COMMUNITY CONNECTION MISSING: memorial for those who lost their lives on this site
- **scredington-ed439**: COMMUNITY CONNECTION MISSING: Highgate Farm Scrodington, a local area
- **sergeant-f-rowney-and-flight-sergeant-t-barker-and-handley-page-hampden-ad854**: COMMUNITY CONNECTION MISSING: The inscription mentions that the crash site is close to where the surviving crew members landed, indicating a local connection.
- **sergeant-t-butterley-and-sergeant-a-priest-vickers-wellington-r1538**: CRASH DATE MISSING: inscription states 1943-01-30; COMMUNITY CONNECTION MISSING: Wymeswold
- **short-stirling-bk770**: CRASH DATE MISSING: inscription states 1943-04-09; SQUADRON MISSING: inscription mentions 75 (NZ) Squadron R.A.F
- **short-stirling-bk784**: CRASH DATE MISSING: inscription states 1944-05-23; CREW MISSING: inscription has 7 crew names but crew list is empty
- **short-stirling-eh940-and-avro-lancaster-lm292**: CREW MISSING: inscription has 5 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: killed in action at Kettlethorpe
- **short-stirling-eh977**: SQUADRON MISSING: inscription mentions 1660 Heavy Conversion Unit; COMMUNITY CONNECTION MISSING: Based at RAF Swinderby. Commissioned and erected by the Lincolnshire Aircraft Recovery Group for the 70th Anniversary on behalf of the families.
- **short-stirling-eh988**: COMMUNITY CONNECTION MISSING: In MEMORY OF/ IN FRIENDSHIP AND IN SERVICE
- **short-stirling-lj450**: COMMUNITY CONNECTION MISSING: erected by Theaker Family and GP CAPT MP. COLLEY, STATION COMMANDER RAF CRANWELL
- **short-stirling-lj930**: CRASH DATE MISSING: inscription states 1945-04-20; COMMUNITY CONNECTION MISSING: WINDLESHAM, SURREY
- **short-stirling-lk116**: COMMUNITY CONNECTION MISSING: ADJACENT TO THE RIVER CHELMER / IN THE FIELDS BEHIND OAKROYD AVENUE
- **short-stirling-n3703**: SQUADRON MISSING: inscription mentions XV Squadron; COMMUNITY CONNECTION MISSING: honours their sacrifice, and all those who flew with XV Squadron, and recognises the service they gave to their country in its time of need
- **short-stirling-r9245**: SQUADRON MISSING: inscription mentions 75 (NZ) SQUADRON RAF; COMMUNITY CONNECTION MISSING: Ake Ake KIA KAHA
- **short-stirling-r9329**: COMMUNITY CONNECTION MISSING: We Will Remember Them
- **short-stirling-w7441**: COMMUNITY CONNECTION MISSING: This memorial is dedicated to the memory of all airmen and airwomen who were injured, reported missing, or died while in service of their country. It was erected by SAC(T) Jamie Fowler.
- **short-stirling-w7467**: COMMUNITY CONNECTION MISSING: The people of Earith, 7 Squadron Association and this Stone remember them
- **short-stirling-w7473-handley-page-halifax-hr832-and-bristol-blenheim-z7278**: COMMUNITY CONNECTION MISSING: The parish of Clenchwarton, Stirling W 7473; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **short-stirling-w7628**: COMMUNITY CONNECTION MISSING: The memorial is for those killed in the crash of a Stirling bomber at Cliffe, indicating local community connection.
- **short-stirling-x9-y-worry**: COMMUNITY CONNECTION MISSING: The crew were among the first British to land in Oslo, Norway at the end of hostilities and were also involved in the repatriation of POWs as the Allies advanced on Germany.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **st-egwin-s-church-norton-and-lenchwick-ww2-wellington-memorial**: SQUADRON MISSING: inscription mentions 24 OTU, RAF Honeybourne; COMMUNITY CONNECTION MISSING: This village
- **stow-bedon-blenheim-v-5851**: SERIAL NUMBER MISSING: inscription mentions V5851; COMMUNITY CONNECTION MISSING: The memorial is for the community of Watton, likely a local response to the loss of these young men.
- **two-avro-lancaster-crews-st-peter-ad-vincula**: COMMUNITY CONNECTION MISSING: The memorial was erected in grateful appreciation of their sacrifice by George and Alma Sparrow, indicating a local connection.
- **ulceby-cross-pb476**: COMMUNITY CONNECTION MISSING: commemoration of crew members who died
- **vautour-mitchell-crash-site**: AIRCRAFT TYPE MISSING: inscription mentions DE HAVILLAND MOSQUITO NFXIII; SERIAL NUMBER MISSING: inscription mentions NFXIII-MM573
- **vickers-wellington-bj697**: COMMUNITY CONNECTION MISSING: Memorial to crash site
- **vickers-wellington-bk352**: COMMUNITY CONNECTION MISSING: Wellington Bomber of 17 0TU RAF Turweston
- **vickers-wellington-bk491**: COMMUNITY CONNECTION MISSING: Nash End Farm
- **vickers-wellington-dv697**: COMMUNITY CONNECTION MISSING: donated by the members of the ROYAL BRITISH LEGION. The Australian High Commission have donated this Eucalyptus Tree as a symbol/ of the homeland of these countrymen who perished here in the course of duty.
- **vickers-wellington-dv771**: COMMUNITY CONNECTION MISSING: memorial to the crew of Wellington bomber DV771
- **vickers-wellington-dv930**: CREW MISSING: inscription has 5 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: THE PEOPLE OF CHEDISTON
- **vickers-wellington-he159**: SQUADRON MISSING: inscription mentions 424(TIGER) SQUADRON RCAF; COMMUNITY CONNECTION MISSING: UNVEILED ON THE 6OTH ANNIVERSARY BY THE GRATEFUL PEOPLES OF CANADA AND ROLVENDEN AND PAID FOR BY PUBLIC SUBSCRIPTION
- **vickers-wellington-he320**: CRASH DATE MISSING: inscription states 1944-01-09; COMMUNITY CONNECTION MISSING: of Rainham, Essex. / of Big River, Saskatchewan,/ Canada
- **vickers-wellington-he702**: COMMUNITY CONNECTION MISSING: In memory of the crew; FTR MEMORIAL: Granite identifies this as a Failed to Return memorial, not a local crash site
- **vickers-wellington-he818-and-handley-page-halifax-na581**: COMMUNITY CONNECTION MISSING: BLYTH; HODSOCK; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **vickers-wellington-hf570**: CRASH DATE MISSING: inscription states 1944-09-05; COMMUNITY CONNECTION MISSING: The memorial is erected at RAF Desborough, indicating a strong community connection.
- **vickers-wellington-hf641**: COMMUNITY CONNECTION MISSING: over Roade
- **vickers-wellington-hz251**: COMMUNITY CONNECTION MISSING: The Fallen/ They have passed beyond the stress and storm of mortal strife/ through the gateways of the morning to a wider life/ asking only this of us, that we with faith/ and pride/ remember in the after years the things for/ which they died.
- **vickers-wellington-ln181**: CREW MISSING: inscription has 8 crew names but crew list is empty
- **vickers-wellington-lp397**: SQUADRON MISSING: inscription mentions RAF WYMESWOLD / NO 93 GROUP BOMBER; COMMUNITY CONNECTION MISSING: RAF WYMESWOLD / Heritage Group 2011
- **vickers-wellington-lp841-stone**: COMMUNITY CONNECTION MISSING: With Thanks To All The Young Men And Women Who Came From Foreign Shores To Help Our Country In A Time Of Need
- **vickers-wellington-lp841-tablet**: SQUADRON MISSING: inscription mentions 82 O.T.U.; COMMUNITY CONNECTION MISSING: LAXTON
- **vickers-wellington-mf116**: SQUADRON MISSING: inscription mentions 26 OTU, R.A.F. WING, OXFORDSHIRE; CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-mp624**: CRASH DATE MISSING: inscription states 1943-08-24; COMMUNITY CONNECTION MISSING: This stone marks the 50th anniversary of their sacrifice.
- **vickers-wellington-n2749**: SQUADRON MISSING: inscription mentions 27 OTU / RAF Lichfield; COMMUNITY CONNECTION MISSING: community_connection: The Royal British Legion Milford Haven Branch erected this memorial for the Pembrokeshire Aviation Group.
- **vickers-wellington-nb824**: COMMUNITY CONNECTION MISSING: The crash site was at RAF Langham, which is a local airfield.
- **vickers-wellington-nz-n**: SQUADRON MISSING: inscription mentions 304 POLISH SQUADRON; CREW MISSING: inscription has 4 crew names but crew list is empty
- **vickers-wellington-r1465**: COMMUNITY CONNECTION MISSING: The inscription mentions that the memorial is for those who died, indicating a local connection and community impact.
- **vickers-wellington-r1646-and-all-other-aircrew-killed-over-the-cairngorms**: COMMUNITY CONNECTION MISSING: Six crew members lie at rest with the Commonwealth Graves Commission Reservation, Dyce Old Churchyard, Aberdeen and two in their home cemeteries in England.; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **vickers-wellington-t2520**: COMMUNITY CONNECTION MISSING: The inscription mentions 'ALL WERE KILLED', indicating a significant local impact and community connection.
- **vickers-wellington-w5365**: CRASH DATE MISSING: inscription states 1941-02-08
- **vickers-wellington-w5667**: COMMUNITY CONNECTION MISSING: Commonside, Old Leake
- **vickers-wellington-x-hf465**: CRASH DATE MISSING: inscription states 20.10.1944; COMMUNITY CONNECTION MISSING: The memorial is for a crash site in Bridgmere, indicating local community connection.
- **vickers-wellington-z8397**: CREW MISSING: inscription has 6 crew names but crew list is empty
- **vickers-wellington-z8863**: COMMUNITY CONNECTION MISSING: This memorial is dedicated to the crew of Wellington Mk 1c Z8863 KO-G of 115 Squadron; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **vickers-wellingtons-hf517-and-mf589**: COMMUNITY CONNECTION MISSING: Dutch, Canadian and British Airmen
- **vickers-wellingtons-ln532-and-lp172**: COMMUNITY CONNECTION MISSING: The memorial is in Whittlebury, indicating a local connection; MULTIPLE EVENTS: memorial commemorates more than one event — verify crash_date is for the correct event
- **weasenham-r-a-f-aircrew-ww-ii**: CREW MISSING: inscription has 4 crew names but crew list is empty; COMMUNITY CONNECTION MISSING: North American Mitchell II, FL206, 98 Sqn. Flt. Sgt. D.C. Tanner RAFVR Sgt. E.H. Boreham RAFVR Sgt. L.H. Horton RAFVR LAC. F.E. Barnett RAFVR Douglas Boston III, AL285, 342 'Lorraine' Sqn.
- **wellington-bomber-crash-westbury-may-1943**: COMMUNITY CONNECTION MISSING: near the village of Westbury
- **wellington-bomber-crash**: COMMUNITY CONNECTION MISSING: This memorial was erected to their honour in 1988
- **wellington-bomber-he740**: SQUADRON MISSING: inscription mentions UNIT 11 O.T.U. AT WESTCOTT; CREW MISSING: inscription has 6 crew names but crew list is empty
- **wellington-bomber-he746**: COMMUNITY CONNECTION MISSING: Presented to the museum by Sgt Mullis' daughter / on October 4th 2000
- **wellington-bomber-mk-x-mf509**: SERIAL NUMBER MISSING: inscription mentions MF509; CREW MISSING: inscription has 6 crew names but crew list is empty
- **wellington-r1392-crash**: SQUADRON MISSING: inscription mentions 304 POLISH SQUADRON; CREW MISSING: inscription has 4 crew names but crew list is empty
- **wellington-x-he-324-crash**: SERIAL NUMBER MISSING: inscription mentions X HE 324; CREW MISSING: inscription has 6 crew names but crew list is empty

---
*Generated 2026-04-13 00:54:08 | Corrections file: /root/repos/bomber-memorial-site/scripts/../inscription-corrections.json*