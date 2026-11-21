# 09 — Final Recommendation: **Spoolgeist**

> ⚠️ **Superseded by `10`–`15` (due diligence, 21 Nov 2026).** Several claims below were wrong or overstated: AI template generation already exists (Astera AGL, Evaporate); ABDM accepts PDF-only lab reports; small-lab market not evidenced; effort underestimated; a public 9100 endpoint was a poor choice. Current decision: **MODIFY with a 48-hour gate** (see `15`).

> *"Every legacy app can still print. Spoolgeist possesses the printer, and the dead software speaks FHIR."*

---

## 1. Project identity
- **Name:** Spoolgeist (spool + poltergeist). No existing product with this name was found [S39].
- **Category:** **Resurrection**. Also apply for **Best Student Project: Resurrection**, Best Demo (automatic), Bonus Blog and Social Blitz, plus **Best Kiro Crew App** if the Warden stretch ships.
- **One-line pitch:** A virtual printer that turns the printouts of dead and legacy software into verified, standards-compliant data (FHIR lab reports, GST invoices) without touching a single line of the legacy code.
- **Elevator pitch:** Across India, small diagnostic labs and clinics run decades-old software that can't connect to the national digital health network. Rebuilding it is expensive, and the vendors are often gone. But every one of those programs can still *print*. Spoolgeist acts as the printer. AI learns each report layout once and compiles it into a deterministic, property-verified parser. From then on every printout becomes a structured FHIR lab report in milliseconds, with no LLM involved and no patient data leaving the clinic, while the paper copy still prints for the patient.
- **Core problem:** valuable data is trapped in legacy systems with no API. Integration means costly migration or hand-built templates. [S19][S20][S23]
- **Target users:**
  - Primary: small and mid-size diagnostic labs and clinics on legacy software (India, ABDM context).
  - Secondary: integrators and IT vendors serving them; SMEs and retailers on legacy POS or accounting systems (receipts and invoices).

## 2. Why this project?
- **Better than the alternatives:** it is the only finalist that scored ≥15/20 on every official criterion *and* ≥8/10 on feasibility, differentiation and demo reliability (see `06`). Lipi Lazarus has more emotional upside but depends on a capability that the KhatianDoc benchmark found today's models simply don't have [S18]. Ghost Trials and Patient Zero compete with published, validated tools [S28][S29][S30]. Grimoire's impact is limited to Kiro users.
- **Not generic:** it isn't a chat interface, a RAG app or a wrapper. The LLM works as a **compiler** that runs once per layout. Its output is a declarative parser that is checked by properties and then runs deterministically. Most extractions use no AI at all, which also means it doesn't generate fresh, unchecked output on every document.
- **Originality:** report mining is 35 years old (Monarch [S23]) and receipt emulators exist [S24][S26]. What's new is **AI-built, verified parsers + zero-change print capture + healthcare/tax-native output + a focus on small facilities**. No equivalent was found in this research.
- **Real-world impact:** ABDM explicitly names legacy software without APIs as a main barrier and says small facilities lack usable software [S19][S20]. Facilities on legacy software can miss DHIS incentive payments [S21]. The same pattern applies anywhere legacy software outlives its vendor.
- **Technical differentiation:**
  - print-stream decoding (ESC/POS, PostScript, control codes),
  - a position-preserving character grid,
  - a declarative parser language,
  - an LLM build-and-repair loop driven by counterexamples,
  - domain property checks (LOINC↔UCUM, totals),
  - FHIR bundle generation,
  - privacy-preserving redaction.
- **Fits Kiroween:** the dead technology (DOS, FoxPro and VB6 apps, LPT printing) becomes the *interface* to the future, the same pattern that won Best Resurrection in 2025 (Faxi), but for a business and health audience rather than consumers, and with a much deeper engineering core. The spooky framing (possession, binding spells, spirits in the spooler) follows the function rather than decorating it.

## 3. Product definition

