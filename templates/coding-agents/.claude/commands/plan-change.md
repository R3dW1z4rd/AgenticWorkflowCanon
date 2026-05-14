---
description: Plan work required by a spec update. Reads the CHANGE-MANIFEST produced by the discovery agent, proposes the new or modified user stories, and generates issue creation scripts. Run after the discovery agent produces a new SPEC.md version and CHANGE-MANIFEST.
---

# /plan-change

Invokes the orchestrator in **spec change planning mode** (Mode 2). Used when the discovery agent has produced a new version of SPEC.md and a CHANGE-MANIFEST, and you need to plan how to absorb that change into the sprint backlog.

## When to use this vs /plan-sprint

| Situation | Command |
|---|---|
| Starting a new sprint (no spec change) | `/plan-sprint` |
| A spec update just landed (new tag + CHANGE-MANIFEST) | `/plan-change` |
| Checking progress mid-sprint | `/status` |

## Prerequisites

Before running `/plan-change`, the discovery agent must have:

1. Produced an updated `docs/specs/SPEC.md`
2. Tagged the new version: `git tag spec-v1.1` (or whichever version)
3. Produced `docs/specs/CHANGE-MANIFEST-v1.1.md`

If any of these are missing, the preflight will block with a clear remediation step.

## Step 1 — Preflight

```bash
bash .agent/scripts/preflight-plan-change.sh
```

Checks specific to spec changes:
- New spec tag exists in git that differs from `current_spec_tag` in project-state.md
- `docs/specs/SPEC.md` matches the new tag (no post-tag drift)
- `docs/specs/CHANGE-MANIFEST-v[X.Y].md` exists
- Warns if stories are currently in-progress (spec change mid-sprint needs sequencing)

## Step 2 — Orchestrator in Mode 2

The orchestrator reads:
1. `docs/project-state.md` — current sprint state, what's in-progress
2. `docs/specs/CHANGE-MANIFEST-v[X.Y].md` — what changed and which phases it affects
3. `docs/specs/SPEC.md` (new version) — the updated spec
4. Any `ui-spec.md` files for modules affected by the change

The orchestrator walks through the change manifest and proposes:

- **New stories** required by the change (new ACs, new entities, new permissions)
- **Modified stories** where existing stories need rework (AC changed, data model changed)
- **Unaffected stories** that can continue as planned
- **Sequencing** — does the change work happen in the current sprint or the next?
- **In-progress conflicts** — if a story is mid-implementation and the spec changed, what's the resolution?

## Step 3 — Discussion and approval

This is the most important conversation in a spec change cycle. The orchestrator surfaces:

- Exactly which ACs changed (from the CHANGE-MANIFEST's diff section)
- Whether the change affects Phase 5 artifacts already committed (schema changes are expensive mid-sprint)
- Whether UI changes require a `/wireframe` update before planning can complete
- The recommended sequencing

When the developer is satisfied: `APPROVE PLAN`

## Step 4 — Artifacts generated

Same as `/plan-sprint`:
- Updated `docs/project-state.md` — new `current_spec_tag`, new or modified sprint section
- `.work/issue-bodies/US-XXX.md` — for any new stories
- `scripts/create-sprint-N-change-issues.sh` — issue creation script for new stories
- `.work/sprint-plans/spec-change-v[X.Y]-summary.md` — brief summary of what changed and why

For **modified** stories (existing story whose scope changed), the orchestrator produces a comment body to post on the existing issue rather than creating a new one:

```
.work/issue-updates/US-XXX-spec-change-comment.md
```

The developer posts this comment manually (or via `gh issue comment US-XXX --body-file`).

## What /plan-change does NOT do

- Modify the SPEC.md or CHANGE-MANIFEST (those are discovery agent artifacts)
- Automatically update `current_spec_tag` in project-state.md without developer review of the plan
- Create issues without developer running the script
- Close or reopen existing issues

## Common scenarios

**Scenario A — Small AC change, no schema impact:**
The orchestrator proposes a small new story for the affected behavior. Current sprint continues unaffected. New story goes into backlog or next sprint.

**Scenario B — New entity added:**
The orchestrator proposes a new module (new Phase 5–8 cycle). If wireframes exist for the new entity, suggests `/wireframe [new-module]` before planning. New stories likely go into a new sprint.

**Scenario C — Existing field becomes required:**
If the field already exists in the DB (nullable), this is a Phase 7 fix — add validation to the service. The orchestrator creates a small story. If the field needs a migration (type change, new column), it flags this as a Phase 5 change and warns about schema divergence from merged work.

**Scenario D — Spec change mid-sprint while a story is in-progress:**
Preflight warns about in-progress work. Orchestrator asks: pause and absorb the change now, or finish the in-progress story first, then plan the change? Developer decides. Either way, the orchestrator doesn't proceed until the sequencing is explicit.

## Related commands

- `/plan-sprint` — for regular sprint planning (no spec change)
- `/status` — to understand current state before deciding if now is the right time for a spec change
- `/wireframe [module]` — if the spec change affects UI, update the wireframe spec first
