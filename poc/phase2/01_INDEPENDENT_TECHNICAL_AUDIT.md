# 01: Independent technical audit (Phase 2, Stage 1 baseline)

**Date:** 21 Nov 2026.

**System under audit:** the frozen **v2.1** PoC at commit `083bcc6` on branch `poc/spoolgeist-validation`. The audit modified no system file.

**Method:**
- read every source file;
- re-ran the committed benchmark and property test;
- ran ten new read-only probes. The probes are in [audit/probes.py](audit/probes.py) and their raw output is in [audit/results/](audit/results/).

Every claim below is labelled with its evidence type:
- **[EXP]**: verified experimentally in this audit;
- **[SRC]**: verified by reading source code;
- **[DOC]**: taken from earlier reports and not re-verified;
- **[INF]**: inferred but not tested.

---

## 0. Baseline (Stage 1)

| Item | State | Evidence |
|---|---|---|
| Branch | `poc/spoolgeist-validation`, HEAD `083bcc6` (parent `53668b7`) | [EXP] `git` |
| `main` | `53668b7` (initial commit), identical to `origin/main`; **untouched** | [EXP] |
| Pushed? | No; the branch exists only locally | [EXP] |
| Working tree | System files clean; new files only under `phase2/` | [EXP] `git status` |
| Code hashes | 30 system, test, binding and experiment files hashed in [audit/baseline_hashes.json](audit/baseline_hashes.json) | [EXP] |
| Freeze manifest v2.1 | Matches the current code (0 files changed). v1 and v2 manifests differ only by the documented post-freeze changes | [EXP] |
| Freeze ordering | `run_benchmark --freeze && … run_rulegen D/E/F` were chained in one shell command, so the freeze preceded unseen-layout rule generation | [EXP] session transcript |
| Benchmark v2.1 reproducible? | **Yes.** All 326/326 row classes are identical on re-run (`bench_phase2_baseline_repro_*`) | [EXP] |
| Property test (default seed) reproducible? | **Yes.** It matches the committed `runtime/pbt_stats.json` exactly: 1,597 correct accepts, 809 correct rejects, 593 false rejects, **1 unsafe accept** (pbt-A-5208); the test **fails** as designed | [EXP] |
| Windows VM, Kiro, printers on this Mac | **None.** No UTM, Parallels, VirtualBox or QEMU; no Kiro; no CUPS printers. The machine is Apple M5 (arm64) | [EXP] |

### Correction to earlier reporting

**"7 unsafe accepts":**
- The 7 come from two runs: 3 in the v2 default run and 4 in the fresh seed-424242 run.
- They are **6 distinct documents**, because Hypothesis reported `pbt-A-541` twice (once with an extra digit change).
- **All share one mechanism** (F-01).
- The current v2.1 default run has 1. That is not a contradiction: the lab dictionary changed between v2 and v2.1, which shifts Hypothesis's generated cases.

**Property-test false-rejection rate:**
- The PBT false-rejection rate is **about 20–27%** of valid-labelled cases.
- The earlier reports cite only the benchmark's 9/176 (5.1%) and never quote the PBT rate prominently.
- Most of the PBT rate comes from comment lines (rejected 100% by design) and long names (§F-09).
- In a single-variation re-run (P08b): **clean documents 1,510/1,510 accepted**; **long names 192/301 rejected**; every other valid variation was rejected at most 2/~300.

---

## 1. Findings

Severity scale:
- **CRITICAL**: a wrong value is accepted.
- **HIGH**: a defective or unapproved document is accepted, or a real-world harm such as duplicate physical prints.
- **MEDIUM**: data integrity or privacy is weakened, or a metric hides failures.
- **LOW**: hygiene.

**No CRITICAL (wrong-value) defect was found** in this audit. That is a statement about these probes on synthetic data, not a proof.

### F-01 HIGH: layout recognition accepts a redesigned report (anchors match anywhere)
- **Previously known:** yes (KNOWN_LIMITATIONS §2). It is the sole cause of every v2 unsafe accept.
- **Reproduction [EXP]:** `probes.py p01`. Render layout A with the new page-1 letterhead (`new_header`) and a page break. The renderer keeps the old lab name on the continuation page.
  - Result: **200/200 ACCEPTED**, all with correct data.
  - B, D and F reject the same perturbation (200/200 each), because their anchors happen to include a page-1-only element.
  - Variant (b): an unregistered layout-G report with another lab's anchor lines appended as page 2 is **recognised as that lab** in 6/6 layouts. It is then rejected by `missing_field` / `table_start_missing`, so that rejection is luck, not design.
