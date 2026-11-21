# 08 — Feasibility & Execution Analysis

**Time budget:** Sat 21 Nov 2026 → hard deadline **Sat 5 Dec 2026, 03:30 IST** (Fri 4 Dec, 2:00 PM PT). Our internal deadline is **Fri 4 Dec, 18:00 IST**, leaving a 9.5-hour buffer. That's about 13 working days.

**Capacity assumption:** we don't know the team size. Estimates are in **person-hours**. At about 9 productive hours per person per day, 13 days gives roughly 115h for a solo builder, 230h for two and 345h for three. Kiro speeds up implementation, but the estimates below assume it does **not** speed up debugging, design or video production.

---

## Comparing the finalists (core build, person-hours)

| Finalist | Minimum viable product | Ideal competition version | Hardest component | Can we do it in 13 days? |
|---|---|---|---|---|
| **R1 Spoolgeist** | **~95h** | ~150h | AI parser builder with repair loop | **Yes** (MVP even solo; ideal with 2 people) |
| R2 Lipi Lazarus | ~120h + training time | ~200h | Usable handwritten recognition | **No** (accuracy can't be guaranteed) |
| R3 Necromancer | ~90h | ~140h | Generating inputs for real libraries | Yes, but impact is weak |
| F1 Ghost Trials | ~75h | ~120h | CTRI parsing + outcome alignment | Yes |
| S3 Grimoire | ~110h | ~170h | Template + 2 apps on a new platform | Risky |
| C1 Patient Zero | ~70h | ~120h | Citation-context retrieval at scale | Yes |

---

## Spoolgeist: detailed plan

### Phase 1: Foundation (≈12h)
- Monorepo: `agent/` (Python), `decoders/`, `binder/`, `packs/lab`, `packs/retail`, `web/` (Next.js), `samples/`, `.kiro/`, `infra/` (Docker Compose).
- Apache-2.0 LICENSE (check it shows in the GitHub About panel). README skeleton with a "Pre-existing work & dependencies" section.
- Kiro steering (6 docs) and the first two specs. Hooks wired.
- Docker Compose with Postgres, HAPI FHIR (local) and the decoder sandbox.
- CI using Kiro CLI headless plus pytest/Hypothesis.

### Phase 2: Core functionality (≈52h)
| Component | Hours | Notes |
|---|---:|---|
| Capture: raw 9100 listener, job framing (idle timeout), size and time limits, pass-through to a real printer, HTTP upload endpoint | 6 | asyncio streams |
| Decoders: format sniffing; plain text with control codes; ESC/POS (own parser, using escpos-tools as reference); PS/PDF via sandboxed Ghostscript `txtwrite` (keeps positions); preview PNG | 14 | Raster OCR is out of the MVP |
| Print lattice (character grid with row/column) + layout fingerprint (hash of static tokens and their positions) | 6 | Identifies which layout family a job belongs to |
| Binding DSL (JSON Schema) + interpreter (anchors, regions, regex, repeating table blocks, type conversion, where each value came from) | 12 | Data, not code: safe to run |
| Parser-builder loop: redact patient data → LLM proposes a parser → interpret → run properties → feed counterexamples back (≤3 rounds) → human approval | 14 | Model-agnostic adapter |

### Phase 3: Product experience (≈34h)
| Component | Hours |
|---|---:|
| Lab destination: LOINC subset (~60 common Indian tests: CBC, LFT, KFT, lipids, HbA1c, TSH), UCUM units, FHIR R4 DiagnosticReport + Observations bundle (ABDM DiagnosticReportRecord shape), push to HAPI | 12 |
| Dashboard: live job feed (SSE), job detail with **print preview ↔ fields where clicking a value highlights its exact source characters**, parser viewer and approval, property status, destination log, counter of LLM calls avoided | 18 |
| Visual identity: restrained "ghost in the machine" theme (green-phosphor print preview, spectral transitions), loading and empty states, error toasts | 4 |

### Phase 4: Testing (≈14h)
- Kiro PBT suites (see 07).
- A golden corpus of at least 25 synthetic printouts across 3 lab layouts, 2 receipt layouts and 1 invoice layout, with expected outputs.
- E2E with Playwright: upload → parser → approve → FHIR.
- Failure scenarios: oversized jobs, binary garbage, unknown format, LLM timeout, an invalid parser that the checks catch, HAPI down.
- Performance target: decode plus parse in under 300 ms per job once a parser is approved.

### Phase 5: Deployment (≈8h)
- **Dashboard:** Vercel. **DB:** Supabase Postgres.
- **Capture + decoders + parser builder:** Fly.io (public TCP service on 9100 for a "print to our cloud" demo, with rate limits per IP, a 2 MB job cap, 10 s timeouts and stored jobs that expire automatically). HAPI FHIR container on Fly or a public HAPI test server (no real patient data ever).
- Secrets in the platform environment settings. Separate demo tenant with synthetic data only.
- Production check: print from macOS (add an IP printer → HP JetDirect socket) and from a Windows VM.

### Phase 6: Submission (≈16h)
- Video (script, recording, edit, captions, royalty-free or original music): 8h.
- Devpost text plus the Kiro write-up (from `docs/kiro-log.md`): 4h.
- Blog post (Bonus Blog) plus social post (`#KiroweenHackathon26` at the start): 2h.
- Repo hygiene: `.kiro` committed, license detected, README test instructions, sample files, judge quick-start: 2h.

**MVP total ≈ 95h:** P1, capture, decoders without PostScript, lattice, DSL, parser builder, lab destination, core dashboard, basic tests, deploy, submission.
**Ideal total ≈ 150h:** everything above plus PostScript, retail/GST destination, source highlighting, full PBT suite, the Power.
**Stretch (+20–30h):** Crew Warden app; PCL via GhostPCL; LPD/IPP listeners; raster OCR fallback; a Windows tray installer; WhatsApp patient notification; ABDM sandbox push.

### Critical path
**decoders → lattice → DSL interpreter → parser-builder loop → lab destination → dashboard job view → deploy → video.**
Everything else is parallel or optional.

### External dependencies
| Dependency | Risk | Fallback |
|---|---|---|
| LLM API (Claude via Bedrock or Anthropic API, or Gemini) | Low; it's only needed while a parser is being built | Approved parsers are cached; the demo runs on them; model-agnostic adapter |
| Ghostscript (**AGPL**) | License: our repo is open source and we call `gs` as a separate process. Disclose it | Text/ESC-POS only |
| HAPI FHIR (Apache-2.0) | Low | Validate bundles locally with `fhir.resources` |
| LOINC table | Needs a free account [U] | Hand-check about 60 codes on loinc.org |
| Fly.io public TCP | Low–medium | Web upload of `.prn` files + recorded live demo |
| **ABDM sandbox** | **Approval time unknown; vendors quote 4–12 weeks for integration [S38]** | **Not on the critical path.** Produce ABDM-shaped FHIR; present the ABDM push as the roadmap |

### Main failure scenarios
1. **Parser builder produces wrong parsers too often.** Day-6 decision gate: if fewer than 80% of corpus layouts get a correct parser within 3 rounds, switch to "LLM proposes, human corrects in the UI" (still deterministic once approved) and present that honestly.
2. **Print formats from real drivers don't decode.** Lock in the "Generic/Text Only" and PostScript drivers in the setup guide; show raster support as a stretch.
3. **No real users found.** Use the retail/VFP angle and synthetic data, and state clearly that the clinic story is a validated policy gap [S19] but not yet validated with users.
4. **Scope creep.** Feature freeze at end of day 10 (30 Nov). Only bugfix specs after that.
5. **Video quality.** Script locked on day 11; record on day 12; never on the last day.
