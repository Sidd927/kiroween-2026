# Kiro bootstrap kit (inputs for Kiro, not Kiro output)

These files were written with Claude Code **as briefs**. They are *inputs* you give Kiro, so that Kiro generates the real specs, steering and hooks in the new application repository. **Do not copy them into `/.kiro` as if Kiro wrote them.** Let Kiro produce `/.kiro/specs/*` and refine its own steering. That is what makes the Kiro usage genuine and the write-up honest.

## First session, step by step (about 1 hour)
1. **Install and sign in.** Install Kiro from https://kiro.dev (IDE, or the VS Code extension) and sign in. Open the Kiroween credit request form from the hackathon site and submit your **Kiro user ID**. The deadline is 1 Dec 12:00 PT, but submit today.
2. **Create and open the repository.** Create the public repository (e.g. `spoolgeist`) with an MIT licence and open it in Kiro.
3. **Steering.** In Kiro, run *Generate steering docs* (product / tech / structure). Then paste and adapt the content from `STEERING_INPUTS.md` into Kiro's generated files, and add a `safety.md` steering file. Keep Kiro's own wording where it is better.
4. **Prior work.** Copy `PRIOR_WORK.md` into the new repository root and keep it accurate.
5. **First spec.** In Kiro: *New spec* → paste the `engine-core` brief from `SPEC_BRIEFS.md` → let Kiro write `requirements.md` (EARS) → review → `design.md` → `tasks.md`. Ask Kiro to make the "abstain or exactly correct" requirement a **property-based test**.
6. **First hook.** Create a hook in Kiro: *on save in `engine/` → run the property tests*.
7. **Commit early and often** with Kiro-generated work, so the history shows the process.

## Files
| File | Contents |
|---|---|
| `SPEC_BRIEFS.md` | one brief per spec: engine-core, capture-and-forwarding, rule-onboarding, review-ui, fhir-export |
| `STEERING_INPUTS.md` | product, tech, structure and safety content to fold into Kiro's steering |
| `PRIOR_WORK.md` | template disclosure for the application repository |