- **Root cause [SRC]:**
  - `matches_layout()` runs `regex.search` for each anchor over the whole document in MULTILINE mode. Nothing constrains page, position, order or count.
  - The activation gate saw a single `header_changed` dev document, and it had no page break, so it could not expose the issue.
- **Component:** `interpreter.recognise`, `binding_schema` (no positional vocabulary), `rulegen` gate coverage.
- **Remediation:** page-structured recognition, compared in Stage 2.
  - Every page must begin with the binding's page-header template in order.
  - Page 1 must contain the identity block within its first N lines.
  - Any page whose header matches no approved template, or matches a different layout, means reject.
- **Regression test:** the R-ANCHOR suite: old anchors on later pages, new header with old footer, page-order swap, foreign document carrying old anchors. Each must be run on all 6 layouts.

### F-02 HIGH: the forwarder can print a job several times
- **Previously known:** **no.** The earlier docs claim "never forwarded twice".
- **Reproduction [EXP]:** `p07a`. A fake printer reads the whole job, then closes with TCP RST.
  - Result: the printer received **4 identical copies in 9 s**, and the job was still in `retrying` state. A 5th attempt was due.
- **Root cause [SRC]:**
  - In `forward_job`, connect, write, drain, `write_eof` and the status read all sit in one `try`. Any `OSError` after the bytes were delivered (for example `ECONNRESET` during the status read) is treated like a connect failure and retried.
  - Nothing persists a "bytes may have been delivered" state before sending.
- **Real-world relevance [INF]:** some printers and print servers reset rather than close cleanly. Duplicate paper reports are a patient-safety and confidentiality concern.
- **Remediation:**
  - Persist `sending` before the first byte.
  - Retry automatically **only** if no byte was written.
  - After any byte is written, an abnormal close means `sent_unconfirmed` and needs operator action, never an automatic resend.
  - Make `retry_pending` respect this state.
- **Regression test:** an RST printer, a printer that dies mid-stream, and a printer that refuses the connection. Expected delivered copies: 1, ≤1, then 1 after recovery.

### F-03 MEDIUM: FHIR invents a collection time for date-only layouts
- **Previously known:** no.
- **Reproduction [EXP]:** `p10`. Layouts D and E print only a date. Their bundles carry `effectiveDateTime = "YYYY-MM-DDT00:00:00+05:30"`, asserting a midnight collection: 40/120 bundles.
- **Root cause [SRC]:** `interpreter.execute` always stores `datetime.isoformat()` in `collected_dt`, and `fhir_builder` appends the site timezone. Formats without `%H`/`%I` produce a fabricated `00:00:00`. The FHIR validator cannot detect it.
- **Rule violated:** "values are never invented".
- **Remediation:** record the printed precision (date or datetime) from the binding's format, and emit `effectiveDateTime` at exactly that precision.
- **Regression test:** for every layout, the emitted precision must equal the printed precision.

### F-04 MEDIUM: abnormal flags lost silently (layout B); flags are not scored
- **Previously known:** no.
- **Reproduction [EXP]:** `p09`. Over 60 accepted clean layout-B documents there were **225 results printed as abnormal but extracted with no flag**. In the FHIR round trip, 73 Observations lack `interpretation`.
- **Root cause [SRC]:**
  - Layout B marks abnormal values only in **bold** (ESC E / ESC F).
  - `grid.normalize` strips ESC sequences, which destroys an information-bearing signal.
  - The `lab-b` row regex therefore has no flag group, and V6 cannot check a flag that doesn't exist.
  - `score.CRITICAL` excludes flags, so no metric surfaced this.
- **Remediation:**
  - Preserve emphasis as an annotation stream alongside the text, or declare `abnormal_marker` in the binding with an explicit "not captured" state.
  - Never derive FHIR `interpretation` from the dictionary's ranges.
  - Score flag fidelity.
- **Regression test:** flag-fidelity metric per layout; layout B with bold markers.

### F-05 MEDIUM: the critical-field metric omits clinically relevant fields
- **Previously known:** no.
- **Evidence [SRC][EXP]:** `score.CRITICAL` covers patient_id, patient_name, collected, and result code, value and unit. It does **not** cover sex, age, reported date, flags or reference ranges. "Critical-field accuracy 1,887/1,887" is true but narrower than a reader assumes.
  - `p09`: sex and age were correct on all 360 accepted clean documents.
  - The flag loss in F-04 went unseen by every metric.
- **Remediation:** report three tiers separately:
  - identity and date;
  - result code, value and unit;
  - clinical context (sex, age, flag, range, precision).
