---
task: Photo integration UX design for WW2 memorial site
slug: 20260412-120000_photo-integration-ux
effort: Deep
phase: complete
progress: 48/48
mode: ALGORITHM
started: 2026-04-12T12:00:00Z
updated: 2026-04-12T12:00:00Z
---

## Context

Bomber Memorial site (bombermemorial.co.uk) is a WW2 Bomber Command memorial register built in Next.js (static export). Aesthetic: dark navy #1a2332, gold #c9b98a, cream #f8f6f2, brown #8b7355. Max width 900px. Audience: researchers, historians, families, local community.

2,591 photo claims across 192 memorials. 726 unique, non-icon, OK images scraped so far. Avg 709x542px. No licences cleared — display with credit and opt-out later. Photo types are mixed: plaques, crash sites, crew portraits, landscapes, ceremonies, buildings.

The request is to produce a comprehensive UX recommendation document covering 10 topic areas: classification taxonomy, hero treatment, contextual integration, metadata display, multi-photo handling, quality grading, mobile layout, empty state, performance, and accessibility.

### Risks

- No licence clearance: legal exposure if display credit is insufficient for some source tiers
- Uneven distribution (1 photo vs 61 photos): layout must work at both extremes without looking broken
- Crew photo detection relies on caption keyword matching — may misclassify
- Static export constrains: no server-side image processing, no CDN resize, blur placeholders need pre-generation
- Heritage audience includes older users with assistive tech — accessibility bar is high
- Mobile breakpoint at 600px — memorials with many photos need graceful degradation

## Criteria

- [x] ISC-1: Photo classification taxonomy defines at least 8 named categories
- [x] ISC-2: Each taxonomy category has a render treatment description
- [x] ISC-3: Taxonomy includes crew-portrait category with crew section mapping
- [x] ISC-4: Taxonomy includes memorial-exterior category with hero eligibility rule
- [x] ISC-5: Taxonomy includes crash-site category with contextual placement rule
- [x] ISC-6: Taxonomy includes landscape/setting category with placement rule
- [x] ISC-7: Taxonomy includes historical-document category with render treatment
- [x] ISC-8: Taxonomy includes remembrance-ceremony category with placement rule
- [x] ISC-9: Hero selection criteria defined: which categories are hero-eligible
- [x] ISC-10: Hero selection criteria defined: minimum quality threshold for hero
- [x] ISC-11: Hero display treatment defined for 1 photo (single full-width)
- [x] ISC-12: Hero display treatment defined for 2-3 photos (side-by-side or carousel)
- [x] ISC-13: Hero mobile treatment defined (<600px breakpoint)
- [x] ISC-14: Hero fallback defined when no eligible photo exists
- [x] ISC-15: Contextual mapping table defined: each category maps to a page section
- [x] ISC-16: Duplication prevention rule defined (each photo appears in max 1 section)
- [x] ISC-17: Section layout defined for single photo within a section
- [x] ISC-18: Section layout defined for 2-4 photos within a section
- [x] ISC-19: Metadata display spec: credit always visible (not hover-only)
- [x] ISC-20: Metadata display spec: caption visible below image
- [x] ISC-21: Metadata display spec: source domain format defined
- [x] ISC-22: Metadata display spec: date_taken display when present
- [x] ISC-23: Metadata hover/expand treatment defined for secondary fields
- [x] ISC-24: Multi-photo rule defined: threshold for "show more" vs show all
- [x] ISC-25: Lightbox behaviour specified for enlarged photo view
- [x] ISC-26: Horizontal scroll strip treatment specified for ceremony/condition strips
- [x] ISC-27: Quality grading system defines at least 4 grade levels
- [x] ISC-28: Quality grade criteria defined: dimensions threshold
- [x] ISC-29: Quality grade criteria defined: has-caption weighting
- [x] ISC-30: Quality grade criteria defined: source tier weighting
- [x] ISC-31: Quality grade criteria defined: is-duplicate penalty
- [x] ISC-32: Quality grade visual indicator defined (badge, tint, or filter)
- [x] ISC-33: Mobile layout defined for hero section (<600px)
- [x] ISC-34: Mobile layout defined for section photo grids (<600px)
- [x] ISC-35: Mobile layout defined for lightbox (<600px)
- [x] ISC-36: Mobile touch targets sized to minimum 44x44px
- [x] ISC-37: Empty state UI defined for zero-photo memorials
- [x] ISC-38: Empty state CTA defined (contribute photos)
- [x] ISC-39: Performance: lazy loading strategy defined
- [x] ISC-40: Performance: blur placeholder strategy defined for static export
- [x] ISC-41: Performance: above-fold photo loading strategy (eager) defined
- [x] ISC-42: Accessibility: alt text strategy defined for memorial photos
- [x] ISC-43: Accessibility: alt text strategy defined for crew portraits
- [x] ISC-44: Accessibility: focus management defined for lightbox open/close
- [x] ISC-45: Accessibility: screen reader announcement defined for photo count
- [x] ISC-46: Component names defined for all major photo UI components
- [x] ISC-47: ASCII wireframe provided for hero section layout
- [x] ISC-48: ASCII wireframe provided for crew section photo strip

## Decisions

## Verification
