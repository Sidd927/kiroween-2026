# 04: Adversarial test results. Part 1: Stage 2 hardening (v3)

**Date:** 21 Nov 2026.

**Systems compared:**
- **v2.1:** frozen PoC, commit `083bcc6`, untouched.
- **v3:** `spoolgeist_h/` plus `bindings_h/`, frozen in `stage2/freeze_manifest_v3.0.json` (38 files: code, bindings, registry, gate reports, tests, suite, runners).

The freeze manifest was re-checked after every run below and was still valid.

**The property is unchanged and was not weakened:**
- a document with a detectable defect must be rejected;
- an accepted document must have every critical field exactly equal to ground truth.

Part 2 (Stage 3: realistic data, independent catalogue, three-tier metrics) will be appended.

---

> **Correction after the post-freeze red-team review ([stage2/V3_REVIEW.md](stage2/V3_REVIEW.md)):**
> - New attacks written after the freeze show that v3 still **accepts 110 of 190** applicable documents in which a printed result sits on a line that line accounting trusts: a field line, or a line matching a binding skip or anchor regex. The result is dropped silently.
> - F-23 is therefore only **partly** fixed. The 0/776 below is true for the suite's classes but must not be read as "no printed result is ever dropped".
> - A binding-independent result sentinel is proposed as v3.1.

## 1. Headline (raw counts; denominators shown)

| Evidence | v2.1 | v3 | Independence |
|---|---|---|---|
| Adversarial suite v1.1, defective docs **accepted** | **158 / 776** | **0 / 776** (95% upper bound 0.39%) | **Low.** Same author as v3, and v3's design responded to it (§5) |
| Adversarial suite, valid docs accepted correctly | 216 / 240 | 216 / 240 | Low |
| Adversarial suite, silent (wrong-value) errors | 0 / 216 | 0 / 216 | Low |
| PBT, derandomised default (N = 3,000), unsafe and silent | 1 | **0** | Medium: case builder unchanged from the PoC, frozen generator |
| PBT, **pre-registered** seed 20261121 (N = 5,000), unsafe and silent | **4** | **0** | Medium: seed fixed in the log before the run |
| PBT, **pre-registered** seed 4242001 (N = 5,000), unsafe and silent | **2** | **0** | Medium |
| PBT v3 total over 13,000 cases | | 0 unsafe in 3,461 invalid (upper bound 0.087%); 0 silent in 6,700 accepted (upper bound 0.045%) | Medium |
| Original held-out benchmark (326 docs) | 167 correct accepts, 150 correct rejects, 9 false rejects | **identical, row for row** | PoC-era held-out set |
| Benchmark latency, median / p95 | 0.46 / 0.83 ms | 0.51 / 0.97 ms | |
| FHIR validator on v3 bundles | (PoC: 167/167, 0 errors) | **167/167 generic R4, 0 errors; 167/167 ABDM `ndhm.in#6.5.0`, 0 errors** | Official HL7 validator |
| v3 regression tests (`tests_h/`) | | 29 / 29 pass (capture 7, registry/gate/precision 22) | |

Upper bounds are one-sided 95% Clopper-Pearson bounds for k = 0, computed as 1 − 0.05^(1/n).

All of these are **synthetic data from one generator family** (KNOWN_LIMITATIONS §1 still applies). They are not evidence about real reports.

## 2. What changed (v2.1 → v3), and why

