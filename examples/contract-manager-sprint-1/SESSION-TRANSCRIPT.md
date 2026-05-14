# Worked Example — Orchestrator Session: Contract Manager Sprint 1

*This is a fully-worked example of an orchestrator session, end to end. The conversation, the artifacts produced, the developer's actions. Read this once to understand what working with the orchestrator actually feels like.*

---

## Setting

**Project:** Contract Manager (the discovery example in `examples/contract-manager/`)
**Status:** Phase 4 handoff is complete. SPEC.md v1.0 sits in `docs/specs/`, tagged `spec-v1.0`. One module identified: contract-creation. 12 ACs. 37 behavioral specs.
**Team:** One developer, one PM, weekly UAT sessions planned.
**Today:** First sprint of the project. The orchestrator has never been invoked before. The state file was initialized when the developer ran `install-coding-agents.sh`.

The developer opens the project in VS Code. Claude Code is running in the integrated terminal. They type:

```
/plan-sprint
```

---

## The session

### Preflight runs

The slash command executes `bash .agent/scripts/preflight-plan-sprint.sh`. Output:

```
OK: Spec tag spec-v1.0 exists
OK: SPEC.md matches its locked tag
OK: Issue provider: github

PREFLIGHT_RESULT=PASS
```

Exit code 0. The orchestrator agent loads.

### Orchestrator opens

> Good morning. I've loaded the project state and the current spec.
>
> Here's what I see:
>
> - **Project:** Contract Manager, slug `contract-manager`
> - **Spec version:** v1.0 (tag `spec-v1.0`)
> - **Org context:** `org-with-units` — branches under regions, AMs belong to a branch
> - **Current product version:** v1.0.0 (in development)
> - **Sprint:** sprint-1 (no prior sprints)
> - **Modules in spec:** 1 (Contract Creation)
> - **Stories in backlog:** 0 (this is the first planning session)
>
> The spec has 12 acceptance criteria for the contract-creation module — that's enough material for 4–6 user stories, depending on how we group them.
>
> Before I propose a sprint plan, I want to confirm two things:
>
> 1. **Team capacity for this sprint** — single developer? Sprint length?
> 2. **Sprint goal** — what do you want a stakeholder to be able to see at the end?
>
> The second one matters more. If the goal is "AMs can create their first draft contract end-to-end," that shapes the plan very differently from "AMs can do everything from create through approval."

### Developer responds

> One developer, two-week sprint. For sprint 1 I want the AM to be able to create a draft contract and save it. We don't need the Forex API integration yet — that can come in sprint 2. And we definitely don't need approval workflow yet.

### Orchestrator proposes

> Good. That narrows scope significantly and is a sensible first sprint.
>
> Walking through the 12 ACs against your goal:
>
> | AC | What it covers | In sprint 1? |
> |---|---|---|
> | AC-001 | Initiate new contract from list view | Yes — entry point |
> | AC-002 | Required fields on step 1 (start date, AM, type) | Yes — basic validation |
> | AC-003 | Reject past start date | Yes — first validation rule |
> | AC-004, AC-005 | Forex rate display + loading/error | No — deferred to sprint 2 |
> | AC-006, AC-007 | Referrals (up to 5, conditional fields) | No — step 3, beyond draft |
> | AC-008 | Audit log on status change | Partial — only the draft creation audit |
> | AC-009 | Email when moves to Pending Approval | No — no approval flow yet |
> | AC-010 | Save as Draft without validation | Yes — this IS the goal |
> | AC-011 | Commission rate visible only to AM/Finance | Defer — no commission yet |
> | AC-012 | Auto-save every 60s | No — Could priority, defer |
>
> That gives us a sprint focused on AC-001, AC-002, AC-003, AC-010, and partial AC-008.
>
> **Proposed user story breakdown:**
>
> Two stories, both Medium complexity:
>
> **US-001 — AM can create a draft contract with required step-1 fields**
> Covers AC-001, AC-002, AC-003, AC-010. Single happy path: AM clicks "New Contract" → fills start date / AM / contract type → saves as draft. Validation rejects past dates. Saving as draft skips required-field validation.
>
> Files: full Phase 5–8 cycle on the `contracts` module. New table, schema, service stubs, then tests, then implementation, then E2E.
>
> **US-002 — System logs contract creation in audit trail**
> Covers AC-008 (partial — just the draft creation event). Pure backend; no UI work. Adds the audit table integration and writes an audit record when a contract is created.
>
> This depends on US-001 (audit needs a contract to exist).
>
> **Dependency sequence:**
> US-001 → US-002 (US-002 needs US-001's schema)
>
> **Risk areas:**
> - 🚩 Spec section 6.1.11 has an open question: "Should expired contracts be archivable or hard-deletable?" This doesn't affect sprint 1 (we don't have expiry yet) but flag it for PM before sprint 2.
> - The `contracts` module is brand new — no existing schema, no module CLAUDE.md yet. Phase 5 of US-001 creates the foundation. If anything is wrong in Phase 5, US-002 inherits it.
>
> **Deliberately excluded from sprint 1:**
> - Forex API integration (your call — sprint 2)
> - Referrals subsystem (step 3 of the flow, multi-step UI complexity)
> - Approval workflow (status transitions beyond draft)
> - Commission rate field gating (no commission in scope)
> - Auto-save (Could priority, low value for v1.0)
>
> **Assumptions I'm making:**
> - "Save as Draft" creates a `contracts` row with `status = draft` and no required-field enforcement at the DB level (Zod schema gates this in the service layer per the canon)
> - The contract list view exists in the codebase already, or US-001 creates a minimal list to host the "New Contract" button (your call — let me know if list view is a separate story)
>
> **Open questions for you:**
> - Is the contract list view in scope for US-001, or is it assumed to exist?
> - Two-week sprint with two medium stories — does that feel right for a first sprint, or would you prefer to keep it to just US-001 to learn the rhythm?
>
> ---
>
> Reply `APPROVE PLAN` to generate planning artifacts.
> Reply with refinements to continue planning.

