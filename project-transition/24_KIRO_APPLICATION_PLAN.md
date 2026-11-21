# 24: Kiro application plan (22 Nov 2026)

## 1. Users (minimum set, no invented roles)
| Role | Needs to |
|---|---|
| **Operator** (lab or desk staff) | see captured jobs, see what was exported, handle refused jobs, confirm free text |
| **Rule reviewer** (IT, lab manager or integrator) | onboard a new layout, read the gate report, approve, reject or revoke a rule |
| **Administrator** (often the same person) | configure the capture queue (port, code page, forward printer), look at the audit chain |

## 2. Core workflow (the MVP vertical slice first)
1. **A job arrives.** Live: RAW/9100 listener when run locally. Hosted demo: "replay a print job" (upload a `.prn` or pick a sample), **labelled as replay**. The job is persisted with its SHA-256 and forwarded, with the honest F-24 statuses.
2. **Recognise.** An approved rule matches: deterministic extraction, no AI.
3. **Decide.** One of three outcomes:
   - **Accepted** → structured record + FHIR R4 download.
   - **Needs confirmation** → free text present; a person confirms.
   - **Refused** → shown with the line-level reason (the offending line highlighted).
4. **Onboard an unknown layout.** The AI drafts a candidate rule from synthetic look-alikes, the compiler runs, the **gate attacks it** (visible list of mutations tried and results), a person approves with their name, and the rule is recorded in the registry.
5. **Audit.** Registry chain verification; per-job event timeline.

## 3. Architecture options compared
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Python (FastAPI) + server-rendered HTMX | one language; fastest to build; the engine stays Python | harder to reach a polished, interactive document viewer | backup |
| **B. Python engine and API (FastAPI + SQLite) + React/TypeScript (Vite) UI** | engine logic stays in its natural language (regex timeouts, Decimal, the HL7 tooling ecosystem); a rich document viewer with line highlighting; strong Design score potential | two stacks | **selected** |
| C. Full TypeScript rewrite | one stack, easy hosting | re-implementing the safety engine in a new language is the biggest correctness risk | rejected |
| D. Desktop (Tauri/Electron), local-first | true local capture | packaging, signing and judge installation friction; no URL for judges | rejected for MVP (roadmap) |

**Deployment:**
- **Local:** `docker compose up` gives the API, UI and capture listener.
- **Hosted demo:** one container on a PaaS such as Render, Fly.io or AWS App Runner, user's choice, in replay mode, with no live port exposure.
- **AI onboarding on the hosted demo:** either a live LLM call through a server-side key the user provides (rate-limited, synthetic-only guard), or the stored candidate from a recorded run, **labelled as such**.

## 4. Repository
**New public repository** (suggested `Sidd927/spoolgeist`), created by the user or with their permission:
- MIT licence visible in the About section;
- `/.kiro/` at the root, **never git-ignored**;
- the README links this research repository as disclosed prior work, plus a "Built with Kiro" section.

**This repository** (`kiroween-2026`) stays the research and validation archive.

**Reuse policy:**
- The v4 engine is **re-implemented through Kiro specs**. Its existing tests and the sealed-evaluation harness serve as the *acceptance oracle*: Kiro-written code must pass the same properties.
- Anything copied verbatim, such as the lab dictionary JSON and the synthetic generator, is listed in `PRIOR_WORK.md`.

## 5. Genuine Kiro usage plan (each item produces evidence)
| Kiro feature | Concrete use | Evidence |
|---|---|---|
| **Specs** (requirements → design → tasks, EARS) | `engine-core` (acceptance contract, gate conditions as EARS), `capture-and-forwarding` (F-24 state machine), `rule-onboarding`, `review-ui`, `fhir-export` | `.kiro/specs/*/{requirements,design,tasks}.md` with task completion history |
| **Property-based testing** | "abstain or exactly correct"; "every non-blank line is explained"; metamorphic relations, written as Kiro spec properties | PBT test files plus Kiro test runs; a write-up of the bugs PBT caught |
| **Steering** | `product.md` (thesis, cut list), `tech.md` (stack, no AI per document), `safety.md` (synthetic data only, fail-closed, never weaken validators), `structure.md` | `.kiro/steering/` |
| **Hooks** | on save in `engine/` → run the property suite; on change to `rules/` → run the gate; on API change → regenerate OpenAPI types for the UI | `.kiro/hooks/*` plus their run output |
| **MCP** | FHIR/HL7 documentation server or a fetch tool for profile lookups; optionally a local HL7-validator wrapper | config plus write-up |
| **Agent modes** | Plan mode for slice planning; autopilot for scaffold; supervised for the engine | write-up |

**Honesty rule:** the write-up states plainly that the research, prototype and validation history were done with Claude Code.

## 6. Schedule (IST; deadline Sat 5 Dec 03:30; protected buffer all of 4 Dec)
| Day | Date | Deliverable |
|---|---|---|
| 0 | 22 Nov | research checkpoint pushed; reports; user actions C1–C3, C7 |
| 1–2 | 23–24 Nov | Kiro set up; steering; `engine-core` spec; engine port passing the property oracle |
| 3–4 | 25–26 Nov | API + capture/replay + deterministic processing; first UI slice (inbox, document view with line accounting, refuse/accept, FHIR download) |
| 5–6 | 27–28 Nov | rule onboarding + gate report + approval; review queue with free-text confirmation; audit view |
| 7 | 29 Nov | design system applied (report 27); accessibility pass |
| 8 | 30 Nov | hosted deployment; docker compose; end-to-end tests |
| 9 | 1 Dec | demo legacy app + capture recording; bug fixing; **credit-request deadline** (1:30 AM IST on 2 Dec) |
| 10 | 2 Dec | video, write-up, blog |
| 11 | 3 Dec | judge red-team fixes only |
| **Buffer** | 4 Dec | submit by 23:59 IST; no feature work |

**Cut first, if behind:**
1. live LLM call on the hosted demo (use the labelled stored candidate);
2. forwarding panel;
3. revocation UI (keep the CLI);
4. audit chain view (keep the API).
