# 17: Execution status at the start of the transition (Phase 0 recovery, 22 Nov 2026)

Recovered from the repository and process table, not from earlier messages.

| Item | Found |
|---|---|
| Working directory | `/Users/siddhant_patil/Projects/kiroween-2026` (`poc/` inside) |
| Branch | `poc/spoolgeist-validation` at `083bcc6`; `main` at `53668b7` (= `origin/main`); the branch had never been pushed |
| Working tree | all Phase-2/3 work uncommitted: `spoolgeist_h/`, `bindings_h/`, `tests_h/`, `bench2/`, `phase2/`, `data/corpus2/`, `runtime_h/` |
| Mutation work | 334 mutants. The survivor re-check against the unit tests was running and finished during recovery: **119 re-checked, 24 killed, 95 remaining** (the "88 of 119" in earlier messages was an intermediate count). The extended-oracle run was started for the 95 |
| Frozen candidate | none for v4 yet (v3.0, v3.1 and v3.2 frozen and snapshotted) |
| Tests | 100 regression tests passing; metamorphic and property-bench2 development runs only |
| Sealed evaluation | runner written; no seed and no test split yet |
| Market and product docs | 01, 03 and 04 written; a decision draft (05); a draft root README |
| Kiro | `poc/.kiro` authored by Claude Code, never used in Kiro; Kiro not installed |
| Application code | none |

**What happened next** (completed during this session) is tracked in `00_MASTER_EXECUTION_STATUS.md`.
