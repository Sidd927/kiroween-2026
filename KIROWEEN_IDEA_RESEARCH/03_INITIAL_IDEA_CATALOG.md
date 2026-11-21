# 03 — Initial Idea Catalog (28 concepts)

Every idea uses the same compact template:

- **A** Identity
- **B** Problem
- **C** Product
- **D** Technical approach
- **E** Differentiation
- **F** Feasibility
- **G** Competition potential

The critique and verdict for each idea are in `04_IDEA_ELIMINATION.md`. Evidence labels match `02` ([F] fact, [A] assumption, [H] hypothesis, [U] unverified in this session).

How the ideas split by category: Resurrection 8 · Frankenstein 10 · Skeleton Crew 5 · Costume Contest 5.

---

## RESURRECTION

### R1. Spoolgeist: give legacy software an API by possessing its printer
- **A:** Resurrection · Healthcare and SME interoperability · Users: small diagnostic labs, clinics, retailers and the integrators who serve them. *"Every legacy app can print. Point it at Spoolgeist and its printouts become live, structured data."*
- **B:** Legacy systems (DOS, Visual FoxPro, VB6, abandoned vendor software) hold critical data but have no API. ABDM names legacy hospital software without an API layer as a main barrier [F]. Legacy facilities can lose DHIS incentives [F]. Today's options are costly replacement, hand-built report-mining templates (Monarch [F]), or fragile RPA.
- **C:** A virtual network printer (raw 9100/JetDirect, plus web upload). It decodes print streams (plain text with control codes, ESC/POS thermal, PostScript/PDF), and AI builds a **"Binding"**: a declarative, deterministic parser for each report layout, checked by properties. Each job is turned into FHIR R4 DiagnosticReport (ABDM-profile-shaped), GST e-invoice JSON, webhooks or Sheets. The physical printout still prints.
- **D:** Python asyncio capture agent. Decoders (custom ESC/POS parser; Ghostscript text extraction in a sandbox). A "print lattice", i.e. a grid of each character's position. Layout fingerprinting. An LLM (model-agnostic: Claude via Bedrock or Anthropic API) writes Binding DSL in JSON; an interpreter runs it; property checks validate it; a repair loop feeds counterexamples back. LOINC/UCUM mapping. Next.js dashboard with click-a-field-to-see-its-source highlighting. Postgres. **What's new:** the LLM acts as a compiler from print streams to verified parsers, with redaction while the parser is built and no LLM in steady state.
- **E:** Monarch (manual templates, enterprise), receipt emulators (text/HTML only), document AI (scanned images, per-call LLM), RPA. Nobody found combines print-stream capture, AI-built *verified* parsers and health/tax destinations for small facilities.
- **F:** MVP of about 95h, ideal about 150h. No external API that needs approval in the critical path. Main risks: varied print formats and the reliability of AI-built parsers.
- **G:** Could win because it's a visual "magic moment", a developer-relatable pain, a social-impact story (clinics) and Kiro-shaped engineering. Could lose if judges see it as "just document extraction". Strongest criteria: Innovation and Tech. Weakest: proving impact without real users. Good student-prize fit.

### R2. Lipi Lazarus: reading land records written in dead scripts
- **A:** Resurrection · Gov/legal · Users: landowners, revenue officials, lawyers, historians. *"The script is dead; the land claims are not."*
- **B:** Kaithi and Modi records are needed to prove ownership. Readers are scarce, and the Bihar survey stalled [F].
- **C:** Upload a scan. Get line segmentation, transliteration to Devanagari, a modern Marathi/Hindi/English rendering, per-glyph confidence, and a human correction loop.
- **D:** Fine-tune a VLM or TrOCR on MoDeTrans; synthesise training data from Noto Kaithi/Modi fonts; active learning from corrections.
- **E:** IIT Roorkee MoScNet [F], the Bhashini–Bihar MoU [F], academic OCR work. No public consumer tool found.
- **F:** Training data is limited (2,043 Modi images; Kaithi barely available) and the license may be non-commercial [U]. Zero-shot models fail on land records [F]. MVP accuracy is uncertain.
- **G:** The highest emotional and impact story. Highest feasibility risk. Weakest criterion: demo reliability.

