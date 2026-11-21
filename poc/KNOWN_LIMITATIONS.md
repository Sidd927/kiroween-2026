# Known limitations (read before quoting any number)

## 1. The benchmark is synthetic and self-authored (biggest caveat)
- **Same author:** the same author (an AI agent) wrote the layouts, perturbations, validators, prompts and scoring. Blind spots are shared. The perturbation catalogue was known when the validators and the generic prompt guidance ("expect page breaks, long names, optional rows…") were written.
- **Too regular:** the layouts are machine-perfect. Real legacy output has free-text comments, interpretive notes, wrapped lines, mixed panels, software-version drift, special characters and operator typing.
- **Not clinically consistent:** the synthetic values are physiologically inconsistent (CBC indices don't follow Hb/Hct/RBC; differentials can exceed 100%; direct bilirubin can exceed total). The direct-LLM baseline noticed this; our system didn't.
- **Small sample:** 0 silent errors in 167 accepted documents only bounds the true rate below about 1.8% (95%). Per layout the bound is about 10%. The 13,000 property cases are larger but come from the same generator.
- **No real data:** no real lab report, real user or real legacy application was involved.

## 2. Known weaknesses found by our own tests
- **v1 silent-error bug (fixed in v2):** a damaged page-1 column header made the table start on page 2, so page-1 rows were silently dropped. The fix is generic, but it shows coverage logic must cover the **whole document**, not just a region.
- **Anchors match anywhere:** a redesigned report that still contains the old anchor text somewhere (e.g. on page 2) is recognised as the old layout. In 7 property cases the data was still correct, but this is luck, not design. Next step: position-bound anchors (e.g. "within the first N lines of every page").
- **Free-text lines are always rejected:** comment lines inside a results table (common in real reports) are rejected 100% of the time. That's safe, but in practice the refusal rate would be much higher than 0.8% until bindings learn comment patterns.
- **Rules only know labels they've seen:** an optional test absent from the samples causes rejections until a repair round adds it (layouts A and B).
- **Long names:** names overflowing the printed column are rejected (8 of 9 false rejections).
- **Validator V7 is over-strict:** it rejected a valid `0.00` bilirubin.
- **No clinical consistency rules:** e.g. MCHC ≈ Hb/Hct×100, differential sum ≈ 100, DBIL ≤ TBIL. These would catch column misalignment and must be added to the domain pack, together with a realistic generator.
- **Date format confusion is not detectable by validators:** DD/MM vs MM/DD with day ≤ 12 is undetectable by validation. In this run the AI inferred layout F's format correctly only because a generation sample had day > 12. A rule generated from samples that all have day ≤ 12 could be silently wrong for every document. Mitigation for the MVP: require a disambiguating sample, or human confirmation of the date format during approval.
- **The property test fails on purpose:** it fails on the 3 unsafe accepts with correct data. We did not weaken it.

## 3. Rule generation
- **Simulated approval:** human approval is simulated. No human reviewed the 6 active rules.
- **Labelled regression set:** the gate needs an operator-verified regression set (8+ labelled documents per layout plus defect examples). Labelling is a real onboarding cost that the PoC did not measure.
- **One model:** only one model was tested (`claude-sonnet-5-5`, via the Claude Code CLI on the user's account). Results may differ with other models or prompts.

## 4. Print capture
- **Windows untested:** the **Windows 11 VM + Generic / Text Only driver path was not tested** (no VM or Windows image on this machine). We don't know what the driver does to the bytes (line endings, Notepad headers, page formatting) or whether the rules survive that.
- **Physical printer untested:** forwarding was verified only to a **test receiver** (`fake_printer.py`), and once through CUPS. No paper was printed.
- **CUPS ran without a printer driver:** the CUPS test used a queue with no driver, because macOS rejected the "raw" model. It is a real spooler (queueing, retry, backend), but not Windows.
- **Store-and-forward delay:** printing waits until the whole job is received, so a job interrupted mid-transfer isn't printed at all, whereas a real printer would print the partial job.
- **Text only:** only plain text and ESC/P are supported. PostScript, PDF, PCL and raster are forwarded but not extracted.
- **Duplicate detection is weak:** detection uses the SHA-256 from the same client within 10 minutes. An intentional reprint and a spooler retry are indistinguishable.
- **No security hardening:** no TLS, no authentication, no encryption at rest. The listener binds to localhost by default.

## 5. FHIR / ABDM
- **What was done:** only **generic R4** and **ABDM profile** validation (`ndhm.in#6.5.0`). No ABDM sandbox, gateway, consent flow, HIP linking or certification.
- **Placeholders:** `DiagnosticReport.conclusion` is required by ABDM but absent from printed reports, so a labelled placeholder is used. Organisation and patient identifier systems are `urn:spoolgeist:poc:*`, not HFR or ABHA.
- **Timezone:** the timezone is site configuration (+05:30), not read from the document.
- **LOINC mapping:** the 20 LOINC codes resolve on tx.fhir.org, but a human must confirm that each code is the right concept for the lab's method and specimen.

## 6. Baseline fairness
- **Prompt:** the baseline prompt strongly encouraged refusal ("if you are not certain…"). A less cautious prompt would accept more and might make value errors. That variant was not tested.
- **Unscored documents:** 8 of 128 baseline documents went unscored (6 blocked by the pre-send guard, 2 unparseable).

## 7. Kiro
- **Not built in Kiro:** the PoC was built by Claude Code. **No engineering task was performed in Kiro** (Kiro isn't installed here).
- **Untested artifacts:** the `.kiro/` spec, steering and two hooks are authored artifacts. They haven't been loaded in Kiro, and the hook file format is unverified there.
- **Implication:** the hackathon scores Kiro usage, so the MVP should be built *in* Kiro from these specs. That makes the Kiro evidence genuine and adds effort (see DECISION.md).
