---
version: alpha
name: Spoolgeist Greenbar
description: An operations workbench for resurrected print jobs. Warm neutrals carry the chrome. The captured printout is the hero, rendered as continuous green-bar paper in IBM Plex Mono with a line-accounting gutter. Colour exists only to mean something (accepted, needs confirmation, refused, unknown layout); one phosphor-green accent marks the primary action. A ghost glyph appears in exactly one place, on content the system could not explain.
colors:
  # dark theme ("spool room"), the default
  canvas: "#1B1916"
  surface-1: "#24211D"
  surface-2: "#2E2A25"
  hairline: "#3D3832"
  control-border: "#7A7266"
  ink: "#F2EDE4"
  body: "#D2CBBF"
  muted: "#A39B8E"
  primary: "#7EE2A8"
  on-primary: "#12110F"
  accepted: "#7EE2A8"
  accepted-tint: "#1F3326"
  confirm: "#F0BC5E"
  confirm-tint: "#3A2F19"
  refused: "#FF8A80"
  refused-tint: "#3A2220"
  unknown: "#B7AFCB"
  info: "#8EC2FF"
  focus: "#8EC2FF"
  # light theme ("greenbar paper")
  light-canvas: "#FBFAF6"
  light-surface: "#FFFFFF"
  light-greenbar: "#EAF3E8"
  light-hairline: "#DDD8CC"
  light-control-border: "#8A8377"
  light-ink: "#1D1B17"
  light-body: "#3C3832"
  light-muted: "#625C52"
  light-primary: "#17673F"
  light-accepted: "#17673F"
  light-accepted-tint: "#E3F1E8"
  light-confirm: "#7A4F00"
  light-confirm-tint: "#FBF0DA"
  light-refused: "#A8231B"
  light-refused-tint: "#FBE6E4"
  light-unknown: "#574F6E"
  light-focus: "#1F4FB8"
