# 02: Benchmark design v2 (specification, written BEFORE the generator or any system change)

**Date:** 21 Nov 2026.

**Status:** this specification. Changes after this point are allowed only as dated amendments in §9.

This document replaces nothing. The v1 benchmark (`bench/`, `data/corpus/`) stays as historical evidence.

## 1. Purpose and the property under test
The property is unchanged since the PoC and is never weakened:
1. A document with a **detectable defect** must be REJECTED.
2. An ACCEPTED document must have every **tier-1 and tier-2** field exactly equal to ground truth.

Tier-3 fields are scored and reported, but a tier-3 error is reported as a *context error*, not a silent error. That rule is part of this specification so it cannot be moved later.

| Tier | Fields | Error name |
|---|---|---|
| 1 Identity and date | patient_id, patient_name, collected date (and time, if printed) | silent error |
| 2 Results | the set of (code, value, unit); no missing and no extra results | silent error |
| 3 Clinical context | sex, age, reported date, abnormal flag per result, printed reference range per result, date precision, preserved notes | context error |

## 2. Independence measures (and their limits)
The same AI agent writes the generator, the system and this benchmark. Full independence is impossible. These measures reduce, but do not remove, shared assumptions:

1. **Separate packages.**
   - Generator: `bench2/generator.py`, rendering plus ground truth from structured data, never from text.
   - Evaluator: `bench2/evaluate.py`, which sees only system outputs through an adapter.
   - The system (`spoolgeist_h/`) must never import `bench2/`. A test enforces this.
2. **Specification first.** This catalogue (§4), with expected labels and rationales, is fixed before the generator exists.
3. **Pre-registered test split.**
   - The test seed is drawn from `secrets`, and only its SHA-256 goes in the log before the first test run.
   - The seed is stored in `phase2/stage3/sealed/` and is not used during development.
   - The generator and catalogue files are hashed into the log before the test run.
   - Any system change after the first test run requires a new version **and** a new seed.
4. **Dev and test separation.** Development, compilation, gate and debugging use only the gen and dev splits.
5. **Held-out evasion set v3** (hidden results, including qualitative). Written and hash-registered before the v4 code; first run after the freeze.
6. **Metamorphic tests and mutation testing (§6).** These check the system's behaviour without needing new labelled data, and check whether the tests themselves have power.

**Stated limit:** every document is still synthetic, produced by one generator family whose layouts and variations the system's author designed. Results say nothing about real lab reports. Only real documents or an independent tester can address that.

## 3. Splits

| Split | Per layout (A–F) | Used for |
|---|---|---|
| gen | 2 clean, at least one with day > 12 | LLM rule generation, only if a binding is regenerated |
| dev | 12 clean + 2 per valid class + 1 per policy class + 1 per defect class | compiler (approved samples = dev "accept" docs), gate v2 regression set, development |
| test | 25 clean + 4 per valid class + 3 per policy class + 3 per defect class | **evaluation only**, sealed seed |
| foreign | 15 docs of unregistered layout G plus 15 "drifted" documents (new format version) | must be rejected |

## 4. Perturbation catalogue v2
Every class has a group and an expected outcome:
- **VALID:** expected ACCEPT. A rejection counts as a false reject.
- **POLICY:** the system *deliberately* refuses these by documented policy. A rejection is a "policy refusal", reported separately and never mixed into false rejects or into safety numbers. An acceptance is an error only if the extracted data is wrong.
- **DEFECT:** expected REJECT. An acceptance is an unsafe accept, or a silent error if the data is also wrong.

### 4.1 VALID (plausible conditions a correct system should handle)
| Class | What it models | Rationale |
|---|---|---|
| `clean` | normal report | baseline |
| `col_shift` | ±1–2 spaces in result rows | operators and printers vary spacing |
| `crlf_trailing` | CRLF and trailing spaces | Windows text drivers |
| `drop_optional` | an optional test not ordered | panels vary per order |
| `page_break` | table continues on the next page with repeated headers | long panels (A, B, D, F) |
| `long_name_overflow` | patient name longer than its printed column, pushing the text right | common in fixed-width legacy output |
| `referrer_variation` | referring-doctor names of 1–4 tokens, "SELF" | free-text field on headers |
| `approved_note` | a free-text note line, without numbers, in that layout's note style, inside or after the table | real reports carry remarks; must be preserved, not dropped |
| `interpretive_note` | multi-sentence interpretation after the table, without numbers | real reports; must be preserved |
| `section_subheading` | a static subheading inside the table (e.g. "DIFFERENTIAL COUNT") | mixed panels |
| `footer_version_drift` | software version in the footer changes (e.g. "LabSys 3.1" → "3.2") | upgrades that do not change the layout |
| `sex_specific_ranges` | printed reference ranges differ by sex (Hb, Hct, RBC) | real labs; flags must follow the printed range |
| `abnormal_values` | physiologically consistent abnormal results (anaemia, leucocytosis, raised bilirubin) | flags and tier 3 |
| `accented_name` | names with non-ASCII letters, printed in the queue's declared code page (layout C, cp1252) | real names; tests code-page handling |
| `bold_flag` (layout B) | abnormal values marked only by bold | already in the layout; flags now scored |
| `low_direct_bilirubin` | direct bilirubin printed as 0.0x, including 0.00 | a real low value; zero handling |

### 4.2 POLICY (deliberate refusals, reported separately)
| Class | Policy | Rationale |
|---|---|---|
| `note_with_number` | a note containing any number ("repeat after 2 days") is refused | a number outside parsed rows could be a result; a human decides |
| `unapproved_note_style` | free text in a style never seen in approved samples is refused | unexplained content |
| `static_text_damage` | a character changed in a static header or footer line is refused | software prints static text deterministically; damage means capture corruption |
| `multipage_unapproved` (C, E) | multi-page documents without an approved multi-page sample are refused | no evidence the continuation format is understood |
| `long_name_wrapped` | name wrapped onto a second line is refused unless the binding supports it | an ambiguous identity split |

