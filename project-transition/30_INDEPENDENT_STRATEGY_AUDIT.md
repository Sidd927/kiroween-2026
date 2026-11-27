# 30: Independent strategy and viability audit (27 Nov 2026)

**Labels used throughout:**
- **[FACT]:** verified today from a primary source or the repositories.
- **[PRIOR]:** our own earlier research (same author; treat with suspicion).
- **[ASSUMPTION]:** believed, not verified.
- **[OPINION]:** my judgement.
- **[UNKNOWN]:** not known.

**Scope:** strategy only. Nothing in the application repository was read beyond its three files, and nothing there was changed.

---

## 1. Executive verdict
**Build Spoolgeist, but only as a ruthlessly narrow "golden path" demo of one idea: an AI-drafted parser that must *survive an attack* before it may run, then runs with zero AI and refuses, visibly, anything it can't explain.** Present it in Resurrection, with a concrete human story and a live, judge-tryable demo.

**The project is in danger because of execution, not because of the idea:**
- [FACT] Today is 27 Nov, 15:50 IST. The deadline is Sat 5 Dec, 03:30 IST: **about 7.5 days**.
- [FACT] The application repository (`Sidd927/spoolgeist`) still holds only LICENSE, README and PRIOR_WORK.md (committed 22 Nov).
- [FACT] Kiro is now installed on this Mac, but **no Kiro work exists in the application repository**.
- [UNKNOWN] Team size and hours are still unknown.

The single largest risk is reaching 4 Dec with an impressive research archive and an unfinished Kiro app. Every recommendation below follows from that.

## 2. Independent project assessment: built vs researched vs proposed
| Thing | Status | Label |
|---|---|---|
| Research reports 01–15, market and competitive reassessment | written | [PRIOR] |
| v2.1 → v4 engine (Python), compiler, gate, registry, capture, FHIR | **built with Claude Code, in the research repository**; tested on synthetic data | [FACT] |
| Sealed evaluation: 410/410 valid fully correct; **0/399** defective or foreign accepted; 77/78 policy refusals | measured on **new seeds of the same generator family** written by the same author | [FACT] (numbers) / [OPINION] (weak independence) |
| Held-out evasion v3: numeric 0/60 leaked; **qualitative 27/180 leaked** | measured, pre-registered | [FACT] |
| Mutation testing: 252/334 killed; 82 survivors classified | measured | [FACT] |
| FHIR: 410 bundles with 0 validator errors (R4 + ABDM 6.5.0 profiles) | structural and profile validity only | [FACT] |
| Human approval of any rule | **none** (46 agent approvals, 0 human) | [FACT] |
| Real lab report, real legacy app, Windows, physical printer | **never tested** | [FACT] |
| Customer interviews | **zero** | [FACT] |
| Competition application (Kiro) | **not started** | [FACT] |
| Design system "Greenbar", Kiro bootstrap briefs | written (Claude Code) | [FACT] |

## 3. Core thesis assessment
**Thesis:** legacy systems that can only print still hold critical data. AI can draft a parser once; the parser must prove itself; after approval the processing is deterministic, offline and AI-free; anything unexplained is refused.

