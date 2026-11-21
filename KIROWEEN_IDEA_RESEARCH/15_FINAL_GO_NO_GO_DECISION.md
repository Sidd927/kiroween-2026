# 15 — Final GO / MODIFY / PIVOT Decision

> 🧪 **PoC completed 21 Nov 2026. See `poc/DECISION.md`.** Technical gate met on synthetic data (0 silent errors held-out; a property test found and fixed one silent-error bug; FHIR valid against ndhm.in 6.5.0). The direct-LLM baseline also made no value errors, so the "LLM gets it wrong" demo claim is dropped. Windows capture and the market gate are still open. Recommendation: MODIFY.

## Decision: **MODIFY, with a hard 48-hour gate**

Keep the core (zero-change print capture → AI-written rule → deterministic extraction → FHIR). **Change the value proposition, claims and scope:**

1. **Drop** "AI-generated parsers are novel." Astera already ships it [S40][S41]; Evaporate published it [S42].
   **New thesis: *"never silently wrong".*** AI-written rules are only activated after independent held-out and perturbation tests prove they extract correctly or abstain. We measure and publish the silent-error rate against direct LLM extraction.
2. **Drop** "labs can't join ABDM without structured data." The ABDM IG accepts a PDF in `presentedForm` [S44].
   **New healthcare problem:** documented manual-transcription errors when printed results are re-typed (3.7% discrepancy, 0.5% potentially dangerous [S60]), plus legacy HMIS without API layers [S19]. Small-lab demand is presented as *being validated*, not as fact.
3. **Narrow scope:** one vertical (lab reports); raw-text and text-PDF only; capture through Windows' built-in drivers plus a RAW listener (no custom Windows code); FHIR up to **ABDM profile validation**, not sandbox and not certification; **no public 9100 endpoint**.
4. **Gate by Tue 24 Nov, morning** (`14`):
   - **Technical gate:** 0 silent errors and ≤ 15% abstention on held-out and perturbed synthetic documents; ≥ 2 of 3 layouts activated within 3 repair rounds; bundle validates against `ndhm.in#6.5.0`.
   - **Market gate:** ≥ 2 of 5 interviews confirm print-only output or double entry, and acceptance of a local agent.
   - Technical gate fails → **PIVOT**. Market gate fails but technical passes → **continue** with Impact framed honestly (expect about 11–12/20 on Impact).

### Why not GO
The two pillars of the original recommendation, innovation and market, did not survive verification (`10` Part A). Building the original pitch would have exposed us to a judge who knows Astera, or who knows that ABDM accepts PDFs.

### Why not PIVOT (yet)
- The **technical** case survived. Capture is achievable with built-in Windows drivers [S55]; FHIR validation against the real ABDM IG is achievable [S57][S58]; the privacy architecture is sound.
- None of the shortlisted alternatives is clearly better. All scored about 64–66, and **those scores were not re-audited with the same rigor, so they are probably inflated too** (the same bias applies to them).
- Spoolgeist keeps the best feasibility, the best demo, and an unusually natural fit with Kiro's property-based testing ("abstain or exactly correct" is a property).
- Pivoting means another day of ideation with no guarantee of something better.

---

## Phase 3: Positioning test
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Healthcare-specific legacy integration product | Clear story and judge empathy; FHIR is a concrete output | Small-lab market not evidenced; ABDM accepts PDFs; competes with cheap LIS | **Use for the product story and demo**, with honest framing |
| B. Universal print-to-data engine, demonstrated with healthcare | Bigger total market on paper | **Head-on with Astera, Monarch, VeryPDF, Sensible**; generality adds scope with no judging benefit; impact gets diluted | **Reject** |
| C. Domain-specific document intelligence, healthcare first | Wider input (PDFs, scans) | Becomes generic document AI, a crowded field; **loses the Resurrection hook** (live capture of dead software); OCR breaks determinism | **Reject** as the positioning |

