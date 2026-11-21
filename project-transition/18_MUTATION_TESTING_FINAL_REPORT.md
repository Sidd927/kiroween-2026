# 18: Mutation testing, final report (v4, 22 Nov 2026)

**Per-mutant record:** every mutant has an ID, component, line, operator, the stage that killed it (or "survived-all"), a class and a reason. These are in `poc/phase2/stage3/results/mutation_v4_classified.json` (334 rows). Raw data: `mutation_v4.json`, `_recheck.json`, `_extended.json`, `_gapcheck.json`.

## Method
- **Tool:** a custom AST mutator (`poc/phase2/stage3/mutation_test.py`), with no external tool.
- **Targets:** `validators.py` (130 mutants), `sentinel.py` (7) and the structure and extraction functions of `interpreter.py` (197).
- **Operators:** comparison flip, `and`↔`or`, removal of `not`, `raise` → `pass`, integer constant +1.
- **Isolation:** each mutant ran in a temporary copy. The real files were never modified.

**Oracles, applied in sequence:**
1. **Dev-split outcome vector:** bench2 dev, 363 documents (status, results and identity per document).
2. **v4 regression tests:** `test_v4.py` and `test_registry_gate_precision.py`, as they stood before the gap tests.
3. **Extended oracle:** 1,745 *development* documents. These are every catalogue class at new seeds (base 5,000,000), the Stage-2 adversarial suite, and the red-team and evasion-v1 documents. **The sealed test split was not used.**
4. **Gap check:** the updated regression suite after the Stage-3 gap tests, run on the mutants those tests target.

## Results
| Stage | Killed | Cumulative |
|---|---:|---:|
| Dev-split oracle | 215 | 215 / 334 |
| Regression tests | 24 | 239 |
| Extended oracle | 5 | 244 |
| Gap tests | 8 | **252 / 334 (75.4%)** |

**Survivors: 82**, each classified by reading the code at the mutated line:

| Class | Count | Meaning |
|---|---:|---|
| REDUNDANT | 38 | the weakened check is backed by another layer that rejects the same documents; that layer is named per mutant (e.g. `missing_unit` → `unit_not_accepted` on the next line; `skip_hides_row` → text-skeleton and numeric checks on every skipped line; per-page header checks → table coverage and line accounting) |
| EQ-MSG | 24 | only rejection-reason text changes (slices, line numbers) |
| EQ-ROBUST | 19 | a constant or guard change that cannot change any decision for inputs the system accepts (e.g. the bold column offset, since `any()` over a bold span is shift-tolerant; V9 rounding half-width ±1 digit, since inconsistent documents are ≥ 10% off) |
| UNREACHABLE | 1 | `table_start_missing`: the page-1 header template already requires the column-header region |

## Genuine gaps found, and how each was closed
| Gap | Evidence | Fix |
|---|---|---|
| A qualitative word in a trusted line's **variable slot** was checked by code no test exercised | `classify_lines` raise at the qualitative check survived the dev oracle | `test_qualitative_result_inside_referrer_slot_rejected` (it was also killed by the extended oracle) |
| The bold → column mapping was not pinned | offset mutants survived (layout B bolds whole padded cells) | `test_bold_marks_exactly_the_value_characters` (bold value → flag A → refused by V6 when inside range; bold label → no flag) |
| V4 and V8 **boundaries** (age 0/120, collected 2000-01-01 and today+1, reported 0–30 days) were never exercised | 8 constant and bool mutants survived | `test_V8_age_bounds`, `test_V4_reported_window`, `test_V4_collected_window`; all 8 killed |
| Two-script names | the threshold mutant survived | `test_V2_two_script_name_rejected` |
| An unknown skeleton key, with the raise removed, would **crash** rather than reject | survived the dev oracle | covered by `test_G6_permissive_skip_is_neutralised_v4` (a crash fails it) |

## What the survivors mean (stated, not hidden)
- **Defence in depth makes 38 checks individually untestable.** Their removal changes no outcome on 2,108 development documents, so each layer's *independent* contribution is unmeasured. If a backing layer were removed later, these checks would become the last line of defence without having been tested alone.
- **Open risk, documented** (mutant on the note-continuation predicate, line 478): outside the table, a digit-free, label-free, vocabulary-free line right after a note could be absorbed into the note's text. It is preserved verbatim in the record and in FHIR `conclusion`, not dropped, but it is not flagged as unexplained.
- **The mutation score is not a safety score.** It measures whether our tests notice code changes, on synthetic documents.
