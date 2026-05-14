# Contracts Module Context
*Spec section: 6.1 | Slug: `contracts` | Status: phase-8-done (module live)*
*Last updated: feat/contracts-phase8-integration-US-001 — sprint-1*

## Purpose
Manages the lifecycle of client contracts from draft creation through approval and expiry. Replaces the team's spreadsheet-based contract tracking.

## What this module does NOT handle
Contract renewal, payment processing, document signing, and commission rate adjustment are out of scope. Approval workflow (draft → pending → active transitions) comes in a later sprint.

---

## Exports — agent-maintained
<!-- Auto-updated after Phase 8 merge. Do not edit manually. -->

### Service methods (contracts.service.ts)
- `contractService.listByOrg({ ctx, filters? })` → `{ data: Contract[] } | { error: string }`
- `contractService.getById({ contractId, ctx })` → `Contract | null`
- `contractService.create({ data: CreateContractInput, ctx })` → `{ data: Contract } | { error: string }`
- `contractService.createDraft({ data: CreateDraftContractInput, ctx })` → `{ data: Contract } | { error: string }`
- `contractService.update({ contractId, data: UpdateContractInput, ctx })` → `{ data: Contract } | { error: string }`
- `contractService.delete({ contractId, ctx })` → `{ data: Contract } | { error: string }`

### Types (contracts.schema.ts)
- `CreateContractInput` — startDate (future date), accountManagerId (uuid), contractType (enum)
- `CreateDraftContractInput` — all fields optional (AC-010: draft bypasses required-field validation)
- `UpdateContractInput` — partial of CreateContractInput
- `ContractIdInput` — contractId (uuid)
- `ListContractsInput` — page, pageSize, status? (enum)
- `Contract` — the full DB row type (from db/schema)

### Permissions required
- `contracts:create` → Account Manager, Admin (covers both create and createDraft)
- `contracts:update` → Account Manager (own org only), Admin
- `contracts:delete` → Account Manager (own org only), Admin

*Note: `contracts:viewCommissionRate` (for the commission_rate field) is NOT yet implemented — that permission and its enforcement come in a future sprint.*

---

## Design decisions — dev-maintained

- **commission_rate excluded from all Zod schemas** — Sensitive/PII field. Finance sets it through a separate, permission-gated flow (AC-011, future story). Including it in create/update schemas would allow any AM to bypass Finance review.

- **contractType is a fixed enum: standard, premium, enterprise** — PM confirmed this during sprint-1 planning. Not a lookup table. Revisit if types need to be user-configurable.

- **orgId and orgUnitId always sourced from CallerContext** — never from user input. Even if a caller passed an orgId in the request body, the service ignores it and uses ctx.orgId. This is how the org isolation tests pass.

- **status never accepted as user input** — service sets `draft` on creation. Status transitions will be handled by dedicated methods in future stories (approval flow).

- **createDraft uses the same permission as create** — `contracts:create` covers both. Draft creation is a precursor to a full contract, not a separate capability.

---

## Cross-module dependencies
- **Reads from:** (none yet — accountManagerId is a uuid, no FK enforced in this sprint)
- **Referenced by:** (none yet — reporting module will reference this in a future sprint)
- **Coordinating service:** (none — this module is standalone in v1.0)

---

<!-- PHASE 5 SKELETON (shown for reference — this is what Phase 5 produced before Phase 8 filled the Exports section)

# Contracts Module Context
*Spec section: 6.1 | Slug: `contracts` | Status: phase-5-in-progress*

## Purpose
Manages the lifecycle of client contracts from draft creation through approval and expiry.

## What this module does NOT handle
Contract renewal, payment processing, document signing, and commission rate adjustment are out of scope. Approval workflow (draft → pending → active) comes in a later sprint.

## Exports — agent-maintained
(filled after Phase 8)

## Design decisions
- contractType is a fixed enum (standard, premium, enterprise) — PM confirmed during sprint-1 planning

-->