### Developer refines

> Good catch on the list view. Include a minimal list in US-001 — just a table with the new contract button, no filters or sorting. And let's keep both stories in sprint 1, I want to see how the pipeline handles a dependency.

### Orchestrator confirms

> Updating the plan:
>
> US-001 now includes a minimal list view (table + "New Contract" button, no filters/sorting). Slight bump in Phase 7 scope but stays Medium complexity overall.
>
> US-002 unchanged.
>
> Final plan:
>
> - **US-001** — AM can create a draft contract with required step-1 fields (Medium)
> - **US-002** — System logs contract creation in audit trail (Medium, depends on US-001)
>
> Sprint goal: AM creates a draft contract end-to-end, and the system records it in audit.
>
> ---
>
> Reply `APPROVE PLAN` to generate planning artifacts.

### Developer approves

> APPROVE PLAN

### Orchestrator writes artifacts

> Writing planning artifacts to your local working copy.
>
> - Updating `docs/project-state.md` — sprint-1 section added, sprint goal recorded
> - Creating `.work/issue-bodies/US-001.md` — full issue body for US-001
> - Creating `.work/issue-bodies/US-002.md` — full issue body for US-002
> - Creating `scripts/create-sprint-1-issues.sh` — issue creation script (GitHub variant per project provider)
> - Creating `.work/sprint-plans/sprint-1-summary.md` — short PM-readable summary
>
> Committing locally (no push):
>
> ```
> [main 3a9c2f1] plan: sprint-1 — target v1.0.0, 2 user stories
>  5 files changed, 287 insertions(+)
>  create mode 100644 .work/issue-bodies/US-001.md
>  create mode 100644 .work/issue-bodies/US-002.md
>  create mode 100644 .work/sprint-plans/sprint-1-summary.md
>  create mode 100644 scripts/create-sprint-1-issues.sh
>  modify  mode 100644 docs/project-state.md
> ```
>
> ---
>
> **Next steps for you:**
>
> 1. Review the planning commit:
>    ```
>    git log -1 -p
>    ```
> 2. Read `scripts/create-sprint-1-issues.sh` and one of the issue bodies (say, `US-001.md`) to make sure they look right.
> 3. When you're satisfied, push:
>    ```
>    git push
>    ```
> 4. Run the issue creation script:
>    ```
>    bash scripts/create-sprint-1-issues.sh
>    ```
> 5. Issues will appear on GitHub. Begin work with:
>    ```
>    /phase5 contracts US-001
>    ```
>
> US-002 must wait until US-001 is fully done (all four phases merged) because the schema doesn't exist yet.
>
> Session complete. Good luck with sprint 1.

---

## What the orchestrator produced

The five files committed in the planning commit. Each shown below in full or condensed form.

### `.work/sprint-plans/sprint-1-summary.md` (full)

