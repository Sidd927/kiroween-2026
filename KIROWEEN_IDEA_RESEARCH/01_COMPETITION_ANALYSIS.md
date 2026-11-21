# 01 — Competition Analysis: Kiroween 2026

Research date: **Saturday, 21 November 2026**. I read every fact below directly from the official Devpost overview, rules and resources pages on that date, unless it is marked otherwise. Sources are numbered and listed in `SOURCES.md`.

---

## 1. Verified facts

| Item | Verified value | Source |
|---|---|---|
| Event | Kiroween 2026, Kiro's annual Halloween hackathon. Sponsor: AWS. Administrator: Devpost | [S1][S2] |
| Submission period | 30 Oct 2026, 9:00 AM PT → **4 Dec 2026, 2:00 PM PT** | [S2] §1 |
| **Deadline in IST** | 2:00 PM PST (UTC−8, no daylight saving in December) = 22:00 UTC = **Saturday 5 Dec 2026, 03:30 AM IST** | calculated |
| Time left from 21 Nov | About **13.5 calendar days** | calculated |
| Extensions | "No extensions will be granted. Late Submissions will not be accepted." | [S2] |
| Judging period | 16 Dec 2026 → 29 Jan 2027. Winners announced around **3 Feb 2027** | [S2] |
| Team size | Up to **3** | [S2] §3 |
| Eligibility | Must be at least the age of majority where you live. **India is not on the excluded list.** Excluded places include Quebec, Argentina, Brazil, Italy, Philippines, Russia, UAE and OFAC-sanctioned countries. Australia was added on 16 Nov 2026 | [S2] §3 |
| New projects only | Must be built during the Submission Period. "Projects you started before October 30, including Kiroween 2025 projects, are not eligible." Frameworks, libraries and starter templates are allowed, but **any other pre-existing code must be disclosed** | [S1][S2] |
| Kiro credits | One-time grant of **4,000 credits**. Requires ID verification through Didit. **Request by Tue 1 Dec 2026, 12:00 PM PT. Redeem by 4 Dec.** Allow 48 business hours | [S2][S3] |
| Kiro products allowed | IDE, CLI, Web and/or Kiro Crew | [S1] |
| Kiro region note | Availability of features and models can vary by region; that is the entrant's responsibility. India is on Kiro's list of paid billing countries. I found no published list of which models are available in India | [S2][S12] |

### Categories (exact wording)
- **Resurrection:** "Bring your favorite dead technology back to life. Reimagine obsolete tech with today's innovations or solving tomorrow's problems."
- **Frankenstein:** "Stitch together a chimera of technologies into one app. Bring together seemingly incompatible elements to build something unexpectedly powerful."
- **Skeleton Crew:** "Build a skeleton code template lean enough to be clear but flexible enough to support various use cases. Show us its versatility with two distinct applications from your foundation." The repo **must contain 2 separate repo folders for the 2 applications.**
- **Costume Contest:** "Build any app but show us a haunting user interface that's polished and unforgettable. Bring in spooky design elements that enhance your app's function."

### Prizes (over $100k total)
| Prize | Amount |
|---|---|
| 1st / 2nd / 3rd overall | $30,000 / $20,000 / $10,000 |
| Best of each category (×4) | $5,000 each |
| Best Startup Project | $10,000. Must be a founder, with LinkedIn and a startup website |
| Best Ghost of Kiroween Past | $2,000. Must have registered for Kiroween 2025 |
| Best Kiro Crew App | $1,000. Chosen by the Kiro team from the top 50 eligible submissions that include a Crew app repo |
| **Best Student Project, one per category (×4)** | **$1,500 + 1-year Kiro Pro Max.** All team members must be students; proof of enrollment may be requested |
| Best Demo | $1,000. Highest Presentation score among submissions in the top 10% overall |
| Bonus Blog Prize (×100) | 2,000 Kiro credits |
| Social Blitz (×5) | 3-month Kiro Pro+. The post must *start* with `#KiroweenHackathon26` |

