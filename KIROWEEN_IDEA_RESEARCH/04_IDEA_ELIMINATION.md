# 04 — Adversarial Elimination (Round 1)

I judged every idea as a skeptical judge who has already seen hundreds of AI hackathon projects, including the 747 entries from Kiroween 2025.

Each idea gets six lines:

- **Build:** strongest reason to build it
- **Don't:** strongest reason not to
- **Assume:** the most dangerous technical assumption
- **Compete:** the biggest competitive weakness
- **Feas:** the biggest feasibility risk
- **Lose:** the most likely reason it would lose

**Verdicts:**
- REJECT: weak or not differentiated
- REWORK: needs a substantial change
- HOLD: promising, but evidence or feasibility is short
- SHORTLIST: strong enough to survive

Checks applied to every idea: Is it a wrapper? Has it been built already? Does it need data we can't get? Can we demo it live? Does it fit the category? Can another team copy it easily? Does Kiro matter to it?

---

| # | Idea | Verdict |
|---|---|---|
| R1 | Spoolgeist | **SHORTLIST** |
| R2 | Lipi Lazarus | **HOLD → finalist (as the high-variance bet)** |
| R3 | Necromancer | **HOLD → finalist** |
| R4 | Lazarus Lab | REJECT |
| R5 | Dataset Necropolis | REJECT |
| R6 | HyperStack | REJECT |
| R7 | Afterlife | REJECT |
| R8 | Ceefax-over-FM | REJECT |
| F1 | Ghost Trials | **HOLD → finalist** |
| F2 | Sand Sentinel | REJECT |
| F3 | Spreadsheet Exorcist | REWORK → merged into R3 |
| F4 | HeatShield | REJECT |
| F5 | Community Radio Newsroom | REJECT |
| F6 | MissedCall Civic | REJECT |
| F7 | Leak Listener | REJECT |
| F8 | Second Sight Mesh | REJECT |
| F9 | Tactile | HOLD (parked, not a finalist) |
| F10 | RTI Copilot | REJECT |
| S1 | Leakproof | REJECT |
| S2 | Beckn Bones | REJECT |
| S3 | Grimoire | **HOLD → finalist** |
| S4 | Provenance Kit | REWORK → absorbed into R1 |
| S5 | A11y Ward | REJECT |
| C1 | Patient Zero | **HOLD → finalist** |
| C2–C5 | Costume others | REJECT |

---

## Resurrection

**R1 Spoolgeist: SHORTLIST**
- Build: proven demand (Monarch has existed since 1990), a timely policy driver (ABDM legacy barrier, DHIS money), and a demo that is a visual "magic moment". The AI does real work, and the "LLM as a compiler" approach answers the wrapper criticism.
- Don't: it could read as plumbing or as "document AI" to judges who skim.
- Assume: that the LLM can reliably write correct declarative parsers from 1–3 sample printouts. (I believe this is plausible because print streams are clean, exact text, but it has to be proven by day 6.)
- Compete: report mining and receipt emulators exist, so the novelty sits in the combination plus the verification step.
- Feas: the long tail of print formats (PCL, raster). Mitigation: limit scope to text, ESC/POS and PostScript/PDF.
- Lose: impact claimed but not shown with real users.

**R2 Lipi Lazarus: HOLD (finalist as the high-variance option)**
- Build: the strongest human story in the whole catalog, with documented government pain.
- Don't: KhatianDoc shows the core capability is missing in today's models. Government (Bhashini) and IIT Roorkee are already on it.
- Assume: that we can reach usable accuracy with 2,043 images plus synthetic font data in under 10 days.
- Compete: an institutional effort by a government AI agency.
- Feas: data licensing (non-commercial terms likely [U]), no Kaithi corpus, training time on Colab.
- Lose: the live demo produces wrong readings and judges notice.

**R3 Necromancer: HOLD (finalist; F3 merged in)**
- Build: the best possible fit with Kiro's PBT, hooks, Powers and MCP.
- Don't: an abstract audience, a dry demo, and close to the sponsor's own modernization products.
- Assume: that we can generate meaningful inputs for arbitrary library APIs.
- Compete: an academic field that is moving fast [F].
- Feas: Docker legacy runtimes, plus the spread of APIs we'd need to support.
- Lose: Impact and Design scores stay average.

**R4 Lazarus Lab: REJECT**
- Build: the reproducibility crisis is real.
- Don't: running arbitrary repos needs compute and sandboxing we don't have, and agent success rates are low [U].
- Assume: the agent can set up environments reliably.
- Compete: research benchmarks and existing platforms.
- Feas: GPU or long-running jobs.
- Lose: the demo fails or looks cherry-picked.
- *Killed: we can't run the core loop reliably on our budget.*

**R5 Dataset Necropolis: REJECT**
- Build: easy to build.
- Don't: low wow factor, and link-rescue tools exist.
- Assume: archived copies exist for the dead links.
- Compete: IABot and Perma.cc [U].
- Feas: low risk.
- Lose: feels like a script, not a product.
- *Killed: weak on Innovation, Design and Presentation.*

