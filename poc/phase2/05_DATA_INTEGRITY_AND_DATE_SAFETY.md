# 05: Data integrity and date safety (v4)

**Date:** 22 Nov 2026.

**Principle:** every interpretation choice that cannot be checked from a single document is made **once, at onboarding**. It is shown to a person, recorded in the binding or queue configuration, and enforced **fail-closed** on every later document. Nothing is guessed per document.

## 1. Validation layers
Each layer is separate code with separate reasons, so a reviewer can see *which* layer refused a document.

| Layer | What it establishes | Where (v4) | Example reject reasons |
|---|---|---|---|
| 1 Syntactic | bytes are text in the **declared** code page; values are plain decimals; dates parse with the approved format | `grid.normalize` (strict decoding), `interpreter._field` / `_table` | `decode_error`, `invalid_value`, `invalid_type`, `pattern_mismatch` |
| 2 Structural | the document is the approved layout: page-1 header template, continuation headers, table start and end, every row parsed, every other line accounted for (static, approved note, or a trusted line matching its approved text skeleton), numbers outside rows only in approved digit skeletons | `interpreter` structure checks | `unknown_layout`, `page_header_mismatch`, `unparsed_content`, `unaccounted_line`, `unapproved_line_shape`, `unapproved_numeric_text`, `rows_outside_table`, `note_hides_row` |
| 3 Unit and code | each label maps to an approved code; each printed unit is an accepted spelling for that code; flags map through the binding | `_table`, `dictionary` | `unknown_label`, `unit_not_accepted`, `missing_unit`, `unknown_flag` |
| 4 Domain consistency | **definitional** relationships hold within printed precision (report 03 §2.1); no duplicate tests; reference range not inverted; flag agrees with the printed range | `validators` V5 (duplicates), V6, V7, **V9** | `V9 MCHC inconsistent…`, `V9 direct bilirubin exceeds total`, `V6 flag H but…` |
| 5 Plausibility | values within broad physiological limits (dictionary `plausible`); age 0–120; dates in a window; identity sanity; one writing system per name | `validators` V2, V3, V4, V5, V8 | `V5 implausible…`, `V2 … mixes writing systems` |

**Plausible ≠ correct.** Layer 5 bounds are wide (for example Hb 2–25 g/dL). Passing layer 5 says nothing about diagnosis. No layer interprets results clinically, and flags are transcribed, never computed.

## 2. Dates: fail-closed day/month order
**Risk:** "04/05/2026" means 4 May (DD/MM) or 5 April (MM/DD). No validator can tell from one document when both parts are ≤ 12.

**v4 policy:**
1. **Format is fixed per binding:** the strptime format, e.g. `%d/%m/%Y %H:%M`, is part of the approved binding. It never changes per document.
2. **Compiler check:**
   - For every date field whose format contains both `%d` and `%m`, the compiler parses every approved sample's printed date with the *swapped* format.
   - If at least one sample fails under the swapped format (day > 12), the order is **proven by the samples**.
   - Otherwise `samples_disambiguate = false`.
3. **Gate and approval:** `date_format_confirmation_required` blocks approval unless the approver passes `--confirm-date-format`, after checking the order against a known real date. Tested: `test_G8_ambiguous_dates_require_confirmation`.
4. **Runtime:** a date that does not parse with the approved format is rejected (`invalid_type`). It is never re-tried with another format.
5. **Precision:** a date-only format yields a date-only FHIR `effectiveDateTime`. No time is invented (F-03). A time is emitted only if printed.
6. **Window and order:** collected must be after 2000-01-01 and no later than tomorrow; reported must be ≥ collected and ≤ collected + 30 days (V4).

**Residual:** if an approver confirms the wrong order for samples that are all ambiguous, every document will be wrong in the same way. The confirmation step makes this a recorded human decision. It does not make it impossible.

## 3. Other interpretation choices

| Choice | Onboarding decision | Runtime enforcement | Residual |
|---|---|---|---|
| **Code page** | declared per print queue (`Pipeline.process_bytes(raw, codepage)`); a non-ASCII sample name in the approved set must round-trip to the operator's truth (gate G3) | strict decoding; no fallback guess (the v2.1 cp437 guess is removed); one writing system per name (V2) | a wrong declaration that maps letters to letters of the *same* script would pass. The tests cover cp1252↔cp437 for accented Latin names (`test_wrong_code_page_never_accepted_with_wrong_name`) |
| **Decimal separator** | dot (all six layouts) | values must match `^[0-9]{1,7}(\.[0-9]{1,4})?$`; "9,8" → reject (`comma_decimal`, 0 unsafe in dev) | a comma-decimal lab would need a binding-level declaration (not implemented) |
| **Units** | each label maps to a code; only dictionary spellings accepted; conversion factors are exact and human-curated | unknown spelling → reject; unit must be printed (never assumed) | the dictionary's mapping must be right; LOINC and specimen suitability need human confirmation (KNOWN_LIMITATIONS §5) |
| **Reference ranges** | taken only from the document | V7 inversion check; V6 flag check; FHIR `referenceRange.text` keeps the printed text | ranges are not validated clinically |
| **Flags** | binding maps printed markers (H, L, `*`, `!`) or, if the compiler proves it on samples, bold emphasis (`abnormal_marker = "bold"`) | unknown marker → reject; V6 checks direction against the printed range when both are printed | presence-only flags (`*`, `!`, bold) carry no direction |
| **Patient identifier** | regex plus `pattern` per binding; repeated identical values allowed, conflicting values rejected | V3 sanity (charset, length, must contain a digit) | an identifier typed wrongly in the legacy system is transcribed faithfully. This is not detectable, and not our error |
| **Timezone** | site configuration (`SITE_TZ = +05:30`) | applied only when a time is printed | documents never carry a timezone; a wrong site setting would shift every time |
| **Notes** | note markers learned from operator-verified truth notes | preserved verbatim; rejected if they contain a number, a known test label or a qualitative-result word | qualitative results phrased without the vocabulary can pass inside a note (measured by held-out set v3) |
| **Optional fields** | promoted to required if present in every approved sample **or** in every approved sample's truth (F-06, Stage-3 fix) | a missing required field → reject | a field genuinely optional in the layout stays optional |

## 4. Integrity of the evidence chain
- **Bytes:** raw print bytes are persisted with their SHA-256 before anything else, and fsync'd.
- **Rules:**
  - Every binding is reproducibly compiled from a stored LLM output plus referenced samples (path and SHA-256).
  - Approval re-compiles and re-runs the gate.
  - The registry is hash-chained.
  - Changing an approved sample makes approval refuse until the old approval is revoked and the binding recompiled. This happened in Stage 3 (EXPERIMENT_LOG 63–64).
- **Output:** FHIR `presentedForm` carries the normalised text with both hashes, and `conclusion` carries notes verbatim.
- **Not provided:** the registry is tamper-evident, not tamper-proof (the whole chain can be rewritten), and there is no encryption at rest. See report 07.
