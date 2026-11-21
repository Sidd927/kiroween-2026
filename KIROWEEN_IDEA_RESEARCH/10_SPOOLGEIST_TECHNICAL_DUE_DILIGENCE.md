# 10 — Spoolgeist: Technical Due Diligence

Date: 21 Nov 2026. Approach: try to *disprove* the recommendation in `09`. Source IDs S1–S39 are in `SOURCES.md`; new sources (S40+) are listed at the end of this file and appended to `SOURCES.md`.

Labels:
- **[F]** verified this session
- **[U]** unverified
- **[H]** hypothesis
- **[T]** must be tested by us

---

## Part A — Audit of the original reports (Phase 1)

### A1. Claims that were wrong or overstated
| # | Original claim (file) | Finding | Severity |
|---|---|---|---|
| 1 | "AI-built, verified parsers… No equivalent was found" (05, 09); Innovation 16/20 (06) | **Wrong.** **Astera ReportMiner** ships **Auto-Generate Layout (AGL)**: AI analyses a printed or mainframe report and produces a *reusable extraction template in about 5 seconds*, applied to all files with the same format, with validation against business rules [S40][S41]. **Evaporate** (Stanford, VLDB 2024) had LLMs *write extraction functions* that are reused across documents, cutting LLM tokens 110× [S42]. A 1999 US patent covers "print scraping" of legacy reports via a virtual printer [S43]. The idea "an LLM compiles a reusable parser" is **not novel**. I missed this because I searched for print capture, not for AI template generation. | **Critical** |
| 2 | ABDM integration implies structured FHIR is needed (02, 09, implied) | **Wrong framing.** The ABDM IG's `DiagnosticReportLab` allows the entire report as a **PDF in `presentedForm`**. Integration guidance says to send *either* `result`, `presentedForm` or `media` [S44][S45]. **A printout can be linked to ABDM with no structured extraction at all.** Structured parsing is a nice extra, not a requirement. | **Critical** for the healthcare value proposition |
| 3 | "Nothing targets small Indian facilities" [A] (02) | **Wrong.** NHA's **100 Microsites** programme onboards small private clinics and labs and deploys ABDM-enabled HMIS [S46]. Indian lab software costs about **₹4,999–15,000 per year** (Labsmart, ClinikPe, Drlogy) and includes WhatsApp/PDF delivery [S47]. ABDM reports **450+ integrated health-tech solutions** [S48]. | High |
| 4 | "Facilities on legacy software can become ineligible for DHIS" (02, 09) | Source is a **vendor blog** [S21], not NHA. Downgrade to [U]. | Medium |
| 5 | Legacy-HMS barrier (HMPI) [S19] | **Verified verbatim**: "Many facilities run proprietary software with no ABDM-compliant API layer"; LMIS vendors "slow to build ABDM-enabled versions"; integration for mid-size providers costs **INR 30–50 lakh**. Caveat: it's a Stanford GSB *policy analysis* based on 15 interviews, and it is about **hospitals/HMIS**, not small labs. | Claim stands, but its scope is narrower than I presented |
| 6 | Feasibility MVP ≈ 95h (08) | **Optimistic.** It left out Windows VM capture testing, FHIR validator integration, the perturbation benchmark, the review UI and LOINC verification. Revised MVP: **≈125h** (see Part F). | Medium |
| 7 | Public TCP 9100 endpoint on Fly.io for judges (08, 09) | **Poor security decision.** Raw 9100 has no authentication; exposing a parser of untrusted binary data publicly is avoidable risk. **Replaced** by web upload plus a recorded live capture. | Medium |
| 8 | "Only receipt emulators exist" for capture (05) | Incomplete. **VeryPDF Printer Capture** captures PCL, PostScript and Epson streams from legacy and DOS apps (including parallel/serial) to PDF/TIFF, and claims key-data extraction [S49]. IBM i spool tools (InterForm, "40 years"; CoolSpools; Formtastic) turn spool files into JSON/XML/CSV [S50]. | High |
| 9 | Kiro facts (hooks, PBT IDE-only, Powers, Crew Apps) | **Verified**, no change. | — |
| 10 | Competition rules (deadline, categories, `.kiro`, license, video < 3 min, prize stacking) | **Re-verified** against [S2]. No misreadings found. "Skeleton Crew filters weaker teams" was a hypothesis and is now labelled as one. | — |

