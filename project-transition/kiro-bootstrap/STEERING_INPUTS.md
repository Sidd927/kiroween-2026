# Steering inputs (fold into Kiro-generated steering files)

## product.md
- **Thesis:** "AI writes the parser; proof decides whether it may run." Legacy systems that can only print still hold critical data. Spoolgeist captures print jobs, lets an AI draft a parsing rule once, makes that rule pass an adversarial proof gate plus a named human approval, then processes every report deterministically, offline, with no AI. Anything it cannot fully account for goes to a person.
- **Users:** operator (inbox, confirm/refuse), rule reviewer (onboard, approve, revoke), administrator (queue config, audit).
- **Reference domain:** synthetic lab reports. **Stated audience:** hospital IT and integrators with systems they cannot replace. This is a hypothesis; it has not been validated with customers.
- **Never claim:** clinical safety, ABDM integration or certification, novelty of AI templates (Astera ReportMiner exists) or of print capture, real-world accuracy, exactly-once printing.
- **Cut list:** accounts and multi-tenancy, dashboards, analytics, ABDM gateway, serial capture, auto-approval, rule editing by hand.

## tech.md
- **Stack** (decided 27 Nov):
  - **TypeScript everywhere.** The engine is a pure TS package. The API is Hono on Node 22+, with SQLite via `better-sqlite3`. The UI is React + Vite.
  - **Libraries:** `decimal.js` for exact arithmetic; `vitest` + `fast-check` for unit and property tests; Playwright for end-to-end tests; Docker for the hosted demo.
- **Regex safety:** every rule regex is compiled and run with **RE2** (npm `re2`; fallback `re2-wasm`). Never use JavaScript's built-in `RegExp` on a rule pattern. RE2 syntax only: no lookbehind, no backreferences.
- **Numbers:** never use JavaScript floating point for clinical values or units. Use `decimal.js` end to end.
- **No network or AI calls** on the processing path (a test blocks sockets during processing). The LLM is used only in rule onboarding, behind a synthetic-only pre-send guard.
- **Determinism:** the same bytes and the same rule version always give the same output. Rules are pinned by SHA-256 in a hash-chained registry.

## structure.md
A monorepo (npm workspaces):
- `packages/engine` (pure TS, no I/O);
- `packages/gate` (mutation gate, compiler, registry);
- `apps/api` (Hono, capture listener, SQLite);
- `apps/web` (React);
- `fixtures/` (synthetic print jobs only);
- `tests/e2e`.

## safety.md (always included)
- **Synthetic data only.** Never paste real patient data into prompts, fixtures or logs.
- **Fail closed.** When unsure, refuse with a line-level reason. Never weaken a validator, a gate condition or a test to make something pass. If a check seems wrong, write down why and ask.
- **Never silently drop** a line, a result, a note or a field. Never fill a missing value.
- **Logs** carry reason codes, never patient values.
- **Honesty:** results on synthetic data are not clinical evidence. Say "synthetic" wherever numbers are shown.
