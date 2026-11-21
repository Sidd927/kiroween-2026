# 00: Master execution status

**Updated:** 22 Nov 2026.

**Deadline:** Sat 5 Dec 2026, 03:30 IST (4 Dec 14:00 PT). About 12.4 days remain. **Submission target: 4 Dec 23:59 IST.**

## Done (with evidence)
| Milestone | Result | Report |
|---|---|---|
| Phase-0 state recovery | inventory of versions, data, tests, Kiro and git | 01, 17 |
| Mutation testing | 252/334 killed (75.4%); all 82 survivors classified; 5 gap-test groups added | 18 |
| v4 frozen | 517-file manifest `c5bd2f08…`; sealed seed hash logged before generation | 19 |
| Sealed evaluation (887 docs) | valid 410/410 fully correct; **0/399 unsafe**; 0 wrong values; 0 context errors (v3.2: 38/399 unsafe; v2.1: 84/399 unsafe and 6 wrong patient names) | 19 |
| Held-out evasion v3 (pre-registered) | numeric 0/60 leaked; **qualitative 27/180 leaked** (notes and name slots) | 19 |
| Property test (seed 314159, 3,000) / metamorphic (945 pairs) | 0 unsafe, 0 silent / 0 violations | 19 |
| FHIR (410 bundles) | 0 errors generic and ABDM 6.5.0; semantic checks 410/410; negative control fails as expected | 19 |
| Forwarding states (F-24) | mapped; "delivery confirmed" is not possible over RAW; tested against fake printers only | 19 |
| Official rules verified | Kiro mandatory; `/.kiro` at the root; new work after 30 Oct; video under 3 min; credits by 1 Dec 12:00 PT | 20 |
| Organiser clarification | **drafted, not sent** | 21 |
| Market and competition | ReportMiner already has AI templates; print capture exists; small-lab thesis weak | 03, 04 |
| Decision | **MODIFY** (new thesis, Kiro-built app, free-text confirmation, scope cut) | 22 |
| Kiro application plan + MVP acceptance criteria | stack B (Python engine + FastAPI + React), new repository, schedule | 24, 25 |
| GitHub checkpoint | see report 23 | 23 |

## In progress
None. Everything is committed (see 23).

## Blocked on the user
| # | Action | Why | By |
|---|---|---|---|
| C1 | Install Kiro (https://kiro.dev), sign in, and **submit the Kiroween credit request form** with your Kiro user ID | Kiro is mandatory; credits close 1 Dec 12:00 PT and need about 48 business hours | as soon as possible (aim for 24 Nov) |
| C2 | Tell me team size (max 3) and daily hours | sets scope | now |
| C3 | Create a new public GitHub repository for the application (e.g. `spoolgeist`), or authorise me to create it with `gh` | the rules require a public repository with `/.kiro` at the root | before building |
| C7 | Approve or edit and send the organiser clarification (report 21) | eligibility certainty | now |
| C4 | Schedule up to 5 interviews (guide in report 04), or accept hypothesis framing | Impact score | 28 Nov |
| C5 | Review and approve the demo rules as a human | no human has approved any rule | before recording |
| — | Is `Sidd927/kiroween-2026` public or private? (I did not change visibility) | the archive may be linked from the submission | any time |

## Not started (intentionally, until C1–C3)
Kiro specs and implementation, design research (GetDesign.md, report 26/27), the application, deployment, video and submission text.
