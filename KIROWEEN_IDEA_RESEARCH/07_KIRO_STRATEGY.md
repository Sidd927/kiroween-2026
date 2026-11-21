# 07 — Kiro-First Development Strategy

Technological Implementation (20% of the score) measures **only** how well we use Kiro. This plan uses the Kiro features that actually improve the build and drops the ones that would only pad a feature count. Feature facts come from the Kiro docs [S7][S8][S9][S10][S11][S36].

## Kiro capabilities that matter (verified)

| Capability | Fact | Where available |
|---|---|---|
| Specs | requirements.md, design.md, tasks.md. Feature specs and **Bugfix specs**. Tasks run in parallel "waves" | IDE, CLI, Web |
| Property-based testing | Extracts properties from requirements, generates hundreds or thousands of test cases, **shrinks counterexamples**, links failures back to the spec | **IDE only** |
| Steering | Project standards applied automatically | all |
| Hooks | `.kiro/hooks/*.json` files. Triggers: `PostFileSave` (regex on the path), `PreToolUse` (can block), `PostToolUse`, `Stop`. Actions: `command` (shell, gets session JSON on stdin) or `agent` (injects a prompt) | IDE/CLI |
| Custom agents / sub-agents | Specialised agents; tasks delegated in parallel | IDE/CLI |
| MCP | External tools and docs | all |
| Powers | Agent Plugins format (`plugin.json`, `skills/`, `mcp.json`), activated by keyword; registry plus install from GitHub | create in IDE/CLI v3 |
| Kiroignore | Keeps sensitive files away from the agent | all |
| Kiro Crew | Open-source persistent agent workspace. Bots, schedules, heartbeats, channels (Slack/Telegram/…). **Apps** via `app.json` (agents, skills, MCP, cron, dashboard pages, backend) | Crew |

---

## Spoolgeist: concrete Kiro plan

### 1. Steering (`.kiro/steering/`)
| File | Purpose | Why it matters |
|---|---|---|
| `product.md` | Users (lab technician, clinic owner, integrator), the "no change to the legacy app" principle, what's out of scope | Keeps Kiro from piling on features |
| `tech.md` | Python 3.12 + asyncio, FastAPI, Next.js 15 + TypeScript, Postgres, pydantic models, `fhir.resources` | One consistent stack |
| `structure.md` | Monorepo layout (`agent/`, `decoders/`, `binder/`, `packs/`, `web/`) | Gives generated code a predictable home |
| `untrusted-input.md` ⭐ | **Every print job is hostile input**: size limits, timeouts, no `eval`, Ghostscript only in a sandbox with `-dSAFER`, parsers are *data* (a declarative DSL), never executable code | This is the steering doc that makes the biggest difference: it stops Kiro from generating risky shortcuts |
| `fhir-conventions.md` | FHIR R4 rules, NRCeS DiagnosticReportRecord shape, LOINC/UCUM rules, "never invent a LOINC code; unmapped tests become `code.text` only" | Prevents hallucinated medical codes |
| `binding-dsl.md` | The DSL grammar and its rules (e.g. every field needs a type and a source anchor) | Keeps the AI-written parsers consistent |

### 2. Specs (`.kiro/specs/`). At least 6 feature specs plus at least 1 bugfix spec
1. `print-capture`: 9100 listener, job framing, pass-through, limits.
2. `stream-decoders`: format detection, ESC/POS, text with control codes, PostScript/PDF → *print lattice*.
3. `binding-dsl`: grammar, interpreter, where each extracted value came from.
4. `binder-loop`: redact → LLM writes a parser → validate → repair → human approval.
5. `lab-pack-fhir`: LOINC/UCUM mapping, DiagnosticReport bundle, HAPI push.
6. `dashboard`: live feed, source-highlighting view, parser approval.
7. `bugfix-*`: written whenever PBT finds a real defect, with the root cause recorded (this is what the write-up will cite).

Requirements are written so properties can be pulled out of them. For example: "WHEN an ESC/POS byte stream encodes text T THE decoder SHALL produce lattice text equal to T", and "Sum of line items SHALL equal invoice total within ±0.01".

### 3. Property-based testing (our strongest Kiro story)
| Property | Generator | What it would catch |
|---|---|---|
| **Decoder round-trip:** encode random text and styles to ESC/POS (python-escpos), decode, compare | Random Unicode and commands | Codepage and line-wrap bugs |
| **Lattice stability:** adding non-printing control codes doesn't change extracted text | Random control-code noise | Parser brittleness |
| **Parser determinism:** same job → same output; output doesn't change if the layout shifts N spaces | Shifted layouts | Fragile column anchors |
| **Lab invariants:** value parses as a number, unit is valid UCUM, matches the unit LOINC expects, sits in a plausible range | Synthetic lab reports | Fields swapped with each other |
| **Invoice invariants:** line items sum to the total; GST = taxable × rate | Synthetic invoices | Rounding errors |
| **FHIR validity:** every generated bundle validates against the models | Random parser outputs | Schema drift |