- **Regression test:** metric unit tests with seeded wrong-flag and wrong-sex records.

### F-06 MEDIUM: printed demographics dropped silently when their label is damaged
- **Previously known:** no.
- **Reproduction [EXP]:** `p04`. Change one character of the age/sex label:
  - layout A: **30/30 accepted with age = None and sex = None**;
  - layout F: 30/30 accepted with age = None;
  - C, D, E: rejected.
  - B prints the name/age line twice. Damaging one copy leaves the intact copy to supply the correct value.
- **Root cause [SRC]:** optional fields (`required: false`) that fail to match become `None` without any check that the printed line carrying them is present. Sex is needed to interpret reference ranges, and FHIR `Patient.gender` disappears.
- **This is not "filling"** a value; it is silent loss of printed data.
- **Remediation:** add "value optional, presence enforced". If every approved sample carries the field, the gate makes it required. Otherwise the binding names the line that must be absent for `None` to be allowed.
- **Regression test:** label damage on each optional field, all layouts.

### F-07 MEDIUM: binding "SHA-256 pinning" is not an integrity control
- **Previously known:** no. The earlier docs present pinning as a control.
- **Reproduction [EXP]:** `p06`.
  - (a) Swap the M.C.V. and M.C.H. codes in `lab-a` and recompute `_meta.sha256`: **the binding loads.** In this instance the plausibility validator rejected 30/30 documents, but that is a domain-specific catch, not an integrity guarantee.
  - (b) Put a wrong hash in the file: it loads normally under `python -O` (6 bindings), because the check is an `assert`.
- **Root cause [SRC]:** the hash sits in the same file it protects, there is no external approval record, and the check uses `assert`.
- **Remediation:**
  - Keep an append-only approval registry, hash-chained, recording binding id, version, SHA-256, approver, timestamp and the gate report hash.
  - The loader verifies against the registry with an explicit exception.
  - Use immutable versioned file names.
- **Regression test:** tampered binding, wrong hash, binding missing from the registry, running under `-O`.

### F-08 MEDIUM: the activation gate is weaker than described
- **Previously known:** partly. Simulated approval was known; the rest is new.
- **Problems [SRC]:**
  - (a) `rulegen` writes `status: active` itself, so no approval state exists.
  - (b) The clean-acceptance denominator includes the 2 generation samples the LLM wrote the rule from.
  - (c) Only 1 dev document per defect class and no combinations, so F-01 passed.
  - (d) There is **no minimum acceptance on valid variations**: B, D, E and F reject about 100% of long names, yet passed.
  - (e) The collision check is one-way and uses only the other layouts' 2 generation documents. The candidate is evaluated alone, not together with the active set.
  - (f) Regenerating writes to the same `lab-x.v1.json`. A **failed** regeneration overwrites an active binding with `rejected-candidate`.
  - (g) Nothing checks that the samples disambiguate the date format.
- **Remediation:** gate v2. Every condition will be an executable check with a unit test (Stage 2, §4.2 of the brief).
- **Regression test:** one test per gate condition, each showing that a crafted bad candidate is refused.

### F-09 MEDIUM: long names essentially unsupported in 4 of 6 layouts
- **Previously known:** yes, but understated.
- **Reproduction [EXP]:** single-variation re-run: 192/301 long-name documents rejected, about 100% in B, D, E and F (`missing_field: patient_name`). The benchmark's "8 of 9 false rejects" hid the per-layout rate.
- **Root cause [SRC]:** bindings rely on column spacing that overflowing names destroy.
- **Remediation:** Stage 3; every relaxation must pass the adversarial suite.

### F-10 LOW-MEDIUM: V7 rejects valid zero results
- **Previously known:** yes (1 case).
- **Evidence [EXP]:** recurs for TBIL 0.00 (C) and AST/ALT 0 (F).
- **Root cause [SRC]:** `v < rl/50` is true for every `v = 0` when `rl > 0`.
- **Remediation:** treat 0 explicitly: allowed if the dictionary's plausible lower bound is ≤ 0 and the printed precision matches.
- **Regression test:** zero and near-zero values.

### F-11 MEDIUM (latent): encoding guess can corrupt identities
- **Previously known:** no.
- **Reproduction [EXP]:** `p05`.
  - The name "José" encoded in cp1252 fails UTF-8 decoding, falls back to cp437, and becomes **"JosΘ"**. Θ is a Unicode *letter*.
  - Today V2 rejects it only because `NAME_RE` is ASCII-only, which also rejects **every** non-ASCII name, including correct UTF-8 "José" (a false reject).
  - Relaxing V2 to `\p{L}`, the natural fix for that false reject, would turn this into **silent identity corruption**.
  - Separately, DOS cp437 box-drawing reports are refused at `sniff` as `binary-unknown`, because bytes ≥ 0x80 count as non-printable.