### A2. Scoring bias found
- **Anchoring:** Spoolgeist was the first idea that seemed to survive, and I then searched for evidence that *confirmed* the gap ("virtual printer", "receipt emulator") instead of evidence that would *break* the innovation claim ("AI template generation report mining").
- **Inflated:** Innovation 16 → about **11–12**; Impact 15 → about **11–12** (small labs have cheap alternatives; ABDM accepts PDFs).
- **Inflated internal metric:** competitive differentiation 8 → **5**.

---

## Part B — Print capture architecture (2.1)

### B1. Three separate concerns
1. **Capturing print output.** Getting the bytes the application sends to "a printer". This is mechanical. It produces a print stream in some format (plain text, ESC/P, PCL, PostScript, PDF, PWG Raster or XPS) that depends on the **driver** the user chose, not on the application.
2. **Extracting structured content.** Turning those bytes into text with positions, then into fields. This is easy for text and PostScript/PDF that contain text, and needs OCR (with an accuracy penalty) for raster.
3. **Forwarding the original job.** Sending the same bytes, or a re-rendered version, to a physical printer so the paper still comes out. This is only lossless if the physical printer understands the captured format.

**A Python program watching a PDF folder does only (2).** It's not a printer, it needs the user to click Save in a print dialog, and it can't forward.