The write-up will show **real counterexamples Kiro shrank down** and the bugfix specs they produced. Keep a log as we go.

### 4. Hooks (`.kiro/hooks/`)
| Hook | Trigger → Action | What it automates |
|---|---|---|
| `corpus-regression.json` | `PostFileSave` on `decoders/**` or `binder/**` → `command`: run the golden-printout regression suite | Every change is checked against all sample printouts |
| `new-sample-intake.json` | `PostFileSave` on `samples/incoming/**` → `agent`: "fingerprint this job, propose a parser, add it to the corpus, write the expected output for review" | Turns new real-world printouts into tests |
| `no-phi-to-agent.json` | `PreToolUse` on file-read tools with a matcher on `samples/real/**` → block | Real patient data never enters the agent context (alongside `.kiroignore`) |
| `fhir-validate.json` | `PostToolUse` after edits to `packs/lab/**` → `command`: validate FHIR bundles | Keeps the medical output valid |
| `docs-sync.json` | `Stop` → `agent`: update `docs/kiro-log.md` with what changed, which properties were added, which counterexamples were found | **Writes the raw material for the Kiro write-up automatically** |

### 5. Custom agents
- **`binding-smith`**: a sub-agent with a restricted toolset (read samples, write only under `bindings/`) that we use during development to hand-write and debug reference parsers.
- **`fhir-reviewer`**: a read-only agent that reviews `packs/lab` changes against `fhir-conventions.md`.

### 6. MCP
- **Context7 (or similar docs MCP)** for FHIR, fhir.resources, Next.js and FastAPI docs, to avoid hallucinated APIs (the same lesson InteractionKit used).
- **Our own MCP server: `spoolgeist-mcp`** exposes tools such as `decode_job`, `run_binding` and `validate_fhir`. Kiro uses it during development, *and* it ships inside the Power (below). Building it once gives us both.
- GitHub MCP for managing issues and PRs (optional).

### 7. Powers: something we ship to users
- **`spoolgeist-power`** (Agent Plugins format): `plugin.json` with keywords like "print stream", "spool", "legacy printer", "FHIR binding"; `skills/write-domain-pack/` and `skills/debug-binding/`; `mcp.json` pointing at `spoolgeist-mcp`.
- Any developer can then say *"Kiro, add a destination that turns these pharmacy receipts into Google Sheets rows"*, and the Power provides the right context and tools. **This copies the grand-prize pattern (the template ships its own Kiro configuration), applied to a product.**

### 8. Kiro Crew App (stretch, adds eligibility for Best Kiro Crew App)
- **`spoolgeist-warden`**, a separate public repo with an `app.json` that contributes:
  - an agent and skill ("triage failed parses"),
  - a **cron job** (nightly digest of jobs, failures and LLM calls avoided, sent to Slack/Telegram),
  - a **heartbeat** (alert if no prints arrive during clinic hours, i.e. the capture is down),
  - a small dashboard page.
- Build it only if the core product is frozen by 1 Dec.

### 9. Using several Kiro surfaces (the write-up asks how they differ)
- **IDE:** specs, PBT, hooks (main build).
- **CLI (headless):** run the regression corpus and spec tasks in GitHub Actions CI.
- **Web:** hand off a self-contained task (e.g. "GST invoice destination") to run on its own and open a PR. Note how it compared with the IDE.
- **Crew:** the Warden app.

### 10. Honesty rules for the write-up
- Keep `docs/kiro-log.md` (generated by the hook) as an honest timeline.
- Include one or two places where we chose to *vibe-code* (e.g. CSS polish) and say why, as the rules invite that comparison.
- Never claim Kiro built something that it didn't.

---

## Kiro strategies for the other finalists (for comparison)
| Finalist | Kiro angle | Weakness |
|---|---|---|
| R2 Lipi Lazarus | Specs for the data pipeline; PBT for transliteration mapping round-trips | Most of the value lies in model training, which happens outside Kiro |
| R3 Necromancer | PBT and a Power as the product itself | Strong Kiro use, weak impact |
| F1 Ghost Trials | Specs plus an MCP for registries | Ordinary Kiro use |
| S3 Grimoire | The product *is* Kiro configuration | Audience limited to Kiro users |
| C1 Patient Zero | Steering for the design system, hooks for visual tests | Ordinary Kiro use |
