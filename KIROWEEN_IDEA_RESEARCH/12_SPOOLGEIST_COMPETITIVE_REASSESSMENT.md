# 12 — Spoolgeist: Competitive Reassessment

## 1. Specific competing products
| Product | Capture | AI-generated reusable template | Verification / abstention | Health output (FHIR/ABDM) | Target / price | Source |
|---|---|---|---|---|---|---|
| **Astera ReportMiner** (AGL, 11.2) | Files (printed/mainframe reports, PDF) | **Yes**: "reusable extraction template in 5 seconds"; BYO OpenAI/Anthropic key | Validation against business rules; abstention not documented [U] | No | Enterprise, licensed | [S40][S41] |
| **RapidMiner/Altair Monarch** | Spool/PRN/text report files | Hand-built models | Rules | No | Enterprise | [S23] |
| **VeryPDF Printer Capture** | **Virtual printer; PCL/PS/Epson; DOS parallel/serial** | No (claims key-data extraction; details unclear) | No | No | SMB/custom builds | [S49] |
| InterForm / CoolSpools / Formtastic | IBM i spool | Rules/templates | Rules | No | IBM i shops | [S50] |
| **Sensible** | API upload | Configs in SenseML; hybrid LLM + layout-specific deterministic configs | Confidence signals on LLM fields | No | Developers, SaaS | [S56] |
| Evaporate (research) | — | **Yes** (LLM writes functions; weak supervision) | Aggregation by weak supervision | No | Research | [S42] |
| escpos-netprinter / virtual-printer.online | Raw 9100 (receipts) | No | No | No | Hobby / testing | [S24][S26] |
| lab-report-to-fhir-skill (GitHub, 0★) | PDF | Rule/agent-skill parsing | Structural FHIR checks; no abstention | **FHIR R4** | OSS | [S61] |
| Modern Indian LIS (Labsmart, CrelioHealth, Drlogy…) | Native | n/a | n/a | **ABDM M1–M3** (some, e.g. CrelioHealth) | ₹5k–₹3L/yr | [S47] |
| ABDM integrators (Nirmitee etc.) | DB/API integration | n/a | n/a | Certified flows | Services | [S38] |

## 2. "If a judge searches for this idea, what will they find?"
Astera's 2026 AI template feature, VeryPDF's virtual-printer capture, and the ABDM IG's PDF-in-`presentedForm` examples. A well-informed judge could reasonably say: *"Print capture exists, AI template generation exists, and ABDM accepts PDFs. What's new?"*

## 3. What is still genuinely different
1. **Verified activation and abstention.** A rule only goes live after held-out and perturbation tests show it **never silently emits a wrong value**. Below full deterministic confidence, the system abstains. We **measure and publish a silent-error rate** against a direct-LLM-extraction baseline. *No competitor found publishes this* [U, absence of evidence].
2. **An open, declarative, inspectable rule format** (data, not code) whose source spans are visible down to the character.
3. **The end-to-end open-source chain:** live capture → verified rule → ABDM-profile-validated FHIR bundle that keeps the original printout as `presentedForm`.
4. **Local-first:** steady-state extraction needs no cloud and no LLM.

Each piece exists somewhere. The **combination plus measured safety** is the differentiation. That is **incremental innovation, not breakthrough**. Revised Innovation estimate: **11–13/20** (was 16).

## 4. Differentiation test (revised)
A competent team could reproduce the core pipeline in **about 1–1.5 weeks** using Astera-style ideas plus pdfplumber, an LLM and `fhir.resources`. The parts that are harder to copy are the **perturbation benchmark plus abstention guarantees** and the quality of the evidence. That's a moderate moat for a hackathon and a weak one for a business.

## 5. Comparison with previous Resurrection winners
| | Faxi (Best Resurrection 2025) | Spoolgeist |
|---|---|---|
| Dead tech | Fax machine (consumer-visible) | Legacy app printing via LPT/RAW port (less visible) |
| Audience | Seniors in Japan (emotional, clear) | Labs and hospitals (B2B; market not yet validated) |
| Magic moment | Handwritten fax → AI action → reply fax | Print → verified rule → FHIR record; abstains on bad input |
| Risk | — | Could look like "ETL with a ghost theme" |

Category fit is **acceptable but not obvious**. The demo must *show* the old software (DOS/text-mode app) to make the Resurrection angle land.

### New source
- [S61] terravic/lab-report-to-fhir-skill: https://github.com/terravic/lab-report-to-fhir-skill
