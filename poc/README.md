# Spoolgeist — isolated technical proof of concept

**This is an engineering experiment, not the product.** It tests one hypothesis. An AI-generated parser can reliably turn unfamiliar legacy report layouts into structured data while rejecting uncertain or incorrect outputs, provided it is subjected to independent validation and fail-closed execution. **All data is synthetic.** Nothing here touches any other project.

Read in this order:
1. [DECISION.md](DECISION.md): answers to the 10 questions and the recommendation.
2. [TEST_RESULTS.md](TEST_RESULTS.md): every number, with how it was produced.
3. [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md): what is weak, untested or unproven.
4. [ARCHITECTURE.md](ARCHITECTURE.md): how it works.

## Layout
```
spoolgeist/            the system under test
  capture.py           RAW/9100 listener: store-and-forward, retry, duplicate flag, quarantine
  grid.py              print bytes -> normalised text (ESC/P stripped; PostScript/PDF/raster refused)
  binding_schema.json  JSON Schema of an AI-written rule ("Binding")
  rulegen.py           LLM rule generation + activation gate + <=3 repair rounds
  interpreter.py       deterministic execution of a Binding (no LLM)
  validators.py        independent checks V1-V8 (no knowledge of the Binding)
  lab_dictionary.json  human-curated domain pack: 20 tests, LOINC, UCUM, unit spellings, plausibility
  fhir_builder.py      generic R4 + ABDM-profiled document Bundles
  llm.py               the ONLY LLM entry point (headless Claude CLI, tools off, empty cwd, pre-send guard)
bench/                 synthetic corpus generator, scoring, benchmark, baseline
tests/                 Hypothesis property test: "abstain or exactly correct"
experiments/           print-capture experiments (automated + CUPS + Windows runbook), FHIR validator wrapper
bindings/              the 6 AI-generated rules (status active, SHA-256 pinned)
data/corpus/           generated synthetic documents (gen / dev / test splits)
runtime/               all raw results, logs, freeze manifests, FHIR bundles, validator output
.kiro/                 spec, steering, hooks (authored for Kiro; NOT yet run inside Kiro, see KNOWN_LIMITATIONS)
```

## Reproduce (macOS, from `poc/`)
Prerequisites: Python 3.9+, the `claude` CLI (only for rule generation and the baseline), and internet access for the one-time downloads.

1. Create the environment:
   ```bash
   python3 -m venv .venv && .venv/bin/pip install regex jsonschema hypothesis pytest
   ```
2. Generate the synthetic corpus (deterministic seeds):
   ```bash
   .venv/bin/python -m bench.generator
   ```
3. AI rule generation. This step needs the LLM. The committed `bindings/` can be reused instead.
   ```bash
   .venv/bin/python -m bench.run_rulegen A B C
   ```
   ```bash
   .venv/bin/python -m bench.run_rulegen D E F --against A B C D E F
   ```
4. Freeze, then run the held-out benchmark. LLM calls are forbidden during this run.
   ```bash
   .venv/bin/python -m bench.run_benchmark --freeze
   ```
   ```bash
   .venv/bin/python -m bench.run_benchmark --split test --tag test_repro
   ```
5. Property-based test (3,000 cases; a fresh seed is optional):
   ```bash
   PBT_SEED=424242 PBT_N=5000 PBT_TAG=_repro .venv/bin/python -m pytest -q tests
   ```
6. Direct-LLM baseline (about 128 LLM calls, about US$3):
   ```bash
   .venv/bin/python -m bench.baseline --per-layout-clean 5
   ```
7. FHIR. First download a portable Java runtime and the HL7 validator into `.tools/`:
   ```bash
   mkdir -p .tools/jre && curl -sSL "https://api.adoptium.net/v3/binary/latest/21/ga/mac/aarch64/jre/hotspot/normal/eclipse" | tar -xz -C .tools/jre --strip-components=1
   ```
   ```bash
   curl -sSL -o .tools/validator_cli.jar https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar
   ```
   Then build the bundles and validate them as generic R4 and against the ABDM profiles:
   ```bash
   .venv/bin/python -m bench.run_fhir
   ```
   ```bash
   experiments/fhir/validate.sh generic all_generic runtime/fhir/generic/*.json
   ```
   ```bash
   experiments/fhir/validate.sh abdm all_abdm runtime/fhir/abdm/*.json
   ```
8. Print capture. The automated experiments E1–E9 come first:
   ```bash
   .venv/bin/python -m experiments.print_capture.run_experiments
   ```
   The real CUPS spooler test adds a TEMPORARY macOS print queue and removes it on exit:
   ```bash
   experiments/print_capture/cups_experiment.sh
   ```
   The Windows VM test is in `experiments/print_capture/WINDOWS_VM_RUNBOOK.md`; it has not been run.

`.venv/`, `.tools/` (about 820 MB: JRE, validator, FHIR package cache) and `runtime/` are git-ignored. Java's `user.home` is redirected into `.tools/` so nothing is written outside `poc/`.

## How this PoC was built (honest note on tooling)
The PoC was implemented by **Claude Code (an AI coding agent), not Kiro**, because Kiro isn't installed on this machine. The `.kiro/` spec, steering and hooks were written so the team can continue in Kiro, but they haven't been loaded or run in Kiro. Hackathon judges score Kiro usage, so this matters. See KNOWN_LIMITATIONS §7 and DECISION.md.
