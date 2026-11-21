# Architecture (PoC)

```
 legacy app ──print──▶ OS spooler (Windows RAW port / CUPS socket://)
                              │  TCP 9100 (RAW / AppSocket)
                              ▼
                    ┌─────────────────────┐   byte-identical, store-and-forward, retried
                    │ capture.py          │──────────────────────────────▶ printer (fake_printer in PoC)
                    │ persist bytes+meta  │
                    │ (SHA-256) FIRST     │── incomplete / oversize / idle ─▶ quarantine (not printed, not parsed)
                    └─────────┬───────────┘
                              ▼ complete jobs only; duplicates flagged
                    ┌─────────────────────┐
                    │ grid.py             │  ESC/P stripped, CRLF/FF/tabs normalised;
                    │                     │  PostScript / PDF / PCL / raster ─▶ REJECT (unsupported)
                    └─────────┬───────────┘
                              ▼
   bindings/*.json  ┌─────────────────────┐
   (SHA-256 pinned) │ interpreter.py      │  1 recognise: ALL anchors match; 0 or >1 layouts ─▶ REJECT
   ───────────────▶ │  NO LLM             │  2 fields: regex; missing / conflicting / bad type / pattern ─▶ REJECT
                    │                     │  3 table: start…end; every non-blank char covered by a row match
                    │                     │    (else REJECT); rows outside the table ─▶ REJECT (v2)
                    │                     │  4 rows: label∈map, strict decimal, unit∈dictionary, flag∈map
                    └─────────┬───────────┘
                              ▼
                    ┌─────────────────────┐  V1 required  V2 name sanity  V3 ID sanity  V4 date window/order
                    │ validators.py       │  V5 code/unit/plausibility/duplicates  V6 flag vs range
                    │ (binding-agnostic)  │  V7 range sanity / column-confusion guard  V8 age/sex
                    └───────┬───────┬─────┘
                     ACCEPT │       │ REJECT + reasons ─▶ review_queue/
                            ▼
                    ┌─────────────────────┐
                    │ fhir_builder.py     │  document Bundle: Composition, Patient, Organization,
                    │                     │  DiagnosticReport (+ original text in presentedForm), Observations
                    └─────────┬───────────┘
                              ▼
                 HL7 validator_cli: base R4 (generic)  |  ndhm.in#6.5.0 profiles (ABDM)
```

## Rule generation (offline, once per layout)
```
2 synthetic samples ─▶ llm.py (pre-send guard: synthetic marker required; tools off; empty cwd)
                     ─▶ candidate Binding (JSON)
                     ─▶ static_check: JSON Schema, regex compile, required groups (label/value/unit),
                        codes exist, anchors non-empty, permissive-skip guard
                     ─▶ gate on gen + dev (operator-verified regression set):
                        0 silent errors, 0 unsafe accepts, ≥90% clean acceptance, no collision with other layouts
                     ─▶ fail: repair prompt with concrete diagnostics (≤3 rounds)
                     ─▶ pass: SHA-256 pinned, status=active (human approval SIMULATED in the PoC)
```
The LLM never sees held-out test documents and never judges its own output.

## The Binding (what the AI writes)
Declarative JSON, validated against `spoolgeist/binding_schema.json`. It has no code and no expressions, only regexes run with a 0.5 s timeout:
- `layout.anchors`: static text that identifies the layout (all must match).
- `fields.{patient_id, patient_name, collected, …}`: regex with group `v`, plus type (string, integer, date, enum), strptime format, required flag and a validation `pattern`.
- `results`: `start`/`end` lines, `skip_lines`, a `row` regex with label/value/unit (and optional flag/ref groups), a `labels` → canonical code map, a `flags` map, and min/max rows.

Example: `bindings/lab-c.v1.json` (multi-line rows) and `bindings/lab-e.v1.json` (two results per line).

## Separation of duties
| Component | Written by | Trust |
|---|---|---|
| Binding (layout rule) | LLM | untrusted until gated; pinned by hash after |
| Interpreter, validators, dictionary, FHIR mapping | humans | trusted, frozen for evaluation |
| Ground truth | generator, from structured data (not from text) | independent of the parser |

## Evaluation protocol
1. Develop and tune only on dev layouts A–C (gen and dev splits).
2. **Freeze**: SHA-256 manifest of 11 system files (`runtime/freeze_manifest_v1.json`).
3. Generate rules for unseen layouts D–F after the freeze, then run the held-out test split with LLM calls forbidden.
4. Run the property-based stress test with combinations and fuzz operations not used in the benchmark.
5. Every post-freeze change is a new labelled version (v2, v2.1) with a new manifest and a re-run.