### 4.3 DEFECT (must be rejected)
**Carried from v1 (13 classes):**
`unit_incompatible`, `unit_missing`, `value_corrupt`, `value_implausible`, `patient_id_missing`, `date_invalid`, `duplicate_conflict`, `unknown_test`, `truncated`, `layout_drift`, `header_changed`, `flag_inconsistent`, `conflicting_patient_id`.

**Carried from the Stage-2 adversarial suite:**
`header_changed_paged`, `extra_section_unknown_tests`, `two_patients_one_job`, `page_order_swap`, `text_between_rows_with_number`.

**New:**
| Class | What it models | Why it must be rejected |
|---|---|---|
| `row_value_swap` | values of two adjacent results swapped (e.g. MCV and MCH), units unchanged | column or row misalignment; plausibility alone may pass it, domain-consistency rules must not |
| `index_inconsistent` | one derived red-cell index printed inconsistently with Hb, Hct and RBC beyond rounding | a mis-transcription or misalignment signal |
| `bilirubin_inverted` | direct > total bilirubin | impossible by definition |
| `protein_inverted` | albumin ≥ total protein | impossible by definition |
| `differential_over_100` | NEUT% + LYMPH% > 100 | impossible by definition |
| `hidden_numeric_result` | a numeric result on a header, referrer or note line | silent drop (RV-1) |
| `hidden_qualitative_result` | "HIV reactive", "HBsAg POSITIVE", … on a header, referrer or note line | silent drop (RV-1, the remaining gap) |
| `wrong_code_page` | a cp1252 document arriving on a cp437-declared queue (accented name) | identity corruption (F-11) |
| `comma_decimal` | "9,8" printed for 9.8 in a dot-decimal layout | locale ambiguity |

## 5. Metrics (all as raw counts with denominators)
Reported separately for:
- known layouts A–C and "unseen-at-PoC" layouts D–F;
- the foreign or unsupported group;
- each VALID, POLICY and DEFECT class;
- the adversarial combinations (PBT).

**Valid documents:**
- correct accepts;
- false rejects;
- silent errors (tier 1 or 2 wrong);
- context errors (tier 3 wrong);
- patient-identity accuracy, date accuracy and result-row completeness on accepted documents.

**Defect documents:**
- unsafe accepts, and among them how many have wrong tier-1 or tier-2 data;
- defect-specific rejection rate.

**Policy documents:** refusal count, plus accepts with wrong data.

**Other:**
- layout recognition: recognised binding equals the expected binding, or none for foreign documents;
- latency median and p95;
- AI calls per new layout and per subsequent document;
- rule-activation rate and generation cost (if any regeneration happens);
- FHIR validator results on all accepted test documents.

**Confidence intervals:** one-sided 95% Clopper-Pearson upper bounds where k = 0, and Wilson intervals otherwise.

**No single combined "accuracy" number is reported.**

## 6. Method tests
**Metamorphic relations** (Hypothesis, on valid documents). If the system accepts both the source and the transformed document, the stated relation must hold. If it accepts one and rejects the other, the case is recorded as an instability:
1. Rename the patient consistently: only patient_name changes.
2. CRLF and trailing spaces: identical record.
3. Move the page break to another row: identical record.
4. Scale every value by one unit-preserving reprint (same values, different column spacing): identical record.
5. Add an approved note: identical record plus that note.
6. Change the referring doctor's name: identical record.

**Mutation testing** (custom AST mutator; no external tool):
- **Targets:** `validators.py`, `sentinel.py` and the structure checks in `interpreter.py`.
- **Operators:** comparison flip, boolean negation, `return`/`raise` removal, constant change.
- **Measure:** a mutant is *killed* if `tests_h` or the v2 dev evaluation produces any different classification.
- **Report:** the kill rate, and every surviving mutant with an explanation (equivalent, or a test gap).

**Property test:** the PoC PBT, unchanged, plus a v2 PBT drawing combinations from catalogue v2.

## 7. Decision rules fixed in advance
- The test split is run once per frozen version. Results are reported whatever they are.
- If any DEFECT class has an unsafe accept with **wrong** tier-1 or tier-2 data, the result is called a **safety failure**, not a limitation.
- A VALID class with more than 50% false rejects is reported as **unsupported**, not hidden in an average.

## 8. Out of scope (stated, not hidden)
- Real documents.
- Clinical validation of reference ranges.
- OCR or scanned input.
- Non-text print formats.
- Qualitative tests as *extracted* results: the dictionary is numeric-only. They are in scope only as "must not be silently dropped".

## 9. Amendments
All three were made before the test split was generated or sealed.

1. **(22 Nov) Generator realism: MCHC.** A severe-anaemia draw produced MCHC 19.2 g/dL, which is physiologically unrealistic and below the dictionary's plausibility floor of 20. Hb is now clamped so that MCHC stays within 26–37 g/dL. The gen and dev splits were regenerated and the bindings recompiled from them (EXPERIMENT_LOG 63).
2. **(22 Nov) `row_value_swap` is restricted to swaps that violate a definitional identity** (the generator swaps HCT and MCHC). Swaps between independent analytes with the same unit (e.g. ALT and AST) cannot be detected by any validation rule and are declared out of scope rather than counted as defects.
3. **(22 Nov) `wrong_code_page` direction:** the generator encodes the accented layout-C report in cp437 and delivers it on the cp1252-declared queue. The reverse direction is covered by `tests_h/test_v4.py`.
