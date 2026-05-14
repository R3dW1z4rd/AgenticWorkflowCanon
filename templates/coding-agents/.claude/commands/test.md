---
description: Phase 6 — Failing Tests. Invoked via /test [module-slug] US-XXX after Phase 5 PR is merged.
---

# /test [module-slug] US-XXX

Runs Phase 6 for a user story.

## Usage

```
/test contracts US-001
/test customers US-007
```

## Step 1 — Preflight

```bash
bash .agent/scripts/preflight-phase.sh test [module-slug] [US-XXX]
```

Checks that Phase 5 PR is merged, no open branch already exists for this phase, and the working directory is clean. Handles PASS / WARNINGS / BLOCKED with the same pattern as /plan-sprint.

## Step 2 — Load and propose

The test agent reads the Phase 5 service interface and behavior expectations from the issue body, then presents a complete behavior list for developer approval before writing any test code.

Approval phrase: `BEHAVIORS APPROVED`

## Step 3 — Generate, verify, commit

The agent writes BEHAVIORS.md (commit 1), then test files (commit 2). All service tests must fail. Schema tests may pass.

Branch: `feat/[module-slug]-phase6-tests-[STORY_ID]`

## Step 4 — Developer review and merge

When the PR merges, GitHub/Gitea Actions ticks the Phase 6 checkbox and updates `docs/project-state.md`.

## Next

```
/code [module-slug] [US-XXX]
```

## Related commands
- `/schema [module] US-XXX` — Phase 5, must be merged before this
