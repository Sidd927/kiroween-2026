# Steering inputs (fold into Kiro-generated steering files)

## product.md
- **Thesis:** "AI writes the parser; proof decides whether it may run." Legacy systems that can only print still hold critical data. Spoolgeist captures print jobs, lets an AI draft a parsing rule once, makes that rule pass an adversarial proof gate plus a named human approval, then processes every report deterministically, offline, with no AI. Anything it cannot fully account for goes to a person.
- **Users:** operator (inbox, confirm/refuse), rule reviewer (onboard, approve, revoke), administrator (queue config, audit).
- **Reference domain:** synthetic lab reports. **Stated audience:** hospital IT and integrators with systems they cannot replace. This is a hypothesis; it has not been validated with customers.
- **Never claim:** clinical safety, ABDM integration or certification, novelty of AI templates (Astera ReportMiner exists) or of print capture, real-world accuracy, exactly-once printing.
- **Cut list:** accounts and multi-tenancy, dashboards, analytics, ABDM gateway, serial capture, auto-approval, rule editing by hand.

## tech.md
- **Stack:** Python 3.11 (engine, FastAPI, SQLite), React + TypeScript + Vite (UI), Docker Compose, pytest + Hypothesis, Playwright for end-to-end tests.
- **No network or AI calls** on the processing path (a test blocks sockets during processing). The LLM is used only in rule onboarding, behind a synthetic-only pre-send guard.
- **Determinism:** the same bytes and the same rule version always give the same output. Rules are pinned by SHA-256 in a hash-chained registry.

## structure.md
`engine/` (pure functions, no I/O) · `capture/` · `rules/` (bindings, registry, gate reports) · `api/` · `web/` · `tests/` (unit, property, metamorphic, e2e) · `fixtures/` (synthetic only).

## safety.md (always included)
- **Synthetic data only.** Never paste real patient data into prompts, fixtures or logs.
- **Fail closed.** When unsure, refuse with a line-level reason. Never weaken a validator, a gate condition or a test to make something pass. If a check seems wrong, write down why and ask.
- **Never silently drop** a line, a result, a note or a field. Never fill a missing value.
- **Logs** carry reason codes, never patient values.
- **Honesty:** results on synthetic data are not clinical evidence. Say "synthetic" wherever numbers are shown.