**Primary user journey (lab technician Meena):**
1. One-time setup by an integrator (about 5 minutes): on the lab PC, add a network printer pointing at the Spoolgeist agent (`Generic / Text Only` or a PostScript driver). Spoolgeist forwards each job to the real printer.
2. Meena prints a CBC report from the 2004-era lab software as usual. The paper comes out as always.
3. **First time a layout is seen:** Spoolgeist fingerprints it as a new layout family and builds a parser (about 10–30 s). The integrator sees the report next to the extracted fields, with every value linked to its source characters, plus green property checks (units match LOINC, values in range). One click approves it.
4. **Every print after that:** parsed in milliseconds, without the LLM. A FHIR R4 DiagnosticReport bundle (LOINC-coded) is sent to the configured FHIR server (ABDM HIP flow on the roadmap).
5. The dashboard shows jobs, failures, records linked and LLM calls avoided.

**Core features (MVP):**
- 9100 capture with pass-through, plus web upload
- Decoders for text/control codes and ESC/POS (PostScript in the ideal version)
- Character grid and layout fingerprinting
- Binding DSL and interpreter
- Parser builder with property checks and repair
- Approval UI
- Lab FHIR destination
- Hosted demo

**Ideal version adds:** PostScript/PDF, the retail/GST destination, source highlighting, the Spoolgeist Power, the full PBT suite.

**The feature judges will remember:** **"Watch the ghost learn."** The first printout of a new layout triggers a visible parser-building sequence: the property checks first fail, a counterexample is fed back, and the corrected parser goes green. Then five more printouts flow through instantly while the counter of LLM calls avoided climbs. It shows on screen why this isn't an AI wrapper.

## 4. Technical architecture

```
Legacy app ──print──▶ [Spoolgeist Agent :9100] ──raw job──▶ [Decoder sandbox]
   (DOS/VFP/VB6)          │ pass-through               │ text/ESC-POS/PS→ print lattice + preview
                          ▼                            ▼
                    physical printer          [Fingerprinter] ──known layout?──yes──▶ [Binding interpreter] ─▶ [Domain pack] ─▶ FHIR/GST/webhook
                                                     │no                                   ▲
                                                     ▼                                     │ approved binding
                                              [Binder: redact → LLM → DSL → properties → repair] ─▶ human approval (dashboard)
                                                                         │
                                     Postgres (jobs, bindings, outputs, audit)  ◀──▶  Next.js dashboard (SSE live feed)
```

| Layer | Choice | Reasoning |
|---|---|---|
| Frontend | Next.js 15 + TypeScript, Tailwind, shadcn/ui, Server-Sent Events for the live feed | Team strength; fast to polish |
| Backend | Python 3.12, FastAPI + asyncio TCP server | Good for bytes and parsing; pydantic models |
| AI/ML | Model-agnostic LLM adapter (Claude via Amazon Bedrock *or* Anthropic API; Gemini fallback). Prompts output **JSON that must match the Binding DSL schema** (structured output). Redaction step before any LLM call (names, phones, IDs → typed placeholders). Optional second-model cross-check on learning samples | The LLM is used only while learning a layout, so cost and privacy are bounded |
| Data sources | Synthetic printout corpus modelled on real report formats (plus real samples from partner labs if they consent, with no patient data in the repo); LOINC subset; UCUM; FHIR R4 + NRCeS profile guidance; GST e-invoice JSON schema | All public or self-generated; nothing in the critical path needs approval |
| Database | Postgres (Supabase): jobs, layout families, parsers (versioned), outputs, audit log | Relational audit trail |
| External services | HAPI FHIR (self-hosted container or public test server), Fly.io (public TCP), Vercel | Free or cheap tiers |
| Deployment | Docker Compose locally; Fly.io (agent/decoder/builder), Vercel (web), Supabase (DB) | A public demo that judges can use without installing anything |
| Security | Every job treated as hostile: size and time limits; Ghostscript in a no-network, read-only, non-root container with `-dSAFER`, kept up to date; parsers are *data*, never code; rate limits per IP; synthetic data only in the demo tenant; `.kiroignore` + PreToolUse hook keep real samples away from the agent | The untrusted-input steering doc enforces this |
| Monitoring | Structured JSON logs, a `/metrics` page (jobs, parse failures, average latency, LLM calls avoided), optional Sentry free tier; stretch: Crew Warden heartbeat | Shows how it would be operated in production |

