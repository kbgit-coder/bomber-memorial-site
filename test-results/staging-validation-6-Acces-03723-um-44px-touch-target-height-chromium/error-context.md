# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: staging-validation.spec.ts >> 6. Accessibility >> Key interactive elements have minimum 44px touch target height
- Location: tests/staging-validation.spec.ts:560:7

# Error details

```
Error: Nav anchors below 44px touch target: "Bomber Command Memorial Register" height=34px

expect(received).toHaveLength(expected)

Expected length: 0
Received length: 1
Received array:  ["\"Bomber Command Memorial Register\" height=34px"]
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - banner [ref=e2]:
    - generic [ref=e3]:
      - link "Bomber Command Memorial Register" [ref=e4] [cursor=pointer]:
        - /url: /
      - navigation [ref=e5]:
        - link "Home" [ref=e6] [cursor=pointer]:
          - /url: /
        - link "Regions" [ref=e7] [cursor=pointer]:
          - /url: /region/united-kingdom
        - link "Squadrons" [ref=e8] [cursor=pointer]:
          - /url: /squadron
        - link "Search" [ref=e9] [cursor=pointer]:
          - /url: /search
        - link "Insights" [ref=e10] [cursor=pointer]:
          - /url: /insights
        - link "About" [ref=e11] [cursor=pointer]:
          - /url: /about
  - main [ref=e12]:
    - generic [ref=e13]:
      - generic [ref=e14]:
        - heading "Bomber Command Memorial Register" [level=1] [ref=e16]:
          - text: Bomber Command
          - text: Memorial Register
        - paragraph [ref=e17]: The stories behind the memorials that communities built to remember the crews who fell near their homes.
        - paragraph [ref=e18]: Other registers record the losses. We record the people who chose to remember — the parishes, the families, and the villages where the connection endures, passed from one generation to the next.
        - generic [ref=e20]:
          - generic [ref=e21]:
            - generic [ref=e22]: "466"
            - generic [ref=e23]: Memorials
          - generic [ref=e24]:
            - generic [ref=e25]: "9"
            - generic [ref=e26]: Countries
          - generic [ref=e27]:
            - generic [ref=e28]: 1,347
            - generic [ref=e29]: Crew Recorded
      - textbox "Search memorials by name, location, aircraft, squadron, or crew..." [ref=e33]
      - generic [ref=e34]:
        - heading "Browse by Region" [level=2] [ref=e35]
        - paragraph [ref=e36]: Explore memorials across 9 countries.
        - generic [ref=e37]:
          - link "United Kingdom (435)" [ref=e38] [cursor=pointer]:
            - /url: /region/united-kingdom
            - text: United Kingdom
            - generic [ref=e39]: (435)
          - link "Netherlands (10)" [ref=e40] [cursor=pointer]:
            - /url: /region/netherlands
            - text: Netherlands
            - generic [ref=e41]: (10)
          - link "France (6)" [ref=e42] [cursor=pointer]:
            - /url: /region/france
            - text: France
            - generic [ref=e43]: (6)
          - link "Belgium (5)" [ref=e44] [cursor=pointer]:
            - /url: /region/belgium
            - text: Belgium
            - generic [ref=e45]: (5)
          - link "Germany (4)" [ref=e46] [cursor=pointer]:
            - /url: /region/germany
            - text: Germany
            - generic [ref=e47]: (4)
          - link "Denmark (3)" [ref=e48] [cursor=pointer]:
            - /url: /region/denmark
            - text: Denmark
            - generic [ref=e49]: (3)
          - link "Australia (1)" [ref=e50] [cursor=pointer]:
            - /url: /region/australia
            - text: Australia
            - generic [ref=e51]: (1)
          - link "Norway (1)" [ref=e52] [cursor=pointer]:
            - /url: /region/norway
            - text: Norway
            - generic [ref=e53]: (1)
          - link "Luxembourg (1)" [ref=e54] [cursor=pointer]:
            - /url: /region/luxembourg
            - text: Luxembourg
            - generic [ref=e55]: (1)
          - link "Canada (0)" [ref=e56] [cursor=pointer]:
            - /url: /region/canada
            - text: Canada
            - generic [ref=e57]: (0)
          - link "New Zealand (0)" [ref=e58] [cursor=pointer]:
            - /url: /region/new-zealand
            - text: New Zealand
            - generic [ref=e59]: (0)
      - generic [ref=e60]:
        - heading "Featured Memorials" [level=2] [ref=e61]
        - paragraph [ref=e62]: Some of the most detailed records in the register — showcasing crew stories, photographs, and community contributions.
        - generic [ref=e63]:
          - link "Farnsfield Halifax MZ519 Memorial Comprehensive 5 external sources Farnsfield, Nottinghamshire, Nottinghamshire1944-07-06 Handley Page Halifax Mk.III MZ519 • 578 Squadron The only operational combat loss in the Farnsfield area. P/O Parfitt's crew had bombed V-1 launch sites that afternoon. Crossing back over Dieppe, heavy anti-aircraft fire struck the Halifax. One engi... 7 crew recorded Read the full story →" [ref=e64] [cursor=pointer]:
            - /url: /memorial/farnsfield-halifax-mz519
            - generic [ref=e65]:
              - generic [ref=e66]:
                - heading "Farnsfield Halifax MZ519 Memorial" [level=3] [ref=e67]
                - generic [ref=e68]:
                  - generic [ref=e69]: Comprehensive
                  - generic [ref=e70]: 5 external sources
              - generic [ref=e71]:
                - text: Farnsfield, Nottinghamshire
                - generic [ref=e72]: ", Nottinghamshire"
                - text: 1944-07-06
              - generic [ref=e73]: Handley Page Halifax Mk.III MZ519 • 578 Squadron
              - paragraph [ref=e74]: The only operational combat loss in the Farnsfield area. P/O Parfitt's crew had bombed V-1 launch sites that afternoon. Crossing back over Dieppe, heavy anti-aircraft fire struck the Halifax. One engi...
              - generic [ref=e75]:
                - generic [ref=e76]: 7 crew recorded
                - generic [ref=e77]: Read the full story →
          - link "Elsham Wolds — Black Swan Memorial (Halifax JD386) Comprehensive 2 external sources Elsham Wolds, Lincolnshire, Lincolnshire1944-02-29 Halifax JD386 • 1666 HCU Flying from their station at Elsham Wolds, the crew of Halifax JD386 were undertaking a training sortie with 1666 Heavy Conversion Unit when the aircraft crashed on 29 February 1944. Pilot Officer Joh... 7 crew recorded Read the full story →" [ref=e78] [cursor=pointer]:
            - /url: /memorial/elsham-wolds-jd386
            - generic [ref=e79]:
              - generic [ref=e80]:
                - heading "Elsham Wolds — Black Swan Memorial (Halifax JD386)" [level=3] [ref=e81]
                - generic [ref=e82]:
                  - generic [ref=e83]: Comprehensive
                  - generic [ref=e84]: 2 external sources
              - generic [ref=e85]:
                - text: Elsham Wolds, Lincolnshire
                - generic [ref=e86]: ", Lincolnshire"
                - text: 1944-02-29
              - generic [ref=e87]: Halifax JD386 • 1666 HCU
              - paragraph [ref=e88]: Flying from their station at Elsham Wolds, the crew of Halifax JD386 were undertaking a training sortie with 1666 Heavy Conversion Unit when the aircraft crashed on 29 February 1944. Pilot Officer Joh...
              - generic [ref=e89]:
                - generic [ref=e90]: 7 crew recorded
                - generic [ref=e91]: Read the full story →
          - link "Cloot Drove Lancaster Mid-Air Collision Memorial Comprehensive 4 external sources Cloot Drove, Deeping Fen, Lincolnshire, Lincolnshire1944-06-23 Lancaster III ME625 and ND981 • 97 Squadron Six Lancasters of 97 Squadron took off from RAF Coningsby on the afternoon of 23 June 1944 for formation flying practice. Fl/Lt Van Raalte's Lancaster ME625 (OF-O) became trapped in the slipstream of ... 14 crew recorded Read the full story →" [ref=e92] [cursor=pointer]:
            - /url: /memorial/cloot-drove-nd981-and-lancaster-me625-mid-air-collision-
            - generic [ref=e93]:
              - generic [ref=e94]:
                - heading "Cloot Drove Lancaster Mid-Air Collision Memorial" [level=3] [ref=e95]
                - generic [ref=e96]:
                  - generic [ref=e97]: Comprehensive
                  - generic [ref=e98]: 4 external sources
              - generic [ref=e99]:
                - text: Cloot Drove, Deeping Fen, Lincolnshire
                - generic [ref=e100]: ", Lincolnshire"
                - text: 1944-06-23
              - generic [ref=e101]: Lancaster III ME625 and ND981 • 97 Squadron
              - paragraph [ref=e102]: Six Lancasters of 97 Squadron took off from RAF Coningsby on the afternoon of 23 June 1944 for formation flying practice. Fl/Lt Van Raalte's Lancaster ME625 (OF-O) became trapped in the slipstream of ...
              - generic [ref=e103]:
                - generic [ref=e104]: 14 crew recorded
                - generic [ref=e105]: Read the full story →
          - link "Kirkley (Lowestoft) Halifax Memorial Comprehensive 4 external sources Kirkley (Lowestoft), Suffolk, Suffolk1944-04-27 Halifax LL356 • 138 (SD) Squadron On the night of 27/28 April 1944, Halifax LL356 departed the secret airfield at RAF Tempsford on its 13th operation, carrying supplies destined for Belgian resistance fighters in German-occupied Europ... 8 crew recorded Read the full story →" [ref=e106] [cursor=pointer]:
            - /url: /memorial/kirkley-lowestoft-ll356
            - generic [ref=e107]:
              - generic [ref=e108]:
                - heading "Kirkley (Lowestoft) Halifax Memorial" [level=3] [ref=e109]
                - generic [ref=e110]:
                  - generic [ref=e111]: Comprehensive
                  - generic [ref=e112]: 4 external sources
              - generic [ref=e113]:
                - text: Kirkley (Lowestoft), Suffolk
                - generic [ref=e114]: ", Suffolk"
                - text: 1944-04-27
              - generic [ref=e115]: Halifax LL356 • 138 (SD) Squadron
              - paragraph [ref=e116]: On the night of 27/28 April 1944, Halifax LL356 departed the secret airfield at RAF Tempsford on its 13th operation, carrying supplies destined for Belgian resistance fighters in German-occupied Europ...
              - generic [ref=e117]:
                - generic [ref=e118]: 8 crew recorded
                - generic [ref=e119]: Read the full story →
  - contentinfo [ref=e120]:
    - generic [ref=e121]:
      - generic [ref=e122]:
        - heading "Bomber Command Memorial Register" [level=3] [ref=e123]
        - paragraph [ref=e124]: Honouring the memorials, crash sites, and aircrew of RAF Bomber Command, 1939–1945. We will remember them.
      - generic [ref=e125]:
        - heading "Navigate" [level=4] [ref=e126]
        - generic [ref=e127]:
          - link "Home" [ref=e128] [cursor=pointer]:
            - /url: /
          - link "FAQ" [ref=e129] [cursor=pointer]:
            - /url: /faq
          - link "Contact" [ref=e130] [cursor=pointer]:
            - /url: /contact
          - link "Site Terms" [ref=e131] [cursor=pointer]:
            - /url: /terms
      - generic [ref=e132]:
        - heading "Contribute" [level=4] [ref=e133]
        - paragraph [ref=e134]:
          - text: Know of a memorial not listed here? Have photographs, crew details, or corrections? We welcome contributions from researchers, families, and enthusiasts. Contact us at
          - link "admin@bombermemorial.co.uk" [ref=e135] [cursor=pointer]:
            - /url: mailto:admin@bombermemorial.co.uk
          - text: .
    - generic [ref=e136]: © 2026 Bomber Command Memorial Register. All rights reserved.
  - alert [ref=e137]
```

