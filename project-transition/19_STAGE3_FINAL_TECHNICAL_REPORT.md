# 19: Stage 3 final technical report (v4 frozen, 22 Nov 2026)

## 1. Frozen candidate
| Item | Value |
|---|---|
| Engine | `poc/spoolgeist_h/` (v4) |
| Compiler | `spoolgeist_h.compile/5` |
| Rules | `lab-{a..f}` **v11**. LLM sources: v1 output (A, C); one long-name repair (D, E, F); two repairs (B). Stage-3 LLM spend: 5 calls, US$0.38 |
| Generator | `bench2/generator.py`, catalogue v2 (spec `phase2/02_BENCHMARK_DESIGN.md` + amendments 1–3) |
| Freeze manifest | `poc/phase2/stage3/freeze_manifest_v4.0.json`: **517 files**, manifest SHA `c5bd2f08a725721c…`, frozen 22 Nov 01:19 IST. Re-checked valid after every run |
| Sealed seed | drawn with `secrets` **after** the freeze; SHA-256 `d95df366…7e36` logged before generation |
| Test corpus | 887 documents; per-document file and truth SHA-256 in `phase2/stage3/test_corpus_manifest.json` (manifest `d953442b2381b217`) |
| Dependencies | Python 3.9.6 (macOS CLT), `regex`, `jsonschema`, `hypothesis`, `pytest` (versions in `.venv`); HL7 `validator_cli` + Adoptium JRE 21 in `.tools/` |
| Approvals | 58 hash-chained entries; **all `agent` approvals; no human has reviewed a rule** |

## 2. Architecture (v4)
1. **Normalise:** print bytes are decoded with the queue's **declared code page**, strictly. Bold (ESC E/F) is preserved and overstrike resolved.
2. **Recognise:** anchors plus the page-1 header template.
3. **Check pages:** continuation headers.
4. **Extract:** fields and the table. Approved notes and static subheadings inside the table are kept separate from result rows.
5. **Account for every other line:** static template line, approved note (preserved verbatim), or trusted line matching an approved text skeleton.
6. **Vocabulary-free numeric rule:** a number outside the parsed rows must match an approved digit skeleton.
7. **Qualitative-word check** on notes and variable slots.
8. **Vocabulary sentinel.**
9. **Validators V1–V9.** V9 checks definitional identities using interval arithmetic.
10. **FHIR R4** output.

**Rule lifecycle:** LLM candidate → deterministic compiler (from operator-verified samples, with provenance) → gate v2 (9 conditions, generic adversarial mutations) → approval that **re-compiles and re-runs the gate** → hash-chained registry, with revocation and no silent fallback.

## 3. Sealed evaluation (887 documents; same generator family, new sealed seeds)

### 3.1 Headline (raw counts)
| Metric | v4 (frozen) | v3.2 | v2.1 |
|---|---|---|---|
| Valid documents correctly accepted (tiers 1–3 all correct) | **410 / 410** | 326 / 410 | 168 / 410 ¹ |
| Valid false rejections | **0 / 410** | 84 / 410 | 49 / 410 |
| Wrong-value accepts (tier 1 or 2 wrong) | **0 / 410** | 0 / 326 | 0 / 361 |
| Context errors on accepted docs (sex, age, reported, flags, ranges, precision, notes) | **0 / 410** | 52 / 326 (flags) | 193 / 361 (precision 114, flags 58, notes dropped 35) |
| Defective + foreign documents accepted (unsafe) | **0 / 399** (95% upper bound 0.75%) | 38 / 399 | 84 / 399 |
| Policy documents refused | 77 / 78 (1 accepted, data correct) | 77 / 78 | 29 / 78 (**6 accepted with a wrong patient name**) |
| Recognition correct on accepted | 410 / 410 | 326 / 326 | 361 / 361 |
| AI calls per document | 0 | 0 | 0 |
| Latency, median / p95 | 0.86 / 1.63 ms | 0.67 / 1.29 | 0.46 / 0.84 |