**How the components communicate:** the agent posts each job (bytes plus metadata) to the decoder service over HTTP. The decoder returns the character grid. The fingerprinter looks up the layout family in Postgres. Known layouts are interpreted synchronously. Unknown ones are queued for the builder (Postgres-backed queue). Results go to destinations, and events stream to the dashboard over SSE.

## 5. Kiro development strategy
The full plan is in `07_KIRO_STRATEGY.md`. In summary:
- **6 steering docs.** The key one is `untrusted-input.md`.
- **At least 6 feature specs and at least 1 bugfix spec**, with requirements written so properties can be extracted.
- **PBT** on decoder round-trips, parser determinism, lab and invoice invariants, and FHIR validity, with counterexamples logged.
- **5 hooks:** corpus regression, intake of new samples, a guard that keeps patient data away from the agent, FHIR validation, and auto-logging for the write-up.
- **2 custom agents:** binding-smith and fhir-reviewer.
- **MCP:** a docs MCP plus our own `spoolgeist-mcp`.
- **A Power we ship to users** (`spoolgeist-power`).
- **Multiple Kiro surfaces:** IDE, CLI (CI), Web (one task handed off), Crew (Warden, stretch).

## 6. Competition strategy

| Criterion (official /10) | Target | How |
|---|---:|---|
| Potential Impact | 7–8 | Policy evidence [S19][S20] + **real lab or clinic voices** + a working FHIR output |
| Technological Implementation | 8–9 | Kiro as part of the product (Power, MCP), PBT counterexamples, hook automation, several surfaces, honest log |
| Design | 7–8 | One coherent flow; the source-highlighting view; restrained spectral theme; polished states |
| Innovation | 8 | The "LLM as a compiler" approach; unusual combination of print streams + FHIR |
| Presentation | 8 | A DOS-to-FHIR before/after "magic moment" in 150 s |

**Biggest competitive weakness:** Potential Impact rests on a *policy-level* problem, not on users we've validated.
**How we overcome it:** in the first 72 hours, visit or call 3–5 local labs, clinics or shops in our city. Record (with consent) one 10-second quote and collect anonymised layout examples. If nobody runs software that only prints, switch the lead story to SME accounting and retail (VFP evidence [S22]) and keep the lab destination as the second example. **Never fake testimonials.**

## 7. Implementation roadmap (day by day)

| Date | Focus | Exit criteria |
|---|---|---|
| **Sat 21 Nov** | Register on Devpost; **request Kiro credits today** (ID check; deadline 1 Dec 12:00 PT); confirm student status for every member; repo + Apache-2.0 + `.kiro` steering; first specs (capture, decoders); book user conversations | Repo public with license detected; credits requested |
| Sun 22 Nov | Capture agent (9100, upload, pass-through); text and ESC/POS decoders; PBT round-trip | Printing from a Mac reaches our server |
| Mon 23 Nov | Character grid + fingerprint; synthetic corpus v1 (3 lab layouts); legacy demo app (a small DOS-style program in DOSBox-X, **clearly disclosed as a stand-in**); **user conversations 1–2** | 10 golden printouts decoded |
| Tue 24 Nov | Binding DSL spec + interpreter + properties; **user conversations 3–5; decide which story leads** | Hand-written parser extracts the CBC correctly |
| Wed 25 Nov | Parser builder: redaction, LLM to DSL, property checks, repair loop | Parser built automatically for 1 layout |
| **Thu 26 Nov** | Builder hardening across the corpus. **Decision gate: ≥80% of layouts get a correct parser within ≤3 rounds?** If not, switch to "propose + human correct" | Gate decided |
| Fri 27 Nov | Lab destination: LOINC/UCUM subset, FHIR bundle, HAPI push, FHIR validation hook | Valid bundle in HAPI |
| Sat 28 Nov | Dashboard: live feed, job detail, parser approval | Full flow works in the UI |
| Sun 29 Nov | Source highlighting; visual identity; PostScript decoder (ideal); deploy to Fly/Vercel/Supabase | Public URL works end to end |
| **Mon 30 Nov** | **Feature freeze.** E2E (Playwright), failure scenarios, security pass, performance; retail/GST destination only if green | All tests green |
| Tue 1 Dec | Spoolgeist Power + MCP packaging; README / judge quick-start; Kiro write-up draft; *(stretch: Crew Warden)* | Power installs from GitHub |
| Wed 2 Dec | Lock script; record the demo (real printing on a real machine); blog draft | Raw footage done |
| Thu 3 Dec | Edit video (<2:50), YouTube public; blog + social post (`#KiroweenHackathon26` first); fill in the Devpost draft | Draft complete |
| **Fri 4 Dec** | Final checks (license in About, `.kiro` not ignored, URLs, credentials field); **submit by 18:00 IST** | Submitted. Hard deadline is 03:30 IST Sat 5 Dec |

