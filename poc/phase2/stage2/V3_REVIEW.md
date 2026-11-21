# v3 review (post-freeze red team + code review), 21 Nov 2026

**Scope:** frozen v3 (`freeze_manifest_v3.0.json`). Nothing in v3 was changed by this review.

**Method:**
- New attack probes written **after** the freeze, which therefore did not inform v3's design: `phase2/stage2/redteam_v3.py`, raw output in `results/redteam_v3.json`.
- A line-by-line read of the v3 changes against v2.1. The validators, dictionary and lab dictionary are byte-identical to v2.1.

## Status after v3.1 (see report 04 §10)
- **RV-2, RV-3, RV-4:** fixed and tested.
- **RV-1:**
  - After v3.1, the specific attacks R1–R4 were 190/190 rejected, but 7 of 15 held-out phrasings evaded the sentinel.
  - **v3.2** (report 04 §11) adds a vocabulary-free numeric rule.
  - Pre-registered held-out set v2: numeric 0/264 accepted, **qualitative 45/66 still accepted**.
  - Numeric results are closed. Qualitative results on trusted lines remain open (a text-skeleton rule, decided together with comment handling).

## Verdict
v3 closes the defects it was designed against. It **does not yet fully close F-23** (results dropped silently), and it has **three governance and robustness gaps**. None of these produces a wrong value, but the "0 / 776" headline overstated the safety of the line-accounting design. Report 04 has been corrected.

## Findings

### RV-1 HIGH: a printed result can still hide on a "trusted" line (F-23 is only partly fixed)
Line accounting treats three kinds of line outside the parsed rows as explained:
- any line touched by a field match;
- any line matching one of the binding's skip or anchor regexes;
- static template lines.

The LLM-written skip regexes are often prefix-only (`^Ref\. By\s*:.*$`, `^Referred by\s*:`, `^Consultant\s*:`), and lab-e's anchor `Sex/Age:` is unanchored. So a result written on such a line is accepted and dropped.

Each attack used 10 documents per applicable layout. The table shows how many of the applicable documents each system accepted while dropping the result:

| Attack | v2.1 accepted | v3 accepted | Applicable documents |
|---|---:|---:|---:|
| R1: result appended to the patient-ID line (a field line) | 50 | **40** (A, B, C, D) | 60 |
| R2: new line outside the table that matches a skip or anchor regex, e.g. `Ref. By : SODIUM 138 mmol/L` | 40 | **40** (A, B, C, E) | 40 |
| R3: the same inside the table region, via a skip regex (`skip_hides_row` only looks for known labels) | 30 | **30** (A, B, C) | 30 |
| R4: header field line duplicated with a result appended | 60 | **0** (header template) | 60 |
| **Total** | 180 | **110** | 190 |

- **Realism [INF]:** a deliberately smuggled result is unlikely. Free text on header lines is not. Examples: `Ref. By : Dr X - repeat Hb 9.8 g/dL advised`, or a remark added after a software update. Either way, the printed page carries a value the record lacks.
- **Proposed fix (v3.1):** a **binding-independent result sentinel** in the domain layer, beside the validators.
  - After extraction, scan all document text **not consumed by a parsed result row**.
  - Reject if it contains a result-like token: a decimal next to a unit spelling from the dictionary, plus a short list of common clinical units (mmol/L, mEq/L, ng/mL, µmol/L, …), or a known test label from the dictionary.
  - The LLM never writes it, so permissive skip regexes can't weaken it.
  - Reference-range columns are part of row matches, so they are already consumed.
  - The risk is false rejects on header text that happens to look like a value with a unit. That has to be measured on the valid sets, and any hit explained.
- **Second fix:** a gate check (an extension of G6) that inserts a result-like line through each skip regex and requires rejection. That turns R2 and R3 into an executable activation condition.

### RV-2 MEDIUM: `registry approve` trusts the gate-report file
`R5`: a hand-written gate report with `"passed": true` for an obviously unsafe binding (skip everything inside the table) was **accepted by `approve`**. That binding happened to fail at runtime (`skip_hides_row`), but the approval control was bypassed.

**Fix:** `approve` re-runs gate v2 itself from the binding and its declared sample set, and records the gate-input hash. A gate report on disk is only ever informational.

### RV-3 MEDIUM-LOW: revoking the newest version silently re-activates an older one
`R6`: after v3 and v4 of lab-a were approved, revoking v4 left **v3 active automatically**. If v4 was revoked because the layout itself changed, silently falling back to v3 is wrong.

**Fix:** a revocation deactivates the binding id until a person explicitly re-activates a chosen version.

### RV-4 MEDIUM: a processing exception leaves no trace
`R7`: if processing throws (simulated here with a broken registry chain):
- the job **is** persisted;
- but there is **no review-queue entry, no `out` entry and no event-log line**, only an unhandled exception in asyncio.

The same is true of v2.1. A job that silently goes nowhere is the kind of gap reviewers worry about.

**Fix:** wrap processing. On any exception, write `review_queue/<job>.result.json` with status `PROCESSING_ERROR` and log `job_processing_error` with the exception class only.

### Code-review notes (lower severity)
| # | Note | Action |
|---|---|---|
| CR-1 | **The compiled template and the gate share data.** `compile` derives the header and template lines from gen + dev accept documents, and gate G4 then measures clean acceptance on the same dev documents. For the compiled parts, G4 is in-sample. The out-of-sample evidence is the unchanged held-out benchmark (identical) and the PBT | Disclose in 04 (done). Stage 3: split approved samples into derive and check sets |
| CR-2 | Header patterns re-use LLM skip regexes, some prefix-only (`^Name\s*:`). The position constraint limits the damage (R4 rejected), but those header lines accept arbitrary tails | Covered by the RV-1 sentinel |
| CR-3 | `sent_unconfirmed` is the safe choice. But a printer that normally closes with RST would make **every** job need an operator. Unknown until tested on real printers | Physical-printer test (Stage 4) |
| CR-4 | Duplicate detection is still in memory (F-14) | Stage 4 |
| CR-5 | Capture tests rely on `sleep`, so they could be flaky on a slow or loaded machine | Replace with event or polling waits when touched next |
| CR-6 | `rulegen` v3 path not exercised (0 LLM calls) | Exercise once in Stage 3 if a new layout is added |
| CR-7 | The registry is tamper-evident, not tamper-proof (the whole chain can be rewritten) | Production item: anchor the chain head in git or an external log |

## What I recommend before Stage 3 (about 2–3 h, as v3.1)
1. RV-1 result sentinel plus the G6 skip-line probe. Re-run the suite, the PBT (the same two pre-registered seeds plus one new one, fixed before the run), the benchmark and these red-team probes. Report the false-reject change honestly.
2. RV-2: `approve` re-runs the gate.
3. RV-3: no silent fallback on revocation.
4. RV-4: processing errors go to the review queue.

v3.0 stays frozen as evidence. v3.1 gets its own manifest and log entries.

## How you can review v3 yourself (about 30 min)
1. `spoolgeist_h/interpreter.py`: the "v3 structure checks" section (`page1_ok`, `check_pages`, `account_lines`, `process`), about 120 lines.
2. `bindings_h/lab-a.v3.json`, the `compiled` block, which is what the compiler derived, and `bindings_h/gate_reports/lab-a.v3.gate.json`.
3. `spoolgeist_h/gate.py`: are the nine conditions the right ones? Is anything missing?
4. `spoolgeist_h/capture.py` `forward_job`: do you agree with "never auto-resend once bytes were written"?
5. Run the red team yourself:
   ```bash
   .venv/bin/python -m phase2.stage2.redteam_v3
   ```