The short summary the PM might read:

```markdown
# Sprint 1 — Contract Manager

| Field | Value |
|---|---|
| **Sprint goal** | AM can create a draft contract end-to-end, system records it in audit |
| **Target product version** | v1.0.0 |
| **Spec version** | v1.0 (tag spec-v1.0) |
| **Duration** | 2 weeks |
| **Stories** | 2 (both Medium complexity) |

## Stories

### US-001: AM can create a draft contract with required step-1 fields
Covers AC-001, AC-002, AC-003, AC-010. Includes a minimal contract list view (table + "New Contract" button, no filters). Full Phase 5–8 cycle on the contracts module.

### US-002: System logs contract creation in audit trail
Covers AC-008 (partial — draft creation event only). Backend-only. Adds audit table integration. Depends on US-001 being fully complete first.

## Deliberately excluded
Forex API integration, referrals subsystem, approval workflow, commission rate gating, auto-save. Each will be addressed in later sprints.

## Risk
The contracts module is brand new. US-001 Phase 5 establishes the foundation; any issues there propagate to US-002.

## Open from spec
SPEC.md section 6.1.11 open question on archival vs hard-delete for expired contracts. Not relevant to sprint 1 (no expiry yet). PM input needed before sprint that introduces lifecycle.
```

### `.work/issue-bodies/US-001.md` (condensed — see full version in template)

Following the issue template structure from `docs/issue-template.md`:

```markdown
# US-001: AM can create a draft contract with required step-1 fields

## User story
**As an** Account Manager
**I want to** create a new contract with start date, AM assignment, and contract type
**So that** I can capture client agreements as drafts before finalizing details

## Business context
The contract creation module replaces the existing spreadsheet workflow.
This first story establishes the minimal create-as-draft flow without
exchange rate fetching, referrals, or approval — those come in later sprints.

## SPEC reference
- **Module:** Contract Creation (slug: `contracts`)
- **Spec sections:** 6.1.1 (purpose), 6.1.4 (core flow steps 1–2), 6.1.6 (data dict), 6.1.7 (ACs 001, 002, 003, 010)
- **Spec tag:** `spec-v1.0`

## Acceptance criteria
- **AC-001** (Must): allow AM to initiate a new contract from the list view
  - Permission: `contracts:create`
- **AC-002** (Must): require Start Date, AM, and Contract Type before proceeding past Step 1
  - Permission: (none)
- **AC-003** (Must): reject a Start Date set in the past with a clear inline error
  - Permission: (none)
- **AC-010** (Should): allow saving as Draft without triggering required-field validation
  - Permission: `contracts:create`

## Security boundaries
- SB-1: User from Org B cannot access contracts from Org A (404)
- SB-2: User without `contracts:create` cannot create a contract (403)
- SB-3: Unauthenticated visitor at `/contracts/new` is redirected to /login

## Files this work will touch
**New:**
- db/schema/contracts.ts (Phase 5)
- modules/contracts/contracts.schema.ts (Phase 5)
- modules/contracts/contracts.service.ts (Phase 5 stubs, Phase 7 impl)
- modules/contracts/contracts.actions.ts (Phase 5 stubs, Phase 7 impl)
- modules/contracts/contracts.service.test.ts (Phase 6)
- modules/contracts/contracts.schema.test.ts (Phase 6)
- modules/contracts/BEHAVIORS.md (Phase 6a)
- modules/contracts/CLAUDE.md (Phase 5 skeleton, Phase 8 final)
- modules/contracts/components/ContractsList.tsx (Phase 7)
- modules/contracts/components/CreateContractForm.tsx (Phase 7)
- app/(dashboard)/contracts/page.tsx (Phase 7)
- app/(dashboard)/contracts/new/page.tsx (Phase 7)
- tests/e2e/contracts-create-draft.spec.ts (Phase 6 stubs, Phase 8 real)
- db/migrations/0001_create_contracts.sql (Phase 5 — auto-generated)

**Modified:**
- db/schema/index.ts (add contracts export)
- components/layout/Sidebar.tsx (add Contracts nav link)
- lib/auth/permissions.ts (register contracts:create)

## Business rules
- Start Date must not be in the past (AC-003)
- Required step-1 fields: startDate, accountManagerId, contractType (AC-002)
- Save as Draft bypasses required-field validation (AC-010) but still validates types and ranges
- New contracts are created with `status = 'draft'`
- Contracts are scoped to org and org unit (per `org-with-units` pattern from SPEC 3)

## Permissions required
| Permission | Required by | Default roles |
|---|---|---|
| `contracts:create` | AC-001, AC-010 | Account Manager, Admin |

## Cross-module dependencies
- **Depends on:** spec-v1.0 tag (already exists)
- **Blocks:** US-002 (audit log needs contracts to exist)

## Phase breakdown
- [ ] Phase 5 — Schema & Contracts → `feat/contracts-phase5-schema-US-001`
- [ ] Phase 6 — Failing Tests → `feat/contracts-phase6-tests-US-001`
- [ ] Phase 7 — Implementation → `feat/contracts-phase7-impl-US-001`
- [ ] Phase 8 — Integration → `feat/contracts-phase8-integration-US-001`

## Specialist agent invocations
1. `/phase5 contracts US-001`
2. After Phase 5 PR merged → `/phase6 contracts US-001`
3. After Phase 6 PR merged → `/phase7 contracts US-001`
4. After Phase 7 PR merged → `/phase8 contracts US-001`

## Definition of done
- [ ] All four phase PRs merged to main
- [ ] npm test passes
- [ ] npm run test:e2e passes
- [ ] Four required org isolation tests present
- [ ] No NotImplementedError in production code
- [ ] Module CLAUDE.md Exports section reflects final state
- [ ] Manual smoke test: create a draft as AM, see it persisted

## Risk and complexity
| Field | Value |
|---|---|
| Complexity tier | Medium |
| Estimated PR count | 4 (one per phase) |
| Risk areas | First module in this project — Phase 5 decisions cascade |
| Spec ambiguities | None for this story (AC-001/002/003/010 are well-defined) |
```