**Do not attempt if time runs short (in order of what to cut first):** Crew Warden → retail/GST destination → PostScript decoder → source-highlighting animation → Power packaging (keep the MCP). **Never cut:** the parser-building demo moment, FHIR validity, the hosted URL, the `.kiro` artifacts, the video.

## 8. Demo strategy (150 seconds)

| Time | Scene | Shows |
|---|---|---|
| 0:00–0:15 | Cold open: a green-phosphor DOS lab app on a dusty PC; a dot-matrix-style printout is handed over. VO: *"This lab's software was written before most of us were born. It will never speak to India's digital health network. But it can still print."* | The problem, emotionally |
| 0:15–0:30 | One line of evidence on screen: "Legacy hospital systems lack ABDM API layers" [S19]. Then the real lab owner's quote (if obtained) | Who it's for and why it matters |
| 0:30–0:45 | "Add printer → 192.x.x.x:9100". That's the whole integration | Zero change to the legacy app |
| 0:45–1:25 | **Watch the ghost learn:** print → job appears → new layout detected → parser builds → one property fails ("unit mg/dL doesn't match LOINC 718-7, which expects g/dL") → repair → all green → approve | The real technical achievement, live |
| 1:25–1:50 | Print five more reports rapidly: each lands in under 300 ms as a FHIR DiagnosticReport in HAPI; LLM-calls-avoided counter: 5. The physical printer still prints | Determinism, speed, privacy |
| 1:50–2:15 | Quick cut: the same engine turns a thermal POS receipt into GST invoice JSON (if built), showing it works beyond labs | Versatility |
| 2:15–2:40 | How Kiro built it: the `.kiro` tree, a PBT counterexample Kiro shrank, the hook that blocks patient data, the Spoolgeist Power used to generate a new destination in one prompt | Technological Implementation |
| 2:40–2:55 | Close: *"We didn't replace the dead software. We gave it a voice."* Logo, URL, repo | Memorable ending |

No copyrighted music (use original or royalty-free tracks). No third-party logos. Show it running on a real machine, as the rules require.

## 9. Five biggest risks

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | AI-built parsers wrong or unstable | Medium | Strict DSL schema; per-field type, range and unit properties; repair with counterexamples; human approval; decision gate on 26 Nov with a "propose + correct" fallback |
| 2 | Impact judged as hypothetical | Medium | User conversations by 24 Nov; real-format samples; honest wording; retail/VFP backup story |
| 3 | Real driver output (PCL/raster) doesn't decode | Medium | Setup guide uses Generic/Text and PostScript drivers; raster OCR as a stretch; state supported formats openly |
| 4 | Hosted demo abused or unstable (public TCP port) | Low–medium | Rate limits, 2 MB cap, timeouts, sandboxed decoder, expiring jobs, synthetic-only tenant; web upload fallback |
| 5 | Running out of time / scope creep | Medium | Freeze on 30 Nov; cut list above; video recorded 2 Dec, not 4 Dec |

