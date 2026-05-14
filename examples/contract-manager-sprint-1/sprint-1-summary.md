# Sprint 1 — Contract Manager

| Field | Value |
|---|---|
| **Sprint goal** | AM can create a draft contract end-to-end, system records it in audit |
| **Target product version** | v1.0.0 |
| **Spec version** | v1.0 (tag spec-v1.0) |
| **Duration** | 2 weeks (2026-05-12 → 2026-05-26) |
| **Stories** | 2 (both Medium complexity) |
| **Developer capacity** | 1 |

## Stories

### US-001: AM can create a draft contract with required step-1 fields
Covers AC-001, AC-002, AC-003, AC-010. Includes a minimal contract list view (table + "New Contract" button, no filters or sorting). Full Phase 5–8 cycle on the contracts module.

Complexity: Medium. First module of the project — Phase 5 decisions establish patterns the rest of the codebase will follow.

### US-002: System logs contract creation in audit trail
Covers AC-008 (partial scope — draft creation event only). Backend-only work. Adds audit-table integration following canon Section 9.

Complexity: Medium. Depends on US-001 being fully complete (all four phases merged) before it can begin.

## Sequence and dependencies

```
US-001 → US-002
```

US-002 cannot start until the contracts schema exists. There is no parallelism in this sprint.

## Deliberately excluded from sprint 1

| Excluded | Why |
|---|---|
| Forex API integration (AC-004, AC-005) | Per developer call, deferred to sprint 2 |
| Referrals subsystem (AC-006, AC-007) | Step 3 of flow, multi-step UI complexity, scoped to a later sprint |
| Approval workflow (AC-009) | Email + status transition out of scope until basic CRUD is shipped |
| Commission rate gating (AC-011) | No commission rate in this story — defer permission/field-level work |
| Auto-save (AC-012) | Could priority, low ROI for v1.0 — defer to a polish sprint |

## Risk areas

1. **First-module foundation effect.** The contracts module is brand new — no existing schema, no module CLAUDE.md, no patterns established for this codebase. Decisions made in US-001 Phase 5 cascade through both stories.

2. **Audit integration not previously used.** This is the first time `lib/audit.ts` is being called from a service in this project. The pattern from canon Section 9 should be followed exactly. If the pattern is implemented incorrectly in US-002, future stories will copy the mistake.

## Open from spec (flagged for PM review before later sprints)

- **SPEC.md section 6.1.11**: "Should expired contracts be archivable or hard-deletable?" Not relevant to sprint 1 (no expiry yet). PM input needed before any sprint that introduces contract lifecycle states beyond draft.

## Assumptions made during planning

- Save as Draft creates a row with `status = 'draft'` and bypasses required-field validation at the Zod schema layer
- The contracts list view is minimal — a table with a "New Contract" button, no filters/sorting/pagination beyond defaults
- Audit log table either exists from canon scaffolding or is created in US-002 (specialist's call)

## Definition of sprint done

- Both stories closed (all 8 PRs merged — 4 per story)
- `docs/project-state.md` updated to reflect completion
- Manual smoke test on staging: AM logs in → creates a draft → sees it in audit log
- Module CLAUDE.md for `contracts` has Exports section filled