| Finding | Change | Evidence it works |
|---|---|---|
| **F-01** anchors anywhere | Page-1 **header template** derived deterministically from approved samples. Each line is either exact static text or one of the binding's own anchor/skip regexes that matched that line in *every* sample, and the template must open page 1 in order | Suite: `X_orig_pbt_unsafe` 8→0, `X_new_header_old_continuation` 24→0, `X_title_replaced_page1_only` 24→0, `X_old_header_page_appended` 30→0. PBT: 7→0 |
| **F-23 (new, found by the suite)** results for unknown tests printed outside the table were silently dropped | **Whole-document line accounting:** every non-blank line outside the table region must be a header-template line, a static template line, a binding skip/anchor line, or a line containing a field match. Otherwise REJECT `unaccounted_line` | `X_extra_section_after_end_unknown_tests` 36→0, `…before_table…` 36→0. **Bypassed** by results placed on field, skip or anchor lines (V3_REVIEW RV-1) |
| **F-02** duplicate physical prints | Retry only if no byte was written. After that, an abnormal close means `sent_unconfirmed` with no automatic resend; an operator uses `--resend`. A `sending` state is persisted before the first byte, so a crash mid-send also becomes `sent_unconfirmed` | `test_rst_after_full_receipt_is_not_resent`: 1 copy (v2.1 sent 4). Mid-stream death, crash on restart, offline-then-online (exactly 1) and operator resend all pass |
| **F-03** invented midnight times | Date precision recorded; `collected_dt` only when the format prints a time | `test_F03_no_invented_time` for all 6 layouts. D and E now emit a date only |
| **F-06** optional demographics dropped silently | An optional field present in 100% of approved samples is promoted to required at compile time | lab-a promotes age, sex and reported; lab-f promotes age and sex; `test_F06…` |
| **F-07** self-referential hash, `assert` | **Approval registry:** append-only, hash-chained `approvals.jsonl`. The loader verifies each binding's exact SHA-256 against the registry with explicit exceptions; versioned immutable files; revocation | 9 registry tests, including an edit after approval, a history edit, and `python -O` |
| **F-08** weak gate | **Gate v2** with 9 executable conditions (`spoolgeist_h/gate.py`), see §3. Generation samples are excluded from the acceptance denominator. Bidirectional collision check against the active set. Rejected valid variations become warnings that must be acknowledged at approval. Date-order disambiguation check. Generic self-adversarial mutations. Fails closed if compilation fails | 7 gate tests, each with a deliberately bad candidate (wrong code map, no header identity, permissive skip, collision, ambiguous dates) |
| **F-13** patient values in logs | Event log carries reason codes only. Files are 0600 and directories 0700. Spool writes are fsync'd | `test_no_patient_values_in_event_log_and_private_files` |
| **F-16** mislabelled presentedForm | Retitled "Normalised text…", with both hashes | `test_F03…` asserts the title |
| **F-17** freeze scope | The v3 manifest covers code, bindings, registry, gate reports, tests, the suite and the runners | `run_benchmark_v3` refuses to run on any change |
| **F-21 / F-22** | Forward tasks referenced; runtime loads bindings through the registry, not the benchmark module | inspection |
| rulegen | LLM output is only ever a **candidate** in `bindings_h/candidates/` and is never active | inspection. **Not exercised against the LLM in Stage 2** (0 LLM calls, US$0) |

## 3. Gate v2 results for the six compiled bindings

All six pass all nine conditions. The approver must acknowledge these warnings:

| Binding | Header lines (identity index) | Continuation lines | Promoted to required | Warnings to acknowledge |
|---|---|---|---|---|
| lab-a | 9 (0) | 1 | age, sex, reported | none |
| lab-b | 8 (0) | 6 | sex, reported | unsupported_variation:long_name |
| lab-c | 8 (0) | none | age, sex, reported | multipage_documents_rejected |
| lab-d | 7 (1) | 7 | age, sex | unsupported_variation:long_name |
| lab-e | 3 (0) | none | age, sex | unsupported_variation:long_name, multipage_documents_rejected |
| lab-f | 4 (0) | 4 | age, sex | unsupported_variation:long_name |

**G8 dates:** every day/month-order format is disambiguated by the approved samples. This holds because the corpus builder deliberately gave the first generation sample a day > 12. `test_G8…` shows that samples with every day ≤ 12 force explicit confirmation at approval.

