---
description: Read-only sprint and project progress review. Shows current sprint status, module completion, blocked items, and upcoming milestones. No files are written. Invokes the orchestrator in status mode.
---

# /status

Invokes the orchestrator in **status review mode** (Mode 3). Read-only. No files written, no issues created.

Use this at any point during a sprint to understand where the project stands.

## What it shows

```
## Sprint 1 Status — Contract Manager (2026-05-12 → 2026-05-26)

Sprint goal: AM can create a draft contract end-to-end

Stories:
  US-001  AM can create a draft contract      ✓ ✓ ✓ ☐   in-progress (Phase 7 merged, Phase 8 pending)
  US-002  System logs contract creation        ☐ ☐ ☐ ☐   open (waiting on US-001)

Progress: 1/2 stories complete, 1 in-progress

Module status:
  contracts   phase-7-done

Upcoming:
  - US-002 unblocked once US-001 Phase 8 merges
  - Sprint 1 ends 2026-05-26 (13 days from now)
  - Sprint 2 planning: 2 deferred stories in backlog (Forex API, contract list view)

Open questions and blockers:
  - (none logged)

Spec status: spec-v1.0 (current), no pending change manifest
```

## When to use /status

- **Start of day** — quick check before picking up work
- **Before a sprint review** — understand what's done vs in-progress
- **Before running /plan-sprint** — confirm the current sprint is in a state to close
- **Before running /plan-change** — understand sequencing risk before absorbing a spec update
- **When something feels stuck** — the orchestrator will flag stories open longer than expected

## What the orchestrator looks for

**Normal patterns:**
- Stories progressing through phases in order
- Phases completing within a sprint window

**Patterns worth surfacing:**
- A story open for more than 5 days without a phase change
- Multiple stories in-progress simultaneously on the same module (coordination risk)
- Stories in the backlog that are blocked on another module's completion
- A spec version with stories still mid-implementation when a change manifest arrives

**The orchestrator does NOT:**
- Suggest closing or reopening issues
- Change priorities
- Modify project-state.md
- Create or modify issues

It reads, summarises, and observes. All decisions remain with the developer.

## No preflight

`/status` has no preflight. It is read-only and safe to run at any time from any branch state.

## Related commands

- `/plan-sprint` — when you've confirmed the current sprint is wrapping up
- `/plan-change` — when a new CHANGE-MANIFEST has arrived and you need to absorb it
- `/schema [module] US-XXX` — to resume work on a specific story
