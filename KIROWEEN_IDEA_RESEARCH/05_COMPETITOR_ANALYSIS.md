# 05 — Competitor Analysis (Finalists)

Rule I followed: a competitor is listed only if I found it during this session (with a source) or it is marked **[U]** (known to me, not re-verified). I made up no feature claims about competitors.

---

## R1. Spoolgeist (legacy print stream → verified structured data)

| Competitor | Type | What it does | Strengths | Gaps relative to Spoolgeist | Source |
|---|---|---|---|---|---|
| **Altair/RapidMiner Monarch** (Datawatch, since 1990; now Siemens) | Commercial report mining | Parses print/spool/PRN files into tables using **hand-built layout models**; server automation | Mature; huge enterprise footprint; **proves the demand** | Templates are hand-made; enterprise pricing; no AI-built parsers; no FHIR/ABDM or GST output; not aimed at small facilities | [S23] |
| **escpos-netprinter** | OSS (fork) | Docker virtual ESC/POS printer on 9100/515; renders receipts as HTML | Free; captures jobs without changing the POS | Visual rendering only, no structuring; the README says it's unsafe on public networks; receipts only | [S24] |
| **Color Pilot Virtual POS Printer** | Commercial driver | Accepts ESC/POS, extracts text, makes PDF, forwards to a real printer | Pass-through printing | Text only; no understanding of meaning, no verification, no destinations | [S25] |
| **virtual-printer.online** | SaaS test tool | Public TCP virtual thermal printer plus REST API returning parsed receipts as JSON | Closest to "print → JSON" | Built for *testing* POS developers; receipts only; no domain mapping or verification | [S26] |
| escpos-tools / pyesc2txt | OSS libraries | ESC/POS → text/HTML | Useful building blocks (we would disclose any use) | Libraries, not products | [S37] |
| Document AI (Textract, Google DocAI, LlamaParse) | Cloud APIs | Extract from scanned images/PDFs | Strong on scans | Works *after* the paper exists (OCR errors), an LLM or model call on every document, no print capture, no layout-specific deterministic parser | [U] |
| RPA (UiPath etc.) | Commercial | Screen-scrapes the legacy UI | General purpose | Brittle, needs a desktop session and licences, expensive | [U] |
| ABDM integrators (Nirmitee, Adrine, etc.) | Services | Custom HMIS integration with ABDM (4–12 weeks) | Domain knowledge | Need API access to the HMIS, which legacy systems can't provide; slow and costly | [S38] |

**If a judge searches for this idea, what will they find?** Monarch (enterprise report mining) and receipt emulators. **Why we're different:**
1. **AI builds the parser, properties verify it, and it then runs deterministically.** Monarch needs a person to build each template. Emulators don't extract meaning at all.
2. **Destination-native output.** FHIR R4 lab reports with LOINC/UCUM codes and GST invoice JSON, not just tables.
3. **Privacy.** Real patient data never reaches an LLM once a layout is learned (redaction during parser building; no LLM afterwards).
4. **Aimed at small facilities**, which can't afford Monarch or a migration.

**Verdict:** the space has existing players but no one has occupied this combination. Judges will find related tools, which makes our differentiation *easier* to explain ("Monarch with AI-built, verified parsers and modern health/tax output").

---

## R2. Lipi Lazarus (dead-script land records)

| Competitor | What | Source |
|---|---|---|
| IIT Roorkee MoScNet + MoDeTrans | Research VLM for Modi → Devanagari; 2,043-image dataset | [S16] |
| Bihar Revenue Dept × Bhashini | Government AI transliteration of Kaithi (MoU, 2025) | [S17] |
| Earlier academic Modi OCR (character level, LSTM) | Research | [S16] |
| Human Kaithi/Modi experts | Paid manual reading | [S13][S15] |

**Verdict:** government and academia already lead on the core capability, and we would have no advantage in data or models. Our only possible edge is UX and a human-in-the-loop workflow, and that doesn't hold up if recognition is poor.

---

## R3. Necromancer (verified resurrection of abandoned code)

| Competitor | What | Source |
|---|---|---|
| Locksmith Loop (COBOL→Java parity gate) | Research | [S34] |
| AgentModernize (behavioural spec graphs plus differential and metamorphic tests) | Research | [S34] |
| Mokav, DiffSpec, BreakGuard | Differential testing tools cited in the literature | [S34] |
| Large-vendor modernization services | Commercial | [U] |
| OpenRewrite, Renovate, Dependabot | Automated upgrades without proving equivalence | [U] |

**Verdict:** the research field is crowded and the commercial field is dominated by large vendors. Our differentiation (packaged as a Kiro Power and focused on developers) is real but narrow.

---

## F1. Ghost Trials (outcome switching)

| Competitor | What | Strength | Source |
|---|---|---|---|
| RegCheck | LLM workflow; 85.6% accuracy at detecting misreporting | Validated against COMPare | [S29] |
| Mayo-Wilson et al., npj Digital Medicine 2026 | Registry vs posted results; sensitivity 0.97, PPV 0.95; costs $0.13–$1.80 per trial | Peer-reviewed | [S30] |
| FDAAA TrialsTracker (Oxford Bennett Institute) | Live compliance tracker for unreported results | Running since 2018 | [S27] |
| LLM registry-change pipeline (medRxiv, Nov 2026) | Detects changes between registry versions | Very recent | [S29] |
| COMPare (manual, historical) | Benchmark | — | [S29] |

**Verdict:** the core AI capability is already published and validated. Our edge would be limited to the reviewer UX and adding CTRI coverage. Low Innovation score.

---

## S3. Grimoire (Kiro Crew App template)

| Competitor | What | Source |
|---|---|---|
| Official Crew App examples (on-call triage, service monitor, Mochi desktop pet) | Reference apps | [S9] |
| `kirocrew app dev` / `app import` CLI tooling | Official scaffolding and import | [S9] |
| MCP Apps / other agent app SDK templates | Adjacent ecosystems | [U] |

**Verdict:** the field is thin (an opportunity), but so is the audience, and official tooling may expand quickly.

---

## C1. Patient Zero (zombie citations)

| Competitor | What | Source |
|---|---|---|
| Problematic Paper Screener: Feet of Clay + Annulled detectors | Flags 764k+ citing articles; adds PubPeer comments | [S28] |
| RetractoBot (Oxford) | Emails authors who cited retracted papers; RCT protocol | [S28] |
| Zotero / reference-manager retraction alerts | Alerts inside citation managers | [U] |
| scite.ai | Citation context and retraction notices | [U] |
| arXiv 2611.10474 | Shows that citing retracted work weakly predicts retraction (84% of later retractions cite none) | [S31] |

**Verdict:** crowded. The evidence even weakens the core premise. The only differentiation left is design.

---

## Summary: competitive position

| Finalist | Is the space crowded? | Does a defensible gap exist? | How believable is our edge to a judge? |
|---|---|---|---|
| **R1 Spoolgeist** | Moderate (old enterprise player plus emulators) | **Yes: AI-built verified parsers + health/tax output + small facilities** | **High** |
| R2 Lipi Lazarus | Government and academia | Capability gap, not a product gap | Low (we lack data) |
| R3 Necromancer | Research plus big vendors | Narrow (Kiro Power packaging) | Medium |
| F1 Ghost Trials | Validated research tools | UX/CTRI only | Low–medium |
| S3 Grimoire | Thin | Yes, but a niche audience | Medium |
| C1 Patient Zero | Established tools | Design only | Low |
