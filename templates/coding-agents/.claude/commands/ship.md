---
description: Phase 8 — Integration & Polish. Invoked via /ship [module-slug] US-XXX after Phase 7 PR is merged.
---

# /ship [module-slug] US-XXX

Runs Phase 8 for a user story.

## Usage

```
/ship contracts US-001
/ship customers US-007
```

## Step 1 — Preflight

```bash
bash .agent/scripts/preflight-phase.sh ship [module-slug] [US-XXX]
```

Checks that Phase 7 PR is merged, no open branch already exists for this phase, and the working directory is clean. Handles PASS / WARNINGS / BLOCKED with the same pattern as /plan-sprint.

## Step 2 — Load and propose

The ship agent reads the Phase 7 implementation, runs the gate checklist, and replaces E2E stubs with real tests.

Approval phrase: `SMOKE PASSED`

## Step 3 — Generate, verify, commit

The agent runs E2E tests, a11y audit, smoke test confirmation, updates CLAUDE.md Exports, then commits.

Branch: `feat/[module-slug]-phase8-integration-[STORY_ID]`

## Step 4 — Developer review and merge

When the PR merges, GitHub/Gitea Actions ticks the Phase 8 checkbox and updates `docs/project-state.md`. The issue closes automatically.

## Next

```
/schema [module-slug] US-XXX   ← next story
```

## Related commands
- `/code [module] US-XXX` — Phase 7, must be merged before this
