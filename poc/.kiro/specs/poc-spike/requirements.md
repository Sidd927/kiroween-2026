# Requirements: Spoolgeist PoC spike (engineering validation, not product)

## R1 Print capture
- R1.1 WHEN a spooler sends a job to the RAW/9100 listener THE SYSTEM SHALL store the exact bytes and a metadata record (peer, size, SHA-256, format) before any other processing.
- R1.2 WHEN a forward target is configured THE SYSTEM SHALL send byte-identical data to it, retrying on failure without creating duplicate prints from the retry logic.
- R1.3 IF a transfer is interrupted or exceeds limits THEN THE SYSTEM SHALL quarantine it and SHALL NOT forward or process it.
- R1.4 WHEN the same bytes arrive twice from the same client within 10 minutes THE SYSTEM SHALL forward both but emit data only once.

## R2 Rule generation
- R2.1 WHEN a new layout is enrolled THE SYSTEM SHALL ask the LLM for a declarative Binding using only synthetic generation samples.
- R2.2 THE SYSTEM SHALL activate a Binding only if static checks pass and the gate (0 silent errors, 0 unsafe accepts, >=90% clean acceptance on the regression set) passes, within at most 3 repair rounds.
- R2.3 THE SYSTEM SHALL pin each active Binding by SHA-256.

## R3 Deterministic extraction and validation
- R3.1 WHEN processing a document THE SYSTEM SHALL make zero LLM calls.
- R3.2 THE SYSTEM SHALL output either ACCEPT with a record or REJECT with explicit reasons.
- R3.3 Property (PBT): for any generated document of an active layout, the output SHALL be REJECT, or ACCEPT with critical fields exactly equal to ground truth; documents with an injected defect SHALL be REJECTED.

## R4 FHIR
- R4.1 WHEN a document is accepted THE SYSTEM SHALL build a FHIR R4 document Bundle with Patient, Organization, DiagnosticReport, Observations and the original text in presentedForm.
- R4.2 THE SYSTEM SHALL validate bundles with the HL7 validator against base R4 and, separately, against ndhm.in 6.5.0 profiles.

## R5 Evidence
- R5.1 THE SYSTEM SHALL report silent errors, refusals, recognition, field accuracy, latency and AI-call counts separately for development and unseen layouts.