¹ v2.1: 361 accepted with correct tiers 1 and 2, of which 193 had context errors.

**By layout group (v4):**
- A–C: 211 / 211 valid correct, 195 / 195 defects rejected.
- D–F: 199 / 199 valid correct, 174 / 174 defects rejected.

### 3.2 Categories requested
| Category | v4 result | Denominator |
|---|---|---|
| Identity errors (name, id, collected date and time) | 0 | 410 accepted valid |
| Age, sex and reported-date errors | 0 | 410 |
| Abnormal-flag errors (direction for A/D/F, presence for B/C/E) | 0 | 410 |
| Reference-range errors | 0 | 410 |
| Note omissions (`approved_note`, `interpretive_note`) | 0 | 44 note documents (all preserved, and in FHIR `conclusion`) |
| Result-row completeness (missing or extra results) | 0 | 410 |
| Hidden numeric results accepted | 0 | 18 (catalogue) + 60 (held-out v3) + 198 + 66 (evasion v2, at v3.2 freeze) |
| **Hidden qualitative results accepted** | 0 / 18 (catalogue); **27 / 180 (held-out v3)** | see §4 |
| Domain-consistency defects accepted (index, swap, bilirubin, protein, differential) | 0 | 33 |
| Unsupported layouts accepted (foreign + drifted) | 0 | 30 |
| Repeated or conflicting tests accepted | 0 | 18 duplicate-conflict |
| Unknown tests accepted | 0 | 18 |
| Report identifier, sample identifier, date of birth | **not extracted** (the target schema has no such fields) | n/a |
| Qualitative test **results as data** | **not extracted** (the dictionary is numeric-only); only "must not be silently dropped" is tested | n/a |

## 4. Held-out adversarial sets (pre-registered, first run after the freeze)
**Evasion v3** (240 cases; 12 qualitative + 4 numeric phrasings × 5 placements × A, B, C):

| Placement | v4 accepted (result dropped or only kept as note text) |
|---|---|
| Field line, referrer-line end, new trusted line | **0 / 108** |
| Approved note | **18 / 36** (kept verbatim in `notes` and FHIR `conclusion`, but not refused) |
| Inside the referrer name slot | **9 / 36** |
| Numeric, all placements | **0 / 60** |

v3.2 accepted 132 / 180 qualitative cases and v2.1 accepted 240 / 240.

**Conclusion:** qualitative results remain the open gap wherever free text is legitimately allowed (notes, name slots). Closing it needs either a qualitative-test dictionary (extract them) or a policy that refuses all free text except approved fixed phrases. That is a product decision (report 22).

## 5. Property and metamorphic testing (pre-registered seeds)
- **Property test, catalogue-v2 combinations** (seed 314159, N = 3,000):
  - 0 unsafe and 0 wrong-value accepts;
  - 4 / 746 valid false rejects;
  - 247 policy refusals;
  - 9 policy accepts with correct data.
- **Metamorphic** (N = 1,000): 945 pairs (rename, CRLF, column shift, moved page break, added note, changed referrer), with **0 violations and 0 instabilities**.
- **v3.x property tests (v1 case builder):** 0 unsafe and 0 silent in 23,000 cases at v3.2. Not re-run as v4 evidence, because V9 correctly rejects the v1 generator's physiologically inconsistent "valid" documents.

## 6. Mutation testing
252 / 334 killed (75.4%); 82 survivors classified (38 redundant, 24 message-only, 19 robust, 1 unreachable); 5 gap tests added. See report 18.

## 7. FHIR (410 accepted sealed-test documents)
| Check | Result |
|---|---|
| Structural validity (HL7 validator, R4 4.0.1) | 0 errors / 410 |
| ABDM profile conformance (`ndhm.in#6.5.0`) | 0 errors / 410 |
| Negative control (broken ABDM bundle) | 3 errors (profiles enforced) |
| Representation checks (our script): patient id, name, gender, date, **time precision**, observation count, **unit conversion to UCUM**, interpretation presence, **notes in `conclusion`** | 410 / 410 each |
| Clinical correctness of LOINC choices | **not established** (needs a human terminologist) |
| ABDM sandbox / gateway / certification | **not done** |