**R6 HyperStack: REJECT**
- Build: nostalgic and lovable.
- Don't: the AI app-builder market is saturated.
- Assume: people want card stacks.
- Compete: Lovable, Bolt, Decker.
- Feas: OK.
- Lose: "this is just an AI app builder".
- *Killed: not differentiated.*

**R7 Afterlife: REJECT**
- Build: an emotional "they killed my device" story.
- Don't: needs physical bricked devices, and the general "AI writes integrations" claim can't be shown honestly.
- Assume: local protocols can be discovered.
- Compete: Home Assistant community integrations.
- Feas: hardware.
- Lose: the demo is staged on one device.
- *Killed: demo honesty and hardware.*

**R8 Ceefax-over-FM: REJECT**
- *Killed: broadcasting needs a licence and hardware; judges can't test it.*

## Frankenstein

**F1 Ghost Trials: HOLD (finalist)**
- Build: public data, a timely hook (FDA enforcement in 2026), and AI is genuinely needed for aligning outcomes semantically.
- Don't: RegCheck and the npj tool already show the approach works, so our innovation is mostly UX. The audience is narrow.
- Assume: CTRI can be parsed.
- Compete: academic tools with published accuracy numbers.
- Feas: moderate.
- Lose: Innovation is scored low ("this exists in medRxiv").

**F2 Sand Sentinel: REJECT**
- Build: visual maps, environmental impact.
- Don't: needs lease boundaries that probably aren't public, and there's no ground truth.
- *Killed: depends on data we can't get.*

**F3 Spreadsheet Exorcist: REWORK → merged into R3**
- *The same "old system as reference oracle + property-based equivalence" core; kept as a possible R3 domain.*

**F4 HeatShield: REJECT**
- Build: high impact.
- Don't: a common dashboard pattern that likely competes with big-tech tools [U], and it can't be validated in 13 days.
- *Killed: low differentiation and heavy data work.*

**F5 Community Radio Newsroom: REJECT**
- *Killed: weak fit with Frankenstein, and risky local-language TTS quality.*

**F6 MissedCall Civic: REJECT**
- *Killed: a crowded LLM-over-IVR wrapper with telephony cost and regulatory friction.*

**F7 Leak Listener: REJECT**
- *Killed: hardware and no data.*

**F8 Second Sight Mesh: REJECT**
- *Killed: recycles our own earlier Anchor project (edge CV); the brief forbids that.*

**F9 Tactile: HOLD (parked)**
- Build: strong accessibility impact.
- Don't: the output is physical, and I haven't gathered evidence yet.
- *Parked: worth a deeper look after the hackathon.*

**F10 RTI Copilot: REJECT**
- *Killed: an LLM wrapper.*

## Skeleton Crew

**S1 Leakproof: REJECT**
- Build: our data-science credibility.
- Don't: `unleak` already ships an agent skill plus a write hook for coding agents [F].
- *Killed: already built, exactly where we would aim.*

**S2 Beckn Bones: REJECT**
- *Killed: the official Beckn-ONIX and the Google DPI Accelerator cover it [F].*

**S3 Grimoire: HOLD (finalist)**
- Build: maximum Kiro depth, and could win Best Kiro Crew App.
- Don't: the audience is only Kiro Crew developers, and Crew APIs are 3 months old.
- Assume: the Crew App APIs are stable and well enough documented.
- Compete: official examples.
- Feas: documentation gaps.
- Lose: Impact scored as "only matters to Kiro users".

**S4 Provenance Kit: REWORK → absorbed into R1**
- *Too generic alone; its "every value carries its source" idea becomes part of Spoolgeist's Binding engine.*

**S5 A11y Ward: REJECT**
- *Killed: low novelty against existing linters.*

## Costume Contest

**C1 Patient Zero: HOLD (finalist; it is the best of the Costume ideas)**
- Build: the spooky metaphor carries real meaning ("contagion" is the function), and public data is easy to get.
- Don't: Feet of Clay and RetractoBot cover first-order flags, and a 2026 study says the signal is weak [F].
- Assume: we can get citation-context text for most papers.
- Compete: established integrity tools.
- Feas: OK.
- Lose: Innovation and Impact.

**C2 Haunted Codebase / C3 Graveyard / C4 Phish House / C5 Séance Desk: REJECT**
- *Killed: derivative (2025 winners, mature tools) or inheriting R2's feasibility problem.*

---

## Six finalists going to Round 2
1. **R1 Spoolgeist** (Resurrection)
2. **R2 Lipi Lazarus** (Resurrection, high-variance)
3. **R3 Necromancer** (Resurrection / Kiro Power)
4. **F1 Ghost Trials** (Frankenstein)
5. **S3 Grimoire** (Skeleton Crew)
6. **C1 Patient Zero** (Costume Contest)

All four categories are represented, so the final choice isn't biased toward one category by default.