Also on the radar: Kiro credits/ID verification delays (request today); model availability in India (test on day 0); dependency licenses (Ghostscript AGPL is fine for an open-source repo; disclose escpos-tools if any code is adapted).

## 10. Final verdict

*"If you were judging Kiroween 2026 against hundreds of highly capable developers, would you consider this project a serious contender?"*

**Yes, for the category and student prizes. Plausibly, though not likely, for the top 3.**
- **For it:** it fixes a real, documented infrastructure gap. It has a striking live "magic moment". Its AI is defensible engineering, not a wrapper. And it's built in the way the Kiro team wants to see (specs + PBT + hooks + a Power we ship), echoing why the 2025 grand prize won.
- **Against it:** infrastructure tools are harder to make *beloved* than consumer experiences (SpookBnB took 3rd on charm alone). The impact claims will rest on policy evidence plus a few conversations, not on adoption. A strong Costume or consumer entry with an emotional story could out-score it on Design and Presentation.
- **Realistic reading:** if executed well, this belongs in the upper tier of submissions and has a real shot at **Best Resurrection** and **Best Student Project: Resurrection**. A top-3 overall finish needs exceptional execution and a strong video. Nothing here guarantees winning.

---

## 11. Final self-critique (Part 13): assume another team proposed this

**The case for rejecting it:**
- "It's ETL with a spooky name." *Response:* a reasonable criticism if the demo hides the parser-building and verification. The demo design puts them front and centre. Risk accepted.
- "Who actually prints to network printers in 2026?" *Response:* the targets are exactly the systems that do nothing *but* print. The hidden assumption about how many such facilities exist **is still unvalidated** (marked [H]); it has a 72-hour validation plan and a backup story.
- "Resurrection fit is a stretch; legacy apps aren't 'dead tech'." *Response:* VFP has been out of support since 2015 [S22], and DOS-era LPT printing is obsolete technology by any definition. The pitch must say "dead software" explicitly.

**Compared with the strongest alternative (Lipi Lazarus):** Lipi wins on emotional impact. Spoolgeist wins on feasibility (8 vs 3), demo reliability (8 vs 3), differentiation (8 vs 4) and data (8 vs 3). With 13 days, a project that can't reliably demo its core feature can't win. **Spoolgeist stays.**

**Bias check:**

| Trap | Did we fall in? |
|---|---|
| Familiarity bias | No. It doesn't resemble FedMed, OmniBrain, ClimateChain, SecondLook, Chhaya, ChronoForge, Anchor or UrjaSetu. It uses our data-engineering and LLM skills on a new problem |
| Overconfidence in AI | Mitigated: the LLM is limited to building parsers, verified by properties, with a human gate and a fallback mode |
| Futuristic appeal | No. It's deliberately unglamorous infrastructure |
| Assuming an API works untested | ABDM was kept *off* the critical path for this reason. LLM structured output and Fly TCP must be smoke-tested on day 1–2 |
| Underestimating data collection | Synthetic corpus planned and budgeted (6h); real samples are a bonus |
| Ignoring competitors | Monarch, receipt emulators, document AI and RPA are all addressed in `05` |
| Too many features | MVP is 95h with an explicit cut list |
| Weak category fit | Addressed with the "dead software" framing; acceptable |
| Insufficient Kiro usage | Kiro is part of the product (Power + MCP) plus deep build use |
| Overvaluing complexity | The demo shows one simple idea: print → verified data |
| Underestimating presentation | 16h budget, script locked 2 Dec |

**The recommendation survives the review.**

---

## Action items for today (21 Nov 2026)
1. Join the hackathon on Devpost. **Request Kiro credits now** (needs ID verification; allow 48 business hours).
2. Confirm every teammate is a current student and collect student emails and LinkedIn profiles.
3. Check that Kiro IDE PBT and your preferred models work from India.
4. Message 5 local labs, clinics or shops for a 10-minute conversation this week.
5. Create the public repo with an Apache-2.0 license; commit `.kiro/steering/` first.
