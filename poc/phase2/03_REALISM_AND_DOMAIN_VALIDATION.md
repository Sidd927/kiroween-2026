# 03: Realism and domain validation (Stage 3)

**Date:** 22 Nov 2026.

**Scope:** the bench2 synthetic generator (`bench2/generator.py`) and the v4 domain-consistency validator (`spoolgeist_h/validators.py`, V9).

**Not clinical validation:** nothing here is clinical validation. Every value is synthetic, and reference intervals are laboratory-specific in reality.

## 1. Why this was needed
The v1 generator drew every analyte independently and uniformly around its range. As a result:
- CBC indices contradicted Hb, Hct and RBC;
- differentials could exceed 100%;
- direct bilirubin could exceed total.

The direct-LLM baseline refused 29 of 58 valid v1 documents largely *because* it noticed this, while our validators did not (PoC DECISION.md §7).

That unrealism had two consequences:
1. It made the system look better than a careful reader. The system accepted documents a human would question.
2. It prevented us from using definitional relationships as a safety check, because the test data itself violated them.

## 2. Relationships used, and how strongly they are claimed

### 2.1 Definitional identities: used both to generate data and as validator V9
These follow from how the quantities are defined or calculated. A printed report that violates them, beyond rounding, contains a transcription, alignment or printing error.

| Relationship | Source | How V9 checks it |
|---|---|---|
| MCV = Hct ÷ RBC (× 10 with Hct in % and RBC in 10⁶/µL) | StatPearls, *Normal and Abnormal Complete Blood Count With Differential* (NCBI Bookshelf NBK604207): MCV "calculated by dividing Hct by RBC"; also "Hct = RBC × MCV/10" | interval arithmetic on printed precision |
| MCH = Hb ÷ RBC (× 10 with Hb in g/dL) | same source: "calculated by dividing hemoglobin by red cell count" | same |
| MCHC = Hb ÷ Hct (× 100) | same source: "calculated by dividing the hemoglobin by the hematocrit" | same |
| Total bilirubin = direct + indirect, therefore direct ≤ total | Mayo Clinic, *Bilirubin test*: "indirect bilirubin levels equal total bilirubin minus direct bilirubin". The inequality is an inference from that definition | lower bound of DBIL > upper bound of TBIL → reject |
| Globulin = total protein − albumin, therefore albumin < total protein | PMC7467286 (an A/G ratio study) computes globulin as total protein − albumin. The inequality is an inference from that definition | lower bound of ALB ≥ upper bound of TP → reject |
| Differential percentages are fractions of the total WBC, therefore NEUT% + LYMPH% ≤ 100 | NBK604207: the differential "may be reported as a percentage of the total WBC". The bound is an inference | sum of lower bounds > 100 → reject |

**Rounding-safe by construction:**
- Each printed value v with d decimals stands for the interval [v − 0.5·10⁻ᵈ, v + 0.5·10⁻ᵈ], converted exactly to canonical units.
- The derived interval is computed (for positive quantities a/b: [a_lo/b_hi, a_hi/b_lo]).
- A document is rejected only if the printed index interval does **not** overlap the derived interval.
- Correct rounding can therefore never trigger V9. `test_V9_consistent_cbc_passes_including_rounding` is the explicit check.

**Assumption:** labs compute MCH, MCHC and MCV (or Hct) from the same measurements they print. An analyzer that reports indices computed from unrounded internal values still satisfies the interval check. One that prints indices from a *different* measurement run would not. The latter would be rejected (false reject, never unsafe).

### 2.2 Approximate clinical relationships: generator only, NOT validated
These shape realistic synthetic data but are **not** used to reject documents, because real patients can violate them:
- Typical adult distributions, centred inside the printed reference intervals, with abnormal subpopulations: anaemia (20%, of which 60% microcytic), leucocytosis (≈15%), thrombocytopenia (10%), raised bilirubin, transaminases, ALP, glucose, creatinine and urea (10–20% each).
- Direct-bilirubin fraction: 0–35% when total < 1.2 mg/dL, up to 60% when raised.
- Albumin ≈ 50–68% of total protein (albumin "more than 50% of total serum proteins", MDApp *A/G ratio*; ≈60% per e3learn).
- **MCHC kept within 26–37 g/dL** (spec amendment 1). Severe iron deficiency can push MCHC down to the mid-20s; values below 20 do not occur in practice.

