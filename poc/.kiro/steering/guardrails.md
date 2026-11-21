---
inclusion: always
---
# Spoolgeist PoC guardrails (apply to every agent action in this folder)

1. **Synthetic data only.** Every document must contain the line `SYNTHETIC SAMPLE - NOT A REAL PATIENT`.
   Never add, read or paste real patient data. `spoolgeist/llm.py` enforces this with a pre-send guard; do not weaken it.
2. **No LLM at runtime.** `spoolgeist/interpreter.py`, `validators.py`, `grid.py`, `capture.py` and `fhir_builder.py`
   must never call `spoolgeist/llm.py`. The LLM is used only to *write* bindings (and for the baseline experiment).
3. **Fail closed.** When unsure, reject with an explicit reason. Never fill a missing patient identifier, unit, date or result.
4. **Never weaken the test set to pass a gate.** Do not edit `data/corpus/test/**` or `bench/score.py` to improve metrics.
   Any change to frozen files (`bench/run_benchmark.py: FROZEN`) requires a new freeze manifest and a note in TEST_RESULTS.md.
5. **The LLM never validates its own output.** Activation depends only on deterministic checks in `rulegen.evaluate`.
6. Claims: generic FHIR R4 validation and ABDM *profile* validation only. No sandbox, certification or compliance claims.
