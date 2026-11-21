# 13 — Spoolgeist: Security, Privacy & Safety

Health data is treated as highly sensitive. In India it is personal data under the Digital Personal Data Protection Act 2023 and its Rules [U: we did not re-verify the Rules' notification date or exact obligations this session; do not cite specifics in the submission]. The hackathon MVP uses **only synthetic data**.

## 1. Threat model (MVP scope)
| Asset | Threat | Control |
|---|---|---|
| Captured print jobs (contain patient data) | Read off disk; sent to an LLM; leaked through logs | Local-first storage; encryption at rest; never sent to the LLM; logs contain hashes and IDs only |
| Port 9100 listener | Unauthenticated LAN or internet jobs; malformed input exploiting the decoder | Bind to `127.0.0.1` or a configured LAN interface only; allow-list of client IPs; 2 MB limit and 10 s timeout per job; **no public 9100 endpoint** (changed from `08`) |
| Decoders (Ghostscript, PDF libraries) | Parser vulnerabilities from hostile files | Run in a separate process or container: no network, read-only filesystem, non-root, CPU/memory limits; keep dependencies patched; PostScript is a stretch goal for exactly this reason |
| Generated rules (Bindings) | LLM-written rule tries to run code, exfiltrate data, or extract the wrong field | Rules are **declarative JSON validated against a strict schema**: no expressions beyond a small whitelisted constraint grammar, no file or network access. Activation requires tests to pass and a human to approve. Rules are versioned and SHA-256 hashed; any edit invalidates approval |
| LLM calls | Patient data sent to a third party | Rule generation uses **synthetic look-alike samples only** (see §2); a pre-send guard blocks content containing any value from the real-data PHI detector; the LLM is never called in steady state |
| FHIR output | Sent to the wrong endpoint | Destinations configured by an admin; demo destination is a local HAPI server; no outbound data from the demo tenant |
| Review UI | Unauthorised viewing | Local login (single admin role in the MVP); session timeout |
| Development (Kiro agent) | Real samples enter the agent's context | `.kiroignore` on `samples/real/**` plus a `PreToolUse` hook that blocks reads of those paths; the repo contains synthetic data only |

## 2. Keeping real patient data away from the AI
Regex redaction of names is **not reliable enough** to promise (it misses unusual names and free text). Instead:
1. The rule generator works on **layout, not content**. An operator (or the tool) creates a **synthetic twin** of a real report: same layout, every variable value replaced with generated data. The synthetic twin goes to the LLM. Real reports never do.
2. In the MVP demo, *all* reports are synthetic from the start: a generator we write produces "legacy lab" printouts with fake patients.
3. A **pre-send guard** compares outgoing LLM payloads against the captured job's variable fields. If any real value appears, the call is blocked and logged.

## 3. Data minimisation, retention, encryption, audit
- **Minimisation:** extract only fields the destination needs. The PDF rendering in `presentedForm` is configurable (on by default, because clinicians need the original).
- **Retention:** raw jobs are deleted after successful delivery plus N days (default 7); abstained jobs are kept until reviewed; a hard maximum is configurable.
- **Encryption:** SQLite/Postgres on an encrypted disk (FileVault/BitLocker) **plus** application-level encryption of raw job blobs (libsodium secretbox, key in the OS keychain). TLS for any network delivery.
- **Access control:** MVP has one admin role; roles (reviewer, admin) are on the roadmap.
- **Audit log:** append-only table recording job received (hash), rule applied (ID, version, hash), validators passed or failed, abstained or emitted, reviewer decision, destination response. No patient values in the log.
- **Consent:** the facility (data fiduciary) is responsible for patient consent. ABDM linking needs patient consent flows that **we don't implement** (sandbox and certification are out of scope).

## 4. Safety: never silently wrong
- **The LLM never validates its own output.** Activation and runtime emission depend only on deterministic validators.
- Runtime emission needs: fingerprint match, all required anchors found, all required fields parsed with strict types, unit and terminology checks passed, constraints satisfied. **Anything else means abstain** → review queue showing the original with the failing spans highlighted.
- Unmapped lab tests are never assigned a guessed LOINC code.
- Reprinted or duplicate jobs are detected and not re-sent.
- A clinical disclaimer in the UI and README: output is a data bridge, not diagnostic software.

## 5. Security claims we can honestly make in the hackathon
✅ "Processes print jobs locally; the LLM is used only on synthetic samples while creating a rule, never on patient data."
✅ "Generated rules are declarative data, schema-validated, tested and human-approved before use; they can't run code."
✅ "Abstains and asks for human review rather than emitting uncertain data. Silent-error rate measured on our synthetic benchmark: X%" (report the real number).
✅ "Demo uses only synthetic data."
❌ No claims of DPDP, HIPAA, ABDM or ISO compliance. No penetration-test claims. No "production-ready" claim.
