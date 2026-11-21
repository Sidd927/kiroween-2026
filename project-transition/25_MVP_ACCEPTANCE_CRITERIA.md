# 25: MVP acceptance criteria (Kiro-built application)

Each criterion is testable. "Oracle" means the frozen v4 harness from the research repository (sealed split, held-out sets, property tests).

## Engine (spec `engine-core`)
- **E1:** On the bench2 sealed test split (887 documents), the Kiro-built engine produces **0 unsafe accepts and 0 wrong-value accepts**, and **≥ 405 / 410** valid documents correctly accepted. Any difference from v4 is listed and explained.
- **E2:** Pre-registered held-out evasion v3: **0 / 60 numeric** accepted. Qualitative cases end in REJECT or the **"needs confirmation"** state, never in silent export.
- **E3:** The property test "a document is refused, or accepted with exactly correct tier-1 and tier-2 data" passes on ≥ 3,000 generated cases with a seed fixed before the run.
- **E4:** No AI or network call on the processing path. Enforced by a test that blocks sockets during processing.

## Capture and forwarding (spec `capture-and-forwarding`)
- **C1:** The job is persisted with SHA-256 before forwarding. An interrupted, oversize or idle job is quarantined and never parsed.
- **C2:** Forward states are exactly: `captured`, `persisted`, `forwarding`, `sent` (peer closed normally, not proof of printing), `unconfirmed`, `failed`. The UI shows the F-24 caveat next to `sent`.
- **C3:** No automatic resend after any byte was written. An operator resend is logged.
- **C4:** Hosted demo replay jobs are labelled "replay" everywhere they appear.

## Rule onboarding (spec `rule-onboarding`)
- **R1:** An unknown layout produces a candidate rule: an LLM call on **synthetic** look-alike samples only (pre-send guard).
- **R2:** The gate report shows every condition, every mutation tried and its outcome, and every warning.
- **R3:** Approval requires a typed approver name. The approval is appended to a hash-chained registry, re-compiling and re-running the gate. A candidate can never become active without it.
- **R4:** Revoking a rule leaves the layout with no active rule; there is no silent fallback.

## Review and UI (spec `review-ui`)
- **U1:** The inbox lists jobs with their status (accepted, needs confirmation, refused, unknown layout), time and layout.
- **U2:** The document view shows the original text with every line marked by how it was explained, or why it was refused. Keyboard accessible, WCAG 2.1 AA contrast.
- **U3:** For needs-confirmation jobs, free text is highlighted next to the extracted record. Confirm exports; refuse moves the job to refused. Both are audited.
- **U4:** Exports offer FHIR R4 JSON, plus the validator status for pre-validated demo bundles.
- **U5:** Empty, loading and error states exist for every view. No button without a working action.

## Export (spec `fhir-export`)
- **F1:** Bundles pass the HL7 validator, generic R4 and `ndhm.in#6.5.0`, with 0 errors on the demo set. A negative control fails.
- **F2:** Time precision matches the print, notes are carried verbatim, and units are UCUM.

## Submission
- **S1:** The public repository has an MIT licence, `/.kiro` at the root, `PRIOR_WORK.md`, and a README with run instructions.
- **S2:** A hosted URL works for judges without login, or credentials are given in the form.
- **S3:** The video is under 3 minutes, shows the live end-to-end workflow, and is public on YouTube.
- **S4:** The Kiro write-up covers specs, steering, hooks, PBT and MCP with concrete examples, plus the honest prior-work statement.
