# 06 — Finalist Evaluation (Round 2): Red Team, Demo Test, Scorecard

## Scoring method

**Official criteria** are each scored out of 20 (the 10-point official scale doubled to give finer resolution):

| Band | Meaning |
|---|---|
| 17–20 | Exceptional. Concrete evidence and a clear edge over the 2025 winners |
| 13–16 | Strong. Credible, but has a visible weakness |
| 9–12 | Average for the field |
| ≤ 8 | Weak |

- **Technological Implementation** is scored *as the rules define it*: depth and variety of Kiro use, not engineering difficulty.
- **Potential Impact** requires a credible audience *and* that what we demonstrate actually addresses their problem.

**Internal criteria** are each scored out of 10:
- Technical feasibility within about 13 days
- Kiro integration depth possible
- Competitive differentiation
- Data accessibility
- Demo reliability

---

## R1. Spoolgeist

**Red team (assume it failed, then explain why):**
1. *Hidden assumption:* small labs or clinics actually run software that can only print. → **Validate by 24 Nov** with 3–5 local visits or calls. If none exist, pivot the primary story to retail and SME legacy accounting (VFP evidence) and keep labs as the second domain pack.
2. *Bottleneck:* the AI writes a parser that passes the checks but grabs the wrong field (e.g. swaps the reference range and the result). → Mitigations: type and range properties per field (a LOINC code implies a unit and a plausible range), a cross-check against a second independent LLM extraction on the learning samples, and human approval before a parser goes live.
3. *Bottleneck:* format variety. Many Windows drivers emit PCL or raster output. → Recommend the built-in "Generic / Text Only" or a PostScript driver when setting up (both standard on Windows). OCR on raster output is a stretch goal only.
4. *Competitive threat:* a judge says "Monarch already does this". → Show that the parser is built automatically in about 20 seconds against Monarch's hand-built templates, and show the FHIR output.
5. *Simpler, stronger version?* We considered "upload a PDF → FHIR". It's weaker: it loses the zero-change capture, which is the Resurrection hook, and becomes plain document AI.
6. *Would a substantially different project have more upside?* Only R2, and it fails on feasibility.

**Three highest-leverage improvements:**
1. Have the **parser itself be the visible artifact**: show it as readable JSON with green property checks, and show the count of LLM calls avoided going up.
2. **Real-world grounding:** short video quotes from a real lab owner or clinic receptionist, plus a sample printout layout based on a real one (with no patient data).
3. **Kiro as part of the product:** ship a *Spoolgeist Power* so developers can ask Kiro to write new domain packs (destinations), plus an optional *Crew App* "Warden" that watches failed parses.

**Differentiation test.** To copy this, a competitor needs:
- a raw-print listener and multi-format decoders,
- a position-preserving text grid,
- a declarative parser language with an interpreter,
- an LLM loop that builds and repairs parsers using counterexamples,
- domain property checks,
- FHIR/LOINC/UCUM mapping,
- and a dashboard that shows where each value came from.

That is about 2 weeks of focused work for a strong team. Hard to copy casually, and no single piece of it is a commodity wrapper.

**Demo test (150 s): passes.**
- 0–20 s: the problem (dusty clinic PC, DOS screen, printout handed to the patient; "this data dies on paper").
- 20–100 s: hit Print → the job lands in Spoolgeist → AI builds the parser live → property checks turn green → FHIR report appears → the next five prints are parsed instantly with no LLM.
- 100–150 s: impact, the Kiro story, and the closing line.

---

## R2. Lipi Lazarus

**Red team:** the recognition models won't reach usable accuracy in 10 days (KhatianDoc shows zero-shot failure; little Kaithi data exists). A demo with cherry-picked lines invites the question "what's the CER on unseen pages?". Government programmes (Bhashini) make it hard to argue we're needed.

**Improvements:**
1. Narrow to Modi only.
2. Make it a human-reader assist tool (glyph lens plus a teaching mode) instead of claiming automation.
3. Partner with an archive for real data.

All three take time we don't have.

**Differentiation test:** the competitor is a government AI agency. We have no data advantage.

**Demo test:** fails on reliability unless results are pre-recorded, which risks honesty.

---

## R3. Necromancer

**Red team:** the audience doesn't recognise the pain until it bites them. Watching an "equivalence certificate" appear isn't memorable. Judges at AWS know their own modernization products. Generating inputs for real libraries with side effects is hard.

**Improvements:**
1. Pick one vivid domain (financial rounding in old Python 2 code).
2. Animate the divergences that get found.
3. Package it as a Kiro Power plus hooks.

**Differentiation test:** a strong team could copy it in about 1 week; the research is public.

**Demo test:** borderline. It's technical, and non-developer judges would lose the thread.

---

## F1. Ghost Trials

**Red team:** "RegCheck already does this at 85.6% accuracy." The audience (journal editors) is small. CTRI scraping breaks easily.

**Improvements:**
1. Make it a journal-submission screening workflow.
2. Add CTRI coverage (India).
3. Show changes across registry versions over time.

**Differentiation test:** it could be reproduced from published methods.

**Demo test:** passes, but it isn't memorable.

---

## S3. Grimoire

**Red team:** Impact is scored as "only matters to Kiro users". Crew App APIs are moving (0.12.0 on 5 Nov). Building the template plus two apps on a 3-month-old platform with thin docs is the riskiest schedule of all.