### R3. Necromancer: bringing abandoned libraries back, with a proof of equivalence
- **A:** Resurrection · Developer tooling · Users: maintainers and teams stuck on dead runtimes (Python 2, old Node, deprecated APIs).
- **B:** Migrating abandoned code with an LLM silently changes behaviour; even the models misjudge their own migrations [F, S34].
- **C:** A Kiro Power plus CLI. Run the old library in its old runtime (Docker) as the reference ("oracle"), let Kiro migrate it, then auto-generate property tests that compare old and new outputs and issue an "equivalence certificate".
- **D:** Docker legacy runtimes, Hypothesis/fast-check, a type-strict comparison layer, Kiro hooks and PBT, an MCP server that runs the oracle.
- **E:** Research prototypes (Locksmith Loop, AgentModernize) [F]; commercial modernization services from large vendors [U].
- **F:** About 120h. Generating inputs for arbitrary APIs is hard; restrict to pure-function libraries.
- **G:** Excellent Kiro story (PBT, hooks, Power). Dry demo, abstract impact, and close to the sponsor's own products.

### R4. Lazarus Lab: getting research code from papers running again
- **A:** Resurrection · Science · Users: researchers and reviewers.
- **B:** Code published with papers often doesn't run (reproducibility crisis) [U].
- **C:** An agent infers the environment, fixes dependency problems, runs the code, and compares results with the figures in the paper.
- **D:** Sandboxed containers, an LLM agent, figure-number extraction.
- **E:** Existing research benchmarks for agents setting up repos, which report low success rates [U]; Code Ocean and Binder [U].
- **F:** Needs heavy compute and sandboxing; success rates are low and demos unreliable.
- **G:** Strong story, unreliable demo.

### R5. Dataset Necropolis: bringing back dead dataset links cited in papers
- **A:** Resurrection · Research data · Users: researchers and librarians.
- **B:** Dataset links in papers break, and US government data takedowns in 2025 made this worse [U].
- **C:** Scan a paper's references, find archived copies (Wayback, Zenodo, mirrors), verify them by checksum and schema, and produce repaired citations.
- **D:** Wayback CDX API, OpenAlex, schema fingerprinting.
- **E:** Internet Archive's IABot (for Wikipedia) [U], Perma.cc [U], community data-rescue projects [U].
- **F:** Feasible.
- **G:** Low "wow"; feels like a utility script.

### R6. HyperStack: HyperCard reborn with AI
- **A:** Resurrection · End-user programming · Users: teachers, hobbyists.
- **B:** Non-programmers lost a simple way to build small tools when HyperCard died.
- **C:** Card-and-stack apps built with natural-language scripting.
- **D:** A canvas editor, an LLM that generates HyperTalk-like scripts, a sandboxed runtime.
- **E:** Decker (a modern HyperCard-like tool) [U] and every AI app builder (Lovable, Bolt, etc.).
- **F:** Feasible.
- **G:** Nostalgic, but a crowded field and a vague audience.

### R7. Afterlife: reviving smart-home devices bricked by cloud shutdowns
- **A:** Resurrection · Consumer IoT · Users: owners of abandoned devices.
- **B:** Cloud shutdowns brick devices [U].
- **C:** An agent finds the device's local protocol and generates a local bridge or Home Assistant integration.
- **D:** Network discovery, protocol inference, code generation.
- **E:** Home Assistant community integrations, Tasmota [U].
- **F:** Needs physical devices that are rare in India; the general claim can't be demonstrated.
- **G:** Great story, can't be demoed honestly.

### R8. Ceefax-over-FM: text broadcasting for disasters
- **A:** Resurrection · Disaster communications · Users: disaster agencies.
- **B:** When the internet fails, information stops flowing.
- **C:** AI-summarised alerts broadcast as RDS/teletext-style data over FM.
- **D:** SDR transmission, summarisation.
- **E:** Cell Broadcast and NDMA SACHET alerts [U].
- **F:** Transmitting needs a licence; hardware.
- **G:** Not feasible.

---

## FRANKENSTEIN

### F1. Ghost Trials: catching clinical trials whose outcomes quietly changed
- **A:** Frankenstein · Research integrity · Users: journal editors, systematic reviewers, research-integrity officers.
- **B:** Published outcomes differ from registered ones; results go unreported [F].
- **C:** Paste a DOI. The tool finds the registration (ClinicalTrials.gov, CTRI), aligns registered and published outcomes using the SPIRIT/CONSORT elements, and produces a "haunting report".
- **D:** ClinicalTrials.gov API v2, CTRI pages, PubMed/Europe PMC full text, LLM outcome alignment, version-diffing of registrations.
- **E:** RegCheck (85.6% accuracy) [F], npj 2026 tool (0.97 sensitivity) [F], TrialsTracker [F].
- **F:** About 90h; data is public. CTRI scraping is fragile [A].
- **G:** Solid but academic; innovation lags existing research.

