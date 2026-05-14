# US-001: AM can create a draft contract with required step-1 fields

## User story

**As an** Account Manager
**I want to** create a new contract with start date, AM assignment, and contract type
**So that** I can capture client agreements as drafts before finalizing details

## Business context

The contract creation module replaces the existing spreadsheet workflow. Currently, AMs track contracts in shared spreadsheets, which creates version conflicts, missed approvals, and unauditable changes. This first story establishes the minimal create-as-draft flow without exchange rate fetching (sprint 2), referrals (sprint 3+), or approval workflow (sprint 3+). Saving as a draft lets AMs capture partial information without enforcing all final-state requirements.

## SPEC reference

- **Module:** Contract Creation (slug: `contracts`)
- **Spec sections:**
  - 6.1.1 (Business purpose)
  - 6.1.4 (Core flow, steps 1–2 only)
  - 6.1.6 (Data dictionary — entity: Contract)
  - 6.1.7 (Acceptance criteria AC-001, AC-002, AC-003, AC-010)
- **Spec tag:** `spec-v1.0`

## Acceptance criteria

*Verbatim from SPEC.md 6.1.7.*

- **AC-001** (Must): The system must allow an Account Manager to initiate a new contract from the list view.
  - Permission: `contracts:create`
- **AC-002** (Must): The system must require Start Date, Account Manager, and Contract Type before proceeding past Step 1.
  - Permission: (none)
- **AC-003** (Must): The system must reject a Start Date set in the past and display a clear inline error.
  - Permission: (none)
- **AC-010** (Should): The system must allow saving a contract as Draft without triggering required-field validation.
  - Permission: `contracts:create`

## Security boundaries

*All three are non-negotiable per the canon.*

- **SB-1** (cross-org access): User from Org B requesting a contract ID belonging to Org A receives 404 (not 403, to avoid leaking existence).
- **SB-2** (missing permission): Authenticated user without `contracts:create` attempting to create a contract receives 403 / `{ error: 'Forbidden' }`.
- **SB-3** (unauthenticated): Visitor navigating to `/contracts/new` without an active session is redirected to `/login`.

## Files this work will touch

### New files

| File | Phase | Notes |
|---|---|---|
| `db/schema/contracts.ts` | 5 | Drizzle table with orgId, orgUnitId per org-with-units pattern |
| `db/migrations/0001_create_contracts.sql` | 5 | Auto-generated from schema |
| `modules/contracts/contracts.schema.ts` | 5 | Zod schemas (create, update, list, id) |
| `modules/contracts/contracts.service.ts` | 5 / 7 | Service stubs at 5, impl at 7 |
| `modules/contracts/contracts.actions.ts` | 5 / 7 | Server Action stubs at 5, impl at 7 |
| `modules/contracts/contracts.service.test.ts` | 6 | Service tests including 4 org isolation tests |
| `modules/contracts/contracts.schema.test.ts` | 6 | Zod schema validation tests |
| `modules/contracts/BEHAVIORS.md` | 6a | Given-When-Then bullets, committed separately |
| `modules/contracts/CLAUDE.md` | 5 / 8 | Skeleton at 5, Exports filled at 8 |
| `modules/contracts/components/ContractsList.tsx` | 7 | Minimal table + New Contract button |
| `modules/contracts/components/CreateContractForm.tsx` | 7 | Step 1 form (start date, AM, type) |
| `app/(dashboard)/contracts/page.tsx` | 7 | List page wired to listByOrg |
| `app/(dashboard)/contracts/new/page.tsx` | 7 | Form page wired to create action |
| `tests/e2e/contracts-create-draft.spec.ts` | 6 / 8 | Stubs at 6, real assertions at 8 |

### Modified files

| File | Phase | Notes |
|---|---|---|
| `db/schema/index.ts` | 5 | Add `export * from './contracts'` |
| `lib/auth/permissions.ts` | 5 | Register `contracts.create` |
| `components/layout/Sidebar.tsx` | 7 | Add Contracts nav link |

## Business rules to enforce

- Start Date must not be in the past (AC-003) — Zod refinement on the date field, error displayed inline by the form
- Required fields on step 1: `startDate`, `accountManagerId`, `contractType` (AC-002) — enforced at the Zod schema level for non-draft saves
- Save as Draft bypasses required-field validation (AC-010) — the `createDraftContractSchema` makes all fields optional except those needed to identify the record
- New contracts are created with `status = 'draft'`
- Contracts are scoped to org and org unit per the project's `org-with-units` pattern (SPEC.md section 3)
- Created by: the AM's user ID is captured at creation time

