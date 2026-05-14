---
description: Phase 5 — Schema & Contracts. Produces the Drizzle table, Zod schemas, service stubs, action stubs, and module CLAUDE.md skeleton for a user story. Run after the issue exists and before /test.
---

# /schema [module-slug] US-XXX

Runs Phase 5 for a user story. Produces the data model and service interface the test and code agents build on.

## Usage

```
/schema contracts US-001
/schema customers US-007
/schema referrals US-012
```

## Step 1 — Preflight

```bash
bash .agent/scripts/preflight-phase.sh schema [module-slug] [US-XXX]
```

**Exit 0 (PASS):** proceed to Step 2.

**Exit 2 (WARNINGS):** surface warnings to developer conversationally and ask whether to proceed. Common warnings: working directory not clean, module slug not found in SPEC, story already shows Phase 5 complete.

**Exit 1 (BLOCKED):** stop and explain remediation. Common blockers: story not in project-state.md (run `/plan-sprint` first), previous phase not complete (not applicable for Phase 5 — it's the first phase).

## Step 2 — Load and propose

The schema agent reads the issue body, project state, SPEC module section, and any existing module files. It presents a **full design proposal** covering:

- Drizzle table columns with types and nullability decisions explained
- Zod schemas with explicit exclusion reasoning (Sensitive/PII, system-controlled fields)
- Service method signatures
- New permissions to register
- CLAUDE.md skeleton contents
- Open questions that need developer input before proceeding

The developer reviews the proposal and may refine it through conversation.

## Step 3 — Approval and generation

When the developer is satisfied with the proposal, they type:

```
SCHEMA APPROVED
```

The schema agent then:
1. Writes all files within its allowed write surface
2. Runs gate checks (`tsc --noEmit`, `db:generate`, `db:migrate` up and down)
3. Fixes any issues found during gate checks
4. Commits to `feat/[module-slug]-phase5-schema-[STORY_ID]`
5. Opens a PR

## Step 4 — Developer review and merge

Review the PR focusing on:
- Table structure vs SPEC data dictionary
- Zod schemas — confirm no Sensitive/PII fields present
- Service method signatures — these are what Phase 6 tests call
- Migration — does it run cleanly up and down?

When the PR merges, the GitHub/Gitea Actions workflow ticks the Phase 5 checkbox in the issue and updates `docs/project-state.md` automatically.

## Step 5 — Proceed to Phase 6

After the PR merges:

```
/test [module-slug] [US-XXX]
```

## What /schema never does

- Implements service methods (all stubs throw)
- Writes test files
- Writes components, pages, or routes
- Modifies SPEC.md
- Touches other modules' service or schema files
- Pushes to remote (developer reviews and pushes)

## Related commands

- `/plan-sprint` — creates the issue this command works from
- `/wireframe [module]` — produces the ui-spec.md the schema agent reads for nullable field decisions
- `/test [module] US-XXX` — Phase 6, runs after this PR merges
