# Prior work disclosure (template for the application repository)

This application was built with **Kiro** during the Kiroween 2026 Submission Period. It builds on earlier work by the same entrant, also created during the Submission Period (21–22 Nov 2026), **with a different AI coding assistant (Claude Code)**:

- **Research and validation repository:** https://github.com/Sidd927/kiroween-2026, branch `poc/spoolgeist-validation`.
  - Contents: idea research, a technical proof of concept, the hardened reference engine (v4), synthetic generators, the sealed evaluation, adversarial test sets, mutation testing and FHIR validation reports.

**How it is used here:**
- As **reference material and a test oracle.** The application's engine was re-specified and implemented in Kiro. The research repository's sealed test split and held-out adversarial sets are used to check that the Kiro-built engine meets the same acceptance criteria.

**Copied verbatim** (keep this list exact):
- [ ] `lab_dictionary.json` (human-curated test dictionary)
- [ ] synthetic report generator `bench2/generator.py` (test fixtures only)
- [ ] _add any other file here_

**Not reused:** the research engine source is not part of this application's runtime, unless listed above.