### F2. Sand Sentinel: spotting illegal river sand mining
- **A:** Frankenstein · Environment · Users: NGOs, journalists, district officials.
- **B:** Illegal sand mining damages rivers [U].
- **C:** Detect changes in Sentinel-2 imagery along rivers, compare against licensed lease polygons, and produce evidence packets.
- **D:** Earth Engine or Sentinel Hub, change detection, LLM-written reports.
- **E:** Academic studies, Global Forest Watch-style platforms [U].
- **F:** Lease-boundary data probably isn't openly available [H]; no ground truth.
- **G:** Visual, but the data dependency is fatal.

### F3. Spreadsheet Exorcist: verified migration of critical spreadsheets to code
- **A:** Frankenstein · Finance/research · Users: analysts, NGOs, public agencies.
- **B:** High-stakes spreadsheets hide errors [U].
- **C:** Use the spreadsheet itself as the reference; generate Python; prove the two match with property tests; flag suspicious formulas.
- **D:** openpyxl/formulas evaluation, Hypothesis, an LLM.
- **E:** Spreadsheet auditing tools (PerfectXL, ExceLint) [U].
- **F:** About 110h.
- **G:** Clever, but the demo is dry; overlaps with R3.

### F4. HeatShield: ward-level heat-vulnerability planning
- **A:** Frankenstein · Climate · Users: municipal heat-action-plan officers.
- **B:** Heat action plans lack local vulnerability data [U].
- **C:** Combine Landsat surface temperature, OSM buildings, census and IMD forecasts into ward risk scores and cooling-centre siting.
- **D:** Geospatial pipelines, ML risk model.
- **E:** Big-tech heat resilience tools [U], academic dashboards.
- **F:** Data-heavy; validation weak.
- **G:** Worthy, but a common pattern.

### F5. Community Radio Newsroom
- **A:** Frankenstein · Agriculture/media · Users: community radio stations.
- **B:** Small stations lack staff to make local-language agricultural bulletins [H].
- **C:** Daily audio bulletins built from mandi prices and IMD forecasts, read by Indic text-to-speech.
- **D:** data.gov.in APIs, LLM, Indic TTS.
- **E:** Gram Vaani and similar IVR platforms [U].
- **F:** Feasible.
- **G:** Weak category fit; quality of Indic TTS is a risk.

### F6. MissedCall Civic: access to grievance systems by phone
- **A:** Frankenstein · Civic · Users: citizens without smartphones.
- **B:** Grievance portals are hard to use without a smartphone.
- **C:** IVR plus LLM files and tracks grievances.
- **D:** Telephony API, ASR/TTS, LLM.
- **E:** Many government and NGO chatbots and IVRs [U].
- **F:** Telephony costs; India telecom regulations.
- **G:** Crowded wrapper.

### F7. Leak Listener: finding water leaks by sound
- **A:** Frankenstein · Utilities · Users: water utilities.
- **B:** Non-revenue water losses [U].
- **C:** Phone microphones plus GIS to locate leaks.
- **D:** Audio ML.
- **E:** Commercial acoustic loggers [U].
- **F:** No labelled data, hardware.
- **G:** Not feasible.

### F8. Second Sight Mesh: old phones as edge-AI sensors
- **A:** Frankenstein · E-waste/edge AI · Users: communities, schools.
- **B:** E-waste; sensors are expensive [U].
- **C:** Repurpose old Android phones as sensing nodes.
- **D:** On-device YOLO, mesh sync.
- **E:** Home-camera apps like Alfred [U]. **Overlaps with our earlier Anchor project.**
- **F:** Feasible, but derivative.
- **G:** Reject: recycles our own earlier work.

### F9. Tactile: AI-generated tactile graphics for blind STEM students
- **A:** Frankenstein · Accessibility · Users: special educators, blind students.
- **B:** Producing accessible STEM diagrams is slow [H].
- **C:** Textbook figure → simplified tactile SVG plus Braille labels (BRF).
- **D:** Vision model, SVG simplification, Liblouis.
- **E:** BrailleBlaster, TactileView [U], academic work [U].
- **F:** The physical output is hard to demo. Not enough research done this session.
- **G:** Promising; parked.

