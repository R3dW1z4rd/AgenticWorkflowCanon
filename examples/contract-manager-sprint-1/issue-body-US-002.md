# US-002: System logs contract creation in audit trail

## User story

**As a** system administrator (and compliance reviewer)
**I want to** have an audit record for every contract creation
**So that** I can trace who created what and when, and demonstrate audit-readiness to clients

## Business context

The contract manager is replacing a spreadsheet workflow that has no audit trail. From day one, every contract creation must produce an audit record so the system is compliant with the client's record-keeping requirements. This story handles audit for the draft creation event only — later stories will add audit for status transitions (pending → active, etc.) as those transitions get implemented.

## SPEC reference

- **Module:** Contract Creation (slug: `contracts`)
- **Spec sections:**
  - 6.1.4 (Core flow, step 4 — "system creates audit log entry whenever a contract status changes")
  - 6.1.7 (Acceptance criteria AC-008)
- **Spec tag:** `spec-v1.0`

## Acceptance criteria

- **AC-008** (Must, partial scope for this story): The system must create an audit log entry whenever a contract status changes.
  - Permission: (none — audit is system action)
  - **Scope for this story:** draft creation event only. Audit for transitions (e.g. draft → pending) handled by future stories that implement those transitions.

## Security boundaries

- **SB-1**: Audit records are scoped to org. User from Org B cannot read Org A's audit records via the audit service (handled by canon Section 9 pattern).
- **SB-2**: Audit recording is a system action, not user-facing. No permission required to *trigger* an audit record; permission applies to *reading* audit records (out of scope for this story).
- **SB-3**: N/A — audit recording happens server-side after authenticated action.

## Files this work will touch

### New files

| File | Phase | Notes |
|---|---|---|
| `modules/contracts/audit/contract-audit.service.test.ts` | 6 | Tests for audit record format and write |

### Modified files

| File | Phase | Notes |
|---|---|---|
| `modules/contracts/contracts.service.ts` | 7 | `create()` and `createDraft()` call `audit.record()` after successful insert |
| `modules/contracts/contracts.service.test.ts` | 6 | Add assertions: audit record is written, contains expected fields |
| `modules/contracts/CLAUDE.md` | 8 | Update Exports section to note audit integration |

### Note on `lib/audit.ts`

This story assumes `lib/audit.ts` exists from the canon starter scaffolding. If it does not exist yet in the project, the Phase 5 specialist will need to scaffold it from the canon Section 9 pattern. Verify before starting.

## Business rules to enforce

- Every successful contract creation (draft or full) writes an audit record
- Audit record contains: timestamp, actor (user ID), action (`contract.created`), resource (contract ID), and the CallerContext metadata (orgId, orgUnitId, ip if available)
- Audit recording is part of the same transaction as the contract creation — if audit write fails, contract creation rolls back
- Per canon Section 9: audit records are append-only, never deleted, never updated

## Permissions required

None for this story. Audit is a system action triggered by the contract creation. Reading audit records is governed by a separate permission (`audit:read`) handled in future stories.

## Cross-module dependencies

- **Depends on:**
  - US-001 fully complete (all four phase PRs merged) — the contracts table and service must exist
  - `lib/audit.ts` from canon scaffolding (verify exists)
- **Blocks:**
  - None for sprint 1
- **Related, not blocking:**
  - Future stories that add status transitions will follow the pattern established here

## Phase breakdown

- [ ] **Phase 5 — Schema & Contracts** → `feat/contracts-phase5-audit-US-002`
  - No new table (audit table provided by canon)
  - Update `contracts.service.ts` interface to indicate audit integration
  - No new Zod schemas

- [ ] **Phase 6 — Failing Tests** → `feat/contracts-phase6-tests-US-002`
  - Commit 1: `BEHAVIORS.md` updates with audit-related behaviors
  - Commit 2: Test files
    - Update `contracts.service.test.ts` to assert audit records are written
    - New file `modules/contracts/audit/contract-audit.service.test.ts` for audit-specific tests

- [ ] **Phase 7 — Implementation** → `feat/contracts-phase7-impl-US-002`
  - Update `contractService.create()` to call `audit.record()` per canon Section 9
  - Update `contractService.createDraft()` to call `audit.record()`
  - Ensure both calls share the same transaction as the contract insert
  - All tests pass

- [ ] **Phase 8 — Integration & Polish** → `feat/contracts-phase8-integration-US-002`
  - E2E test: create a draft contract, query the audit log, verify the record
  - Manual smoke test on staging
  - Update `modules/contracts/CLAUDE.md` Exports section to mention audit integration

## Specialist agent invocations

```
1. /phase5 contracts US-002
2. After Phase 5 PR merged → /phase6 contracts US-002
3. After Phase 6 PR merged → /phase7 contracts US-002
4. After Phase 7 PR merged → /phase8 contracts US-002
```

**Important:** /phase5 will refuse to start US-002 if US-001 is not fully done. Confirm US-001's four PRs are merged before invoking /phase5 contracts US-002.

## Definition of done

- [ ] All four phase PRs merged to main
- [ ] Tests assert audit records are written for create and createDraft
- [ ] Transactional integrity verified (audit fails → contract creation rolls back)
- [ ] Manual smoke test on staging: create a draft, query audit log, see the record with correct fields
- [ ] Module CLAUDE.md mentions audit integration in Exports
- [ ] Issue auto-closed when Phase 8 merges

## Risk and complexity assessment

| Field | Value |
|---|---|
| **Complexity tier** | Medium |
| **Estimated PR count** | 4 (smaller than US-001 since no new UI) |
| **Risk areas** | First audit integration in this project. Pattern established here will be copied by every future status transition story. Get the transactional semantics right — audit and contract write must be atomic. |
| **Spec ambiguities** | None for this story. AC-008 is well-defined for the draft-creation case. |

## Attachments

- Audit pattern reference: canon Section 9 (loaded automatically by the Phase 5 / 7 specialist)
- Behavioral specs: SPEC.md section 6.1.8 (audit-related behaviors)
