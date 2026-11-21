# Spoolgeist: validation and research repository

> **What this repository is:** the research, technical proof-of-concept and validation history behind Spoolgeist.
> It is **not** the competition application. That will be built **in Kiro**, in a separate repository with `/.kiro` at its root (see `project-transition/05_FINAL_PROJECT_DECISION.md`).
> Everything here was produced with **Claude Code**, not Kiro. All data is **synthetic**.

## The idea in one paragraph
Legacy systems that can only *print* still hold critical data. Spoolgeist captures the print job, has an AI write a parsing rule for an unfamiliar layout **once**, and then forces that rule to **prove itself** before it runs:
- deterministic compilation;
- adversarial self-tests;
- a check that every line of the document is accounted for;
- definitional domain checks;
- a hash-chained approval.

After approval, every report is processed **offline, deterministically, with no AI**. Anything it cannot fully account for is refused and sent to a person instead of being silently half-extracted. Accepted lab reports become FHIR R4 bundles.

## Status: prototype, validated on synthetic data only
| Capability | Status |
|---|---|
| RAW/9100 print capture, store-and-forward, no automatic duplicate printing | **prototype**, tested against fake printers and once through macOS CUPS; **Windows and physical printers untested** |
| AI rule generation and repair (LLM writes a candidate) | **prototype** (6 layouts; 8 rule-generation calls in the PoC + 5 repair calls in Stage 3; ~128 further calls were spent on a direct-LLM baseline comparison) |
| Compiler, activation gate, approval registry | **prototype with tests**; every approval so far is an *agent* approval, **no human has reviewed a rule** |
| Deterministic extraction + validation (v4) | **validated on synthetic data** (see `project-transition/02_STAGE3_FINAL_TECHNICAL_ASSESSMENT.md`) |
| FHIR R4 / ABDM-profile output | **validated with the official HL7 validator**; no sandbox, no certification |
| Real lab reports, real legacy software, market demand | **unverified** |

## Layout
```
KIROWEEN_IDEA_RESEARCH/     idea research and due diligence (reports 01-15)
poc/                        the PoC and its hardened successors
  spoolgeist/ bindings/     v2.1 PoC (frozen)
  spoolgeist_h/ bindings_h/ v3.x -> v4 hardened engine, rule registry
  bench/ bench2/            synthetic generators (v1; v2 = consistent values, catalogue v2) and evaluators
  tests/ tests_h/           property, metamorphic, regression and capture tests
  phase2/                   Phase-2 audit, benchmark design, results, experiment log, frozen snapshots
project-transition/         current-state inventory, final technical assessment, market, decision
```

## Reproduce (macOS, from `poc/`)
Create the environment:
```bash
python3 -m venv .venv && .venv/bin/pip install regex jsonschema hypothesis pytest
```
Run the regression tests:
```bash
.venv/bin/python -m pytest -q tests_h/test_v4.py tests_h/test_registry_gate_precision.py tests_h/test_capture_v3.py
```
Run the metamorphic tests:
```bash
.venv/bin/python -m pytest -q tests_h/test_metamorphic_v4.py
```
Check that nothing changed since the freeze:
```bash
.venv/bin/python -m phase2.stage3.freeze_v4 --check
```
Run the sealed evaluation (needs the frozen test split):
```bash
.venv/bin/python -m phase2.stage3.sealed_eval --run
```
FHIR validation needs a JRE and `validator_cli.jar` in `poc/.tools/` (see `poc/README.md`).

## Security and privacy
- Synthetic data only.
- The LLM path refuses documents that are not marked synthetic.
- Spool files are 0600 and event logs carry no patient values.
- No encryption at rest and no authentication on the capture port yet.
- The listener binds to localhost by default.

## Licence
MIT (see `LICENSE`).
