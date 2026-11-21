# 02 — Opportunity Research

**Evidence labels:**
- **[F]** verified fact with a source (see `SOURCES.md`)
- **[A]** reasonable assumption
- **[H]** hypothesis that still needs validation
- **[U]** something I believe from prior knowledge but did **not** re-verify in this session

I didn't survey domains evenly. I used the competition signals (Resurrection rewards "dead tech that still matters"; Innovation rewards combining public datasets; Technological Implementation rewards Kiro-native tooling) to choose where to dig deeper. Domains I only skimmed are listed at the end with their status.

---

## O1. Dead scripts that still decide who owns land (India)

| Question | Findings |
|---|---|
| Who has the problem? | Landowners, revenue officials, courts and historians in Bihar (Kaithi script) and Maharashtra (Modi script). |
| How often? | **[F]** Bihar's 2024 special land survey stalled because old khatiyan records are in Kaithi. Most districts have **fewer than 10 Kaithi readers**, who charge high fees. The survey covers **more than 25 crore** revenue documents [S13][S14]. **[F]** Around **40 million** Modi-script documents are cited as not yet transliterated, held mainly in Pune archives; only "a few experts" can read them [S15][S16]. |
| Current solution | **[F]** Bihar made Kaithi classes mandatory for surveyors and brought in readers from Uttar Pradesh [S13]. **[F]** In 2025 Bihar signed an MoU with **Digital India Bhashini** for AI transliteration of Kaithi [S17]. **[F]** IIT Roorkee researchers published the **MoDeTrans** dataset (2,043 images) and the MoScNet vision-language model for Modi → Devanagari [S16]. |
| Why it's still unsolved | **[F]** A Sept 2026 benchmark (**KhatianDoc**) found that six multimodal LLMs (8B–72B+) got **zero correct answers** on 39.3% of question types for handwritten Bengali land records [S18]. Handwritten historical-script recognition is a capability that current models lack, not a gap prompting can close. |
| Could a hackathon demo it convincingly? | **Unlikely.** The core feature, accurate recognition, needs data and training we can't secure and validate in 13 days. The government and IIT Roorkee are already working on it. |

**Verdict:** the highest-impact problem I found, and the least feasible for a 13-day build.

---

## O2. Business data trapped inside legacy software that can only print

| Question | Findings |
|---|---|
| Who has the problem? | Small and mid-size clinics, diagnostic labs, retailers and SMEs running old desktop software (DOS-era, Visual FoxPro, VB6, abandoned vendor builds) that cannot talk to modern APIs. |
| Evidence the problem is real | **[F]** India's health digitisation push (ABDM) names "the large installed base of legacy hospital management systems" with "no ABDM-compliant API layer" as a main challenge, and says lab software vendors have been slow to add ABDM support (HMPI, July 2026) [S19]. **[F]** ABDM's own incentive policy admits that "easy to use software to assist the small clinics and hospitals is also a significant challenge" [S20]. **[F]** The Digital Health Incentive Scheme pays facilities for every digital health record they link to a patient's ABHA ID (up to ₹4 crore per facility). Facilities on uncertified or legacy software can become ineligible [S20][S21]. **[F]** Visual FoxPro lost extended support in 2015. Data vendors still count thousands of companies using it, with India among the top countries (the vendors' numbers disagree with each other) [S22]. |
| How it's solved today | (1) Replace the system: expensive, risky, staff retraining. (2) Vendor-built integration: often not on offer, since many vendors are gone. (3) Screen-scraping RPA (UiPath etc.) **[U]**. (4) **Report mining**: [F] Altair/Datawatch **Monarch** has parsed printed reports and spool files since **1990** using hand-built templates [S23]. A 35-year-old commercial category is strong evidence that "data trapped in printouts" is a real enterprise problem. (5) Virtual receipt printers: [F] escpos-netprinter (open source, renders receipts to HTML for viewing), Color Pilot's Virtual POS Printer (text/PDF extraction), virtual-printer.online (a testing emulator with a JSON API) [S24][S25][S26]. |
| What's wrong with existing solutions | Monarch needs a hand-built template per report and is priced for enterprises. Receipt emulators stop at text or HTML, with no meaning extracted, no checks that the output is correct, and no connection to the destinations people actually need (FHIR health records, GST invoices). RPA is fragile and needs a desktop session. Nothing targets small Indian facilities. **[A]** |
| What would be much better | Install nothing in the legacy app. Point its printer at us. AI learns each report layout once and **writes a deterministic parser for it**, which is verified by property checks. After that, extraction is instant and free and sends no data to an LLM. Output goes to real destinations such as FHIR/ABDM records, GST invoice JSON, spreadsheets or webhooks, and the physical printout still comes out. |
| Important enough? | **[A]** Yes: interoperability is a national policy priority with money attached (DHIS), and legacy integration is a global pain. **[H]** How many small Indian labs or clinics run software that only prints is unknown. **Validate this in the first 72 hours by talking to 3–5 local labs, clinics or shops.** |
| Could a hackathon demo it convincingly? | Yes. It's software-only: a virtual network printer on port 9100, decoders, an AI parser builder and a dashboard. The "magic moment" (an old app hits Print and a structured health record appears) is visual and fits in seconds. |

**Verdict:** strong. Real problem, proven commercial demand (Monarch), a clear gap (AI-built verified parsers plus modern destinations), feasible, demoable, and a natural Resurrection fit.

---