- **Root cause [SRC]:** `grid.normalize` guesses the encoding (UTF-8, then cp437) instead of using an approved one.
- **Remediation:** the binding declares a code page approved at onboarding; there is no fallback; invalid bytes mean reject. `sniff` evaluates printability under the declared code page.
- **Regression test:** cp1252, cp437 and UTF-8 names, mojibake, box drawing.

### F-12 LOW: underline overstrike destroys text
- **Previously known:** no.
- **Evidence [EXP]:** `X\b_` resolves to `_`, so the name becomes "___________". It is rejected by V2: fail-closed, but a false reject. `_\bX` and bold overstrike work.
- **Remediation:** when resolving an overstrike, prefer the non-underscore character.

### F-13 MEDIUM (privacy): patient data in logs; world-readable spool
- **Previously known:** partly ("no security hardening").
- **Reproduction [EXP]:** `p07c`.
  - The patient name appears in `events.jsonl`, through a reject reason such as `V2 implausible patient_name '…'`.
  - The same text goes into `review_queue/*.result.json`.
  - Job files are created `0644`. There is no retention policy and no encryption.
- **Remediation:** logs carry reason codes and field names only. Values go only into a protected review record. Set `umask 077`, add a retention job, and encrypt at rest as a production item (Phase F).

### F-14 LOW-MEDIUM: duplicate handling is volatile and byte-based
- **Previously known:** partly.
- **Evidence [EXP]:** `p07b`.
  - A reprint within 10 minutes is flagged.
  - After a listener restart the same bytes are **not** flagged, because the state lives only in memory.
- **More problems [SRC]:**
  - A deliberate reprint and a spooler retry are indistinguishable.
  - A reprint of a job that was **rejected** is suppressed as `DUPLICATE` even after a fixed binding could now accept it.
- **Remediation:**
  - Persist the dedup index.
  - Make the data idempotency key semantic (binding, patient_id, collected and result-set hash), not byte-based.
  - Re-process duplicates whose original was rejected.

### F-15 LOW: "complete" means graceful EOF, not a complete job
- **Previously known:** no.
- **Evidence [SRC][EXP]:** a spooler that cancels and closes cleanly delivers a prefix that `capture.py` calls complete.
- **Mitigation already in place:** `p02` swept all 2,157 line-boundary prefixes of 90 clean documents.
  - 2,007 were rejected.
  - The 150 accepted prefixes had lost only footer or marker lines, and **every one produced a record identical to the full document**.
  - The required table-end marker is what contains this risk.
- **Remediation:** keep the end-marker requirement mandatory in the schema, and flag a "footer missing" warning.

### F-16 LOW: `presentedForm` is mislabelled
- **Previously known:** no.
- **Evidence [EXP]:** `p10`, 120/120. The attachment is titled "Original printed report (print job sha256 …)" but contains *normalised text*, whose hash differs from the job hash.
- **Remediation:** title it as normalised text, include its own SHA-256, and reference the raw job hash separately.

### F-17 LOW: freeze manifest scope
- **Previously known:** no.
- **Evidence [SRC]:** `FROZEN` excludes `bindings/*.json`, `fhir_builder.py`, `capture.py` and `tests/`. The benchmark summary records binding ids, not hashes.
- **Mitigation [EXP]:** all of these are now in git commit `083bcc6`.
- **Remediation:** for v3, the manifest covers every pipeline file and every binding hash, and the summary records them.

### F-18 LOW: results depend on the run date
- **Evidence [SRC]:** V4 uses `date.today()`.
- **Remediation:** a fixed evaluation date stored in the manifest.

### F-19 MEDIUM (evaluation validity): the property test's labels mix policy with defects
- **Previously known:** no.
- **Evidence [EXP]:**
  - `comment_line` and `static_char_damage` are labelled "valid, should accept", yet the system rejects comment lines **by design**.
  - The PBT's 20–27% false-rejection figure therefore mixes intended refusals, genuine false rejects (long names, zero values) and arguable cases (damaged static text).
  - `digit_change` can create implausible values that are still labelled valid (2 cases, V5).
- **Remediation:** an explicit, separately specified perturbation catalogue with an expected label and rationale per class, and per-class reporting (Stage 3).