**How prizes stack:** a project can win **one** overall prize **or** one category prize, **plus any number of bonus prizes**. The student prizes are bonus prizes, so a student team can win, for example, Best Resurrection **and** Best Student Project: Resurrection **and** Best Demo.

### Judging ([S2] §6)
- **Stage One (pass/fail):** the project "reasonably fits the theme and reasonably applies the required tools." Also: "Insufficient use of Kiro will result in disqualification at the Judges' sole discretion."
- **Stage Two:** five criteria, weighted equally at 10 points each:
  1. **Potential Impact.** A credible real problem for a real audience. Does what is demonstrated actually address it? Would someone use it?
  2. **Technological Implementation.** ⚠️ **This criterion is entirely about Kiro**: "How thoroughly and skillfully does the project use Kiro? … Was a variety of Kiro tools used impactfully? … deep understanding of Kiro features? Was there experimentation?" Engineering difficulty alone earns nothing here; it scores only through the depth of Kiro use.
  3. **Design.** "A complete, coherent product experience, not just a technical proof of concept."
  4. **Innovation/Idea.** Novelty, how it differs from existing concepts, and "unusual technologies or **public resources (like datasets)** leveraged or combined in a unique way."
  5. **Presentation.** Does the video show the project working end-to-end? Is the problem, audience and reason it matters clear? Is it creative and memorable?
- Judging may use "expert panels, peer review, **automated AI-driven analysis**, or any combination." Our README, write-up and `.kiro` folder therefore need to be machine-readable and explicit.
- Tie-break: judges re-score from scratch on 20-point scales.

### Submission requirements (any of these can disqualify us)
1. **Public GitHub repo** (not GitLab or Bitbucket) containing all source, assets and instructions.
2. An **open-source license file that GitHub detects** and shows in the repo's About section.
3. A **`/.kiro` directory at the repo root** showing specs, hooks and steering. **Do not gitignore it or any subfolder.**
4. A **URL to the working app**. Put test credentials in the private Devpost field. The app must stay free and available to judges until judging ends.
5. A text description of features and functionality.
6. A **demo video under 3 minutes**, public on YouTube, showing the project running on its intended device. No copyrighted music or third-party trademarks without permission.
7. A **write-up on how Kiro was used**. The rules list prompts: IDE/CLI/Web/Crew differences, custom agents, hooks, specs vs vibe coding, steering strategy, MCP, property-based testing (PBT), powers.
8. Everything in English.
9. Skeleton Crew only: 2 separate app folders.

---

## 2. Ambiguities and what they mean for us

| Ambiguity | What it means / how we handle it |
|---|---|
| A "URL to your working app" for tools that run locally or on a LAN (dev tools, printer agents) | The 2025 1st-place winner was a local Python template, so local tools clearly pass. Even so, **we will host a public demo that judges can use without installing anything**, because judges "may choose to judge based solely on the text description, images, and video." |
| "2 separate repo folders" (Skeleton Crew) | Most likely two top-level folders in one repo. Only relevant if we choose Skeleton Crew. |
| Kiro Crew App: "separate repo submission", "GitHub account must match" | Crew apps live in their own git repos anyway ([S9]). Plan a **second public repo** owned by the same GitHub account. |
| What counts as "sufficient use of Kiro" | Not defined. A rich `.kiro/` (several specs, steering, hooks, custom agent) plus a concrete write-up keeps us well clear of the line. |
| Pre-existing code | Disclose every OSS dependency and any adapted snippet in the README under "Pre-existing work". Don't reuse code from any of our earlier projects. |
| Model availability in India | Do a quick check on day 0 that the Kiro models we want (and PBT, which is IDE-only) work from India. |
| Student status | "Students at a recognized academic institution." Collect student emails and enrollment proof for every member now. |

---

## 3. What the 2025 winners tell us (747 submissions, about 4,957 participants)

I looked up each winner's prize on its Devpost project page ([S4][S5]).