| Question | Candid answer |
|---|---|
| Compelling hackathon project? | **Yes, if shown as a drama, not a pipeline.** The memorable moment is a rule being *attacked* and a forged report being *refused, line highlighted*. A judge will not remember "deterministic extraction" [OPINION] |
| Important problem? | **Plausible, unproven.** Manual re-typing in labs is widely claimed, but by vendors [PRIOR, VENDOR]. Small labs can switch to cheap cloud LIS products [PRIOR]. No interview evidence |
| Differentiated? | **Partly.** "AI auto-generates a reusable template" is a shipping commercial feature (Astera ReportMiner "Auto-Generate Layout") [PRIOR→SRC]. Print capture is commercial (VeryPDF, Retro-Printer, RedTitan) [PRIOR→SRC]. **Faxi, Kiroween 2025's Best Resurrection winner, is the same narrative family: legacy device → AI → modern data** [FACT] |
| Healthcare angle: compelling or restrictive? | **Both.** It gives stakes (a dropped Hb value matters) and domain checks (red-cell identities) that make the gate non-trivial. It also invites "is this clinically safe?" questions we cannot answer. Keep it as *the demo domain*; never claim clinical use [OPINION] |
| Is the core innovation novel? | **The combination is unusual; the components are not.** Unusual: (a) AI output gated by *generated adversarial mutations* plus a whole-document "every line explained" contract; (b) AI removed from the per-document path entirely; (c) refusals with line-level reasons. I found no competitor that markets this contract, but I have not tested ReportMiner or Unstract hands-on [OPINION] |
| Overestimating AI-written rules? | **Yes, somewhat.** The prior work shows LLM-written rules needed repairs (long names in 4/6 layouts, age in B) and that much of the safety comes from **human-written** layers (compiler, line accounting, V9). The honest framing is that the AI is the cheap draftsman and the proof is the product [OPINION] |
| Is the gate innovation or hygiene? | **Hygiene, unless it is visible.** Shown as a log line, it reads as engineering diligence. Shown as "here are 214 ways we tried to break the AI's rule; 1 succeeded; the AI repaired it; now 0 succeed", it reads as an idea [OPINION] |
| Dismissable as an "LLM + regex wrapper"? | **Yes, if the demo leads with the LLM.** It must lead with the refusal and the no-AI processing, and show the AI only as the draftsman [OPINION] |
| Strongest version | §8 below |
| A better direction inside the project we missed? | **Yes: the patient-facing payoff.** The prior work ends at "FHIR bundle", which judges cannot feel. Faxi won partly because a human visibly benefits. A clinic or lab whose 1998 system only prints could give a patient a verified digital report (a QR/HTML page plus FHIR) *because* the proof gate makes that safe. This adds a human beneficiary without new infrastructure [OPINION] |

## 4. Competitor, market and differentiation
- **Commercial report mining**
  - Monarch: 35+ years; print-stream decomposition; ~$1.6–2k per user per year (dated third-party list prices).
  - Astera ReportMiner: **AI auto-generated layouts**, LLM extraction, validation rules [PRIOR→SRC].
