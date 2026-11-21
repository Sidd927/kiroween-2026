# 03: Market and competitive reassessment (22 Nov 2026)

**Evidence labels:**
- **[SRC]**: a cited source.
- **[VENDOR]**: a vendor or marketing claim, with no methodology.
- **[INF]**: our inference.
- **[NONE]**: no evidence found.

**No customer interviews have been conducted**, so all customer-side evidence is pending (report 04).

## 1. The original problem, re-examined
**Original thesis:** small Indian labs run legacy software that prints reports but cannot export structured data, so their results never reach ABDM/FHIR; Spoolgeist captures the print stream and turns it into validated FHIR.

| Question | What we found | Strength |
|---|---|---|
| Do labs rely on non-exporting systems? | Vendor blogs claim "60% of India's 1.5 lakh labs still rely on manual registers or basic Excel" and "70% of mid-sized labs still manually transcribe results from analyzers" [VENDOR: Adrine]. Hospital labs "often the last department still running on registers and manual report typing" [VENDOR: MedXL]. | Weak: no methodology |
| Is the gap *legacy software that prints*, or *no software at all*? | The most-cited pain is **transcription from analyzers** and **registers or Excel**, not "legacy LIS that prints but cannot export" [VENDOR]. A lab with no LIS produces no print stream to capture. | **Undermines the thesis for small labs** [INF] |
| What does manual entry cost? | "Errors in 1–3% of results", "+15–30 min turnaround" [VENDOR: Adrine]. No independent survey found [NONE]. | Weak |
| Is ABDM a driver? | DHIS incentivises ABHA-linked records: labs earn ₹20 per transaction above 100 a month [SRC: PIB, scheme summaries]. But by 18 Jun 2026 diagnostic centres, labs and pharmacies together had received only **₹2.95 crore**, against ₹107 crore for hospitals [SRC: PIB press release]. | Mixed: the incentive exists, lab uptake is small |
| Is there a cheaper alternative for labs? | Cloud LIS products cost about ₹417 to ₹25k a month and **claim ABDM/ABHA push** (CrelioHealth "M1–M3 certified", PractoLab, Lisfi, Adrine, MocDoc …) [VENDOR, comparison blogs; certifications not checked against the official list]. | **Strong alternative**: a small lab can switch software instead of bridging old software |

**Conclusion [INF]:** for *small independent labs*, "replace the system" or "adopt a cheap cloud LIS" is probably easier than "install a print-capture agent next to an old one". The problem Spoolgeist solves is real only where the source system **cannot be replaced or modified**:
- hospital HIS or LIS lock-in;
- vendor-abandoned software;
- regulated or validated systems;
- **older analyzers and devices that only print**;
- cost or contractual barriers.

That is a narrower, more technical audience (hospital IT and integrators), and it has not been validated with anyone.

## 2. Competitive landscape
| Product | What it does | Input | Deployment | AI use | Validation and audit | Price (if found) | What Spoolgeist could genuinely differ on |
|---|---|---|---|---|---|---|---|
| **Monarch** (Datawatch → Altair → Siemens/Rapidminer) | "Pioneered report mining over 35 years ago"; text and PDF reports from core banking, healthcare and similar systems; **print stream decomposition** (Monarch Server) [SRC] | PRN/TXT/PDF, print queues | desktop + server | template-based (no AI claim found) | not established | ~$1,595–1,995 per user per year (older third-party list prices); server from ~$10k [SRC: TechRepublic, 360Quadrants; dated] | fail-closed acceptance and a provable no-silent-drop property; healthcare-domain validators; FHIR output; open source |
| **Astera ReportMiner** | **"Auto-Generate Layout": AI builds a reusable extraction template in seconds** and applies it to every file with that format; "LLM Generate" for variable layouts; validation against **user-defined** rules; 200+ destinations [SRC: astera.com] | PDF, TXT, PRN, COBOL … | desktop/enterprise | **AI writes the template once, deterministic afterwards (our core idea already exists commercially)** | user-defined rules; error and null counts | not published | **Not the AI-template idea.** Possible differences: an adversarial activation gate, whole-document accounting, a binding-independent domain check, signed approval chain, print-port capture, FHIR. None of these has been compared hands-on with ReportMiner [INF] |
| **VeryPDF Printer Capture** | virtual port monitor and virtual printer; captures EMF/SPL/PCL/PS/PDF; can extract fields to XML/CSV [SRC] | print streams (USB, TCP/IP, IPP, LPR) | Windows | not stated | not stated | not found | validation depth; open source |
| **Retro-Printer** | hooks into the print stream of legacy systems; PCL, PostScript, Epson, IBM and other emulation; outputs files; "more complete installation" parses to structured output [SRC] | many printer languages | appliance/software | not stated | not stated | not found | extraction safety, domain output |
| **RedTitan Print2USB / EscapeE** | hardware stands in for a printer for "locked down black box" hosts; reprocesses PDL to PDF or data [SRC] | parallel/USB/PDL | hardware + software | not stated | not stated | not found | Spoolgeist has **no** hardware path (RAW/9100 only) |
| **Unstract** (open source, AGPL) | LLM extraction platform; **"LLMChallenge": a second LLM checks the first → right value or nothing**; human-in-the-loop; MCP server [SRC] | PDFs and documents | cloud/on-prem | **LLM on every document** | dual-LLM consensus | open source + paid cloud | no AI per document (cost, privacy, determinism); offline |
| **Docling** (IBM, MIT) | converts PDF, Office and similar into structured documents locally [SRC] | documents, not print streams | library | layout models | none (conversion, not validation) | free | different layer; not a competitor for field extraction |
| HL7 interface engines (Mirth/NextGen Connect, PilotFish, …) | route and transform HL7/FHIR messages [SRC: PilotFish templates; general knowledge] | structured messages | server | no | message validation | varies | complementary: Spoolgeist would *feed* them |
| Cloud document AI (Textract, Document AI, Azure DI) | OCR plus field extraction from images and PDFs [general knowledge, not re-verified today] | images, PDFs | cloud | ML per page | confidence scores | per page | no cloud upload of patient data; print streams are already text (no OCR) |
| RPA (UiPath and others) | screen scraping and keystrokes [general knowledge] | UI | desktop | optional | workflow logs | licences | no UI automation needed |

