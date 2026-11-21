# 14 — Spoolgeist: Proof-of-Concept Plan (design only; no code written)

**Purpose:** settle the two assumptions that decide GO or PIVOT within **about 2 days (≈18h)**, before committing the remaining time. **Approval is needed before any code is written.** The PoC would live in an isolated `poc/` folder (or a separate scratch repo), built in Kiro with a spec so it counts as Kiro usage, and it **contains only synthetic data**.

## 1. Scope: the 10 required demonstrations
| # | Demonstration | PoC implementation | h |
|---|---|---|---:|
| 1 | Legacy-style app produces a printable report | `legacy_lab.py`: generates fixed-width "1998-style" CBC/LFT reports from fake patients (2 layouts, A and B). Printed from **Notepad in a Windows 11 ARM VM (UTM)**. Optional: DOSBox-X `PRINT` via LPT1 | 2 |
| 2 | Spoolgeist captures output | Windows built-in **Generic / Text Only** driver → Standard TCP/IP **RAW** port → Mac host `:9100` asyncio listener; stores bytes plus SHA-256 | 3 |
| 3 | Convert to an extractable representation | Strip control codes → character grid (rows × cols) → fingerprint | 2 |
| 4 | AI generates a rule for an unfamiliar layout | LLM (structured output against the Binding JSON Schema) from 2 synthetic samples of layout A | 3 |
| 5 | Rule saved | `bindings/lab-A.v1.json` with hash; status `candidate` → `active` after the gate | 0.5 |
| 6 | Second document processed with no AI call | A new layout-A print is parsed by the interpreter; a log line proves 0 LLM calls | 1.5 |
| 7 | Deterministic validation | Required/type/date/UCUM/dictionary/plausibility/constraint checks | 2 |
| 8 | Valid FHIR R4 resource | `fhir.resources` → document Bundle (Composition DiagnosticReportRecord, Patient, Organization, DiagnosticReportLab with `presentedForm`, Observations) → **`validator_cli.jar -version 4.0.1 -ig ndhm.in#6.5.0`**; save the exact output | 2.5 |
| 9 | Original output preserved or forwarded | The listener tees identical bytes to `socket://127.0.0.1:9101` (a second listener standing in for the "physical printer", writing `forwarded/`), with matching SHA-256 shown; optionally `ippeveprinter -D` | 0.5 |
| 10 | Invalid or ambiguous output goes to review | Print a layout-A variant with a unit swapped, a missing anchor, and a layout-B document → each abstains into `review_queue/` with reasons | 1 |
| | **Total** | | **18** |

## 2. Two decision gates (measured, not argued)
**Gate T: technical (must pass by end of PoC day 2)**
- Corpus: 3 synthetic layouts × 30 documents each. Perturbation generator: column shifts ±2, extra or missing optional rows, page break inside a table, unit swaps, out-of-range values, missing anchors, foreign layout.
- **Pass if:**
  - ≥ 2 of 3 layouts reach an active rule within ≤ 3 repair rounds,
  - **0 silent errors** on held-out and perturbed documents (every output is either exactly right or abstained),
  - abstention ≤ 15% on clean held-out documents,
  - the FHIR bundle validates against `ndhm.in#6.5.0` with no errors except documented terminology-server/offline issues.
- Baseline for the story: the same documents through *direct* LLM extraction, counting silent errors. If direct extraction is *also* at 0 silent errors with low cost, our differentiation weakens. **Record it honestly either way.**

**Gate M: market (in parallel, by 24 Nov)**
- ≥ 5 conversations using the script in `11`. **Pass if** ≥ 2 describe either software that can only print, or double entry of printed results, *and* would accept a local agent. Otherwise the healthcare framing becomes "a demonstrated safe extraction engine for an evidenced transcription-error problem", with Impact capped around 11–12.

## 3. Environment checklist (Mac M5, 16 GB)
- UTM + Windows 11 ARM evaluation VM (bridged or shared networking so the guest can reach the Mac's IP) [T].
- Python 3.12 (uv), `fhir.resources`, `hypothesis`, `pdfplumber`.
- Java 17+ for HL7 `validator_cli.jar`; download the `ndhm.in` 6.5.0 package.tgz for offline runs.
- Optional: CUPS `ippeveprinter` (ships with macOS CUPS tools [U]) to test the IPP path and see what Windows' IPP class driver sends (PDF vs PWG Raster) [T].
- An LLM API key with structured outputs (any provider). Budget: under US$5 for the PoC [A].

## 4. What the PoC deliberately excludes
Dashboard/UI, PostScript and PDF decoders, ESC/POS, the IPP production path, ABDM sandbox, authentication, deployment, Crew app.

## 5. Outputs
- `poc/RESULTS.md`: gate metrics table, validator output, silent-error and abstention numbers, the 3 most interesting counterexamples.
- A 60-second screen recording of steps 1→10 (later reused in the final video).
- Kiro artifacts: one spec (`poc-spike`), the PBT property for "abstain or exactly correct", one hook (regression on save).

## 6. If approved: timeline
- **Sun 22 Nov:** VM + capture/forward + corpus generator + grid (≈8h). Send interview requests.
- **Mon 23 Nov:** rule generation + interpreter + validators + FHIR + gates (≈10h). Interviews 1–3.
- **Tue 24 Nov (morning):** go/pivot decision against the gates (see `15`).