typography:
  display:  { fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif", fontSize: 28px, fontWeight: 600, lineHeight: 1.2, letterSpacing: -0.3px }
  title:    { fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif", fontSize: 20px, fontWeight: 600, lineHeight: 1.3 }
  body:     { fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif", fontSize: 15px, fontWeight: 400, lineHeight: 1.5 }
  label:    { fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif", fontSize: 13px, fontWeight: 600, lineHeight: 1.3, letterSpacing: 0.2px }
  caption-mono: { fontFamily: "'IBM Plex Mono', ui-monospace, monospace", fontSize: 12px, fontWeight: 500, lineHeight: 1.4, letterSpacing: 0.3px }
  printout: { fontFamily: "'IBM Plex Mono', ui-monospace, monospace", fontSize: 13px, fontWeight: 400, lineHeight: 1.6 }
  data:     { fontFamily: "'IBM Plex Mono', ui-monospace, monospace", fontSize: 14px, fontWeight: 500, lineHeight: 1.4, fontVariantNumeric: tabular-nums }
rounded: { none: 0px, xs: 2px, sm: 4px, full: 9999px }
spacing: { xxs: 2px, xs: 4px, sm: 8px, md: 12px, base: 16px, lg: 24px, xl: 32px, xxl: 48px }
components:
  button-primary: { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", typography: "{typography.label}", rounded: "{rounded.sm}", padding: 8px 14px }
  button-secondary: { backgroundColor: "transparent", textColor: "{colors.ink}", border: "1px solid {colors.control-border}", typography: "{typography.label}", rounded: "{rounded.sm}", padding: 8px 14px }
  button-danger: { backgroundColor: "transparent", textColor: "{colors.refused}", border: "1px solid {colors.refused}", rounded: "{rounded.sm}" }
  tile: { backgroundColor: "{colors.surface-1}", border: "1px solid {colors.hairline}", rounded: "{rounded.none}", padding: 16px }
  status-badge: { typography: "{typography.caption-mono}", rounded: "{rounded.xs}", padding: 2px 6px }
  printout-sheet: { backgroundColor: "{colors.light-canvas}", stripe: "{colors.light-greenbar}", textColor: "{colors.light-ink}", typography: "{typography.printout}" }
---

# Spoolgeist Greenbar: design system

## Overview
Spoolgeist is a workbench, not a marketing page. Its users verify that a machine got a document **exactly** right, or see precisely why it refused. The design therefore has three jobs:
1. **Make the printout the hero.** The captured job is shown as what it was: continuous-form green-bar paper, fixed-width, every line numbered.
2. **Make evidence legible at a glance.** A gutter beside every printout line states how that line was explained (result row, field, static, note) or that it was not.
3. **Let colour mean one thing each.** The chrome is warm neutral. Colour appears only for state and for the single primary action.

**Theme:** dark ("spool room") is the default, honouring Kiroween's "code in dark mode". The printout sheet stays light paper in both themes, as the physical artefact. A full light theme ("greenbar paper") exists for accessibility and for daylight demos.

**Key characteristics**
- Square tiles with 1px hairlines; no drop shadows. Depth comes from the surface ladder canvas → surface-1 → surface-2 (IBM-style structural discipline).
- Two type families: Atkinson Hyperlegible Next for interface text; IBM Plex Mono for printouts, values, identifiers, hashes and technical captions.
- Tabular numerals everywhere numbers are compared.
- One accent, phosphor green (`primary`), for the primary action and the "accepted" state. These are deliberately the same: the happy path is green.
- **Ghost glyph** (a small outlined ghost with "?") appears **only** in the gutter of an unexplained line and on the "refused: unexplained content" reason. It is the one spooky element, and it carries meaning.

## Colors (roles; all text pairs meet WCAG 2.1 AA, most AAA)
| Role | Dark | Contrast on canvas | Light | Contrast on canvas | Used for |
|---|---|---|---|---|---|
| ink | #F2EDE4 | 15.0 | #1D1B17 | 16.5 | headings, primary text |
| body | #D2CBBF | 10.9 | #3C3832 | 11.2 | running text |
| muted | #A39B8E | 6.4 | #625C52 | 6.3 | secondary text, timestamps |
| primary / accepted | #7EE2A8 | 11.1 | #17673F | 6.6 | primary button, accepted state |
| confirm | #F0BC5E | 10.1 | #7A4F00 | 6.8 | "needs confirmation" (free text present) |
| refused | #FF8A80 | 7.7 | #A8231B | 6.9 | refused, destructive actions |
| unknown | #B7AFCB | 8.4 | #574F6E | 7.3 | unknown layout, no active rule |
| info / focus | #8EC2FF | 9.5 | #1F4FB8 | 7.0 | links, focus ring (2px outline + 2px offset) |
| control-border | #7A7266 | 3.7 | #8A8377 | 3.6 | input and button borders (≥ 3:1 non-text requirement) |
| hairline | #3D3832 | 1.5 | #DDD8CC | 1.4 | decorative dividers only, never the sole boundary of a control |

**Status tints** (badge and row backgrounds) keep the status text ≥ 5.9:1:
- accepted: dark 8.6, light 5.9;
- confirm: dark 7.5, light 6.3;
- refused: dark 6.4, light 6.0.

**Rule:** state is never shown by colour alone. Every status badge carries a word and an icon (✓ accepted, ◐ confirm, ✕ refused, ? unknown).

## Typography
| Style | Use |
|---|---|
| display 28/600 | page title (one per view) |
| title 20/600 | panel headings |
| body 15/400 | text, descriptions |
| label 13/600 | buttons, field labels, table headers |
| caption-mono 12/500 | technical captions: SHA-256 prefixes, rule versions, timestamps |
| printout 13/1.6 Plex Mono | the captured document; no reflow, horizontal scroll if needed |
| data 14/500 tabular Plex Mono | extracted values, units, reference ranges |

## Layout
- **App shell:** a 56px top bar (product mark, queue status, theme toggle) and a 220px left navigation (Inbox, Rules, Audit, Settings) that collapses to an icon rail below 1200px.
- **Inbox:** a dense table with rows 40px tall. Columns: status, received, layout/rule, patient (masked to initials + id suffix in the list), source (capture or replay).
- **Job view** (the signature screen), as a three-column split:
  1. the printout sheet with its line-accounting gutter (≥ 50%);
  2. the extracted record (fields + results table with flag, range and unit);
  3. the decision panel (status, reasons, actions: confirm, refuse, download FHIR).
  - Clicking a result highlights its source line(s), and vice versa.
- **Rule onboarding:** a stepper (Samples → Candidate → Gate → Approve). The gate step lists the 9 conditions as a checklist with counts, plus the adversarial mutations as a compact table (mutation, tried, rejected).
- **Grid:** 8px base with a 4px half-step; panels separate with 1px hairlines and 16px gutters.
- **Breakpoints:**
  - ≥ 1440: three columns;
  - 1024–1439: printout + record, with decisions in a drawer;
  - 768–1023: stacked tabs;
  - < 768: read-only summary.
  - Review actions require ≥ 768 px, and the UI says so explicitly instead of degrading silently.

## The line-accounting gutter (signature component)
A 28px gutter left of each printout line. Each glyph also has a tooltip and screen-reader text, e.g. "Line 14: result row, Haemoglobin".

| Glyph | Meaning |
|---|---|
| ▌ green | consumed by a result row |
| ▌ info | field value (identity or date) |
| ▌ muted | static template / approved header |
| ✎ confirm | approved note (free text, needs confirmation) |
| ghost-with-? (outlined SVG icon) in refused colour | **unexplained**: the reason the job was refused |

## Elevation and motion
- **No shadows.** Overlays (dialogs, drawers) use surface-2 plus a 1px control-border and a 40% canvas scrim.
- **Motion:** 120ms ease-out for state changes; a single 600ms "print-head" sweep the first time a printout renders (respects `prefers-reduced-motion`: no sweep).

## States
- **Empty inbox:** "No print jobs yet". Shows the local capture address (e.g. `127.0.0.1:9100`) or a "Replay a sample print job" button. No illustration.
- **Loading:** skeleton rows in surface-2, with no spinners on lists.
- **Error:** an inline refused-tinted banner with what failed, what was kept (the original job is always persisted) and the next action.
- **Unknown layout:** an unknown-tinted panel. Primary action: "Onboard this layout".

## Data visualisation
Only where counts matter: gate mutations, and the sealed-evaluation summary on the About page.
- Horizontal bars with direct labels and raw counts ("216 / 216 rejected"), never percentages alone.
- Status colours as above; no pie charts.

## Accessibility (WCAG 2.1 AA, target AAA for text)
- Keyboard: every action reachable. `j`/`k` move through the inbox; `Enter` opens; `c` confirm and `x` refuse, both with a confirmation dialog.
- A visible focus ring in `focus`. Accessible labels on gutter glyphs. No information by colour alone.
- Printout text selectable and zoomable to 200% without loss.
- Language and timestamps in ISO format plus local time.

## Demo-only surface: "the legacy system"
- The fake 1998 lab application used in the demo is styled as a DOS/text-mode program: 80×25 grid, blue background, grey text. It is clearly separate from Spoolgeist.
- Inspired by the period-web references (Dell 1996, Nintendo 2001) only in spirit: it is the patient being resurrected, not the product.
