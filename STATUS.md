# Canon Status — Snapshot

*One-screen view of where the canon and pipeline are right now. Updated at every major milestone.*

---

## Where we are

**The canon is published (v2.0).** Sections 0–11 + guidelines. Read `canon/quick-reference.md` first.

**The discovery pipeline is complete.** Runs in Codex. Produces module cards, data dictionary, ACs, behavioral specs, permission extraction, Miro prompt, SPEC.md consolidation, and change manifests.

**The coding agent pipeline is complete (Step 9).** Six agents, eight commands, two preflight scripts:

| Command | Agent | Phase |
|---|---|---|
| `/wireframe [module]` | wireframe-agent | Design — PDF analysis or prototype generation |
| `/plan-sprint` | orchestrator | Planning — wireframe-aware sprint planning |
| `/plan-change` | orchestrator | Planning — spec change absorption |
| `/status` | orchestrator | Review — read-only progress summary |
| `/schema [module] US-XXX` | schema-agent | Phase 5 — Drizzle + Zod + service stubs |
| `/test [module] US-XXX` | test-agent | Phase 6 — BEHAVIORS.md + failing tests |
| `/code [module] US-XXX` | code-agent | Phase 7 — implementation |
| `/ship [module] US-XXX` | ship-agent | Phase 8 — E2E + a11y + CLAUDE.md exports |

**Worked examples exist** for the full pipeline: sprint planning session, US-001 four-phase implementation, wireframe discussion.

**The starter template is documented but not bootstrapped.** `templates/starter/STARTER-PLAN.md` defines the structure. The actual project repo has not been built.

**Brownfield workstream is fully deferred.**

---

## Current state: stable checkpoint, ready for pilot

The pipeline is complete enough to run against a real project. Recommended next action: pilot with the golden example module. Capture what diverges from the worked examples and revise the agents accordingly.

---

## What's decided but not yet built

| Item | Notes |
|---|---|
| Starter template actual files | STARTER-PLAN.md exists; repo not built |
| Golden example module | After first pilot |
| `acceptance-criteria-guide.md` permission column update | See OPEN-ISSUES.md |
| `phase-handoffs.md` wireframe + change manifest update | See OPEN-ISSUES.md |
| Section 12 update for change manifest gate | Partially described in orchestrator |
| Production patterns | Soft deletes, uploads, email, background jobs, i18n, theming — all deferred |

---

*Last updated: May 2026 — Step 9 complete*