## O3. Research integrity: trial outcome switching and "zombie" citations

| Question | Findings |
|---|---|
| Problem | Clinical trials whose published outcomes differ from the registered ones, unreported trial results, and papers that keep citing retracted work. |
| Evidence | **[F]** The FDA wrote to more than **2,200 sponsors** about missing trial results in March 2026 [S27]. **[F]** The Problematic Paper Screener has flagged **764,000+** articles that cite retracted works [S28]. |
| Existing solutions | **[F]** **RegCheck** (an LLM tool) detects outcome misreporting with **85.6% accuracy** against COMPare [S29]. **[F]** Mayo-Wilson et al. (npj Digital Medicine, 2026) detect registry outcome changes with sensitivity 0.97 [S30]. **[F]** FDAAA TrialsTracker (Oxford) is live [S27]. **[F]** The Feet of Clay Detector and **RetractoBot** already flag and notify citations of retracted papers [S28]. **[F]** A Nov 2026 study found that citing retracted papers is a weak predictor of future retraction: 84% of later retractions cite no retracted paper [S31]. |
| Gap | Academic tools exist but are scattered. A reviewer-friendly product that combines CTRI (India's trial registry), ClinicalTrials.gov and publications is still open. |
| Verdict | Real but **academically crowded**; our differentiation would come from UX, not innovation. Moderate impact story for a developer judging panel. |

---

## O4. Data leakage in ML code (including code written by AI agents)

- **[F]** Leakage affects at least 294 papers across 17 fields (Kapoor & Narayanan, *Patterns* 2023) [S32].
- **[F]** Tools already exist: Yang et al. (ASE '22) static detector; **LeakageDetector 2.0** for VS Code; scicode-lint; **leakray** (CLI/CI); and **unleak**, which already ships *an agent skill plus a write hook for Claude Code, Codex and Cursor* [S33].
- **Verdict:** crowded right where we would aim. Rejected.

---

## O5. Checking that LLM-migrated legacy code still behaves the same

- **[F]** This is a very active 2026 research area: the "Locksmith Loop" COBOL→Java parity gate, AgentModernize, "Articulate but Wrong" (models misjudge whether their own migrations preserved behaviour), and "Accepted but Wrong" on silent failures after API migrations [S34]. Commercially, AWS's own modernization tools sit here **[U]**.
- **Gap:** a lightweight, developer-facing tool that compares old and new versions with property-based tests. It would fit Kiro's PBT feature well.
- **Risk:** it competes in the sponsor's own product space, the impact story is abstract, and the demo is dry.

---

## O6. Digital Public Infrastructure developer tooling (Beckn/ONDC)

- **[F]** The official open-source **Beckn-ONIX** (plus an ONDC fork and a Google Cloud DPI Accelerator) already provides adapters for signing, schemas, registry and routing [S35].
- **Verdict:** the gap has been closed by official tools. Rejected.

---

## O7. What Kiro itself enables (developer-platform opportunity)

- **[F]** **Kiro Crew** (open-sourced 4 Aug 2026; long-running Bots added 5 Nov 2026) supports installable **Apps** that can contribute agents, skills, MCP servers, cron jobs, dashboard pages and backends through an `app.json` manifest [S8][S9].
- **[F]** **Powers** are installable bundles of skills and MCP config that activate on keywords [S10]. **Hooks** support `PostFileSave`, `PreToolUse`, `PostToolUse` and `Stop`, with command or agent actions [S11]. **PBT** turns requirements into properties and shrinks failing cases, IDE only [S36].
- **Opportunity:** the Crew App ecosystem is three months old, so the **Best Kiro Crew App** bonus probably has few strong entrants **[H]**. Any product can add a small Crew App companion to deepen its Kiro story.

---

## Domains skimmed but not researched in depth

| Domain | Idea area | Why I didn't go deeper |
|---|---|---|
| Climate/heat | Ward-level heat-vulnerability planning | Likely competition from big-tech heat tools **[U]**; heavy data work |
| Disaster | Broadcasting data over radio when the internet fails | Hardware and licensing |
| Water | Acoustic leak detection | Hardware, no ground truth |
| Accessibility | AI tactile graphics and Braille for STEM diagrams | Promising **[H]**. The output is physical (embossers), which is hard to show judges. Parked as a future idea |
| Civic tech | RTI (Right to Information) drafting copilot; missed-call/IVR access to services | Mostly LLM wrappers; the IVR/WhatsApp space is crowded **[U]** |
| Consumer IoT | Reviving smart devices bricked by cloud shutdowns | Needs physical devices; the "AI writes the integration" claim can't be proven in a demo |
| Cybersecurity | Leaked-secret scanners; dependency "graveyards" | Mature tools exist **[U]** |

---

## Cross-cutting insights that shaped the ideas
1. **AI as a compiler, not a runtime.** Where reliability matters, the strongest designs use the LLM *once* to produce a deterministic, testable artifact (a parser, a mapping, a migration), then run that artifact without the LLM. This answers the "generic LLM wrapper" criticism, reduces hallucinations, cuts cost and keeps private data away from the LLM. It also mirrors Kiro's own spec → code → property-test philosophy.
2. **The dead technology should be the *interface*, not the subject.** Faxi won because the user keeps their trusted old device. The equivalent here is that the clinic keeps its old software.
3. **Avoid problems where government or big-lab capability is the bottleneck** (O1), and areas already covered by official open-source tools (O6) or agent hooks (O4).