| Prize | Project | Category | Why it likely won (my interpretation) |
|---|---|---|---|
| **1st overall** | **InteractionKit**: MediaPipe gesture-app template | Skeleton Crew | The template **shipped its own Kiro configuration** (3 hooks that auto-wire new gestures, 2 steering docs, Context7 MCP). The Kiro integration *was* the product. It fixed a specific pain: agents hallucinating MediaPipe APIs. |
| **2nd overall** | **UnitSet**: canvas + AI + live-sandbox UI builder | Frankenstein | An ambitious, polished developer tool that stitches real parts together. |
| **3rd overall** | **SpookBnB**: a rental site whose "dark mode" becomes an escape room | Costume Contest | Pure design and presentation flair; a clever twist on a familiar UI. |
| Best Resurrection | **Faxi**: handwritten fax → AI agents → fax reply, for offline seniors in Japan | Resurrection | A dead technology plus a real, underserved audience plus working end-to-end agents (live fax number). |
| Best Frankenstein | **rumorNet**: multilingual multi-agent misinformation detection | Frankenstein | A social-impact problem and an explicit "why this is a chimera" narrative. |
| Best Costume | **Seance**: folklore map with a page-flip book UI | Costume | Atmosphere, 3D smoke, sound design. |
| Best Skeleton Crew + Most Creative | **Impulse Kit**: Go/No-Go training engine with 3 themes | Skeleton Crew | One engine reused across clearly different domains, grounded in neuroscience. |
| Best Startup | Splat-n-Treat: spatial CMS with Gaussian splats | — | — |

**Lessons:**
1. **Make Kiro part of the product, not only the build process.** The grand-prize winner gave *its users* hooks, steering and MCP. That is the most reliable way to score on the Kiro-only Technological Implementation criterion.
2. **A real audience with a concrete story beats abstract ambition** (Faxi: Japan's seniors and fax machines).
3. **Developer tools do very well** with this judging panel (InteractionKit, UnitSet, Splice).
4. **A polished, coherent product beats a feature list.**
5. **Expect copycats in 2026.** Many teams will build "Kiro-native templates" and "old-tech bridges". The idea has to be clearly different from Faxi and InteractionKit, not just reskinned.

---

## 4. Category strategy

| Category | Opportunity | Extra engineering it forces | Fit for us | Assessment |
|---|---|---|---|---|
| **Resurrection** | The "dead tech → real audience" story is rewarded (Faxi). Clear theme fit. Impact is easy to argue | The dead tech has to be real and visible in the demo | High. Pairs legacy and obsolete systems with modern AI | **Strongest for an impact-led data/AI team** |
| Frankenstein | The broadest category, so likely the most entries (hypothesis; we can't verify counts) | Needs a believable "why these incompatible parts" story | High | Crowded; it's hard to stand out |
| Skeleton Crew | Won 1st overall in 2025. Two apps required, which probably filters out weaker teams | **About 1.6–2× the work** (template plus two apps) | Medium | High upside, but 13 days is tight; 2026 copycats are likely |
| Costume Contest | Design and presentation heavy; 3rd overall in 2025 | Heavy visual and motion design and sound | Low-medium (our strength is AI and data, not visual design) | Hard to win against design-first teams |

**Student prizes.** Each category's student prize goes to the highest-scoring all-student submission in that category. So **winning a student prize means out-scoring the other student teams in our category**, which is a much more realistic target than 1st overall. The recommendation is optimised first for **Category + Student prize**, while staying capable of reaching the top 3.

---

## 5. What the final submission must show
1. A working end-to-end flow in the video, on the real target device or setup, within about 150 seconds.
2. A hosted, testable URL that judges can use without installing anything.
3. A `.kiro/` folder that tells a story: multiple **specs** (feature and bugfix), **steering** (product, tech, structure, plus a domain-specific doc), **hooks** that automate real chores, at least one **custom agent**, **MCP** use, **PBT** linked to requirements, and ideally a **Power** or **Crew app** we wrote ourselves.
4. A Kiro write-up that answers every prompt in the rules with specifics: before/after examples, counterexamples that PBT caught, and what each hook automated.
5. Evidence of real users: conversations, quotes, real or realistic sample data.
6. Bonuses that cost little: a blog post (Bonus Blog), a social post starting with `#KiroweenHackathon26`, and student details.