**Your hypothesis was mostly right, with one refinement.** Reusability belongs in the **architecture**: a domain pack is a dictionary plus validators plus a destination mapper, kept as a clean seam. It does **not** belong in the features or the pitch. Build exactly one domain pack. A universal engine gives no competitive advantage here; it only adds scope.

## Phase 7: Competition re-evaluation
| Question | Answer |
|---|---|
| Does it resurrect obsolete technology? | Yes, if the demo shows a text-mode or DOS-era app printing via LPT/RAW. Otherwise it reads as ETL |
| Is the category fit obvious? | **Medium.** Less obvious than Faxi's fax machine; it depends on the visuals |
| Differentiated from previous Resurrection winners? | Yes: business-to-business, a verification-centred engine, no consumer bridge |
| Does the demo communicate the innovation immediately? | Only if we show the **abstention moment** (bad print → refused) next to direct LLM extraction confidently getting it wrong |
| Substantial Kiro usage? | **Yes:** specs; PBT for "abstain or correct" (IDE); hooks (regression corpus, patient-data guard, FHIR validation); steering for untrusted input; MCP for docs; optional small Power |
| Exceptional on all five criteria? | **No.** Realistically strong on Tech and Presentation, average-to-good on Design, Impact and Innovation |

**Revised scorecard (/20 per criterion):**

| Criterion | Original pitch (re-scored honestly) | Modified Spoolgeist | Previous estimate (09) |
|---|---:|---:|---:|
| Potential Impact | 11 | 12 | 15 |
| Technological Implementation (Kiro) | 17 | 17 | 17 |
| Design | 14 | 14 | 15 |
| Innovation | 11 | 13 | 16 |
| Presentation | 15 | 15 | 16 |
| **Total** | **68** | **71** | 79 |

Internal: feasibility 8 → **7** (effort ≈125–135h, not 95h); differentiation 8 → **5**; demo reliability **8**.

**Realistic competitive reading:** a credible contender for **Best Student Project: Resurrection**, an outside chance at Best Resurrection, and **unlikely** to place top-3 overall. I am lowering my previous verdict.

## Phase 8: Red-team arguments and what survives
| Attack | Strength | Resolvable? |
|---|---|---|
| "Not innovative: Astera AGL does AI templates for printed reports" | **Strong** | Partly. Reframe to measured verified abstention. Residual weakness remains (**fundamental, but limited**) |
| "Market too small: small labs buy a ₹5k LIS" | **Strong** | Not within 13 days. Mitigated with honest framing and interviews (**fundamental for business, tolerable for a hackathon**) |
| "Existing software solves it: PDF + ABDM-enabled LIS" | Strong for ABDM linking | Resolved by **dropping** that claim |
| "Printing infrastructure too complicated" | Weak | **Resolved:** built-in drivers + RAW listener; no driver development |
| "Parser unreliable" | Medium | **Resolvable and measurable:** gate + abstention |
| "FHIR overambitious" | Weak | **Resolved:** levels 1–2 only, validator output shown |
| "Healthcare privacy makes it impractical" | Medium | **Resolved for the MVP:** local-first, synthetic twins, no LLM at runtime |
| "Demo fragile" | Medium | **Resolved:** recorded VM capture plus web upload; cached active rules; no live LLM dependency |
| "Another category or concept wins more" | Medium | **Unknown.** A design-led Costume entry may outscore us on Design and Presentation. Not provable either way |

**Spoolgeist survives in modified form,** because none of the *technical* attacks are fundamental and the fundamental attacks (innovation, market) can be handled through honest positioning that judges can verify. It doesn't survive as the "clear winner" the first report claimed.

---

