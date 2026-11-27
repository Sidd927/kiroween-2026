# Spec briefs (paste one into Kiro's "New spec" prompt)

Reference material for every spec: the research repository `Sidd927/kiroween-2026`, branch `poc/spoolgeist-validation`. Most useful paths:
- `poc/spoolgeist_h/` (the v4 reference engine);
- `poc/bench2/` (generator and evaluator);
- `poc/phase2/02_BENCHMARK_DESIGN.md`;
- `project-transition/25_MVP_ACCEPTANCE_CRITERIA.md`;
- `project-transition/27_DESIGN_SYSTEM.md`.

---

## 1. engine-core
> Build the deterministic extraction engine for Spoolgeist as a **pure TypeScript package** (no I/O): Node 22+, strict TS.
>
> **Libraries:**
> - all rule regexes run on **RE2** (npm `re2`, falling back to `re2-wasm` if the native build fails on the host), so evaluation is linear-time and AI-written patterns cannot cause catastrophic backtracking;
> - exact decimal arithmetic with `decimal.js`;
> - property tests with `fast-check` under `vitest`.
>
> **Input:** the raw bytes of a print job plus the queue's declared code page.
>
> **Output:** exactly one of:
> - ACCEPT, with a structured lab record (patient id, name, age, sex, collected date at its printed precision, reported date, results with code, value, unit, flag and printed reference range, and notes);
> - NEEDS_CONFIRMATION (the same record, but approved free text is present);
> - REFUSE, with a reason that names the offending line.
>
> **Rules** are declarative JSON "bindings" that were approved earlier; there is **no AI on this path**. Binding regexes use **RE2 syntax only** (no lookbehind, no backreferences). A pattern RE2 rejects makes the binding invalid; it is never "fixed up" at runtime. Every non-blank line must be explained: result row, field, static template line, approved note, or trusted line matching an approved text skeleton. Otherwise refuse.
>
> **Also require:**
> - definitional consistency checks (MCV = Hct×10/RBC, MCH = Hb×10/RBC, MCHC = Hb×100/Hct with interval arithmetic on printed precision; NEUT% + LYMPH% ≤ 100; DBIL ≤ TBIL; ALB < TP);
> - plausibility limits from a dictionary;
> - strict decoding (no encoding guessing);
> - one writing system per patient name.
>
> **Correctness property (write it as a property-based test):** for any generated document, the engine either refuses, or accepts with every tier-1 and tier-2 field exactly equal to ground truth; every defective document is refused.
>
> **Acceptance:** criteria E1–E4 in `25_MVP_ACCEPTANCE_CRITERIA.md`, measured with the research repository's sealed test split and held-out sets as the oracle.

## 2. capture-and-forwarding
> In TypeScript (Node `net`): a RAW/AppSocket (TCP 9100) listener that persists every complete job (bytes + SHA-256, fsync, 0600) before anything else, quarantines incomplete, oversize and idle jobs, and forwards byte-for-byte to a configured printer.
>
> **Forwarding states:** `captured → persisted → forwarding → sent | unconfirmed | failed`.
> - Automatic retry happens **only** if no byte was written.
> - Once bytes are written, an abnormal close means `unconfirmed` (operator decides); never an automatic resend.
> - `sent` only means the peer closed normally. It is not proof of printing; RAW has no acknowledgement.
>
> **Replay mode:** for the hosted demo, an uploaded `.prn` is processed identically but labelled "replay" everywhere.
>
> **Also require:** event logs carry no patient values. Write tests with fake printers (normal, reset after full receipt, death mid-stream, offline then online).

## 3. rule-onboarding
> When a job matches no approved rule, the reviewer can onboard its layout:
> 1. **Candidate:** an LLM drafts a binding from **synthetic look-alike samples only** (a pre-send guard refuses unmarked documents). The prompt states that every regex must be valid **RE2 syntax**.
> 2. **Compile:** a deterministic compiler derives the header template, static lines, note markers, numeric and text skeletons, and field promotions from operator-verified samples, recording provenance (sample hashes).
> 3. **Gate:** 9 conditions, plus generic adversarial mutations of the samples (identity line replaced, unknown lines, unit deleted, results smuggled onto trusted lines, …). All must be rejected.
> 4. **Approve:** a human types their name; approval re-compiles and re-runs the gate, then appends to a hash-chained registry.
>
> **Also require:** revocation leaves the layout with no active rule. Show the gate report in full.

## 4. review-ui
> A React + TypeScript (Vite) workbench, served by the same Node service (Hono API + SQLite via `better-sqlite3`), following `27_DESIGN_SYSTEM.md` ("Greenbar").
>
> **Views:**
> - **Inbox:** status, time, layout, source.
> - **Job view:** the printout as green-bar paper with a line-accounting gutter; the extracted record; a decision panel with confirm, refuse and download FHIR.
> - **Rule onboarding stepper.**
> - **Audit:** registry chain status and a job timeline.
>
> **Also require:** WCAG 2.1 AA, keyboard navigation, and empty, loading and error states. No mock data: every view calls the real API.

## 5. fhir-export
> In TypeScript: convert an accepted (or confirmed) record into a FHIR R4 document Bundle: Composition, Patient, Organization, DiagnosticReport (with `presentedForm` = the normalised text and both hashes, and `conclusion` = the notes verbatim, or a labelled placeholder), and Observations (LOINC, UCUM, converted values, interpretation only from printed markers, printed reference range).
>
> **Also require:**
> - `effectiveDateTime` at the printed precision;
> - the site timezone applied only when a time is printed.
>
> **Validate** offline (a Java CLI, used as a test-time tool rather than at runtime) with the official HL7 validator, generic R4 and `ndhm.in#6.5.0`, plus a negative control. Make no ABDM integration or certification claims.
