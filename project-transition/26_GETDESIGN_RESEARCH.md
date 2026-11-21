# 26: GetDesign.md research (22 Nov 2026)

## 1. What GetDesign.md actually is (inspected today)
- **Site:** https://getdesign.md, "DESIGN.md collection for AI coding agents", maintained by the VoltAgent team.
- **Format:** each entry is a DESIGN.md file. The format comes from Google Stitch: YAML tokens (colours, typography, rounding, spacing, components) plus a prose rationale (Overview, Colors, Typography, Layout, Elevation, …).
- **Catalogue:**
  - The home page claims "550+ DESIGN.md analyses, ready to request", most of them paid or private ("DESIGN.md Pro", "Catalog Pass").
  - The **free set** is the ~90 entries listed on the home page and mirrored in the MIT-licensed GitHub repository `VoltAgent/awesome-design-md` (`design-md/<slug>/DESIGN.md`).
- **Official install instruction**, shown on each entry page: `npx getdesign@latest add <slug>`. We did **not** run it, because it executes a third-party package. We downloaded the same files as plain markdown from the MIT-licensed repository (commit recorded in `design-references/SOURCE_COMMIT.txt`), so no code was executed.
- **Key limitation:** every entry is an interpretation of a company's **public marketing website**, not of an in-product operations UI. The site says so itself: "The goal is not 'copy Vercel.' It is to give the agent a starting language." None of the entries is a ready-made design for a dense review tool.
- **Cookies:** declined non-essential cookies on the site.

## 2. Candidates explored
- **Scanned:** all ~90 free entries, from the descriptions on the home page.
- **Read in full and preserved:** 18 relevant files, unmodified, in `project-transition/design-references/<slug>/DESIGN.md`, plus the repository licence.

| Candidate | Why considered | Fit for our workflows (inbox, document review with line-level evidence, gate report, approval, audit) | Verdict |
|---|---|---|---|
| **IBM** (Carbon interpretation) | enterprise data density; square tiles; one accent; hairlines instead of shadows | **High** for tables, forms and audit; accessibility culture | **Structural reference** (layout discipline, square geometry, hairline tiles). We do **not** use IBM Blue or IBM branding |
| **OpenCode** | fully monospaced, cream "manpage" canvas, ASCII markers, 4px radius | **High** for the *document surface*: our core object is a fixed-width printout | **Document-surface reference** (mono, paper canvas, bracket markers), *not* for app chrome (all-mono hurts scanning) |
| **Warp** | warm near-charcoal canvas, terminal blocks, very tight radii | High for a dark theme with warmth; fits "code in dark mode" | **Dark-theme reference** (warm neutrals, tight radii) |
| Linear | precise dark product UI, surface ladder | high for an inbox | rejected as the lead: very widely imitated, so low originality; its surface-ladder idea is reused generically |
| Raycast | hairline dark cards, command palette | medium | rejected: a command-palette idiom doesn't serve our review flow |
| Sentry | developer triage brand, playful mascots | medium; issue-triage resemblance | rejected: lime/violet brand too loud for clinical-adjacent data; mascots risk undercutting trust |
| Supabase | monochrome + one green CTA, dashboard mockups | medium | rejected as the lead: close to our needs but generic |
| Vercel | black/white precision, mono captions | medium | mono-caption idea reused for technical labels |
| Ollama | README-like minimalism | low for dense UI | rejected |
| WIRED | broadsheet density, hairline story rows | medium for audit and timeline lists | the row-density idea is noted |
| Dell 1996 / Nintendo 2001 | period web aesthetics: literal "dead tech" | **low for usability and accessibility** | rejected for the app. **Used only to inspire the fake "legacy lab system" in the demo** (the thing being resurrected), never the product UI |
| ClickHouse, HashiCorp | black canvas + one voltage colour | low (marketing-heavy) | rejected |
| Airtable, Notion | spreadsheet / workspace, pastel cards | medium for tables | rejected: pastel database chips conflict with the status semantics we need |
| Mintlify | documentation density, mono for code | medium | 3-column doc layout considered for the gate report; not adopted |
| Oracle | warm neutral ladder, one charcoal action colour | medium | the "neutral ladder, colour only for meaning" principle is adopted |

## 3. Approaches compared
| Approach | Pros | Cons |
|---|---|---|
| A single reference (e.g. IBM) | coherent, fast | marketing-derived; generic; weak identity for Design and Innovation scores |
| An existing open design system (Carbon itself) | accessible components | heavy; looks like IBM; time to integrate |
| **A hybrid: original product system informed by 3 references** | identity tied to *our* object (the printout); accessible; small token set we control | we must write and maintain the spec (report 27) |
| A fully original system with no references | maximum originality | slower; no external calibration |

## 4. Decision: an original system, "Greenbar", informed by IBM (structure), OpenCode (document surface) and Warp (dark warmth)
- **Why it fits the product:** the hero object is the **captured printout**. Continuous-form "green-bar" tractor-feed paper is the literal dead technology being resurrected. Rendering the printout as green-bar paper with a **line-accounting gutter** makes the core innovation visible: every line is explained, or the job is refused, and you can see which line and why.
- **Why it supports the workflows:** IBM-style square tiles, hairlines and dense tables suit inbox, audit and gate-report lists. One functional accent plus strict status semantics stop colour from competing with evidence.
- **Why not copy:**
  - No IBM Blue, no Berkeley Mono, no Warp brand colours.
  - Fonts are open: **Atkinson Hyperlegible Next** (UI; designed for legibility, OFL) and **IBM Plex Mono** (documents and data; OFL).
  - Colours are our own and contrast-checked (report 27).
- **Kiroween fit:** a restrained "spectral" phosphor-green accent and a ghost glyph used **only** as the marker for *unexplained content*, the poltergeist in the spool. Playful in one place, never at the expense of trust or legibility.
- **Rejected reference ideas, explicitly:** mascots, gradients, pastel chips, all-monospace chrome, retro period styling in the product UI.

## 5. Preserved files
- `project-transition/design-references/<slug>/DESIGN.md`: 18 files, unmodified.
- `LICENSE-awesome-design-md` (MIT).
- `SOURCE_COMMIT.txt` (upstream commit).