### F-20 INFO: the "review queue" is a directory
- **Evidence [SRC]:** each rejected job leaves only a result JSON with reasons.
  - There is no state (open, resolved, approved), no reviewer identity, no link to the failing text spans, no access control and no audit trail.
  - The extracted partial record of a rejected document isn't kept.
- **Remediation:** a minimal state machine plus an append-only review log (P1).

### F-21 LOW: capture robustness details
- **Problems [SRC]:**
  - Background forward tasks are not referenced, so asyncio may garbage-collect them.
  - "Persist first" writes without `fsync`.
  - Quarantined oversize or idle jobs are never printed, and the spooler retries them indefinitely.
  - Failed forwards are retried only at restart.
- **Remediation:** listed in report 06.

### F-22 INFO: runtime depends on benchmark code
- **Evidence [SRC]:** `capture.process_job` imports `bench.run_benchmark.load_bindings`.
- **Remediation:** move the loader and registry check into `spoolgeist/`.

---

### F-23 HIGH (added in Stage 2): results for unknown tests printed outside the table are dropped silently
- **Previously known:** no. Found by the Stage 2 adversarial suite, which was run on v2.1 before any fix.
- **Reproduction [EXP]:** `phase2/suites/adversarial.py`, classes `X_extra_section_after_end_unknown_tests` and `X_extra_section_before_table_unknown_tests`. Add a section such as "ELECTROLYTES / SERUM SODIUM 138 mmol/L" after the end marker or before the column header.
  - Result: **72/72 ACCEPTED** across all six layouts. The record omits the extra result without any trace.
- **Root cause [SRC]:** coverage is enforced only between `start` and `end`. The v2 `rows_outside_table` check looks only for labels the binding already knows.
- **Status:** fixed in v3 by whole-document line accounting (report 04 §2).

## 2. The 12 audit questions

| # | Question | Answer |
|---|---|---|
| 1 | Partial transfers handled correctly? | **Mostly.** Resets, idle and oversize transfers are quarantined [SRC][DOC E3–E5]. A graceful close after cancellation counts as complete (F-15), but the end-marker requirement contained it in 2,157/2,157 prefixes [EXP] |
| 2 | Can incomplete or oversized jobs enter extraction? | **No** [SRC]: `handle()` returns before persist, forward or process |
| 3 | Is duplicate detection logically correct? | **Only within one process lifetime, and only byte-level** (F-14). Forwarding duplicates **paper** under RST (F-02) |
| 4 | Are original bytes preserved? | **Yes** on disk and in forwarding [DOC E1, CUPS SHA match]. The FHIR attachment is normalised text, mislabelled (F-16) |
| 5 | Can the parser silently omit rows? | **Not in any probe since the v2 fix:** concatenation 480/480 rejected, truncation 0 data-changing accepts. Abnormal **flags** are omitted in B (F-04), and optional demographics in A and F (F-06) |
| 6 | Are fields tied to the correct patient and report? | **Yes in all probes:** multi-patient jobs rejected (480/480), conflicting repeated fields rejected [EXP] |
| 7 | Is layout recognition sufficiently constrained? | **No** (F-01) |
| 8 | Does the gate enforce every stated condition? | Stated conditions yes; **missing conditions and approval are the problem** (F-08) |
| 9 | Are the rule hash and code freeze meaningful? | Freeze: yes for its 11 files, and ordering verified. Hash pinning: **no** (F-07) |
| 10 | Are validators independent of extraction? | **Code-independent** [SRC]: they import only the dictionary. V6 and V7 consume the binding-extracted reference ranges, so they test internal consistency, not independent truth |
| 11 | Does FHIR preserve units, codes, IDs and dates? | Units, LOINC codes, IDs and values: 0 discrepancies in 120 bundles [EXP]. Time precision invented (F-03); flags lost (F-04) |
| 12 | Is review-queue behaviour safe and auditable? | **Safe** in that nothing rejected is emitted; **not auditable** (F-20); leaks names into logs (F-13) |

## 3. Verified strengths (keep)
- Fail-closed coverage rule, conflicting-field rule and v2 `rows_outside_table` check: 0 wrong-value accepts in every probe.
- Benchmark and PBT are bit-reproducible from the commit.
- The validators caught a deliberate code swap even after the integrity check was bypassed.
- Unit conversion and LOINC mapping are correct in every bundle checked.

## 4. Priority for Stage 2
- **P0:** F-01, F-02, F-03, F-07, F-08.
- **P1:** F-04, F-05, F-06, F-11, F-13, F-19.
- **Stage 3:** F-09, F-10, F-12.
- The rest go to the roadmap (report 13).
