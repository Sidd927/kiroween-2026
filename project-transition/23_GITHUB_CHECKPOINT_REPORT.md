# 23: GitHub checkpoint report (22 Nov 2026)

| Item | Value |
|---|---|
| Repository | `https://github.com/Sidd927/kiroween-2026` (**PUBLIC**; visibility not changed by us) |
| Branch pushed | `poc/spoolgeist-validation` (new on the remote; upstream set) |
| Commits added | `53cd236` "Add Phase 2-3 validation: hardened engine v3.x-v4, bench2, sealed evaluation"; `40696d5` "Add transition reports, decision and root README"; this report in a follow-up commit (hash in `00_MASTER_EXECUTION_STATUS.md`) |
| Earlier history preserved | `083bcc6` (research + v2.1 PoC) → `53668b7` (initial). No rewrite, no force-push |
| `main` | unchanged at `53668b7` on the remote (checked with `git ls-remote`) |
| Remote verification | `git ls-remote` branch head = local HEAD `40696d5…`; GitHub API lists all `project-transition/` reports; `poc/phase2/stage3/freeze_manifest_v4.0.json` present (60,829 bytes) |
| Tracked files | 2,394 |
| Added payload | ≈ 42 MB. Largest files: the HL7 validator outputs `fhir_v4_{generic,abdm}.json` (≈ 8.4 MB each) and `fhir_v3_*` (≈ 3.4 MB each), kept as cited evidence |

**Excluded** (`.gitignore`):
- `.venv/`, `.tools/` (≈ 817 MB of JRE and validator);
- caches;
- regenerable FHIR bundles (`runtime/fhir/{generic,abdm}`, `runtime_h/fhir*`);
- `runtime_h/capture/`;
- the mutation-oracle pickle;
- `.DS_Store`.

**Secret scan:** no API keys, tokens or passwords found in tracked text files. All data is synthetic. The LLM call log stores prompt hashes and costs, not prompts.

**Note:** because the repository is public, this push published the research, evidence, reports and the sealed test seed (needed for reproduction, revealed after evaluation).
