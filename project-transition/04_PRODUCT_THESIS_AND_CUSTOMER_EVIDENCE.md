# 04: Product thesis and customer evidence (22 Nov 2026)

## Status of customer evidence: **PENDING. 0 interviews conducted.**
Nothing below is customer evidence. It is a plan and a set of falsifiable assumptions.

## 1. Candidate product positions
Scored 1 (poor) to 5 (strong), with the evidence label in brackets.

| # | Position | Problem severity | Frequency | Adoption willingness | Deployment complexity (5 = easy) | Security concerns (5 = few) | Differentiation | Feasibility by 4 Dec | Demo strength | Kiroween fit | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Small-lab bridge: legacy lab software → ABDM/FHIR | 2 [VENDOR] | 3 [VENDOR] | 2 [INF: cheap cloud LIS alternative] | 3 | 2 | 2 | 4 | 4 | 4 | the original thesis; weakest on "why not switch software" |
| P2 | Verified print-stream bridge for **systems that cannot be replaced** (hospital HIS/LIS, abandoned vendors), sold to hospital IT and integrators | 3 [INF] | 2 [NONE] | 3 [INF] | 2 | 2 | 3 | 3 | 4 | 4 | a real niche if it exists; incumbents Monarch and ReportMiner |
| **P3** | **"AI proposes, proof disposes": an open-source, offline trust layer that turns AI-written parsers for fixed-format legacy output into rules that must *prove* they cannot silently drop or corrupt data before they run, demonstrated end-to-end on legacy lab print jobs → FHIR** | 3 [INF] | 3 [INF] | 3 [INF] | 4 | 4 (local, no per-document AI) | **4** [INF: the acceptance contract and gate are not marketed by the competitors we found] | **4** (core engine exists) | **5** (print → capture → AI rule → gate → approve → reject a defective report → FHIR) | **5** (Resurrection: dead printer ports brought back) | needs honest framing: not "first to use AI templates" |
| P4 | Capture for **older analyzers that only print** (serial/parallel) | 4 [VENDOR: analyzer transcription is the commonest pain] | 4 [VENDOR] | 3 | 1 (hardware) | 3 | 3 | **1** (no hardware path or devices) | 3 | 4 | the best real-world pain, but infeasible by 4 Dec; roadmap |
| P5 | General legacy-report extraction for any industry | 3 | 3 | 2 | 3 | 3 | 2 (crowded) | 3 | 3 | 3 | Monarch and ReportMiner territory |

**Selected thesis: P3, with P2 as the stated target audience and P4 as the stated next step.**

> Legacy systems that can only print still hold critical data. AI can write a parser for a new printout in seconds, but an AI-written parser that silently drops one result is worse than none. Spoolgeist makes every AI-written rule **prove itself before it runs**:
> - adversarial self-tests;
> - whole-document accounting;
> - definitional domain checks;
> - a signed human approval.
>
> After approval it runs **offline, deterministically and with no AI per document**. Anything it cannot fully account for goes to a person, not into the database.

**Why not the original healthcare-only thesis:** small labs can switch to cheap cloud LIS products that already claim ABDM push (report 03). The pitch must not depend on "labs can't digitise".

**What the thesis does not claim:**
- clinical safety;
- ABDM integration or certification;
- novelty of AI-generated templates (ReportMiner);
- novelty of print capture (VeryPDF, Retro-Printer, RedTitan);
- real-world accuracy.

## 2. Interview programme (5 conversations, before 28 Nov if at all possible)
**Targets, in order of value:**
1. Hospital IT administrator, or HIS/LIS implementation engineer (×2).
2. Lab manager of a hospital or large lab (×1).
3. Independent lab owner or technician (×1).
4. Healthcare integration consultant (×1).

**Rules:**
- No pitch during the first 15 minutes.
- Record facts about the *last time* something happened, not opinions about the future.
- Never ask "would you use…".

### Interview guide (neutral)
1. Walk me through what happens from the moment a result is ready until it reaches the patient or doctor. Which systems and which people?
2. Which of your systems produce printouts? Of those, which can also export data electronically (API, HL7, CSV, database)? How do you know?
3. When did someone last re-type data from a printout or screen into another system? What was it, how long did it take, and who did it?
4. How often does that happen in a week? Is it written down anywhere (logs, staffing)?
5. Tell me about the last error caused by re-typing or a missing result. How was it found? What did it cost?
6. Have you tried to connect or replace the system that only prints? What happened? Who said no, and why?
7. What do you use today to move data between systems (interface engine, vendor module, Excel, RPA, nothing)?
8. Who decides whether new software can be installed on a machine that talks to the printer or the HIS? What do they ask for (security review, vendor approval, NABL/ISO change control)?
9. Do ABDM/ABHA or other digital-record requirements affect you today? Concretely how?
10. *(Only after 1–9)* If a tool could turn those printouts into validated structured records, but refused any report it could not fully account for, what would make you distrust it? What would you need to see?

### Disconfirming questions (they must be asked)
- "Is there any system here that prints but **cannot** be replaced or connected another way?" A "no" kills P2 for that site.
- "If a result were missing from the electronic record, how would anyone notice?" If the answer is "it never matters", fail-closed is not valued.
- "Would IT allow a program to listen on the printer port or network?" A "never" kills the capture approach.

### Notes template (one file per interview, in `market-evidence/`)
```
id: INT-0x | date | role | organisation type & size | systems in use (names, versions)
consent to record notes: yes/no | identifying details removed: yes
facts (last-time events, with quantities):
quotes (verbatim, short):
current workaround + cost:
blockers to adoption:
evidence class per assumption: A1..A6 → supports / contradicts / no data (with the fact it rests on)
follow-ups:
```

### Evidence classification
- **E1:** observed artefact (screenshot, log, printout with identifiers removed).
- **E2:** a specific past event described with quantities.
- **E3:** a general statement from experience.
- **E4:** an opinion or prediction.

Only E1 and E2 can move a decision.

### Assumption validation matrix
| ID | Assumption | Supports if… | Contradicts if… | Status |
|---|---|---|---|---|
| A1 | Some organisations run systems that print but cannot export or be replaced | ≥2 interviewees name such a system (E1/E2) | all systems can export or be replaced | **pending** |
| A2 | Re-typing from such printouts happens weekly or more | quantified weekly events (E2) | rare or none | pending |
| A3 | Silent omissions or errors are a recognised risk | a described incident (E2) | "never matters" | pending |
| A4 | IT would permit a local capture agent | a named approval path | categorical refusal | pending |
| A5 | Offline / no-per-document-AI is valued | privacy or cost concerns raised unprompted | indifference | pending |
| A6 | FHIR/ABDM output is useful *now* | a concrete current requirement | "not relevant to us" | pending |

**Contradictory evidence log:** `market-evidence/CONTRADICTIONS.md` (create on the first interview). Every contradicting fact is logged even if the interview is otherwise positive.

**Decision rule (pre-committed):**
- If at least 2 of 5 interviews support A1 **and** A2 with E1/E2 evidence, the impact claim may say "observed with N practitioners".
- Otherwise the submission must present impact as a hypothesis and lean on the technical and trust contribution.
