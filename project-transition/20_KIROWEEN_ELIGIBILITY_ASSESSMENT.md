# 20: Kiroween 2026 eligibility assessment (22 Nov 2026)

**Source:** the official rules at https://kiroween.devpost.com/rules, read in full on 22 Nov 2026 (page notes "Updated November 16, 2026"). Quotations are verbatim, and kept short.

## 1. Requirements and how we stand
| Requirement (official) | Quote | Our status | Classification |
|---|---|---|---|
| Submission deadline | "Submission Period: October 30, 2026 (9:00 am Pacific Time) – December 4, 2026 (2:00 pm Pacific Time)". "No extensions will be granted." | 4 Dec 14:00 PST (UTC−8) = 22:00 UTC = **Sat 5 Dec 03:30 IST** | Confirmed |
| New work | "Projects must be newly created by the Entrant after the start of the Hackathon Submission Period." | First research and commits date from 21 Nov 2026, after 30 Oct (`git log`: initial commit 21 Nov 10:58 IST) | **Confirmed on dates** |
| Pre-existing code | "must disclose any other pre-existing code or work incorporated into the Project." "The work described and submitted must have been built during the Submission Period." | The PoC and validation engine were built 21–22 Nov **with Claude Code**, inside the period. They must be disclosed if reused | Confirmed: disclose |
| Kiro use | "Entrants must build a working software application using Kiro (IDE, CLI, Web, and/or Kiro Crew)… **Insufficient use of Kiro will result in disqualification at the Judges' sole discretion.**" | **No Kiro use so far.** Kiro is not installed | **Potentially ineligible as things stand.** Likely acceptable only if the submitted application is substantially built in Kiro (awaiting clarification) |
| Kiro artifacts | "Your repo must contain the /.kiro directory at the root of the project to show usage of Kiro such as specs, hooks, and steering. Do NOT add the /.kiro directory … to your .gitignore" | The existing `.kiro` sits at `poc/.kiro`, was written by Claude Code and was never run in Kiro. It is **not** evidence of Kiro use | Not met (application repository to be created) |
| Kiro write-up | "Provide a write up on how Kiro was used … specs … hooks … steering … MCP … Property-based testing …" | Plan in reports 24 and 05 | Not started |
| Stage-One gate | "reasonably fits the theme and reasonably applies the required tools" | The theme fits (Resurrection). Tools: depends on the Kiro work above | Unclear |
| Repository | "public URL to your code repository on GitHub … must be public and open source by including an open source license file … visible … (in the About section)" | `Sidd927/kiroween-2026` has an MIT licence. Visibility not checked (the user's call). The application repository does not exist yet | To do |
| Functional application | "Provide a URL to your functional application(s)." "must be capable of being successfully installed and running consistently" | None yet | To do |
| Video | "less than three (3) minutes", "publicly visible on YouTube", "footage that shows the Project functioning" | None yet | To do |
| Team | "maximum 3 participants per team" | Team size unknown | User input |
| Credits | "one-time allotment of 4,000 Kiro credits … Credit requests must be submitted by Tuesday, December 1, 2026 at 12:00 pm Pacific Time" (allow 48 business hours) | Not requested | **User action** |
| Student bonus | "All members of a submitting team must be students" (LinkedIn, student email, …) | Unknown | User input |
| Third-party data | must be authorised | synthetic data only; HL7 validator and ABDM IG are public | OK |

## 2. The key question: Claude Code prototype → Kiro application
**What the rules say:**
- Work must be built during the period (ours was).
- Kiro must be used sufficiently, at the judges' discretion.
- Pre-existing work incorporated must be disclosed.

**What the rules do not say:**
- They do not say other AI tools are forbidden.
- They do not define "insufficient".
- They do not say whether research or a prototype built with another tool during the period may seed a Kiro-built application.

**Our interpretation:** the safest compliant path is as follows.
1. Build the **submitted application** in a **new repository** with Kiro: specs, steering, hooks, implementation and tests done in Kiro, with real history.
2. Treat this repository as **disclosed prior work and reference material**: research, design and test oracle.
3. If any engine code is reused, list it explicitly. **Prefer re-implementing the engine through a Kiro spec**, with the existing property tests as acceptance criteria. That turns reuse into a genuine Kiro story: spec, PBT, implementation.
4. State plainly in the submission and the write-up which parts Claude Code produced and which parts Kiro produced.

**Classification: Likely acceptable if the steps above are followed, awaiting organiser clarification.**
- **Potentially ineligible:** submitting the current Claude Code engine with a `.kiro` folder added.

Draft clarification request: report 21. **It has not been sent**; that needs the user's permission.

## 3. Countdown (from 22 Nov 2026; deadline Sat 5 Dec 03:30 IST)
| Window | Dates (IST) | Purpose |
|---|---|---|
| Day 0–1 | 22–23 Nov | Stage 3 closed; checkpoint pushed; Kiro installed; credits requested; clarification sent (if approved); interviews scheduled |
| Day 2–5 | 24–27 Nov | Kiro: specs and steering; engine port under PBT; first vertical slice (capture → extract → refuse/accept → FHIR) |
| Day 6–8 | 28–30 Nov | Rule onboarding + approval UI; review queue; design pass; interview results folded in |
| Day 9–10 | 1–2 Dec | Deployment; polish; demo script; **credit request deadline 1 Dec 12:00 PT = 1:30 AM IST on 2 Dec** |
| Day 11 | 3 Dec | Video recording and editing; write-up; blog (bonus) |
| **Buffer** | 4 Dec, all day IST | **Protected:** submit by 4 Dec 23:59 IST (≈ 3.5 h before the deadline). No feature work on 4 Dec |