## Required answers
- **Strongest reason to build:** technically sound and buildable in time, a vivid demo (old app prints → verified FHIR, bad input refused), and an unusually deep, natural use of Kiro (PBT for an "abstain or exactly correct" property, hooks, specs, steering).
- **Strongest reason not to build:** the headline innovation exists commercially (Astera AGL, 2026) and the healthcare buyer isn't evidenced. Small labs have cheap modern alternatives, and ABDM accepts PDFs.
- **Most dangerous technical assumption:** LLM-generated declarative rules generalise to *unseen* documents of the same layout with **zero silent errors** at ≤ 15% abstention.
- **Most important market assumption:** some facilities have printed output as their only practical data path, re-typing or lack of structured data is a pain they actually feel, and they'd accept a local agent. **[UNVALIDATED]**
- **Minimum convincing demo (≈2:30):**
  1. A text-mode "legacy lab" app in a Windows VM prints.
  2. The job is captured and forwarded byte-for-byte (matching hashes shown).
  3. First time: a rule is generated, a perturbation test fails, it is repaired, then activated.
  4. Second print: parsed with 0 LLM calls; an ABDM-profile-validated FHIR bundle is produced (validator output on screen).
  5. A corrupted print (unit swapped) is **refused** into review, while direct LLM extraction silently accepts it.
  6. A benchmark card: silent errors Spoolgeist 0 vs baseline X%.
  7. The Kiro story.
- **Realistic development effort:** PoC ≈18h (most of it reused), MVP ≈125–135h in total. **Two people are realistically required**; a solo builder must cut the dashboard to a minimal review UI.
- **Critical path:** PoC gates (24 Nov) → interpreter + validators → rule generator with held-out/perturbation tests → FHIR builder + validator_cli → review UI → recorded capture demo → video (record 2 Dec) → submit 4 Dec 18:00 IST.
- **Biggest risks:**
  1. Gate T fails (rules don't generalise).
  2. Impact judged weak.
  3. Innovation judged incremental by an informed judge.
  4. Windows VM/networking problems on the M5.
  5. Scope creep (IPP, PostScript, Power, Crew app).
- **Final competition strategy:**
  - **Category:** Resurrection. Also flag Best Student Project: Resurrection (all members must be students), Best Demo (automatic), Bonus Blog, and Social Blitz.
  - **Skip:** the Crew App bonus and Startup prize. Build the Power only if ahead of schedule on 1 Dec.
  - **Pitch:** "Dead software, trustworthy data. AI writes the rule; math decides whether it may speak."
  - **Aim:** the student prize first, the category prize second.

## Five things you need to verify yourselves (cannot be done by research)
1. **Real users:** 5 conversations (labs, clinics, small hospitals) using the script in `11`. Does print-only output or double entry exist, and would they accept a local agent?
2. **The capture chain on your Mac:** UTM Windows 11 ARM VM → Generic/Text Only → RAW port → Mac listener works; also what Windows' IPP class driver actually sends (PDF or PWG Raster) to `ippeveprinter`.
3. **Gate T numbers** from the PoC: silent-error rate, abstention rate, layouts activated, and a direct-LLM baseline.
4. **ABDM profile validation:** `validator_cli.jar -ig ndhm.in#6.5.0` runs on your machine and our bundle passes; also hand-verify every LOINC code in the dictionary on loinc.org.
5. **Kiro access from India:** credits approved, IDE PBT available, preferred models selectable, hooks behaving as documented. Also confirm every teammate's student status.

## Fallback if Gate T fails (24 Nov)
Pivot to **R3 Necromancer** re-scoped as a Kiro Power: verified migration of abandoned code using the old runtime as a test oracle. It reuses the "verify, don't trust" core and the PBT harness, and needs no market validation. Its weaknesses are known (abstract impact, research competition [S34]); expect about 64–66/100. **Re-audit it for 2 hours before committing.** If neither passes scrutiny, spend no more than half a day on fresh ideation. After 25 Nov, execution quality matters more than idea quality.

## Approval requested
To run the 18-hour PoC in `14`, I need your approval to write isolated experiment code (a `poc/` folder or a separate scratch repo; synthetic data only; no changes to any existing project).