## 8. Print forwarding (F-24)
Implemented states (`spoolgeist_h/capture.py`), mapped to the requested model:

| Requested state | Implemented as | Verified |
|---|---|---|
| Captured | TCP job received until EOF; incomplete, oversize and idle jobs go to `incomplete/` (quarantine, never forwarded or parsed) | fake clients (E1–E9); CUPS once |
| Persisted | `jobs/<id>.prn` + meta with SHA-256, fsync'd, 0600, **before** any forwarding | tests |
| Forwarding initiated | `sending`, persisted before the first byte | tests |
| Delivery confirmed | **not available over RAW/9100.** Status `sent` means "bytes written, peer closed normally". It is **not** proof of printing (F-24: an aborted connection can look like a normal close on macOS) | flaky-test evidence (2 of 6 runs) |
| Delivery unconfirmed | `sent_unconfirmed`: any abnormal close after bytes were written, or a crash during `sending` | tests (RST, mid-stream death, crash on restart) |
| Operator review required | `sent_unconfirmed` + `forward_unconfirmed` event; never resent automatically | tests |
| Retry authorised | `--resend <job>` (operator) | test |
| Failed | `failed` after 5 connection failures in which **no byte was written** (safe to retry; retried at restart) | tests |

**Real delivery confirmation options (not implemented):**
- IPP job-state (`job-state = completed`), where the printer supports IPP;
- SNMP page-counter deltas;
- the printer's own job log.

**Untested:** a physical printer, the Windows spooler, and printers that reset connections routinely (which would make every job "unconfirmed").

## 9. Known limitations
1. **One synthetic generator family**, written by the system's author. The sealed split differs only in seeds. **No real report has ever been processed.**
2. **Qualitative results** in notes and name slots (§4).
3. **Rules approved only by an agent.**
4. **Line-accounting rigidity:** any unseen free-text format is refused. Real reports will have higher refusal rates.
5. Multi-page documents for C and E are refused (no approved sample).
6. Code page is a per-queue configuration; a wrong declaration that maps letters to letters of the same script would pass.
7. No encryption at rest, no capture-port authentication, no retention job.
8. **Built with Claude Code, not Kiro.**

## 10. Reproduce
From `poc/`:

Check the freeze:
```bash
.venv/bin/python -m phase2.stage3.freeze_v4 --check
```
Run the sealed evaluation (re-runs v4, v3.2 and v2.1 on the existing test split):
```bash
.venv/bin/python -m phase2.stage3.sealed_eval --run
```
Run held-out evasion set v3 against v4:
```bash
.venv/bin/python -m phase2.stage3.heldout_evasion_v3 v4 repro
```
Run the property test with the pre-registered seed:
```bash
PBT2_SEED=314159 PBT2_N=3000 .venv/bin/python -m pytest -q tests_h/test_property_bench2.py
```
Run the full regression suite:
```bash
.venv/bin/python -m pytest -q tests_h/test_v4.py tests_h/test_registry_gate_precision.py tests_h/test_capture_v3.py tests_h/test_metamorphic_v4.py
```
Build the FHIR bundles and run the semantic checks:
```bash
.venv/bin/python -m phase2.stage3.post_freeze.fhir_v4
```
Validate them with the HL7 validator:
```bash
phase2/stage3/post_freeze/validate_fhir_v4.sh abdm
```

## 11. Remaining blockers
| Blocker | Who |
|---|---|
| Kiro use (mandatory for the competition) | user installs Kiro and requests credits; then Kiro-based development |
| Any real-world evidence | user (interviews, or a real anonymised report format) |
| Human rule approval | user |
| Windows / physical printer | user hardware |