**G6 self-adversarial:** for all six bindings, 8–9 generic mutations × 4 approved samples were all rejected:
- identity line replaced;
- header line dropped;
- an unknown line after the end, before the start, or inside the table;
- column header truncated;
- unit deleted (not applicable to lab-f, whose unit sits inside the test name);
- two reports in one job;
- pages swapped (where a multi-page sample exists).

**Approval state, stated honestly:**
- The six approvals in `bindings_h/approvals.jsonl` were recorded with `approver_kind = "agent"` and the note "experiment approval; NOT a human review". The agent acknowledged the warnings.
- The v3 pipeline **refuses agent approvals by default**. Experiments pass `allow_agent_approval=True` explicitly.
- **A human approval has not happened yet.** It needs you. The command is in §8.

## 4. Recognition design comparison (Stage 2 §4.1)

Four designs were implemented as modes of the same v3 code and evaluated on the identical frozen suite:

| Mode | What it adds | Defective docs accepted (of 776) | Valid correct (of 240) |
|---|---|---:|---:|
| `anywhere` | v2.1 behaviour: all anchors match somewhere | 158 | 216 |
| `pos` | ordered page-1 header template | 66 | 216 |
| `pos+pages` | plus every page start must repeat the approved continuation header (pages found by form feed **or** by recurrence of the identity line, because the generator's B, D and F continuation pages have no form feed) | 66 | 216 |
| **`full`** (chosen) | plus whole-document line accounting | **0** | 216 |

Per class, v2.1 and the four v3 modes (unsafe accepts):

| Class | n | v2.1 | anywhere | pos | pos+pages | full |
|---|---:|---:|---:|---:|---:|---:|
| `X_orig_pbt_unsafe` (the 7 PBT cases + 1 twin) | 8 | 8 | 8 | 0 | 0 | 0 |
| `X_new_header_old_continuation` | 24 | 24 | 24 | 0 | 0 | 0 |
| `X_title_replaced_page1_only` | 36 | 24 | 24 | 0 | 0 | 0 |
| `X_old_header_page_appended` | 36 | 30 | 30 | 0 | 0 | 0 |
| `X_extra_section_after_end_unknown_tests` | 36 | 36 | 36 | 36 | 36 | 0 |
| `X_extra_section_before_table_unknown_tests` | 36 | 36 | 36 | 30 | 30 | 0 |
| 19 other defect classes (foreign pages, page swap, conflicting identities, repeated rows, missing rows/units, reordered or swapped columns, truncated header, text or unknown results between rows, two patients, same patient twice, new header, …) | 600 | 0 | 0 | 0 | 0 | 0 |
| valid: clean, col_shift, crlf, drop_optional, page_break | 204 | 204 ok | 204 ok | 204 ok | 204 ok | 204 ok |
| valid: long_name | 36 | 12 ok / 24 FR | same | same | same | same |

**Not implemented: structural fingerprint (line-shape similarity).** It needs a similarity threshold, which makes recognition probabilistic. A threshold tuned on samples is exactly the "confidence" mechanism the fail-closed design avoids, and it does not by itself explain *which* line is unexpected. The line-accounting design gives a deterministic, explainable reason instead (`unaccounted_line: line 31 'ELECTROLYTES'`).

**Honest result on per-page checks:**
- `pos+pages` caught nothing that `pos` missed, even after two classes were added specifically to isolate it (suite v1.1).
- v2.1's table-coverage rule already rejects both of those classes.
- It is kept in `full` as defence in depth because its measured false-reject cost was 0 here. Its real cost is that **multi-page documents are rejected for C and E**, which have no approved multi-page sample (both are acknowledged gate warnings).
- Cutting it remains an option if it proves brittle on real reports.

## 5. Threats to validity (read before quoting)

1. **The suite is not independent of v3.** I wrote the suite, designed v3 in response to its "before" results, then added two suite classes after the first comparison. The gate's generic mutations overlap some suite classes. 0/776 shows that **the named weaknesses are closed**. It is **not** an unbiased estimate of real-world unsafe-acceptance.
2. **The stronger evidence is the PBT.** Its case builder and generator were frozen at the PoC, v3 was not tuned on it, and two seeds were fixed in `EXPERIMENT_LOG.md` before running. But its only defect class that reached acceptance in v2.1 was `header_changed`, so it mainly re-confirms F-01.
3. **The cost of v3 is concentrated in one place.** On the same seed, v3 false-rejects **86 more** PBT cases than v2.1 (1,072 vs 986), and all **86** are `static_char_damage`: a random character changed in a static header or footer line. That is 287 → 373 false rejects in that class, and correct accepts there fell from 99 to 13.
   - The PoC test labels these documents valid.
   - v3 treats them as defects: legacy software prints its own static text deterministically, so a mangled static line means capture or transmission corruption.
   - This is a **policy decision**, recorded here rather than hidden. Under the PBT's labels it is a 2.9-point rise in false rejection. No other valid class moved: clean, col_shift, crlf, drop_optional, page_break and long_name are all identical.
4. **Line accounting is only as tight as the binding's skip/anchor regexes and field-line rule.** This was confirmed by the post-freeze red team (RV-1: 110/190 bypasses).
   - A line containing any field match counts as accounted, even if it carries extra text.
   - A permissive LLM-written skip regex would weaken it. G6 tests for this generically (`test_G6_permissive_skip_fails`), but only for the mutation strings it uses.
5. **Real reports will contain lines this design rejects:** free-text comments, interpretive notes, operator remarks. v3 will refuse those documents (safe, but more false rejection). Comment handling is a Stage 3 item and must be added without re-opening F-23.
6. **Long names:** 24/36 still falsely rejected (Stage 3).

## 6. FHIR (v3 bundles, official HL7 validator)
- **Bundles:** the 167 accepted held-out documents were rebuilt with v3 (`phase2/stage2/run_fhir_v3.py`) and validated with the same `validator_cli` (`-version 4.0.1`) and IG as the PoC (`phase2/stage2/validate_v3.sh`).
- **Results:**
  - **Generic R4:** 167/167 with 0 errors.
  - **ABDM profiles:** 167/167 with 0 errors. This now includes the D and E bundles, whose `effectiveDateTime` is date-only (F-03 fix).
  - Raw output: `stage2/results/fhir_v3_{generic,abdm}.{json,log}`.
- **Negative control** (are the profiles still enforced?): one v3 ABDM bundle with `DiagnosticReport.conclusion` and `resultsInterpreter` removed gives **3 errors** (both minimum-cardinality violations plus the resulting profile-match failure).
- **Not done:** no ABDM sandbox, no certification, no consent flow. Profile validation is not integration.

## 7. Findings status after Stage 2

| Fixed in v3 | Partially fixed | Open: Stage 3 | Open: Stage 4 / roadmap |
|---|---|---|---|
| F-01, F-02, F-03, F-07, F-13 (logs, permissions), F-16, F-17, F-22 | **F-23** (only the suite's classes; RV-1 shows 110/190 bypasses), F-06 (only fields present in every sample are promoted), F-08 (real approval state built, **human approval pending**), F-21 (tasks, fsync; quarantine retries unchanged) | F-04 flags, F-05 metric tiers, F-09 long names, F-10 zero values, F-11 encoding, F-12 overstrike, F-19 labels | F-14 persistent and semantic dedup, F-15 footer warning, F-18 fixed evaluation date, F-20 review states, F-13 encryption and retention |

## 8. What you need to do for a real human approval (about 5 min)
Review each binding and its gate report. If you agree, record a human approval:
```bash
.venv/bin/python -m spoolgeist_h.registry approve bindings_h/lab-a.v3.json bindings_h/gate_reports/lab-a.v3.gate.json --approver "Your Name"
```
For layouts with warnings, add `--ack <warning…>` (copy the warnings from the table in §3). Then verify the chain:
```bash
.venv/bin/python -m spoolgeist_h.registry verify
```
After that, the pipeline can run without `allow_agent_approval`.

## 9. Reproduce (from `poc/`)
Build the bindings and gate reports (deterministic, no LLM):
```bash
.venv/bin/python -m phase2.stage2.build_bindings
```
Run the adversarial suite against both systems:
```bash
.venv/bin/python -m phase2.suites.adversarial --system v2.1
```
```bash
.venv/bin/python -m phase2.suites.adversarial --system v3:full
```
Run the original held-out benchmark against v3:
```bash
.venv/bin/python -m phase2.stage2.run_benchmark_v3 --split test --tag repro
```
Run the property test with a pre-registered seed:
```bash
PBT_SEED=20261121 PBT_N=5000 PBT_TAG=_repro .venv/bin/python -m pytest -q tests_h/test_property_v3.py
```
Run the regression tests:
```bash
.venv/bin/python -m pytest -q tests_h/test_capture_v3.py tests_h/test_registry_gate_precision.py
```

---

## 10. v3.1: fixes for the post-freeze review (RV-1 to RV-4)

**Frozen:** `stage2/freeze_manifest_v3.1.json` (53 files). v3.0 is preserved in `stage2/snapshot_v3.0/` with its own manifest. The bindings are now **v4**, which are v3 plus compiler provenance (original LLM output, sample and regression references with SHA-256).

| Item | Change | Result |
|---|---|---|
| RV-1: result hidden on a trusted line | `spoolgeist_h/sentinel.py`: a binding-independent scan of all text not consumed by a parsed row, for value+unit (dictionary units plus common clinical units) or analyte word+number. Gate G6 now also appends a result to every skip, anchor and field line of the samples | Red-team R1–R4: **190/190 rejected** (v3.0: 80/190). Gate G6: 60–160 mutations per binding, 0 accepted |
| RV-1, **held-out** evasion (written after the v3.1 freeze) | n/a | **7/15 phrasings still evade:** "Serum Na 138", "NA+ 138 mEq", "S.Sodium138mmol/L", "K 4.1 mmol per litre", "138 mmol / L", "Na 138 K 4.1 Cl 101", "Hb nine point eight". The sentinel is a **vocabulary heuristic, not a guarantee** |
| RV-2: forged gate report | `approval.py`: approval re-compiles from the stored LLM output and the exact referenced samples (SHA-256 checked), then re-runs the gate. No file-based gate report is read | Hand-edited binding refused (re-compilation mismatch). Unsafe but properly compiled binding refused by the re-run gate. 0 registry entries |
| RV-3: silent fallback on revoke | Last explicit decision wins. Revoking the active version leaves the id inactive until a person approves a new version or runs `reactivate` | No version active after revoking v5 |
| RV-4: processing error left no trace | `process_job_safe`: a `PROCESSING_ERROR` review entry plus a `job_processing_error` event (exception class only) | 1 review entry and 1 event |

**No regression, and no added false rejects:**
- Held-out benchmark: row classes identical to v3.0 and v2.1 (167 correct accepts, 150 correct rejects, 9 false rejects).
- Adversarial suite: 0/776 unsafe, 216/240 valid.
- PBT: identical to v3.0 on the default seed and both earlier seeds. Pre-registered new seed 7311: 0 unsafe, 0 silent (v2.1: 4 unsafe).
- **Total v3.1 PBT: 0 unsafe and 0 silent in 18,000 cases.**
- Development seed 11: the sentinel added 0 false rejects. FHIR builder unchanged since the v3.0 validation, and the accepted set is identical.
- Tests: 51/51.

**Residual risk:** a result printed on a line the binding trusts, written in a form the sentinel's vocabulary does not recognise, can still be dropped silently. This needs to be closed before any safety claim.

**Proposal: fold into Stage 3, together with comment handling, because both decide what free text may contain.** A **vocabulary-free "digit skeleton" rule**:
- Outside parsed rows, after removing field values, any line that still contains a digit must match a digit-shape skeleton seen in the approved samples, for example `ACCESSION #######` or `Page # of #`.
- On the evasion set this would close 6 of the 7 phrasings (all except the spelled-out "nine point eight").
- Its cost is that free-text remarks containing numbers would be rejected unless an approved comment pattern allows them.

---

## 11. v3.2: completing RV-1 (numeric results)

**Frozen:** `stage2/freeze_manifest_v3.2.json` (68 files). v3.1 is preserved in `stage2/snapshot_v3.1/`. The bindings are now **v5**.

**What was added:** a **vocabulary-free numeric-text rule** (`interpreter.numeric_text_check`).
- It applies to every line not consumed by a parsed result row: lines outside the table, the start and end lines, and lines that skip regexes drop inside the table.
- Field values are masked first.
- If the line still carries a number (digits in any Unicode script, or a number word), its digit-shape skeleton (digit runs replaced by `#`) must have been seen in the operator-approved samples.
- The approved skeletons are narrow:

  | Binding | Approved numeric skeletons |
  |---|---|
  | lab-a | the address line |
  | lab-b | `Page # of #`, the address |
  | lab-c | `Patient ID : <V> Sample : S-#` |
  | lab-d | none |
  | lab-e | the `LabSys #.#` footer |
  | lab-f | the accession line, the `RECEIVED` line |

- The compiler warns about any skeleton with fewer than 3 letters, which would be too generic.
- Gate G6 adds bare-number smuggles (`QX 42`) and digit-free unexplained text on every trusted line, so a permissive skip regex is still detected.
- The v3.1 vocabulary sentinel stays as a second layer.

**Pre-registered held-out evasion set v2:**
- 30 phrasings × up to 3 placements × layouts A, B, C, E = 330 cases, all expected REJECT.
- File hash recorded in the log before v3.2 was written; first run after the v3.2 freeze.

| Category | v2.1 accepted (result dropped) | v3.1 | **v3.2** |
|---|---:|---:|---:|
| Numeric, written with digits (incl. full-width and Arabic-Indic) | 179 / 198 | 89 / 198 | **0 / 198** |
| Numeric, spelled out ("nine point eight") | 60 / 66 | 60 / 66 | **0 / 66** |
| **Qualitative** ("HIV reactive", "HBsAg: POSITIVE", "Urine sugar ++", "Malaria parasite seen", "Blood group B negative") | 60 / 66 | 60 / 66 | **45 / 66** |
| Total | 299 / 330 | 209 / 330 | **45 / 330** |

The 21 qualitative rejections in v3.2 are incidental: "Dengue NS1 positive" contains a digit.

**Everything else (frozen v3.2):**

| Check | Result |
|---|---|
| Held-out benchmark | row classes identical to v3.1, v3.0 and v2.1 (167 / 150 / 9) |
| Adversarial suite | 0 / 776 unsafe; 216 / 240 valid |
| PBT | **0 unsafe and 0 silent in 23,000 cases** (default plus four seeds, three of them pre-registered). False rejects identical to v3.1 on every shared seed. v2.1 on the new seed 5150: 5 unsafe |
| Red team R1–R7 | all closed |
| Evasion set v1 | 15 / 15 rejected |
| Tests | 62 / 62 |
| Latency | median 0.67 ms, p95 1.27 ms (v2.1: 0.46 / 0.83) |

**Status of RV-1:**
- **Numeric results are closed on every set we have, including a pre-registered held-out set.**
- **Non-numeric (qualitative) results printed on a trusted line are not.** The system extracts only the 20 numeric tests in its dictionary, so a qualitative result anywhere outside the table is outside what the binding can represent, and v3.2 still drops it silently when it sits on a field, skip or anchor line.
- **Closing it vocabulary-free** means also constraining the *words* on trusted lines: an approved per-line text skeleton with wildcards only where the samples varied, such as the referring doctor's name.
- That is the same decision as comment handling (Stage 3): which free text a document may contain without being rejected.
- It needs a fresh pre-registered held-out set, because evasion set v2 has now been seen.
