# PoC decision report: Spoolgeist (21 Nov 2026)

## Recommendation: **MODIFY**
Keep the technical core: print capture, AI-written declarative rules, the fail-closed interpreter, independent validators, the property test, and FHIR. **Change the claim and the demo.** The central comparative story ("direct LLM extraction silently gets it wrong; we don't") **was not supported by our own baseline**. Rebuild the MVP inside Kiro so that Kiro usage is real.

This is a technical recommendation only. It doesn't settle the market question (Gate M, interviews), which is still open, or the Windows capture question, which is still untested.

---

## The 10 questions

### 1. Does the print-capture approach work?
**Partly proven.**
- **Proven:** RAW/AppSocket (port 9100) capture works with a real OS spooler. macOS CUPS printed 3 synthetic jobs (plain text, ESC/P, multi-line) to our listener with **byte-identical** SHA-256, and all 3 were parsed and accepted with no AI. A Python RAW client passed 9/9 capture experiments.
- **Not proven:** the **Windows 11 + Generic / Text Only** path that the product depends on wasn't tested (no VM here; runbook ready). What that driver does to the bytes is the biggest open capture question.

### 2. Can captured jobs be preserved and forwarded?
**Yes, to a test receiver. Not tested with a physical printer.**
- **Byte-identical:** jobs are persisted before anything else and forwarded byte-identical, including ESC/P control codes and PostScript.
- **Printer outage:** the job was kept and delivered exactly once after recovery.
- **Listener outage:** CUPS showed "printer not responding", retried, and delivered once about 24 s after restart.
- **Bad transfers:** interrupted, oversize and idle transfers were quarantined and neither printed nor parsed.
- **Duplicates:** printed twice, data emitted once.
- **Not tested:** no paper was printed; the forward target was `fake_printer.py`. The Windows spooler's retry behaviour is untested.

### 3. Can AI generate reusable parsers for unseen layouts?
**Yes, on this synthetic benchmark.**
- **6/6 layouts activated:** 4 on the first attempt, 2 after one repair, because an optional test was absent from both samples.
- **Unseen layouts:** D–F were generated after the code freeze, from 2 samples each, in 12–15 s and 1 call each.
- **Varied formats handled:** box tables, two results per line, units inside test names, and US MM/DD dates.
- **Reused without AI:** 167 later documents were processed with **0 AI calls**.
- **Cost:** the whole rule-generation phase used 8 LLM calls and US$0.50.
- **Caveat:** the layouts are far more regular than real legacy output (see KNOWN_LIMITATIONS §1).

### 4. Does deterministic validation meaningfully catch incorrect extraction?
**Yes, and it was necessary, but it isn't sufficient alone.**
- **Validators off:** the same rules produce **30 silent errors** on the held-out set (implausible values, conflicting duplicates, inconsistent flags).
- **Coverage rule:** the "every character of the table must be parsed" rule caught the largest group of defects.
- **Not enough:** the property test found **2 silent errors** in the frozen v1 system. A damaged column header on page 1 made the table start on page 2, and page-1 rows were silently dropped. The validators couldn't see missing rows. A generic v2 fix (reject result rows outside the parsed table) gave **0 silent errors in 13,000 fresh cases**.
- **Gaps that remain:**
  - anchors can match anywhere in the document;
  - no clinical consistency rules;
  - DD/MM vs MM/DD confusion is undetectable when the day is ≤ 12.

### 5. Can the system generate valid FHIR R4 output?
**Yes, up to ABDM *profile* validation.**
- **Generic R4:** 167/167 bundles have 0 errors.
- **ABDM:** 167/167 bundles have 0 errors against the `ndhm.in#6.5.0` profiles. A negative control produced 24 profile errors, which proves the profiles were really enforced.
- **Real validation was needed:** the first run found 18 errors per bundle (missing timezone, wrong LOINC display names). All 20 LOINC codes resolved on tx.fhir.org.
- **Placeholder:** the ABDM-required `conclusion` gets a labelled placeholder, because printed reports have none.
- **Not done:** no sandbox, no certification, no consent flow.

### 6. What are the measured error and refusal rates?
Held-out set, 326 documents:

| Measure | Result |
|---|---|
| **Silent errors** | **0/167** accepted (95% upper bound 1.8%) |
| Invalid documents accepted | **0/150** |
| Layout recognition | **198/198** |
| Critical-field accuracy | **1,887/1,887** |
| Refusal, clean supported docs | **1/120 (0.8%)**; unseen layouts **0/60** |
| False rejection, all valid docs | **9/176 (5.1%)**: 8 long names, 1 over-strict validator |
| Latency | 0.29 ms median per document |
| Property test v1 | **2 silent errors in 3,000** cases (fixed) |
| Property test v2 | **0 in 13,000** cases; 7 unsafe accepts, all with correct data |

