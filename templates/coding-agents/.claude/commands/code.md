---
description: Phase 7 — Implementation. Invoked via /code [module-slug] US-XXX after Phase 6 PR is merged.
---

# /code [module-slug] US-XXX

Runs Phase 7 for a user story.

## Usage

```
/code contracts US-001
/code customers US-007
```

## Step 1 — Preflight

```bash
bash .agent/scripts/preflight-phase.sh code [module-slug] [US-XXX]
```

Checks that Phase 6 PR is merged, no open branch already exists for this phase, and the working directory is clean. Handles PASS / WARNINGS / BLOCKED with the same pattern as /plan-sprint.

## Step 2 — Load and propose

The code agent reads the Phase 6 test suite and the UI Specification from the issue body, then presents an implementation plan for developer approval before writing any code.

Approval phrase: `IMPLEMENTATION APPROVED`

## Step 3 — Generate, verify, commit

The agent implements until all tests pass, verifies no console statements or stubs remain, then commits.

Branch: `feat/[module-slug]-phase7-impl-[STORY_ID]`

## Step 4 — Developer review and merge

When the PR merges, GitHub/Gitea Actions ticks the Phase 7 checkbox and updates `docs/project-state.md`.

## Next

```
/ship [module-slug] [US-XXX]
```

## Related commands
- `/test [module] US-XXX` — Phase 6, must be merged before this