## Permissions required

| Permission | Required by | Default roles |
|---|---|---|
| `contracts:create` | AC-001, AC-010 | Account Manager, Admin |

## Cross-module dependencies

- **Depends on:**
  - `spec-v1.0` tag exists (already true)
  - `lib/auth/caller-context.ts` from canon scaffolding (exists per project starter)
  - `lib/audit.ts` from canon scaffolding (exists per project starter; US-001 does not call audit, US-002 will)
- **Blocks:**
  - US-002 (audit log integration needs the contracts table to exist)
- **Related, not blocking:**
  - Future stories on the contracts module will extend the schema added here

## Phase breakdown

This story moves through all four coding phases. Each phase is a separate branch, separate PR.

- [ ] **Phase 5 — Schema & Contracts** → `feat/contracts-phase5-schema-US-001`
  - Drizzle table with orgId, orgUnitId, status enum, required step-1 fields
  - Zod schemas: full and draft variants
  - Service interface with throwing stubs for: listByOrg, getById, create, createDraft, update, delete
  - Server Action stubs
  - Module CLAUDE.md skeleton (Purpose + Out of Scope from SPEC)
  - Migration runs cleanly up and down

- [ ] **Phase 6 — Failing Tests** → `feat/contracts-phase6-tests-US-001`
  - Commit 1: `BEHAVIORS.md` with Given/When/Then bullets (one per behavior)
  - Commit 2: Test files
    - `contracts.schema.test.ts` — Zod validation including reject-past-date
    - `contracts.service.test.ts` — service methods + four required org isolation tests
    - `tests/e2e/contracts-create-draft.spec.ts` — happy path stub + permission boundary stub
  - All tests fail (NotImplementedError on service, components don't exist yet)

- [ ] **Phase 7 — Implementation** → `feat/contracts-phase7-impl-US-001`
  - Implement service methods, all tests pass
  - Implement Server Actions
  - Build ContractsList and CreateContractForm components
  - Wire pages
  - No NotImplementedError remains

- [ ] **Phase 8 — Integration & Polish** → `feat/contracts-phase8-integration-US-001`
  - E2E happy path passing
  - E2E permission boundary passing (member without `contracts:create` cannot create)
  - A11y audit ≥ 95 on both pages
  - Manual smoke test on staging
  - Module CLAUDE.md Exports section completed

## Specialist agent invocations

```
1. /phase5 contracts US-001
2. After Phase 5 PR merged → /phase6 contracts US-001
3. After Phase 6 PR merged → /phase7 contracts US-001
4. After Phase 7 PR merged → /phase8 contracts US-001
```

The slash commands will refuse to proceed if preconditions aren't met (e.g. /phase6 won't run if /phase5's PR isn't merged).

## Definition of done

- [ ] All four phase PRs merged to main
- [ ] `npm test` passes (unit + integration)
- [ ] `npm run test:e2e` passes
- [ ] Four required org isolation tests present in `contracts.service.test.ts`
- [ ] No `NotImplementedError` in production code (`grep -r "NotImplementedError" src/` returns nothing)
- [ ] `modules/contracts/CLAUDE.md` Exports section reflects final state
- [ ] Manual smoke test on staging: AM logs in → navigates to Contracts → creates draft → sees it persisted
- [ ] PR descriptions reference this issue (US-001)
- [ ] Issue auto-closed by the state-update workflow when Phase 8 merges

## Risk and complexity assessment

| Field | Value |
|---|---|
| **Complexity tier** | Medium |
| **Estimated PR count** | 4 (one per phase) |
| **Risk areas** | First module of project — Phase 5 patterns will be copied by every subsequent module. Get the Drizzle table structure, the Zod schema layout, and the service signature shape right. |
| **Spec ambiguities** | None for this story. AC-001/002/003/010 are well-defined. The 🚩 in 6.1.11 (archival vs hard-delete) does not apply here. |

## Attachments

- Wireframe: _[link to Miro / Figma — to be attached]_
- Data dictionary excerpt: SPEC.md section 6.1.6
- Behavioral specs: SPEC.md section 6.1.8 (specifically B-001 through B-005, B-014)
