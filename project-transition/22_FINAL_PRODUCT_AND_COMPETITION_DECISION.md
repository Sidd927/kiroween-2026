# 22: Final product and competition decision (22 Nov 2026)

## Decision: **MODIFY**
Continue with Spoolgeist **only** with these four changes:
- **(1) Thesis:** a changed thesis ("AI writes the parser; proof decides whether it may run"). Not a small-lab ABDM product, and not "first AI template generator".
- **(2) Build:** a new, **Kiro-built** application in a new public repository, with this repository disclosed as prior work.
- **(3) Free text:** free text routed to a human, closing the qualitative gap by product design rather than vocabulary.
- **(4) Scope:** a hard cut.

## Scored against the ten criteria (evidence-based; no earlier scores reused)
| # | Criterion | Evidence | Assessment |
|---|---|---|---|
| 1 | Technical credibility | Sealed split: 410/410 valid fully correct, 0/399 unsafe, 0 wrong values, 0 context errors. Held-out v3: numeric 0/60 leaked. Mutation 252/334 with every survivor classified. FHIR 0 errors / 410 (generic + ABDM). Report 19 | **Strong on synthetic data from one generator family**; zero real documents |
| 2 | Problem severity | Vendor claims only; the most-cited pain is analyzer transcription and paper registers (report 03) | **Weak and unverified** |
| 3 | Differentiation | AI-generated templates exist (ReportMiner); print capture exists (VeryPDF, Retro-Printer, RedTitan). Not found among competitors: a published no-silent-drop acceptance contract with adversarially gated, provenance-checked rule activation | **Moderate**, if framed precisely |
| 4 | Customer evidence | 0 interviews | **None.** Impact must be presented as a hypothesis unless C4 (below) is met |
| 5 | Feasibility | ≈ 12.4 days to the deadline; the engine design and tests exist as an oracle; team size unknown | **Medium**; viable with the scope cut |
| 6 | Kiro eligibility | Kiro is mandatory, "insufficient use" disqualifies; nothing is Kiro-built yet (report 20) | **Likely acceptable only via a Kiro-built application; awaiting clarification** |
| 7 | Kiro implementation potential | The core property *is* a property-based test; the gate conditions map to EARS requirements; hooks (safety suite on change), steering (synthetic-only, fail-closed) and MCP (HL7 validator, FHIR docs) fit naturally | **High**, if done genuinely |
| 8 | Competition relevance | Resurrection: "bring a dead technology back to life". Printer ports and dot-matrix reports turned into validated FHIR | **Strong fit** |
| 9 | Time to a complete application | The first vertical slice (replay a print job → recognise → accept/refuse with line-level reasons → FHIR) is ≈ 3–4 days in Kiro; onboarding UI plus approval ≈ 2–3 days | Tight but feasible |
| 10 | Demonstration quality | Live: a legacy-style app prints, the job is captured, the AI drafts a rule, the gate attacks it, a human approves, the next report is processed with no AI, and a defective report is refused with the exact line highlighted | **Potentially excellent** |

## The strongest evidence against proceeding
1. **No one has said they have this problem.** Small labs can switch to cheap cloud LIS products that claim ABDM push. Judges score "credible case for solving a real problem for a real audience". We cannot make that case with evidence today.
2. **The idea is less novel than it feels.** ReportMiner markets AI-built reusable templates. Our distinctiveness is rigour, which is harder to show in a 3-minute video than novelty.
3. **Every number comes from data we generated ourselves.** A sceptical judge can dismiss "0/399 unsafe" as self-graded homework.
4. **Kiro risk.** Rebuilding in Kiro costs days. Not rebuilding risks disqualification.

**Why MODIFY still beats PIVOT:**
- None of these is fatal.
- (1) is addressed by framing (hypothesis plus interviews if possible) and by the trust contribution.
- (2) by precise positioning.
- (3) by transparent methodology plus a live demo the judge can try (upload your own malformed print job).
- (4) by building in Kiro from today.
- A pivot with 12 days left discards the strongest technical core and demo we have, for an alternative with no evidence either.

## Product decisions taken
1. **Free-text policy (closes the qualitative gap honestly).**
   - Documents whose only non-structured content is approved notes or variable slots are **not auto-exported**. They go to a **"confirm free text" review state**, where a person sees the note highlighted next to the extracted record and confirms or refuses.
   - Documents with no free text export directly.
   - This turns the 27 / 180 held-out qualitative leak into a *visible* human step rather than a silent pass.
   - This is a policy change for the new application. v4 stays frozen as evidence.
2. **Report identifiers, sample identifiers and date of birth** are out of MVP scope and stated as such.
3. **ABDM:** profile-valid FHIR output only. No gateway or sandbox claims.
4. **Analyzer serial capture:** roadmap, not MVP.

## Category and prizes
- **Primary category:** Resurrection.
- **Bonus tracks worth the small extra effort:**
  - **Best Demo** (it only needs a top-10% overall score);
  - **Blog Post** (a public post mentioning Kiroween 2026; the "how property-based tests caught silent-drop bugs" story is real);
  - **Social Blitz**;
  - **Student** (if the user is eligible: all team members must be students).
- **Skip:** Kiro Crew app, Startup.

## Conditions (user-dependent), unchanged from the draft
- **C1:** Kiro installed and signed in; credits requested before 1 Dec 12:00 PT.
- **C2:** team size and hours.
- **C3:** a product repository (public, MIT, `/.kiro` at the root).
- **C4:** at least 2 interviews, or accept hypothesis framing.
- **C5:** a human approves the demo rules.
- **C6 (optional):** a Windows machine.
- **New, C7:** permission to send the organiser clarification (report 21).
