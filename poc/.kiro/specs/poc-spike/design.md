# Design: Spoolgeist PoC spike
See `../../../ARCHITECTURE.md` for the full design. Summary:

capture.py (RAW/9100, store-and-forward) -> grid.py (control codes stripped, refuse non-text)
-> interpreter.py (recognise by anchors -> fields -> table with full coverage -> v2 rows-outside-table check)
-> validators.py (dictionary + universal rules, independent of the binding) -> ACCEPT | REJECT
-> fhir_builder.py (generic + ABDM-profiled bundles) -> HL7 validator.

rulegen.py: LLM (synthetic samples only) -> Binding JSON -> static checks -> gate on regression set -> repair (<=3) -> pin SHA-256.

Correctness property for PBT: `tests/test_property_abstain_or_correct.py::test_abstain_or_exactly_correct`.