### F10. RTI Copilot: drafting Right to Information requests
- **A:** Frankenstein · Civic · Users: citizens, journalists.
- **B:** Drafting and tracking RTI requests is hard.
- **C:** Draft the RTI, route it to the right authority, track deadlines, draft appeals.
- **D:** LLM plus a rules engine.
- **E:** RTI services and portals [U].
- **F:** Feasible.
- **G:** Wrapper; low innovation.

---

## SKELETON CREW

### S1. Leakproof: an ML pipeline template where leakage can't happen
- **A:** Skeleton Crew · ML engineering · Users: data scientists.
- **B:** Leakage inflates results [F].
- **C:** A typed pipeline template plus leakage properties (e.g. permuting test labels must not change the trained model), with Kiro hooks. Apps: readmission prediction, energy forecasting.
- **D:** sklearn, Hypothesis, static checks.
- **E:** unleak (already includes an agent hook), leakray, LeakageDetector 2.0, scicode-lint [F].
- **F:** Feasible.
- **G:** Beaten by existing tools.

### S2. Beckn Bones: a Kiro-native ONDC/Beckn kit
- **A:** Skeleton Crew · Digital public infrastructure · Users: ONDC developers.
- **C:** Template plus Power. Apps: kirana-store seller, EV charging.
- **E:** Beckn-ONIX, ONDC fork, Google DPI Accelerator [F].
- **G:** Covered by official tools.

### S3. Grimoire: a Kiro-native template for building Kiro Crew Apps
- **A:** Skeleton Crew · Developer platform · Users: Kiro Crew app developers.
- **B:** Crew Apps are 3 months old; docs are thin and there are few examples [F/A].
- **C:** A template (app.json, backend, UI page, skill, cron) plus steering, hooks and PBT for manifest invariants. Apps: an on-call triage bot, a study-group scheduler bot.
- **D:** Crew SDK (TypeScript/Python), MCP, Kiro powers.
- **E:** The official example apps [F].
- **F:** Crew is new and its APIs may change; documentation risk.
- **G:** Maximum Kiro depth; small audience; impact story limited to Kiro users.

### S4. Provenance Kit: a template for document AI with source citations
- **A:** Skeleton Crew · Document AI · Users: developers building extraction apps.
- **C:** A template where every extracted value carries its source location and confidence, plus a review queue. Apps: invoices, lab reports.
- **E:** LlamaParse, Unstructured, cloud document-AI services [U].
- **G:** Generic as a standalone; **merged into R1's Binding engine.**

### S5. A11y Ward: a template that enforces accessibility
- **A:** Skeleton Crew · Accessibility · Users: front-end teams.
- **C:** WCAG enforced by hooks (axe-core on save) plus steering. Apps: a government form, e-commerce.
- **E:** axe linters, Lighthouse CI [U].
- **G:** Low novelty.

---

## COSTUME CONTEST

### C1. Patient Zero: a contagion map of zombie citations
- **A:** Costume · Research integrity · Users: reviewers, science journalists, Wikipedia editors.
- **B:** Retracted papers keep being cited [F].
- **C:** A spooky contagion graph: a retracted paper is "patient zero"; citing papers are "infected", and an LLM reads each citation's context to judge whether the citing paper *relies* on the retracted finding.
- **D:** Crossref Retraction Watch data, OpenAlex, Semantic Scholar citation contexts [U], LLM classification, a WebGL graph.
- **E:** Feet of Clay, RetractoBot, Zotero retraction alerts [F/U]. A 2026 study says the signal is weak [F].
- **F:** About 80h.
- **G:** Strong design potential; differentiation and impact weak.

### C2. Haunted Codebase
- Technical debt shown as a haunted house. **E:** CodeCity-style visualisations [U] and *The Digital Exorcist* (a 2025 winner) [F]. Derivative.

### C3. Zombie Dependency Graveyard
- A software bill of materials drawn as a graveyard of abandoned dependencies. **E:** Socket, Snyk, deps.dev, OpenSSF Scorecard [U]. Crowded.

### C4. Phish House
- A haunted-house phishing trainer. Crowded corporate-training market [U].

### C5. The Séance Desk
- A spooky genealogy UI on top of R2. The name collides with *Seance* (2025 Best Costume) [F], and it inherits R2's feasibility problem.
