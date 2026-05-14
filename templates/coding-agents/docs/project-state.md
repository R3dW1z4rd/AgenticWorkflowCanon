# Project State

> *This file is the source of truth for project status. The orchestrator agent reads it at session start to plan sprints. The GitHub Actions workflow updates it when PRs are merged. Humans read it to understand where things stand.*
>
> **Edit this file with intention.** It is read by both humans and agents. Keep it structured and concise — long-form notes belong in issues or commit messages, not here.

---

## Project info

| Field | Value |
|---|---|
| **Project name** | _[project name]_ |
| **Project slug** | _[kebab-case-slug]_ |
| **Org context** | _[org-only \| org-with-units \| customer-account]_ |
| **Current spec version** | _[v1.0]_ |
| **Current spec tag** | _[spec-v1.0]_ |
| **Current product version** | _[v1.0.0]_ (in development) |
| **Last released version** | _[none]_ |
| **Current sprint** | _[sprint-1]_ |
| **Repository** | _[git remote URL]_ |
| **Default branch** | _[main]_ |
| **Issue provider** | _[github \| gitea \| manual]_ |
| **Gitea server URL** | _[https://gitea.example.com — only if issue_provider=gitea]_ |
| **CI / state automation** | _[GitHub Actions \| Gitea Actions \| manual]_ |

---

## Version history

*One row per released product version. The product version is what ships to the client. The spec version is the SPEC.md tag the work was implemented against.*

| Product version | Released | Spec version | Sprint | Stories shipped | Notes |
|---|---|---|---|---|---|
| _[v1.0.0]_ | _[not yet]_ | _[spec-v1.0]_ | _[sprint-1]_ | _[US-001, US-002, US-003]_ | _[initial release]_ |

---

## Spec version history

*One row per SPEC.md version. The SPEC version may update multiple times before a product version ships, if changes batch together.*

| Spec version | Date tagged | Trigger | Stories enabled | Notes |
|---|---|---|---|---|
| _[spec-v1.0]_ | _[2026-05-01]_ | _[initial spec]_ | _[US-001 through US-008]_ | _[Phase 4 sign-off complete]_ |

---

## Current sprint — sprint-1

| Field | Value |
|---|---|
| **Sprint goal** | _[one-sentence goal: what should the team have done by the end of this sprint]_ |
| **Target product version** | _[v1.0.0]_ |
| **Spec version** | _[spec-v1.0]_ |
| **Started** | _[2026-05-02]_ |
| **Estimated end** | _[2026-05-16]_ |
| **Status** | _[planning \| in progress \| in review \| closed]_ |

### Issues in this sprint

*One row per user story. The "Status" column is auto-updated by the GitHub Actions workflow when PRs are merged. The "Phases" column reflects which of the 4 phases are complete.*

| Story | Title | Module | Status | Phases (5/6/7/8) | Notes |
|---|---|---|---|---|---|
| _[US-001]_ | _[story title]_ | _[contracts]_ | _[open]_ | _[☐ ☐ ☐ ☐]_ | |
| _[US-002]_ | _[story title]_ | _[contracts]_ | _[open]_ | _[☐ ☐ ☐ ☐]_ | |
| _[US-003]_ | _[story title]_ | _[users]_ | _[open]_ | _[☐ ☐ ☐ ☐]_ | |

**Status values:** `open` (not yet started) · `in-progress` (specialist working) · `in-review` (PR open) · `closed` (all 4 phases merged)

---

## Module status

*The current state of every module in the project. Updated when a story completes a phase on that module.*

| Module | Slug | Highest phase complete | Stories | Last touched | Notes |
|---|---|---|---|---|---|
| _[Contract Creation]_ | _[contracts]_ | _[not started]_ | _[—]_ | _[—]_ | |
| _[User Management]_ | _[users]_ | _[not started]_ | _[—]_ | _[—]_ | |

**Phase values:** `not started` · `phase 4 (spec only)` · `phase 5 done` · `phase 6 done` · `phase 7 done` · `phase 8 done (module live)`

---

## Backlog

*Stories the orchestrator has identified from the SPEC but not yet scheduled into a sprint. The orchestrator pulls from this list when planning the next sprint.*

| Story | Title | Module | Priority | Spec section | Notes |
|---|---|---|---|---|---|
| _[US-004]_ | _[story title]_ | _[contracts]_ | _[Must]_ | _[6.1.7]_ | _[depends on US-001]_ |
| _[US-005]_ | _[story title]_ | _[users]_ | _[Should]_ | _[6.2.7]_ | |

---

## Carry-over

*Stories that didn't complete in their original sprint. Tracked separately so retros can identify patterns.*

| Story | Original sprint | Reason | Action |
|---|---|---|---|
| _[—]_ | _[—]_ | _[—]_ | _[carried to sprint-N \| dropped \| split]_ |

---

## Recent activity

*Last 10 state changes, newest first. The GitHub Actions workflow appends to this list when PRs merge. Older entries scroll off the bottom.*

```
[2026-05-12 14:30] state: US-006 phase 7 merged (PR #42)
[2026-05-12 11:15] state: US-006 phase 6 merged (PR #41)
[2026-05-11 16:00] state: US-006 phase 5 merged (PR #40)
[2026-05-10 09:00] plan: sprint-1 created — 3 stories, target v1.0.0
```

---

## Open questions and blockers

*Anything that's holding work back or needs a decision. The orchestrator surfaces these during status reviews.*

| Question / Blocker | Affects | Owner | Status |
|---|---|---|---|
| _[Should we extend contract status enum with 'archived'?]_ | _[US-008]_ | _[PM]_ | _[awaiting answer]_ |

---

## Maintenance notes

- This file is read at the start of every orchestrator session
- The GitHub Actions workflow at `.github/workflows/update-state.yml` updates this file automatically when PRs merge
- Manual edits are allowed but should be committed with a clear message: `state: [description]`
- When this file exceeds 500 lines, consider archiving completed sprint sections to `docs/project-state-archive.md`
- The orchestrator never modifies historical sections (version history, completed sprints) — only the current sprint and module status