# Test source

```ts
  485 |   }) => {
  486 |     const SQUADRON_FILES = [
  487 |       "/data/squadrons/578-squadron.json",
  488 |       "/data/squadrons/106-squadron-raf.json",
  489 |       "/data/squadrons/300-masovia-squadron-paf.json",
  490 |       "/data/squadrons/166-squadron-raf.json",
  491 |       "/data/squadrons/100-squadron.json",
  492 |     ];
  493 | 
  494 |     const apiContext = await request.newContext({
  495 |       httpCredentials: { username: "keith", password: "bmr-staging-2026" },
  496 |       baseURL: "https://staging.bombermemorial.co.uk",
  497 |     });
  498 | 
  499 |     for (const file of SQUADRON_FILES) {
  500 |       const resp = await apiContext.get(file);
  501 |       expect(resp.status(), `${file} returned ${resp.status()}`).toBe(200);
  502 |       // Validate it parses as JSON
  503 |       let parsed: unknown;
  504 |       try {
  505 |         parsed = await resp.json();
  506 |       } catch (e) {
  507 |         parsed = null;
  508 |       }
  509 |       expect(parsed, `${file} is not valid JSON`).not.toBeNull();
  510 |       expect(typeof parsed).toBe("object");
  511 |     }
  512 | 
  513 |     await apiContext.dispose();
  514 |   });
  515 | });
  516 | 
  517 | // ---------------------------------------------------------------------------
  518 | // 6. Accessibility
  519 | // ---------------------------------------------------------------------------
  520 | 
  521 | test.describe("6. Accessibility", () => {
  522 |   test("Body font-size is at least 19px", async ({ page }) => {
  523 |     await page.goto("/");
  524 |     const fontSize = await page.evaluate(() => {
  525 |       const body = document.body;
  526 |       const computedSize = window.getComputedStyle(body).fontSize;
  527 |       return parseFloat(computedSize);
  528 |     });
  529 |     expect(
  530 |       fontSize,
  531 |       `Body font-size is ${fontSize}px — expected >= 19px`
  532 |     ).toBeGreaterThanOrEqual(19);
  533 |   });
  534 | 
  535 |   test("Focus-visible styles exist in loaded CSS", async ({ page }) => {
  536 |     await page.goto("/");
  537 |     const hasFocusVisible = await page.evaluate(() => {
  538 |       for (const sheet of Array.from(document.styleSheets)) {
  539 |         try {
  540 |           for (const rule of Array.from(sheet.cssRules)) {
  541 |             if (
  542 |               rule instanceof CSSStyleRule &&
  543 |               rule.selectorText?.includes(":focus-visible")
  544 |             ) {
  545 |               return true;
  546 |             }
  547 |           }
  548 |         } catch {
  549 |           // Cross-origin sheets — skip
  550 |         }
  551 |       }
  552 |       return false;
  553 |     });
  554 |     expect(
  555 |       hasFocusVisible,
  556 |       ":focus-visible rule not found in any loaded stylesheet"
  557 |     ).toBe(true);
  558 |   });
  559 | 
  560 |   test("Key interactive elements have minimum 44px touch target height", async ({
  561 |     page,
  562 |   }) => {
  563 |     await page.goto("/");
  564 | 
  565 |     // Sample the first 10 visible <a> elements in the nav/header and check
  566 |     // their bounding box height. Note: CSS sets min-height:44px globally,
  567 |     // but some anchors have min-height unset (p a, li a etc).  We check the
  568 |     // navigation anchors specifically.
  569 |     const navAnchors = page.locator("header a, nav a");
  570 |     const count = await navAnchors.count();
  571 |     const toCheck = Math.min(count, 10);
  572 | 
  573 |     const failures: string[] = [];
  574 |     for (let i = 0; i < toCheck; i++) {
  575 |       const el = navAnchors.nth(i);
  576 |       const box = await el.boundingBox();
  577 |       const text = (await el.textContent())?.trim() ?? `anchor[${i}]`;
  578 |       if (box && box.height < 44) {
  579 |         failures.push(`"${text}" height=${box.height}px`);
  580 |       }
  581 |     }
  582 |     expect(
  583 |       failures,
  584 |       `Nav anchors below 44px touch target: ${failures.join(", ")}`
> 585 |     ).toHaveLength(0);
      |       ^ Error: Nav anchors below 44px touch target: "Bomber Command Memorial Register" height=34px
  586 |   });
  587 | });
  588 | 
```