- **Print capture:** VeryPDF Printer Capture, Retro-Printer, RedTitan [PRIOR→SRC].
- **LLM extraction:** Unstract (open source, dual-LLM "LLMChallenge" consensus, human-in-the-loop) [PRIOR→SRC].
- **Indian lab software:** many cloud LIS products claim ABHA/ABDM push at ₹ hundreds to thousands a month [PRIOR, VENDOR].
- **Kiroween precedent:**
  - **Faxi** (2025 Best Resurrection + Influencer Judges' Choice): fax → Gemini Vision → MCP agents → fax back. A live fax number judges could use; 16+ Kiro specs, 4 hooks, custom MCP servers [FACT, devpost.com/software/faxi-16iecy].
  - **Dark Ledger** (a 2025 winner): a "COBOL-verified" payroll engine, showing that verified legacy computation can win [FACT; exact prize not checked].

**Defensible differentiation [OPINION]:** "Faxi trusts the AI on every fax and adds human checks on purchases. Spoolgeist trusts the AI **zero times per document**: the AI writes a rule once, the rule must survive attack, a human signs it, and from then on no AI ever sees a report." This is a crisp, true contrast with a known winner. Use it in the written description, not as an attack on Faxi.

## 5. Kiroween category and positioning
**Published criteria** [FACT, rules + judges update 23 Nov]: five equal criteria.
- **Impact:** "real problem for a real audience… Would someone actually use this?"
- **Technological Implementation:** "How thoroughly and skillfully does the project use Kiro… variety of Kiro tools… experimentation?"
- **Design:** "complete, coherent product experience, not just a technical proof of concept".
- **Innovation.**
- **Presentation:** "video clearly demonstrate the project working end-to-end".

**Published judge statements** [FACT, Devpost updates 23 and 26 Nov]:
- "Show me how you used specs, steering and hooks to get there, not just the final result. Bonus points if Kiro surprised you."
- "simple, focused solutions that tackle a real problem. A clean interface…"
- "breadth of knowledge across the Kiro surfaces"; "a strong demo video that articulates the problem".
- "Scare me, then make it easy… a ghost that guides me or an error message that makes me laugh."
- "things that outlive the hackathon, such as open-source tools".

The organisers also say: show Kiro in the video (a spec, a hook, steering), show the project working in the first 10–15 seconds, and pass the 30-second test.

**Interpretation [OPINION]:**
- Resurrection fits, with "dead printer ports" and green-bar paper.
- **Tech Implementation is a Kiro-usage score, not an engineering score.** Our deepest engineering asset (the v4 harness) scores *nothing* there, because Kiro did not build it.
- The Kiro story must be *produced now*. Its best version is a meta-story: *"We used Kiro's spec-driven, property-tested workflow to build a tool that forces AI-written code to pass spec-driven property tests."* That is Kiro's own philosophy applied to the product's core, so it is coherent rather than decorative.
- **Memorable:** the ghost that refuses to lie ("I can't explain line 31, so I won't pretend I can"), the green-bar printout, and the live attack counter.
- **Generic elements that hurt:** dashboards, settings pages, login, metrics walls, any "AI chat".

## 6. Prior-work and eligibility risks
| Risk | Severity | Status / mitigation |
|---|---|---|
| "Insufficient use of Kiro" → disqualification (judges' discretion) [FACT, rules] | **Critical** | No Kiro code yet. The application must be visibly Kiro-built: specs, tasks, hooks, steering, commit history |
| Pre-existing work must be disclosed [FACT] | High | `PRIOR_WORK.md` exists. Keep it exact |
| Prior work was built with another AI tool *during* the period | Medium | Rules are silent [FACT]. **The clarification to organisers is drafted but, to my knowledge, unsent [UNKNOWN whether sent].** Send it today |
| Unconsciously transplanting the prototype's design or code | High | Do not paste prototype code into Kiro prompts. Do not give Kiro the research engine as context; give it *requirements and properties*. Using a **different language** for the app (see §11) makes independence evident and reduces the temptation |
| Using research results as *submission* evidence | Medium | The 410/410 and 0/399 numbers are about the **research engine, not the Kiro app**. They may only be cited as background ("our prior prototype…"). Claims about the app need fresh numbers from the app itself |
| The sealed corpus is public now (pushed 22 Nov) | Low | If the Kiro app is evaluated on it, say so; it is no longer secret, and its seed is public |
| Credits | Medium | Request closes **1 Dec 12:00 PT** and moves slower over Thanksgiving [FACT]. Request today if not done [UNKNOWN] |

## 7. Alternatives and pivots considered
| Option | Verdict |
|---|---|
| **P0:** full MVP from report 24 (capture, live onboarding, gate, registry, review, FHIR, audit, hosted) | **Reject.** Too big for about 6 working days from zero |
| **P1: golden-path Spoolgeist** (one legacy app, 2 known layouts + 1 onboarded live, attack gate, refusal with ghost, patient-ready output) | **Recommend** |
| P2: Spoolgeist as a domain-agnostic developer library (a Skeleton Crew-style template) | Reject. Weak Design and Impact; Skeleton Crew requires 2 apps |
| P3: patient-centred pivot ("SMS/WhatsApp your lab results from a 1998 printer") | Partly adopt *as the payoff screen* (QR/HTML report). Reject messaging integrations (time, safety, third-party terms) |
| P4: a different project (e.g. "Necromancer") | Reject. No evidence it is better, zero assets, and 7 days left. A pivot now trades a known execution risk for an unknown one plus lost assets |
| P5: Costume Contest framing (pure UI polish) | Reject as category; borrow its spirit (mischief, polish) inside Resurrection |

## 8. Recommended final direction
**"Spoolgeist: the ghost in the print spooler. Old systems print; Spoolgeist makes their printouts *trustworthy* data. AI drafts the parser once; the parser must survive our attack and your signature; after that, no AI ever reads a report, and anything Spoolgeist can't explain, it refuses."**

- **Audience shown:** a small lab's front-desk technician who re-types results from a 1998 lab system, and the patient who gets a verified digital copy. **Label this audience as a hypothesis** unless interviews happen.
- **Category:** Resurrection.
- **Bonuses:** Best Demo; Blog (a real "property tests caught silent-drop bugs" story); Student (if eligible).

## 9. Recommended scope for the deadline
- **One** synthetic "1998 lab system": a tiny text-mode app that prints over RAW 9100 or via CUPS on the Mac.
- **Two** pre-onboarded layouts.
- **One** layout onboarded live in the demo.
- About **12 analytes** (CBC + a few chemistries).
- **Three outcomes:** accepted, needs confirmation (free text), refused.
- **One** export (FHIR JSON) plus **one** human payoff (a patient-friendly verified report page with QR).
- **Hosted demo in replay mode** (upload or pick a print job). Local live capture shown in the video.

## 10. Ideal judge journey (≤ 3 minutes in the app, ≤ 30 seconds to "get it")
1. **Landing card, 10 s:** "1998 lab system → Spoolgeist → verified digital report" with three sample print jobs to drop in. No login.
2. **Drop a known report → Accepted** in about 1 ms. The printout appears as green-bar paper. Every line has a gutter mark; hover a result to see the source line light up. A badge reads **"0 AI calls for this report"**.
3. **Drop a tampered report** (a hidden "HIV REACTIVE" on the referrer line, or a swapped MCV/MCH) → **Refused**. The ghost points at the exact line: *"I can't explain this line, so I won't export it."* This is the money shot.
4. **Drop an unknown layout →** "New layout. Ask the AI to draft a rule?" The AI drafts. **The gate attacks the rule**: a live counter of mutations (identity swapped, a unit deleted, a result smuggled onto a trusted line…). One gets through, the AI repairs, the counter shows 0 surviving. The judge types their name to approve: **the human is the final key**.
5. **Re-drop the same layout → Accepted with no AI.** Download FHIR, and open the **patient copy** (QR + plain-language page, with "verified from print job sha256 …").
6. **"How it's built" tab:** Kiro specs, hooks and steering screenshots, plus the property-test results.

**What must really work:** 2, 3, 4 (with a real LLM call, or a clearly labelled recorded run on the hosted site), 5, and the line gutter. **What can be thin:** settings, audit (a timeline list is enough), forwarding states (local only).

## 11. Architecture (independent of the prototype)
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **TypeScript full-stack** (e.g. Hono or Next.js API + React; engine as a pure TS package; **RE2 via `re2-wasm`/`node-re2`** for rule regexes; `fast-check` property tests; SQLite) | one language; strong Kiro TS support; **RE2 removes ReDoS from AI-written regex by construction** (linear time, a genuine safety improvement); easy single-service deploy; *clearly not a copy* of the Python prototype | must reimplement Decimal math (`decimal.js`); FHIR validation only offline (Java) | **Recommended if the team is comfortable in TS** |
| Python FastAPI + React | Hypothesis is mature; the team knows the domain code | two stacks; the strongest pull to replicate the prototype; the ReDoS defence needs timeouts | second choice |
| Python + HTMX | fastest | weaker Design score | fallback if solo |

**Deterministic:**
- decoding;
- layout match;
- extraction;
- line accounting;
- numeric-text rule;
- definitional checks;
- refusal reasons;
- FHIR mapping.

**AI only for:**
1. drafting a rule from 2 synthetic samples;
2. repairing it from gate failures;
3. optionally, a plain-language explanation of a refusal for the patient page. Templated text is preferable; avoid AI here.

**Omit:** an accounts system, multi-tenancy, queues and workers, the ABDM gateway, Windows installers, serial capture, a rule editor, analytics.

**Most impressive feature that is realistic:** the **live adversarial gate with a mutation counter**, plus the **line-accounting gutter**. Both are pure, deterministic, testable TypeScript and highly visible.

## 12. Prioritised execution plan (IST)
Assumes 1–2 people. If solo, apply the cuts marked ✂.

| When | Do | Kiro evidence produced |
|---|---|---|
| **Fri 27 (tonight)** | Decisions in §16. Request credits; send the clarification. Steering (product, tech, structure, safety). **Spec 1 requirements** (engine + properties) | steering files; a spec with EARS requirements |
| **Sat 28** | Spec 1 design and tasks → engine: rule format, layout match, extraction, line accounting, numeric rule, definitional checks. **Property tests** (refuse or exactly correct; every line explained). Hook: on engine save → run properties | tasks ticked; hook runs; PBT output (screenshot any bug PBT finds; that is the "Kiro surprised me" story) |
| **Sun 29** | Spec 2: gate + LLM draft + repair + approval log (hash-chained). Mutation catalogue (8–10 generic mutations) | spec 2; a hook on rule change → run the gate |
| **Mon 30** | Spec 3: UI slice. Drop zone, job view with gutter, decision panel, refusal ghost. API wiring | spec 3; screenshots |
| **Tue 1** | Onboarding stepper with live attack counter + approve. FHIR export + patient page. **Credit deadline 1:30 AM IST, 2 Dec.** ✂ solo: skip the patient page | |
| **Wed 2** | The "1998 lab system" printer app + RAW capture (local). Hosted deploy (replay mode). End-to-end test. Polish, accessibility, empty and error states | MCP (optional): HL7 validator as a tool Kiro calls to check FHIR, a genuine "Kiro extended" story ✂ |
| **Thu 3** | Video (script first; working product within 10 s; show a spec, a hook and steering on screen). Write-up (Kiro section answering every rules bullet). Blog | |
| **Fri 4 (IST day)** | **Buffer.** Submit by 20:00 IST. No features | |

## 13. Build lists
**Must-build:**
- the engine with property tests;
- refusal with line-level reason and gutter;
- the accepted path with a "0 AI calls" proof;
- the gate with a visible mutation counter;
- human approval;
- one live AI draft (or a labelled recording on the hosted demo);
- FHIR export;
- the hosted replay demo;
- the README, licence and `/.kiro`;
- the video.

**Should-build:**
- the patient-friendly verified page with QR;
- the local RAW 9100 capture with the 1998 printer app;
- the needs-confirmation state for free text;
- a hash-chained approval log view.

**Optional:**
- an MCP server wrapping the HL7 validator;
- forwarding to a printer with honest states;
- a dark/light theme toggle;
- a revocation UI.

**Do-not-build:**
- login or accounts;
- dashboards or analytics;
- ABDM sandbox or gateway;
- Windows installer;
- serial or analyzer capture;
- an OCR or image path;
- chatbots;
- multi-tenant settings;
- a rule editor;
- support for more than 3 layouts;
- re-running the full research benchmark in the app.

## 14. Biggest risks
| Type | Risk | Mitigation |
|---|---|---|
| **Competition** | Kiro usage judged insufficient | Kiro builds everything from now on. Commit per task. Show specs, hooks and steering in the video |
| Competition | Seen as "Faxi for printers" | Lead with "zero AI per document + proof gate". Different audience |
| Competition | Impact judged weak | Name the human, the cost and the risk; label it a hypothesis; ideally get 2 short real conversations by 2 Dec |
| **Technical** | LLM-drafted rules fail on stage | Pre-test the live layout. Have a labelled recorded fallback. The gate itself is deterministic |
| Technical | Line accounting too rigid, so false refusals in the demo | Curate demo inputs. Show one intentional refusal, not accidental ones |
| Technical | Rebuilding the engine takes longer than planned | Cut the analytes to 12 and the layouts to 3. Drop the patient page first |
| **Product** | Overclaiming safety | Every number labelled "synthetic". No clinical claims |
| **UX** | The UI looks like a dev tool | The Greenbar printout, the ghost microcopy, a 3-step happy path, no settings screens |
| Process | Planning paralysis in Kiro specs | 3 specs maximum; specs at the vertical-slice level; start tasks the same day |

## 15. Skeptical judge simulation
**Ways it loses:**
1. "Nice engineering, but who asked for this?" No evidence of users.
2. "The AI writes regex; ReportMiner does that."
3. "Kiro barely appears", or "most of this came from another tool".
4. "Demo shows a lot of panels; I'm not sure what happened."
5. "Synthetic benchmarks graded by the author."

**Ways it wins:**
1. The refusal moment is unforgettable and true.
2. A coherent Kiro meta-story (spec plus PBT, building spec plus PBT).
3. A polished, characterful UI (green-bar paper, a guiding ghost).
4. A judge can *try to break it* on the hosted demo.
5. A clear contrast with "AI on every document".

**Evidence judges would demand:**
- a live link;
- one tampered input they can submit themselves;
- Kiro artefacts in the repository;
- an honest prior-work note;
- property-test output.

**Impressive but unnecessary:**
- the forwarding state machine;
- ABDM profile validation details;
- mutation-testing scores;
- six layouts.

**Dangerous claims:**
- clinically safe;
- ABDM integrated or certified;
- "first to use AI for templates";
- "zero errors" (unqualified);
- "works with any legacy system";
- "tested on Windows or real printers".

**Three changes that most improve the position:**
1. Ship the golden path *in Kiro*, with visible Kiro artefacts, by Tue 1 Dec.
2. Make the gate and the refusal the centrepiece of the UI and video: an attack counter and a ghost-highlighted line.
3. Add the human payoff (the patient's verified report) and an honest, specific impact story.

## 16. Decisions to resolve before Kiro generates the first spec
1. **Team and hours** (sets the ✂ cuts).
2. **Stack: DECIDED 27 Nov: TypeScript + RE2.**
   - Engine: pure TS. API: Hono. UI: React + Vite. Database: SQLite via `better-sqlite3`.
   - Libraries: `decimal.js`, `vitest` + `fast-check`.
   - Regex: npm `re2` (node-re2, BSD-3), falling back to `re2-wasm` (Google, Apache-2.0, last published 2022) if the native build fails on the host.
   - The Kiro briefs in `kiro-bootstrap/` are updated accordingly.
3. **LLM provider and key handling** for drafting (Anthropic API or Amazon Bedrock), and whether the hosted demo calls it live (rate-limited, synthetic-only guard) or shows a labelled recorded draft.
4. **Demo domain fixed:** lab reports, about 12 analytes, 3 layouts. No clinical claims.
5. **The output payoff:** FHIR only, or FHIR plus the patient page.
6. **What, if anything, is reused from the research repository.** Recommended: no code; possibly the synthetic print samples as fixtures, disclosed.
7. **The free-text policy:** "needs confirmation", never auto-export.
8. **Send the organiser clarification now** (yes/no).
9. **Hosting target** for the replay demo.

## Recommendation, prioritised
1. **Today:**
   - request credits if not done;
   - send the clarification;
   - decide items 1–3 in §16;
   - create the Kiro steering;
   - write spec 1 requirements, with the two properties as the acceptance core.
2. **By Sun 29:** a Kiro-built engine passing its property tests, plus the gate with a mutation counter.
3. **By Tue 1:** the UI golden path (accept → refuse with ghost → onboard with attack → approve → accept with no AI → FHIR). If this is not working on 1 Dec, cut everything optional and polish only this path.
4. **Wed 2:** hosted replay demo. **Thu 3:** video and write-up. **Fri 4:** submit early.
5. **Throughout:** cite the research results only as background about the prior prototype, never as the app's results. Measure the app on its own.

**Sources:**
- https://kiroween.devpost.com/rules
- https://kiroween.devpost.com/updates/47909-meet-the-kiroween-judges
- https://kiroween.devpost.com/updates/47910-how-to-make-your-project-stand-out-from-the-graveyard
- https://kiroween-2025.devpost.com/project-gallery
- https://devpost.com/software/faxi-16iecy
- https://devpost.com/software/dark-ledger
- Earlier sources in reports 03, 19 and 20.