### 2.3 Printed reference ranges and flags
- **Ranges:** Hb, Hct and RBC ranges are printed **sex-specifically**. The adult values follow the ranges in NBK604207, adjusted to common Indian lab formats (men: Hb 13.0–17.0, Hct 40–50, RBC 4.50–5.90; women: Hb 12.0–15.5, Hct 36–46, RBC 4.00–5.20). NBK604207 itself gives Hb 13–18 / 12–16, Hct 40–54 / 36–48 and RBC 4.6–6.2 / 4.2–5.4, and notes that intervals are laboratory-specific.
- **Flags** are computed against the **printed** range, which is what a legacy LIS does. They are not computed against a "true" clinical range.
- The v4 system never derives a flag from a range. It only transcribes the printed marker: an H or L letter, `*`, `!`, or bold (layout B, F-04). It then checks that marker against the printed range (V6).

## 3. Realistic variations implemented (catalogue v2, spec 02 §4)

| Variation | Realistic because | System behaviour in v4 |
|---|---|---|
| Notes and interpretive remarks (per-layout styles) | real reports carry remarks | preserved verbatim in `record.notes` and in FHIR `DiagnosticReport.conclusion`; rejected if they contain a number, a test name or a qualitative-result word (policy) |
| Section subheadings inside the table | mixed panels | learned as exact static lines from approved samples |
| Referrer names of 1–4 tokens, "SELF" | free-text header field | text-skeleton variable slot |
| Footer software-version drift | upgrades | the numeric skeleton `LabSys #.#` |
| Long names running into the next label | fixed-width overflow | supported after the LLM repair round (B, D, E, F) |
| Wrapped names | some apps wrap | policy refusal |
| Accented names in cp1252 | real names | declared queue code page; strict decoding; script-consistency check |
| Bold-only abnormal markers | layout B | emphasis preserved through normalisation |
| Low direct bilirubin (0.00–0.02) | below detection | accepted (V7's zero rule only rejects 0 when the printed low limit is > 0) |

**What remains unrealistic** (stated in report 04, part 2):
- one generator family;
- fixed layouts designed by the system's author;
- no OCR noise (not applicable to print capture);
- no operator typing errors in variable fields;
- no real legacy software.

## 4. Generator-to-truth independence
- **Structured truth:** ground truth comes from the structured `Report`, including flags, printed ranges, sex, age, reported date, time precision and notes. It never comes from rendered text.
- **No shared code:** the evaluator `bench2/evaluate.py` scores three tiers from that truth. The system never imports `bench`, `bench2`, `tests` or `phase2`. AST-checked by `tests_h/test_v4.py::test_system_never_imports_benchmark_code`; the gate now carries its own truth comparison.

## Sources
- StatPearls, *Normal and Abnormal Complete Blood Count With Differential*, NCBI Bookshelf NBK604207: https://www.ncbi.nlm.nih.gov/sites/books/NBK604207/
- Mayo Clinic, *Bilirubin test*: https://www.mayoclinic.org/tests-procedures/bilirubin/about/pac-20393041
- *Predictive value of serum albumin-to-globulin ratio for incident chronic kidney disease*, PMC7467286: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7467286/
- MDApp, *Albumin Globulin Ratio Calculator*: https://www.mdapp.co/albumin-globulin-ratio-calculator-463/
- MDApp, *Red Blood Cell (RBC) Indices Calculator* (unit factors): https://www.mdapp.co/red-blood-cell-rbc-indices-calculator-328/
- e3learn, *Total Protein*: https://e3learn.com/education/medical/lab-values/total-protein
