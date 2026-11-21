# Phase 2 execution plan (after the Stage 1 baseline)

**Deadline:** the submission deadline in the earlier research is **4 Dec 2026, 18:00 IST**. It will be re-verified against the official rules in Stage 6.

**Time budget:** 13 calendar days remain. This plan budgets about **24 hours of agent work** for Phase 2, in parallel with the user actions listed at the end.

**Versioning:**
- The v2.1 system (`spoolgeist/`, `bindings/`, `runtime/`) stays **untouched** as the historical baseline.
- The hardened system will live in a separate package, **`spoolgeist_h/`** (v3). It starts as a copy of v2.1, and every change is recorded in `EXPERIMENT_LOG.md`.
- Every new test suite runs against **both** v2.1 and v3, so improvements are shown against the same evidence.

## Stage 2: Critical correctness (about 7 h). P0 findings F-01, F-02, F-03, F-07, F-08

1. **Write the R-ANCHOR / adversarial regression suite first, before any fix.**
   - It covers the 6 original unsafe-accept documents plus the brief's §4.3 list: old anchors on later pages, new header with old footer, page-order changes, repeated or conflicting identities, repeated rows, missing or extra sections, reordered columns, truncated headers, missing units, and text between rows.
   - Run it against v2.1 to record the "before" state.
2. **Compare recognition designs on that suite:**
   - (a) position-bound anchors;
   - (b) ordered page-header template per page;
   - (c) first-page identity block plus cross-page consistency;
   - (d) structural fingerprint (line-shape signature).
   - Criteria: unsafe accepts, clean acceptance, and how far the design generalises without per-layout code.
   - Implement the winner in v3.
3. **Derive positional constraints deterministically** from each existing binding plus its approved samples where possible, with no LLM. If the schema change needs regenerated bindings, use at most US$5 of synthetic-only LLM calls, each logged.
4. **Gate v2:**
   - every condition executable and unit-tested;
   - a real approval state backed by an append-only, hash-chained approval registry (CLI approve and reject commands);
   - versioned, immutable binding files.
5. **Forwarder fix (F-02):** retry only when no byte was written, otherwise `sent_unconfirmed`. Add RST and mid-stream-death regression tests.
6. **Date precision (F-03):** no invented times.
7. **Freeze v3, then run** the suite, the old benchmark and a fresh-seed PBT.
   - **Checkpoint:** if v3 cannot reach 0 unsafe and 0 wrong-value accepts on the suite without a large collapse in clean acceptance, I will report early rather than continue.

## Stage 3: Benchmark integrity (about 7 h)

1. **Write the perturbation catalogue as a specification first** (`02_BENCHMARK_DESIGN.md`). Each class gets an expected label and a rationale, and policy refusals are kept separate from defects (F-19).
2. **Physiologically consistent generator:**
   - Hard identities: MCV = Hct/RBC×10, MCH = Hb/RBC×10, MCHC = Hb/Hct×100, differential total ≤ 100%, DBIL ≤ TBIL.
   - Approximate relationships are kept separate, with sources cited (`03_REALISM_AND_DOMAIN_VALIDATION.md`).
3. **Realistic variations:** wrapped and long names, comments and interpretive notes, multi-section and multi-page reports, version drift, cp437 and cp1252 encodings, bold flags.
4. **System fixes, each with a no-new-unsafe test:**
   - explicit comment-row type;
   - long-name handling;
   - zero values (F-10);
   - flag fidelity (F-04);
   - presence-enforced optional fields (F-06);
   - declared code page (F-11);
   - overstrike (F-12).
5. **Independent evaluation:**
   - a hidden test seed, committed by hash before the run;
   - metamorphic tests;
   - mutation testing of the interpreter and validators;
   - the three-tier metrics from F-05, with raw counts, confidence intervals and per-category tables.
   - Output: `04_ADVERSARIAL_TEST_RESULTS.md`.
6. **Date and domain layer:** `05_DATA_INTEGRITY_AND_DATE_SAFETY.md`.

## Stage 4: Capture and security (about 3 h)
- `06_PRINT_CAPTURE_AND_WINDOWS_READINESS.md`:
  - capture audit;
  - Windows 11 (ARM, since this Mac is Apple Silicon) procedure with expected bytes, hashes and job counts;
  - a physical-printer test procedure;
  - a truthful fallback demo.
- `07_SECURITY_AND_PRIVACY_REVIEW.md`: threat model, split into MVP and production requirements.

## Stage 5: Market and Kiro (about 3 h)
- `08_MARKET_VALIDATION_PLAN.md`: segment research, competitors, an interview guide for 5 interviews with disconfirming questions, and an evidence template. **No invented responses.**
- `09_PRODUCT_POSITIONING_REASSESSMENT.md`.
- `10_KIRO_READINESS_AND_USAGE_PLAN.md`: verified against the official Kiro documentation, plus the in-IDE checks that need the user's installation.

## Stage 6 and 7: Competition, roadmap, decision (about 4 h)
- `11` competition re-assessment against the official rules.
- `12` demo strategy.
- `13` roadmap (P0 to CUT, sized for the real team capacity).
- `14` final GO / MODIFY / PIVOT decision.
- `PHASE2_EXECUTIVE_SUMMARY.md`.

## Needs the user (can start now, in parallel)
1. **Windows test machine:**
   - a Windows 11 PC on the same network, **or** permission to install UTM (free) plus a Windows 11 ARM evaluation image (about 6 GB) on this Mac;
   - not started without your approval.
2. **Kiro:** install Kiro and sign in. I can only verify the IDE's real behaviour (specs, hooks, PBT) once it exists on a machine.
3. **Interviews:** names of 5 reachable people (lab owners or technicians, clinic administrators, hospital IT staff, LIS implementers).
4. **Team capacity:** how many people and hours per day until 4 Dec. The roadmap in report 13 depends on it.
5. **Any physical network printer** (RAW/9100) for one forwarding test. Optional.