These are prototype numbers on self-authored synthetic data, not evidence of clinical safety.

### 7. What failed?
1. **v1 silently dropped page-1 rows** after header damage. It was found only by the property test, written after the benchmark. The held-out benchmark alone would have declared perfection.
2. **The differentiating claim failed:** the direct-LLM baseline (same model, refusal allowed) made **0 wrong-value errors** too. It refused 29/58 valid docs, mostly because it noticed that my synthetic blood counts are physiologically inconsistent, which my validators didn't check.
3. **Anchor recognition accepted a redesigned report** that still contained the old lab name on page 2.
4. **Free-text comment lines** in tables are always rejected. That's safe, but it will hurt real-world refusal rates.
5. **Long names and a `0.00` result** were falsely rejected.
6. **First FHIR output was invalid** until checked with the official validator.
7. **Not built in Kiro.**

### 8. What remains unproven?
- **The Windows path:** Windows Generic / Text Only capture, the Windows spooler's retry behaviour, and LPT/DOS-era printing.
- **Physical-printer forwarding.**
- **Real data:** behaviour on **real** legacy reports (comments, drift, multi-panel output, typos).
- **Date safety:** safety against date-format confusion when the samples don't disambiguate.
- **Onboarding cost:** labelling the regression set, and real human approval of rules.
- **Advantage over a careful LLM:** any accuracy or safety advantage. Only cost, latency, determinism and runtime privacy are shown.
- **The market:** whether anyone has this problem and would install a local agent (Gate M; no interviews yet).
- **Kiro:** whether the `.kiro` hooks load in Kiro, and whether IDE property-based testing works for this property.

### 9. What is the realistic remaining development effort?
Human hours for an MVP built **in Kiro**, reusing this PoC as the reference design and test corpus:

| Work | Hours |
|---|---:|
| Port engine, validators, gate and property test into Kiro via spec (genuine Kiro evidence) | 15–20 |
| Clinical consistency validators + realistic generator (indices, differentials, bilirubin, comments) | 6–8 |
| Position-bound anchors, comment-line handling, long-name handling, date-format confirmation | 6–8 |
| Minimal review UI (queue, original with failing spans highlighted, approve or reject a rule) | 15–20 |
| Rule onboarding flow (synthetic twin, labelling about 8 docs, gate report) | 8–12 |
| Windows VM capture runbook W1–W5 + text-mode "1998" demo app + recorded capture | 8–12 |
| FHIR polish (narratives, local HAPI destination) | 4–6 |
| Web demo (upload path + recorded capture), basic security | 8–10 |
| Write-up, video under 3 minutes, blog, Kiro story | 15–20 |
| Buffer | 10 |
| **Total** | **≈ 95–125 h** |

That is about **2 people × 4–5 h/day** from 22 Nov to 4 Dec. **Not realistic solo.**

### 10. Is Spoolgeist still worth pursuing for Kiroween?
**Conditionally yes.** The technical risk that worried us most, whether AI-written rules can be activated safely and reused without AI, was retired on synthetic data faster and more cheaply than planned. The weak points are now:
- **Positioning:** we can no longer claim to beat a careful LLM on accuracy.
- **Market:** still unvalidated.

**The stronger, evidence-backed pitch:**
> **"AI writes the rule once, from synthetic look-alikes. After that: zero AI, zero per-document cost, sub-millisecond, fully offline, auditable by hash, and fail-closed, proven with property-based tests that already caught a real silent-error bug."**

In healthcare, *not* sending every patient report to a cloud model, and getting the same answer every time, are themselves the value. The property-based test finding a silent bug is an unusually good, true Kiro story: specs plus PBT.

## Conditions before committing (by Tue 24 Nov)
1. **Windows runbook W1–W4:** if Generic / Text Only output breaks the rules in ways one repair round can't fix, fall back to "CUPS/RAW capture + upload" and say so.
2. **Gate M:** at least 2 of 5 interviews.
3. **Team decision to build the MVP in Kiro** (accepting about 15–20 h of rework for genuine Kiro evidence).
4. **Drop from the demo and pitch:**
   - "LLM gets it wrong";
   - any claim of clinical safety;
   - ABDM integration or certification.

If condition 1 fails *and* condition 2 fails, PIVOT. Re-audit Necromancer for 2 hours as planned in report 15.

## What was NOT done (by design)
No product application, UI, deployment, authentication, real data, Windows image download, physical printing, or modification of any existing project. The research reports were changed only to add a pointer to this file.