**Improvements:**
1. Pick two apps with real-world value (e.g. a clinic appointment reminder bot).
2. Ship PBT for manifest invariants.
3. Make the steering and hooks reusable.

**Differentiation test:** official scaffolding could make it unnecessary.

**Demo test:** passes for Kiro judges, weak for everyone else.

---

## C1. Patient Zero

**Red team:** the premise is weakened by the Nov 2026 evidence (citing retracted work doesn't predict retraction well). Feet of Clay already covers the core. We're not design-first, and Costume is where design-first teams win.

**Improvements:**
1. Focus on systematic reviews that may be contaminated by retracted trials.
2. Use citation-context classification.
3. Add sound and motion.

**Demo test:** visually passes; substance weak.

---

## Scorecard (official criteria, /20 each)

| Dimension | R1 Spoolgeist | R2 Lipi Lazarus | R3 Necromancer | F1 Ghost Trials | S3 Grimoire | C1 Patient Zero |
|---|---:|---:|---:|---:|---:|---:|
| Potential Impact | **15** | **19** | 12 | 15 | 10 | 11 |
| Technological Implementation (Kiro) | **17** | 12 | **18** | 13 | **19** | 12 |
| Design Potential | 15 | 14 | 11 | 12 | 12 | **17** |
| Innovation | **16** | 16 | 13 | 11 | 12 | 10 |
| Presentation Potential | **16** | 16 | 12 | 13 | 12 | 15 |
| **TOTAL /100** | **79** | 77* | 66 | 64 | 65 | 65 |

\*R2's 77 assumes the recognition works. Its realistic delivered score is much lower (see the internal metrics).

**Score explanations:**
- **R1 Impact 15:** legacy interop is a documented national barrier [S19][S20], but we can't prove adoption in 13 days. Capped below 17 until real users are on camera.
- **R1 Tech 17:** a natural fit for many Kiro features: multiple specs, PBT on the decoder and parser invariants (a perfect use of Kiro's PBT), hooks that run the regression corpus of sample printouts, steering for untrusted-input safety, a custom agent for building parsers, MCP for FHIR docs and validation, a Power we ship ourselves, and an optional Crew App. Not 19–20, because Grimoire's whole product *is* Kiro.
- **R1 Design 15:** the dashboard plus click-a-value-to-see-its-source highlighting can be polished. Infrastructure tools are harder to make "unforgettable".
- **R1 Innovation 16:** a new combination (print-stream capture + AI-built verified parsers + FHIR/GST output) with prior art visible (Monarch).
- **R1 Presentation 16:** a strong before/after "magic moment", and the DOS-to-FHIR contrast is memorable.
- **R2:** maximum impact (19), but the dependence on capability lowers Tech and Design.
- **R3:** top Kiro use (18) but abstract impact (12) and a dry design (11).
- **F1:** Innovation 11 because the core has already been published and validated [S29][S30].
- **S3:** top Kiro use (19), but Impact 10 (the audience is only Kiro users).
- **C1:** top Design (17), weakest Innovation (10).

## Internal decision metrics (/10 each)

| Metric | R1 | R2 | R3 | F1 | S3 | C1 |
|---|---:|---:|---:|---:|---:|---:|
| Technical feasibility (13 days) | 8 | 3 | 6 | 7 | 5 | 8 |
| Kiro integration depth | 9 | 6 | 10 | 6 | 10 | 6 |
| Competitive differentiation | 8 | 4 | 5 | 4 | 6 | 3 |
| Data accessibility | 8 | 3 | 8 | 9 | 10 | 8 |
| Demo reliability | 8 | 3 | 6 | 7 | 6 | 8 |
| **TOTAL /50** | **41** | 19 | 35 | 33 | 37 | 33 |

Notes:
- **R1 data accessibility 8:** no external approval is needed. Printouts can be synthetic or donated by local labs. The LOINC subset needs a free LOINC account [U]. HAPI FHIR is open source.
- **R1 demo reliability 8:** everything runs on infrastructure we control. The LLM is used only while a parser is being built, so a cached, already-approved parser is a natural fallback if the LLM fails during the demo.

## Ranking

1. **R1 Spoolgeist**: 79 official / 41 internal
2. **S3 Grimoire**: 65 / 37
3. **R3 Necromancer**: 66 / 35
4. **F1 Ghost Trials**: 64 / 33
5. **C1 Patient Zero**: 65 / 33
6. **R2 Lipi Lazarus**: 77 (theoretical) / 19

| Question | Answer |
|---|---|
| Highest theoretical upside | **R2 Lipi Lazarus**, but only if recognition worked. It won't within the deadline |
| Highest probability of successful execution | **R1 Spoolgeist** (tied with C1 on feasibility; R1 wins on everything else) |
| Most innovative concept | **R1 Spoolgeist** (AI as a compiler for print streams); R2 equals it on concept |
| Strongest student-prize candidate | **R1 Spoolgeist** in Resurrection |
| Strongest overall competition candidate | **R1 Spoolgeist** |

**Trade-off:** the idea with the highest score (R1) is also the safest, so there's no conflict between expected value and risk. The only real tension is R2's emotional upside, which isn't reachable within 13 days.