### `.work/issue-bodies/US-002.md` (highlights — same shape as US-001)

```markdown
# US-002: System logs contract creation in audit trail

## User story
**As a** system administrator
**I want to** have an audit record for every contract creation
**So that** compliance reviewers can trace who created what and when

## SPEC reference
- **Module:** Contract Creation (slug: `contracts`)
- **Spec sections:** 6.1.4 (step 4, audit-log step), 6.1.7 (AC-008)
- **Spec tag:** `spec-v1.0`

## Acceptance criteria
- **AC-008** (Must, partial scope): create an audit log entry whenever a contract status changes — this story handles draft creation only; later stories add other status transitions

## Cross-module dependencies
- **Depends on:** US-001 (the contracts table must exist)
- **Depends on:** lib/audit.ts pattern (per canon Section 9)
- **Blocks:** none

## Files this work will touch
**New:**
- modules/contracts/audit/contract-audit.service.ts (Phase 5/7)
- modules/contracts/audit/contract-audit.service.test.ts (Phase 6)
- migration 0002_audit_log if not already present

**Modified:**
- modules/contracts/contracts.service.ts — call audit.record() inside create()
- modules/contracts/contracts.service.test.ts — assert audit record was written

## Phase breakdown
(same four-phase structure; smaller scope than US-001)

## Risk and complexity
| Field | Value |
|---|---|
| Complexity tier | Medium |
| Risk areas | Crosses from contracts module into audit; verify audit pattern matches canon Section 9 |
```

### `scripts/create-sprint-1-issues.sh`

```bash
#!/usr/bin/env bash
# Sprint 1 issue creation — generated 2026-05-12
# Target version: v1.0.0 | Spec version: spec-v1.0 | Provider: github
#
# Review this script before running.
# To create all issues at once: bash scripts/create-sprint-1-issues.sh

set -euo pipefail

gh auth status || { echo "Error: gh CLI not authenticated"; exit 1; }

echo "Creating sprint 1 issues on GitHub..."

gh issue create \
  --title "US-001: AM can create a draft contract with required step-1 fields" \
  --label "user-story,sprint-1,module-contracts,phase-5,phase-6,phase-7,phase-8" \
  --body-file .work/issue-bodies/US-001.md \
  --assignee "@me"

gh issue create \
  --title "US-002: System logs contract creation in audit trail" \
  --label "user-story,sprint-1,module-contracts,phase-5,phase-6,phase-7,phase-8" \
  --body-file .work/issue-bodies/US-002.md \
  --assignee "@me"

echo "Done. Created 2 issues for sprint 1."
echo "Next: /phase5 contracts US-001 to start work on US-001."
echo "Note: US-002 depends on US-001 being fully complete before it can begin."
```

