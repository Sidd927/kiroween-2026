# 01: Current state and evidence inventory (22 Nov 2026)

Inspected directly from the repository, not from conversation summaries.

## Git
| Item | State |
|---|---|
| Remote | `origin` = `https://github.com/Sidd927/kiroween-2026.git` |
| `main` | `53668b7` "Initial commit" (LICENSE and a README stub). Identical to `origin/main`; never touched |
| Working branch | `poc/spoolgeist-validation`, HEAD `083bcc6` (research reports + v2.1 PoC). **Local only, never pushed** |
| Uncommitted | `poc/{spoolgeist_h, bindings_h, tests_h, bench2, phase2, data/corpus2, runtime_h}/`, a `poc/.gitignore` edit, a root `.DS_Store` |
| Root files | `LICENSE` (MIT), a `README.md` stub, `KIROWEEN_IDEA_RESEARCH/`, `poc/` |
| Kiro | `poc/.kiro/{specs,steering,hooks}` were written by Claude Code and **never loaded in Kiro**. Kiro is not installed on this machine. **The competition requires `/.kiro` at the repository root.** |

## System versions

| Version | Location | Status | Evidence |
|---|---|---|---|
| v2.1 (PoC) | `poc/spoolgeist/`, `poc/bindings/*.v1.json`, `poc/runtime/` | **Frozen, historical**. Manifest `runtime/freeze_manifest_v2.1.json`; committed in `083bcc6` | PoC TEST_RESULTS; reproduced bit-for-bit in Phase 2 Stage 1 |
| v3.0 | `phase2/stage2/snapshot_v3.0/` | **Frozen, superseded** (`freeze_manifest_v3.0.json`) | report 04 §1–9 |
| v3.1 | `phase2/stage2/snapshot_v3.1/` | **Frozen, superseded** (`freeze_manifest_v3.1.json`) | report 04 §10 |
| v3.2 | `phase2/stage2/snapshot_v3.2/` | **Frozen, superseded** (`freeze_manifest_v3.2.json`) | report 04 §11; held-out evasion set v2 |
| **v4** | `poc/spoolgeist_h/`, `poc/bindings_h/lab-*.v11.json` | **Being finished now (Stage 3).** Not yet frozen at the time of writing; frozen as described in report 02 | report 02 (this folder) |

## Rule (binding) versions
- **Active:** `lab-{a..f}` **v11**, compiled with `spoolgeist_h.compile/5` from the bench2 gen+dev samples.
- **LLM sources for v11:**
  - lab-a and lab-c: the PoC's v1 LLM output;
  - lab-d, lab-e and lab-f: one LLM repair round (long names);
  - lab-b: two repair rounds (long names, then age).
  - Stage-3 LLM spend: **5 calls, US$0.38**, logged in `runtime_h/llm_calls.jsonl`.
- **Superseded:** v3 to v10 (never deleted). v6 was compiled but never approved (note-continuation bug).
- **Approvals:** `bindings_h/approvals.jsonl`, 58 hash-chained entries. Every approval is `approver_kind = agent` ("NOT a human review"). **No human approval exists.**

## Datasets
| Dataset | Status |
|---|---|
| `data/corpus` (v1 generator: gen, dev, test) | Frozen, historical. Physiologically inconsistent values (known) |
| `data/corpus2/{gen,dev}` (bench2, seeds 2,000,000 and 3,000,000) | Regenerated once after spec amendment 1; used for compilation, gate and development. **In-sample for v4.** |
| `data/corpus2/test` | **Does not exist yet.** It is generated only after the v4 freeze, from a sealed seed (report 02) |
| Held-out evasion set v2 (`phase2/stage2/heldout_evasion_v2.py`) | Used once, on v3.2. Now **seen** |
| Held-out evasion set v3 (`phase2/stage3/heldout_evasion_v3.py`, SHA-256 `3e652b5b…`) | Registered before the v4 note, skeleton and vocabulary code. **Not yet run** |

## Test assets
| Suite | Status |
|---|---|
| `tests/` PoC PBT (v1 generator) | Historical; runs against v2.1 |
| `tests_h/test_capture_v3.py`, `test_registry_gate_precision.py`, `test_v4.py` | 100 tests, all passing against v4 |
| `tests_h/test_property_v3.py` (v1 case builder) | v3.x evidence. Under v4, V9 rejects the v1 generator's inconsistent "valid" documents, so it is no longer a meaningful false-reject measure for v4 |
| `tests_h/test_property_bench2.py` (catalogue v2 combinations) | Development run only (seed 99) |
| `tests_h/test_metamorphic_v4.py` | Development run only (559 pairs, 0 violations) |
| `phase2/stage3/mutation_test.py` | 334 mutants, 215 killed on the dev-split oracle; survivors being classified |
| Adversarial suite (`phase2/suites/adversarial.py`, v1 generator) | v3.x evidence |

## FHIR
- **v2.1:** 167/167 bundles with 0 errors, generic and ABDM 6.5.0.
- **v3.0:** 167/167 with 0 errors; negative control 3 errors.
- **v4:** not yet validated. The builder changed (notes go into `conclusion`).

## Capture and forwarding
- v3+ capture never resends automatically once bytes have been written.
- **F-24:** RAW/9100 gives no delivery acknowledgement, so `sent` is not proof of physical printing.
- **Untested:** Windows and a physical printer.

## What is verified vs unverified
| Verified (synthetic, reproducible) | Unverified |
|---|---|
| fail-closed extraction on the synthetic corpora; adversarial and evasion probes; FHIR structural and profile validity (v3.0); capture state handling against fake printers | real lab reports; real legacy software; Windows printing; physical printers; any market need; any human rule review; Kiro usage; FHIR sandbox or certification |