### B2. Options compared
| Option | How it works | Complexity | Reliability / future | Dev time for us | Verdict |
|---|---|---|---|---|---|
| Native Windows printer driver (v3/v4) | Our own driver renders the job | Very high (C++, signing, ARM64 builds) | **Being phased out.** Microsoft stopped publishing new third-party drivers to Windows Update on 15 Jan 2026 and prefers its IPP class driver from Jul 2026. Windows Protected Print mode removes third-party drivers entirely [S51] | Weeks | **Reject** |
| Print processor DLL | Intercepts spooled data inside the spooler service | High (C, runs inside the spooler, crashes break printing) | Fragile; probably affected by Protected Print mode [U] | 1–2 weeks | **Reject** |
| Port monitor DLL (e.g. RedMon) | A "port" that pipes the job to a program's stdin | Medium–high; RedMon exists but its last release was 2012–2016 and only Win7/Vista/XP are documented [S52] | Unknown on Win 11 24H2 [U] | Days to integrate and test | **Reject for MVP** |
| **IPP virtual printer** (`ippeveprinter` / PAPPL) | Spoolgeist runs as an IPP Everywhere printer; Windows uses its built-in IPP Class Driver | Low on our side (CUPS's `ippeveprinter` can run a command per job, save to a directory, or forward to `socket://host:9100`) [S53] | **The future-proof path** (works under Protected Print mode). **But Windows usually converts XPS → PWG Raster** unless the printer advertises PDF [S54], and raster means OCR | 1–2 days to test | **Stretch, and test early [T]**: if we advertise `application/pdf`, does Windows send PDF that still contains text? |
| PDF printer ("Microsoft Print to PDF") | User saves a PDF | Trivial | Reliable, text-based PDF | Hours | Not zero-change (needs a Save dialog), no forwarding. **Demo fallback only** |
| Print-to-file (FILE: port) | Driver writes the stream to a file | Trivial | Prompts for a filename | Hours | Same problem as above |
| **Local queue: built-in driver + Standard TCP/IP RAW port → Spoolgeist listener → forward** | Windows' built-in **Generic / Text Only** driver (or the built-in PostScript class driver) sends to `127.0.0.1:9100` or a LAN IP; our listener captures, then forwards bytes to the physical printer's `socket://ip:9100` | **Low.** Only Windows' own drivers and a TCP server; no Windows code [S55] | Works on Win 7–11 with Protected Print mode off (opt-in, off by default [S51]). Generic/Text Only gives plain ASCII; forwarding a text-only stream gives a plain-text printout (fine for dot-matrix-era apps, poor for graphical reports) | **1 day** | **MVP choice** |
| DOS apps | `NET USE LPT1: \\localhost\SpoolgeistQueue` sends DOS LPT output into the queue above | Low | Standard Windows behaviour [U: we test it] | Hours | MVP-compatible |

### B3. The minimum *technically honest* demonstration
- A **Windows 11 ARM VM in UTM (free) on the MacBook Air M5** [U: we test it]. Inside it:
  - a "legacy" report app: Notepad or a small fixed-width report program; DOSBox-X optional;
  - printing to a **Generic / Text Only** queue whose Standard TCP/IP RAW port points at **the Mac host's Spoolgeist listener (port 9100)**.
- The Spoolgeist listener (Python asyncio) on the Mac:
  1. **captures** the raw bytes (stored with a SHA-256 hash),
  2. **forwards** the identical bytes to a "physical printer" endpoint (an `ippeveprinter` or a second listener writing to `forwarded/`; a real network printer if one is available),
  3. hands a copy to extraction.
- What we can honestly claim: *"Zero change to the application; uses only Windows' built-in drivers; the original job is forwarded byte-for-byte."*
- What we must **not** claim: support for every driver or for graphical (GDI) reports, Protected Print mode compatibility, or a Windows installer.

---

## Part C — Document extraction (2.2)

| Input | Representation | Technology | Accuracy / determinism | MVP? |
|---|---|---|---|---|
| **Raw text stream** (Generic/Text Only, DOS/ESC-P text) | Character grid (row, column) after stripping control codes; split pages on form-feeds | Own Python decoder | Exact, deterministic | **Yes (primary)** |
| ESC/POS (thermal receipts) | Grid | Own decoder (escpos-tools as reference [S37]) | Exact if the stream contains text; some drivers rasterise | Optional |
| **Text-based PDF / PostScript** | Words with x/y boxes → snapped to a grid | `pdfplumber`/`pdfminer`; Ghostscript `txtwrite` for PostScript (sandboxed; AGPL, run as a separate process) | Near-exact; column snapping needed | **Yes (secondary)** |
| Image-based PDF / PWG Raster / scans | Pixels | OCR (Tesseract/PaddleOCR) or a vision LLM | Probabilistic; dot-matrix fonts and scan quality reduce accuracy; **breaks the deterministic guarantee** | **No.** Out of scope; detect it and route to human review |
| Multi-page | Page list; repeating headers/footers | Detect page breaks; template allows "continued" table blocks | Deterministic if layout is stable | Yes (2-page case) |
| Variable layouts | Layout fingerprint (hash of static labels and their positions) | Matching against fingerprints; drift → abstain | Deterministic | Yes |

**MVP formats:** raw text streams plus text-based PDF. Everything else is explicitly unsupported and gets **abstained**, not guessed.

---

## Part D — AI-generated parsing rules (2.3)

### D1. Honest novelty position
AI-written reusable templates already exist (Astera AGL; Evaporate's code synthesis; Sensible's hybrid "generalized LLM config plus layout-specific deterministic config" [S56]). **Spoolgeist's defensible contribution is therefore not template generation.** It is:
1. **Template generation that has to be independently verified before it can go live.** A failing rule can never be activated.
2. **Abstention by construction.** Confidence is computed *deterministically* from anchor matches, pattern conformity and validator results, never self-reported by the LLM.
3. **An open, inspectable, declarative rule format.** Rules are data, not code, so it is safe to run rules the AI wrote.
4. **A measured silent-error rate** on a public synthetic perturbation benchmark.

None of the competitors found publishes a silent-error or abstention guarantee [U, absence of evidence].

### D2. Rule format ("Binding"), as JSON validated by a JSON Schema

```json5
{
  "binding_id": "lab-alpha-cbc", "version": 3, "layout_fingerprint": "sha256:…",
  "page": {"split_on": "formfeed", "repeat_header_rows": [0, 5]},
  "anchors": [{"id": "hdr", "text": "COMPLETE BLOOD COUNT", "row_hint": 6, "required": true}],
  "fields": [
    {"name": "patient.name", "type": "string", "required": true, "pii": true,
     "locate": {"anchor": "Patient Name", "direction": "right", "until": "  "}},
    {"name": "report.date", "type": "date", "formats": ["%d/%m/%Y", "%d-%b-%Y"], "required": true,
     "locate": {"anchor": "Date", "direction": "right"}}
  ],
  "tables": [{
    "name": "results", "start_after": {"regex": "^TEST\\s+RESULT\\s+UNIT"}, "end_before": {"regex": "^-{10,}|^\\*\\*\\*"},
    "columns": [
      {"name": "test", "cols": [0, 24], "type": "string"},
      {"name": "value", "cols": [24, 34], "type": "decimal", "pattern": "^-?\\d+(\\.\\d+)?$"},
      {"name": "unit", "cols": [34, 46], "type": "ucum_unit"},
      {"name": "ref_low", "cols": [46, 54], "type": "decimal"}, {"name": "ref_high", "cols": [55, 64], "type": "decimal"}
    ],
    "row_map": {"test": {"lookup": "lab_test_dictionary"}}
  }],
  "constraints": ["results.length >= 1", "each(results, value >= 0)", "each(results, unit == dictionary(test).unit)"],
  "confidence": {"min_anchor_score": 1.0, "min_field_coverage": 1.0, "on_fail": "abstain"},
  "provenance": "every extracted value records page/row/col span"
}
```

Supported keys: anchors, positions and regions, regex patterns, repeating table blocks with fixed columns, date formats, type conversion (decimal/date/UCUM), lookups against a curated dictionary (test name → LOINC/unit/plausible range), required flags, constraints and abstention policy. **No code execution.**

### D3. How rules are generated
1. **Input:** 2–3 *synthetic or redacted* samples of the layout plus the target schema (e.g. "lab report" fields).
2. **LLM output:** a Binding JSON, forced to match the JSON Schema (structured output).
3. **Static checks:** schema-valid; every field has an anchor or region; no overlapping columns.
4. **Dry run** on the learning samples: values must equal the hand-labelled expected output (synthetic samples come with ground truth).
5. **Held-out test:** run on N ≥ 5 *other* documents of the same layout (generated variants) that the LLM never saw.
6. **Perturbation test (PBT):** shifted values, extra rows, missing optional fields, page breaks inside tables. The rule must either extract correctly **or abstain**. **Any silent wrong value blocks activation.**
7. **Repair:** failing cases (smallest counterexample) are fed back to the LLM, at most 3 rounds.
8. **Human approval** in the UI. Only then is the rule saved as active, versioned and hashed.

### D4. Most dangerous assumption
**An LLM can write a Binding that generalises to unseen documents of the same layout from 2–3 samples, often enough to be useful (≥ 80% of layouts within 3 repair rounds).** Evaporate saw that synthesised functions often covered only part of the documents and had bugs, and needed weak supervision across many candidate functions [S42]. **This is the first PoC gate (see `14`).**

---

## Part E — Deterministic validation engine (2.4)

| Check | Universal or domain | How |
|---|---|---|
| Schema / required fields | Universal | JSON Schema of the target record |
| Type parsing (decimal, date, enum) | Universal | Strict parsers; no lenient "best effort" |
| Date sanity | Universal | Not in the future; plausible range; formats declared in the rule |
| Anchor completeness and layout fingerprint match | Universal | All required anchors found where expected, otherwise abstain |
| **Layout-version detection** | Universal | Fingerprint distance above threshold → "unknown layout" → abstain and queue for a new rule |
| Duplicate detection | Universal | Hash of (normalised content + key fields); same job reprinted → flag, don't resend |
| Arithmetic invariants | Domain (billing/invoices) | Line items sum to the total; tax = base × rate |
| Unit validation | Domain (lab) | Unit must be valid UCUM *and* match the dictionary's expected unit for that test |
| Terminology validation | Domain (lab) | Test name must map to a curated, **hand-verified** LOINC code; unmapped tests are never guessed → `code.text` only *and* flagged |
| Plausibility ranges | Domain (lab) | Value within physiologically possible limits (not the reference range) |
| Reference-range consistency | Domain (lab) | `ref_low < ref_high`; flag consistent with value vs range |
| Cross-field | Both | Patient age/sex present when ranges depend on them |
| Regression | Universal | A golden corpus re-run on every rule or engine change (Kiro hook) |
| Property-based tests | Universal (engine) | Hypothesis/Kiro PBT on decoder round-trips, interpreter determinism, abstain-or-correct under perturbation |

**Abstention policy:** a document is emitted only if *all* required fields pass *and* deterministic confidence is 1.0 on anchors and coverage. Otherwise **nothing is sent**; the job goes to the **human review queue**, which shows the original printout with the problem fields highlighted. **The LLM is never asked to validate its own output.** A second LLM may optionally *propose* fixes during rule building, but activation always depends on the deterministic checks.

---

## Part F — FHIR and ABDM (2.5)

### F1. The real ABDM IG
**"FHIR Implementation Guide for ABDM" v6.5.0, package `ndhm.in#6.5.0`, FHIR 4.0.1, published 2025-05-08 by NRCeS** [S44][S57]. Relevant profiles:
- **`DiagnosticReportRecord`**: a profile on **Composition** (a document bundle).
- **`DiagnosticReportLab`**: DiagnosticReport for lab reports (CBC, metabolic panel, lipids…). `presentedForm` is 0..*; official examples embed a PDF inline.
- **`Observation`** base profile for lab results.
- **`HealthDocumentRecord`** for unstructured documents uploaded by patients.

The IG says terminology bindings "will be provided with subsequent updates" [S57], so LOINC is used in practice but bindings are loose [U].

### F2. Recommended structure for one lab report
`Bundle` (type `document`) containing:
- **Composition** (profile DiagnosticReportRecord; section → DiagnosticReport)
- **Patient** (name, gender, age or birthDate, a local identifier; ABHA number only if printed)
- **Organization** (the lab)
- **Practitioner** (pathologist, if printed)
- **DiagnosticReport** (DiagnosticReportLab):
  - `code` = panel LOINC (e.g. CBC panel; code to be hand-verified),
  - `result` → Observations,
  - **`presentedForm` = PDF rendering of the original printout**, so nothing printed is lost,
  - `specimen` optional,
  - `issued`/`effectiveDateTime`
- **Observation** per test: `code` LOINC; `valueQuantity` (UCUM `system: http://unitsofmeasure.org`); `referenceRange.low/high`; `interpretation` (H/L/N from v3-ObservationInterpretation)
- **Specimen**: only if the printout states a specimen type (e.g. "Serum").

### F3. Four levels: what we can claim
| Level | Feasible in the hackathon? | Plan |
|---|---|---|
| 1. FHIR R4 resource generation | **Yes** | `fhir.resources` (pydantic) models |
| 2. **ABDM profile validation** | **Yes, with caveats [T]** | HL7 `validator_cli.jar -version 4.0.1 -ig ndhm.in#6.5.0` (Java runs on Apple Silicon). One real project validated ABDM bundles this way: 0 errors on two record types, plus offline MIME-type errors (`-tx n/a`) on HealthDocumentRecord [S58]. We report the exact validator output, warnings included |
| 3. ABDM sandbox integration | **No** | Needs sandbox client credentials, HIP bridge registration, ABHA linking and consent flows; vendors quote 4–12 weeks [S38]. Out of scope; roadmap only |
| 4. Production ABDM certification | **No** | Milestone demonstrations to NHA, security audit [S38] |

**Wording for judges:** *"Generates FHIR R4 document bundles that validate against the ABDM FHIR IG v6.5.0 profiles (HL7 validator output shown). Not ABDM-certified; sandbox integration not attempted."*

---

## Part G — Revised effort (≈125h MVP)
| Work | h |
|---|---:|
| Windows VM + capture/forward listener + DOS LPT test | 10 |
| Decoders (raw text, text-PDF) + character grid + fingerprint | 12 |
| Binding JSON Schema + interpreter + provenance | 14 |
| Rule generator loop (structured output, held-out test, repair) | 14 |
| Validation engine + abstention + review-queue backend | 14 |
| Lab dictionary (≈40 tests, LOINC/UCUM hand-verified) + FHIR builder + validator_cli integration | 14 |
| Synthetic corpus generator + perturbation benchmark | 10 |
| Review UI + dashboard (job feed, source-highlighted view, approve rule) | 20 |
| PBT/regression via Kiro + E2E | 8 |
| Deploy (web upload demo; no public 9100) | 5 |
| Video, write-up, blog | 14 |
| **Total** | **135** (≈125 if the dashboard is cut back) |

Ideal version with PostScript, an IPP path, ESC/POS and a second domain: about 180h.

---

### New sources (also appended to SOURCES.md)
- [S40] Astera ReportMiner (AGL): https://www.astera.com/products/report-miner ; Astera 11.2 notes: https://www.astera.com/type/blog/astera-11-2-whats-new-and-improved ; mainframe extraction blog: https://www.astera.com/type/blog/mainframe-report-extraction-enterprise-scale
- [S41] IT Jungle, "Astera Makes Extracting Legacy Report Data an AI Specialty" (10 Aug 2026): https://www.itjungle.com/2026/08/10/astera-makes-extracting-legacy-report-data-an-ai-specialty/
- [S42] Arora et al., Evaporate, arXiv:2304.09433 / PVLDB 17: https://arxiv.org/abs/2304.09433
- [S43] US 6546133 "Methods and apparatus for print scraping": https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6546133
- [S44] NRCeS DiagnosticReportLab (IG v6.5.0): https://nrces.in/ndhm/fhir/r4/StructureDefinition-DiagnosticReportLab.html ; Lab example bundle: https://www.nrces.in/ndhm/fhir/r4/Bundle-DiagnosticReport-Lab-example-03.json.html
- [S45] CoronaSafe ABDM docs, DiagnosticReport packaging: https://docs.coronasafe.network/abdm-documentation/preparation-of-data-and-data-packaging/diagnostic-reports-as-fhir-diagnosticreport
- [S46] ABDM Microsites: https://blog.mygov.in/editorial/abdm-microsites-building-a-macro-level-digital-health-ecosystem-in-india/ ; https://worldhealthpartners.org/abdm.php?page=project
- [S47] Indian lab software pricing: https://www.labsmartlis.com/blog/pathology-lab-software-price-in-india ; https://www.clinikpe.com/pathology-lab-software/ ; https://www.drlogy.in/pathology-lab-software.html
- [S48] PIB, 100 crore records / 450+ integrated solutions (May 2026): https://www.pib.gov.in/PressReleasePage.aspx?PRID=2264241 ; PIB backgrounder (Jul 2026): https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/jul/doc202676912801.pdf
- [S49] VeryPDF Printer Capture: https://www.verypdf.com/wordpress/202608/virtual-pdf-printer-capture-capture-windows-print-jobs-and-save-them-as-pdf-54401.html ; DOS parallel-port capture: https://www.imagepdf.com/blog/how-to-capture-and-convert-legacy-dos-print-jobs-from-parallel-port-into-pdf-for-compliance/
- [S50] IBM i spool tools: https://interformsoftware.com/ibm-i-as400/ ; https://coolspools.com/ ; https://go.freschesolutions.com/formtastic-request-a-trial
- [S51] Microsoft, end of servicing plan for third-party printer drivers: https://github.com/MicrosoftDocs/windows-driver-docs/blob/staging/windows-driver-docs-pr/print/end-of-servicing-plan-for-third-party-printer-drivers-on-windows.md ; WPP overview: https://4sysops.com/archives/windows-protected-print-and-ipp-internet-printing-protocol-eliminating-third-party-printer-drivers/
- [S52] RedMon: http://www.ghostgum.com.au/software/redmon19.htm ; https://github.com/ARLM-Keller/redmon
- [S53] ippeveprinter(1): https://man.archlinux.org/man/ippeveprinter.1.en
- [S54] PWG IPP list (M. Sweet on Windows XPS → PWG Raster/PDF): https://www.pwg.org/archives/ipp/2024/021562.html ; Microsoft PSA v3 guide: https://learn.microsoft.com/en-us/windows-hardware/drivers/devapps/print-support-app-v3-design-guide
- [S55] Generic/Text Only + Standard TCP/IP RAW setup: https://www.cleverence.com/articles/sage-documentation/set-up-generic-text-only-printer-driver-4827/ ; PDVPrinterSim: https://github.com/gerlanss/PDVPrinterSim
- [S56] Sensible SenseML: https://docs.sensible.so/docs/getting-started ; https://sensible.mintlify.app/senseml-reference/senseml-reference-introduction
- [S57] NRCeS ABDM FHIR IG home and downloads (ndhm.in#6.5.0): https://nrces.in/ndhm/fhir/r4/ ; https://www.nrces.in/ndhm/fhir/r4/downloads.html ; NRCeS adoption guide PDF: https://www.nrces.in/download/files/pdf/Implementation_Guide_for_Adoption_of_FHIR_in_ABDM_and_NHCX.pdf
- [S58] medbrains PR #4988 (validator_cli + ndhm.in 6.5.0 results): https://github.com/medbrains/medbrains/pull/4988