### `docs/project-state.md` (updated section)

The orchestrator added a Current sprint section and updated module status:

```markdown
## Current sprint — sprint-1

| Field | Value |
|---|---|
| **Sprint goal** | AM can create a draft contract end-to-end, system records it in audit |
| **Target product version** | v1.0.0 |
| **Spec version** | v1.0 |
| **Started** | 2026-05-12 |
| **Estimated end** | 2026-05-26 |
| **Status** | planning |

### Issues in this sprint

| Story | Title | Module | Status | Phases (5/6/7/8) | Notes |
|---|---|---|---|---|---|
| US-001 | AM can create a draft contract | contracts | open | ☐ ☐ ☐ ☐ | minimal list + create form |
| US-002 | System logs contract creation | contracts | open | ☐ ☐ ☐ ☐ | depends on US-001 |

## Module status

| Module | Slug | Highest phase complete | Stories | Last touched | Notes |
|---|---|---|---|---|---|
| Contract Creation | contracts | not started | US-001, US-002 | sprint-1 | first module of project |
```

---

## What the developer does next

After the orchestrator session ends:

```bash
# 1. Review the plan
git log -1 -p

# 2. Read the issue body for US-001
cat .work/issue-bodies/US-001.md

# 3. Push the planning commit
git push

# 4. Create the issues on GitHub
bash scripts/create-sprint-1-issues.sh

# 5. Begin work on US-001
/phase5 contracts US-001
```

The Phase 5 specialist takes over from here. The orchestrator's job is done until sprint 1 closes or a spec update triggers `/plan-change`.

---

## What this example demonstrates

**1. Plan-mode discipline**
The orchestrator never wrote a single file until the developer typed `APPROVE PLAN`. The entire conversation — proposal, refinement, dependency analysis, exclusion list — happened before any artifact was committed.

**2. Scope discipline**
The orchestrator pulled the developer's stated goal ("create a draft, save it") and reflected it back as a story plan that deliberately excluded forex, referrals, approval, commissions, and auto-save. Each exclusion was named and justified. This is the orchestrator earning its existence — it could have proposed all 12 ACs in sprint 1 and overwhelmed the team.

**3. Dependency surfacing**
The orchestrator caught that US-002 depends on US-001's schema and recorded the dependency in both the issue body and the script's closing message. The developer doesn't have to remember sequencing.

**4. Risk surfacing**
The orchestrator flagged that the contracts module is brand new — Phase 5 decisions cascade through Phases 6, 7, 8 for both stories. It also surfaced the spec's open question (archival vs hard-delete) as relevant *later*, not in sprint 1. Honest about what's risky now and what's a future concern.

**5. Token discipline**
The orchestrator never read a source file (none exist yet). It read SPEC.md, project-state.md, and the workflow documents — total context cost roughly 12,000 tokens at session start. The conversation added maybe 4,000 tokens of proposal and refinement. The artifacts written total ~3,000 tokens. Whole session under 20,000 tokens for two well-structured user stories with traceable dependencies.

**6. The developer is dispatcher**
The orchestrator produced the script. The developer reads it. The developer runs it. The developer invokes the Phase 5 specialist. Nothing is autonomous. Everything is checked.

---

## Variations on this example

This example shows a happy-path first sprint. Real variations to expect:

**Sprint 2 onwards** — the orchestrator reads the updated state file and proposes building on what's done. Conversation is shorter because there's a rhythm established.

**Spec change planning** — developer invokes `/plan-change` instead of `/plan-sprint` after the discovery agent produces a CHANGE-MANIFEST. The orchestrator reads the manifest and proposes work specifically for the changed sections.

**Mid-sprint status** — developer invokes `/status` to get a read-only progress summary. Orchestrator reads state, summarizes, suggests next steps but doesn't write anything.

**Carry-over** — at the next sprint planning, the preflight warns that US-002 is still open from sprint-1. The orchestrator asks: carry over, drop, or split? The developer decides.

**Refusal scenarios** — developer says "while you're at it, fix this typo in contracts.service.ts." Orchestrator refuses: "That's specialist territory. Open a separate session with the Phase 7 specialist or just fix it manually."

---

*This is the kind of session the orchestrator is designed for. The conversation is the artifact; the committed files are the by-product. When sessions look different from this — when the orchestrator drifts into code review, or skips the approval gate, or proposes work without explaining trade-offs — that's the signal that the agent definition needs revision.*