**What we cannot honestly claim:**
- That "AI generates reusable templates" is novel. ReportMiner markets exactly this.
- That print capture is novel. VeryPDF, Retro-Printer and RedTitan exist.
- That competitors lack validation. ReportMiner validates against user-defined rules, Unstract uses LLM consensus, and we have not tested their failure behaviour.

**What is plausibly distinctive, but unproven against competitors [INF]:**
1. **The acceptance contract.** Every non-blank line must be explained, any unexplained number or unknown result refuses the document, and nothing is ever silently dropped, demonstrated with pre-registered held-out attack sets and mutation testing.
2. **The rule lifecycle as a safety process.** An AI candidate goes through a deterministic compiler, an adversarial self-test gate, approval that re-derives the rule from its provenance, and a hash-chained registry.
3. **Zero AI and zero network per document.** It runs offline and locally, with reproducible output.
4. **Domain-specific definitional checks** (red-cell indices, bilirubin, protein) and **FHIR R4 output** with ABDM profile validation.

## 3. Segments compared
| Segment | Pain evidence | Can replace the source system? | Who buys and operates | Objections [INF] | Fit |
|---|---|---|---|---|---|
| Small independent labs (original) | vendor claims only | **yes, cheaply** (cloud LIS ₹ hundreds to thousands a month) | owner / technician | why not switch LIS; a local agent is IT work they don't have | **weak** |
| Hospital labs with locked HIS/LIS | vendor claims (HIS–LIS still on paper slips) | often no (contracts, validation) | hospital IT; integrator | security review, change control, vendor support terms | **medium (unvalidated)** |
| Healthcare integrators | none collected | n/a | integrator uses it as a tool | competes with their own interface work; ReportMiner/Monarch exist | medium |
| Older analyzers that only print | vendor claims (manual analyzer transcription is the commonest pain) | no (instrument lifetimes) | lab + biomedical engineering | **needs serial/parallel capture hardware, which we don't have** | promising, but a different capture path |
| Non-healthcare legacy reporting (banking, ERP, mainframe) | Monarch/ReportMiner's existence shows a market | sometimes | data teams | strong incumbents | crowded |

## Sources
- Kiroween rules: https://kiroween.devpost.com/rules
- Monarch: https://www.siemens.com/en-us/products/rapidminer/monarch/ ; https://help.altair.com/2022/monarch/help/desktop/ht_input_reports.htm ; pricing: https://www.techrepublic.com/article/altair-monarch-review/ , https://www.360quadrants.com/software/machine-learning-software/angoss-software-corporation
- Astera ReportMiner: https://www.astera.com/products/report-miner ; https://www.astera.com/type/blog/mainframe-report-extraction-enterprise-scale ; https://www.g2.com/products/astera-reportminer/reviews
- VeryPDF Printer Capture: https://www.verypdf.com/wordpress/202508/solution-verypdf-printer-capture-solution-virtual-port-monitor-virtual-printer-for-secure-print-job-interception-conversion-and-automation-51242.html
- Retro-Printer: https://www.retroprinter.com/accessing-printer-data-from-legacy-systems/
- RedTitan: https://www.pclviewer.com/resources/capture/print2usb.html
- Unstract: https://unstract.com/home/ ; https://unstract.com/blog/what-is-unstract/
- Docling: https://research.ibm.com/blog/docling-generative-AI
- PilotFish HL7 templates: https://licensing.pilotfishtechnology.com/wdi/rest/versions/HL7-v2-x-Template-Medical-Lab-Reports-to-and-from-Meditech-246
- DHIS: https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2281466&reg=48&lang=2 ; https://www.pib.gov.in/PressReleasePage.aspx?PRID=1885610&reg=48&lang=2
- Indian LIS comparisons [VENDOR]: https://codingclave.com/guides/best-pathology-lab-software-india-2026 ; https://practolab.in/index.html ; https://www.adrine.in/blog/diagnostic-center-software-india ; https://www.medxl.in/blog/what-is-a-laboratory-information-system-lis.html ; https://emedhub.in/blog/laboratory-information-system-lis-buyers-guide-indian-labs
