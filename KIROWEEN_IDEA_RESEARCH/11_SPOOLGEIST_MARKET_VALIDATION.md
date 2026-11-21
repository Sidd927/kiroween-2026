# 11 — Spoolgeist: Market Validation

**Bottom line:** I found **no direct evidence** that Indian small diagnostic labs run legacy software that can only print and has no export. The evidence I did find points the **other way**. Every market claim below is labelled; **[UNVALIDATED]** means only interviews can settle it.

---

## 1. What small Indian labs actually use

| Finding | Evidence | Implication |
|---|---|---|
| Cheap, modern lab software (LIS) is everywhere | Labsmart ₹4,999–9,999/yr (reports by WhatsApp/SMS/email); ClinikPe from ₹4,999/yr with analyzer integration; Drlogy claims 30,000+ labs; EasyPatho ₹12,000/yr [S47] | Replacing software costs **less than a month's rent**. "Zero-change integration" loses most of its value when change is this cheap. |
| The un-digitised tail uses **Word/Excel templates and paper registers**, not legacy apps | A vendor says "Many small labs run on Excel, a Word report template and a paper register" (1–2 technicians, 20–120 patients/day). Free Word/PDF templates are offered by several vendors [S59] (vendor marketing, not surveys) | Their problem is **manual typing and no structured data at all**, not "data trapped in a legacy app". A print-capture tool *could* structure their Word printouts, but they'd more likely buy a ₹5k LIS that also does billing and WhatsApp. |
| PDF export already exists | All modern LIS deliver PDFs; ABDM accepts a PDF in `DiagnosticReport.presentedForm` [S44][S45] | **PDF export already solves ABDM linkage** for anyone with a modern LIS. |
| ABDM is reaching small facilities through policy | 100 Microsites programme deploys ABDM-enabled HMIS to small private clinics and labs; Punjab and Bihar microsites hit their targets [S46]. 450+ integrated solutions; 105 crore linked records; about 2.72 lakh facilities on ABDM-enabled software (vendor blog citing an MSG meeting [S48][U]) | Government and vendors are actively closing this gap. |
| Legacy HMIS without APIs is a real barrier for **hospitals** | HMPI: "Many facilities run proprietary software with no ABDM-compliant API layer"; INR 30–50 lakh integration costs for mid-size providers [S19] | The real legacy pain sits in **mid-size hospitals**. They have IT staff and databases, and integrators there typically connect at the database level [U], which competes with print capture. |
| Manual transcription errors are well documented | 3.7% of manual entries differed from interfaced values; 0.5% potentially dangerous (JAMIA 2019); 0.83–5% across lab studies [S60] | The **strongest evidence-backed problem** in this space is *re-typing printed results*, not missing APIs. |

## 2. Answers to Phase 4's questions
| Question | Answer | Status |
|---|---|---|
| What software do small labs use? | Low-cost cloud or desktop LIS, or Word/Excel templates | Partly evidenced (vendor sources) |
| Do legacy apps still rely heavily on printing? | Yes, where they exist. Whether they exist at scale in Indian small labs is unknown | **[UNVALIDATED]** |
| Do they lack APIs? | Hospital HMIS often do [S19]; small-lab LIS mostly export PDFs and many integrate with ABDM | Partly evidenced |
| Does PDF export already solve the problem? | **Yes for ABDM linking**; no for structured analytics or decision support | Evidenced [S44] |
| Do existing ABDM integrations make us unnecessary? | **Largely, for labs on modern LIS.** Not for hospitals on legacy HMIS | Evidenced/partial |
| Will organisations install an extra local app? | Unknown. Small labs have little IT capacity; NABL pressure favours a proper LIS [S59] | **[UNVALIDATED]**; skepticism justified |
| Who would buy? | Hypotheses: (a) ABDM integrators/HMIS vendors needing a fast bridge for legacy hospital clients; (b) diagnostic chains acquiring labs with mixed software; (c) hospitals with legacy HMIS. **Not** the small lab itself | **[UNVALIDATED]** |

## 3. Alternative customer segments
| Segment | Evidence | Assessment |
|---|---|---|
| IBM i / mainframe spool users | Served for decades by InterForm (40 years), CoolSpools, Formtastic, Monarch, and now Astera AI [S50][S40] | **Saturated.** Reject |
| SME accounting (India) | Tally dominates and has XML/ODBC interfaces [U]; VFP usage has thousands of companies worldwide, counts inconsistent [S22] | Weak and unvalidated |
| Retail POS receipts | Receipt emulators exist; GST e-invoicing is built into modern billing [U] | Weak |
| **Hospitals receiving outside reports or with legacy HMIS** | Transcription errors [S60]; HMPI legacy barrier [S19] | **Best evidence**, but the buyer is complex and the input is often PDF or paper, not live print capture |
| Lab analyzers with printer-only output | Plausible (older or cheap analyzers) [H]; LIS "machine integration" already covers analyzers with host ports [S47] | Niche; would need hardware |

**Conclusion:** no segment combines (a) live print capture as the *necessary* ingestion method, (b) a high-value structured output, (c) an unserved buyer, and (d) evidence. **The market thesis is the weakest part of Spoolgeist.** For a hackathon, Impact only needs to be *credible and demonstrated*, not a validated business. That's achievable with honest framing (Section 5), but it caps the Impact score at about 12/20 unless interviews show something new.

## 4. Interview script (10 questions, about 10 minutes)
Ask labs, clinics and small hospitals. **Record answers verbatim. Never paraphrase into evidence. Ask consent before quoting.**
1. Walk me through what happens from sample collection to the patient getting the report. Where does the report get typed, printed or sent?
2. What software do you use to create reports? Since when? Who supplied it, and is that vendor still supporting you?
3. Can that software export results (PDF, Excel, API, HL7)? Have you ever tried?
4. Does anyone type the same results twice (from an analyzer printout, a Word file or an outside lab report into another system)? How often, and have you seen mistakes?
5. Have you registered with ABDM/HFR or linked reports to patients' ABHA? What stopped you, or how did it go?
6. If changing software were free, would you switch? What would stop you (data migration, staff retraining, formats doctors know)?
7. Would you let a small program run on your reporting PC that receives your print jobs and still prints them as normal? What worries you about that?
8. Who decides on and pays for software here? What do you pay per year now?
9. What would a tool need to save you each month to be worth paying for?
10. Can you show me (without patient details) what a printed report looks like? May we create a synthetic copy of the layout?

**Decision rule:** if fewer than 2 of 5 respondents describe software that can only print or double entry *and* would accept a local agent, treat the healthcare market thesis as **not validated** (see `15`).

## 5. Honest Impact framing for the submission (if we build it)
- Lead with the **evidenced** problem: re-typing printed results causes measurable errors [S60], and legacy hospital systems lack ABDM API layers [S19].
- Present the small-lab and legacy-print market as **"the target we are validating"**, quoting real interviews only.
- Never claim "labs can't join ABDM without us". It's false [S44].

### New sources
- [S59] Vendor statements on small labs using Word/Excel templates: https://www.pingmedoc.com/pathology-lab-software ; https://www.clinikpe.com/lab-report-formats/ ; https://www.clinikpe.com/best-lims-for-pathology-labs-india-2026/
- [S60] Mays & Mathias, "Measuring the rate of manual transcription error in outpatient point-of-care testing," JAMIA 2019, doi:10.1093/jamia/ocy170: https://academic.oup.com/jamia/article-pdf/26/3/269/27642462/ocy170.pdf ; Kratz et al. 2016: https://doi.org/10.1177/1460458215569004
