# CLAUDE.md Structure Specification
*How to design the context files that Claude Code reads automatically at every coding session.*

---

## The three layers

Claude Code automatically reads `CLAUDE.md` files in a directory hierarchy. The agent working
in `modules/contracts/` receives three files in order:

```
project/CLAUDE.md             ← Layer 0: always loaded, every session
project/lib/CLAUDE.md         ← Layer 1: loaded when working in lib/ (optional)
project/modules/contracts/
  └── CLAUDE.md               ← Layer 1: loaded when working in contracts/
```

Each layer adds context without replacing the previous one. Design each layer to carry only
what agents working at that level actually need.

---

## Layer 0 — Project root CLAUDE.md

**Max length: 150 lines. Non-negotiable.**
This file loads at the start of every session regardless of what the agent is working on.
Every line costs tokens on every invocation. Treat every word as expensive.

### What belongs here

```markdown
# [Project Name]

## Stack
Next.js 15 (App Router) · TypeScript · Drizzle ORM · PostgreSQL
BetterAuth · shadcn/ui · Vitest · Playwright · pino

## Org context
type: org-only | org-with-units | customer-account
[one sentence describing what that means for this project]

## Non-negotiable rules (canon invariants)
- Every database query filters by orgId
- Every write method receives ctx: CallerContext, never loose strings
- Every write calls logger.info AND audit.record({ ..., ctx })
- Zod schemas never include id, orgId, createdAt, updatedAt
- Business failures return { error: string } — never throw
- Not found returns null — never { error }
- Four org isolation tests required per module — never skip

## Build and test commands
npm run dev              # start dev server
npm test                 # Vitest unit + integration
npm run test:e2e         # Playwright
npm run db:generate      # generate migration from schema changes
npm run db:migrate       # apply migrations
npm run scaffold:module  # generate new module skeleton

## Project map
docs/specs/SPEC.md       → locked spec (always read this first)
docs/architecture/       → synced canon (read relevant section per phase)
modules/[name]/          → domain modules (4 files each)
db/schema/               → Drizzle tables only
lib/                     → shared: auth, logger, audit, env, joins, services

## Active spec version
[spec-v1.0]              → read docs/specs/SPEC.md, check out this tag for reference

## Module index
[contracts]    → modules/contracts/   [phase: 5 | 6 | 7 | 8 | done]
[branches]     → modules/branches/    [phase: done]
[users]        → modules/users/       [phase: done]
```

### What never belongs here

- Full canon sections or long explanations of patterns
- Implementation examples or code samples
- Phase-specific workflow instructions
- Anything a developer only needs once
- Tool configuration
- Dependency lists

### Who maintains this file

The **developer** owns this file. The agent may propose additions but never writes to it
without explicit instruction. Update the Module index status after each phase merge.

---

## Layer 1 — Module CLAUDE.md

**Max length: 100 lines.**
Loaded automatically when the agent works in `modules/[name]/`.
Contains what agents need to understand this module without reading its source files.

### Structure

```markdown
# [Module Name] — Context
*Spec section: 6.X | Slug: [slug] | Status: phase-[N]-in-progress | Last updated: [commit]*

## Purpose
[One sentence. What business problem does this module solve?]

## What this module does NOT handle
[One sentence. The out-of-scope, copied from SPEC.md 6.X.10]

---

## Exports — agent-maintained
<!-- Auto-updated after Phase 8 merge. Do not edit manually. -->

### Service methods (contracts.service.ts)
- `contractService.listByOrg({ ctx, filters? })` → `{ data, pagination }`
- `contractService.getById({ contractId, ctx })` → `Contract | null`
- `contractService.create({ data: CreateContractInput, ctx })` → `{ data } | { error }`
- `contractService.update({ contractId, data: UpdateContractInput, ctx })` → `{ data } | { error }`
- `contractService.delete({ contractId, ctx })` → `{ data } | { error }`

### Types (contracts.schema.ts)
- `CreateContractInput` — startDate, accountManagerId, referralType (commission_rate excluded — PII)
- `UpdateContractInput` — all fields optional
- `ListContractsInput` — page, pageSize, status?
- `ContractIdInput` — contractId (UUID)

### Permissions required
- `contracts:create` → Account Manager, Admin
- `contracts:viewCommissionRate` → Account Manager, Finance, Admin
- `contracts:approve` → Finance, Admin

---

## Design decisions — dev-maintained
<!-- Add an entry any time a non-obvious decision is made. Agent may propose entries. -->

- `commission_rate` excluded from `CreateContractInput`: Sensitive/PII field set by Finance
  separately. Including it in create would allow any AM to bypass Finance review.
- Exchange rate fetched client-side every 30s, not stored: client requirement for live rates.
  Stale risk is acceptable per client decision (see SPEC.md 6.1.11 open question #2).

---

## Cross-module dependencies
- Reads from: users module (accountManagerId must be an active AM)
- Referenced by: reporting-dashboard module (contract status and dates)
- Coordinating service: none (this module is standalone)
```

### Who maintains what

| Section | Maintained by | When |
|---|---|---|
| Purpose, Out of scope | Developer | Once, at module creation |
| Exports (service methods, types, permissions) | Agent | Auto-updated after Phase 8 merge |
| Design decisions | Developer or agent (proposed) | Any time a non-obvious decision is made |
| Cross-module dependencies | Developer | After Phase 5 or when connections become clear |
| Status and last-updated | Agent | After each phase merge |

### When is this file created?

The Phase 5 agent creates a skeleton `modules/[slug]/CLAUDE.md` as part of Phase 5 output.
The skeleton has Purpose and Out of Scope from SPEC.md, empty Exports, and no Design decisions.
Exports are filled after Phase 8 (when the module is stable). Design decisions accumulate
through Phases 5–8 as the developer and agent make non-obvious choices.

---

## Optional: lib/ CLAUDE.md

If `lib/` grows to include non-obvious shared utilities, a `lib/CLAUDE.md` can summarize them.

```markdown
# lib/ — Shared utilities

## Auth
- requireOrgAccess() → CallerContext (use for reads)
- requirePermission(P) → CallerContext (use for writes)
- authorizeAgent(token) → CallerContext (use in agent entry points)

## Shared schemas
- lib/schemas/phone.ts → phoneSchema (used by: customers, branches)
- lib/schemas/money.ts → moneySchema (used by: contracts, invoices)

## Cross-module joins
- lib/joins/contracts-with-customer.ts → getContractsWithCustomer(orgId)
```

Add this file only when `lib/` contains things the agent would otherwise have to discover
by reading files. Do not create it preemptively.

---

## The CLAUDE.md lifecycle across phases

```
Project starts
  └─ Developer creates project/CLAUDE.md (from STARTER-PLAN.md template)

Phase 5 begins (for a module)
  └─ Agent creates modules/[slug]/CLAUDE.md skeleton (Purpose + Out of scope only)

Phase 5–7 in progress
  └─ Agent appends Design decisions as they arise
  └─ Developer edits Design decisions when they correct or override

Phase 8 complete, PR merged
  └─ Agent updates Exports section with final service methods, types, permissions
  └─ Agent updates Status in the file header
  └─ Developer reviews the update as part of Phase 8 PR

New module added
  └─ Developer updates Module index in project/CLAUDE.md
  └─ Agent adds cross-module dependency notes if relevant
```

---

## Size enforcement

Both files have hard limits because they load on every session:

| File | Hard limit | Rationale |
|---|---|---|
| `project/CLAUDE.md` | 150 lines | Loads every session — every extra line costs tokens forever |
| `modules/[slug]/CLAUDE.md` | 100 lines | Loads every phase session for this module |
| `lib/CLAUDE.md` | 60 lines | Rarely needed — if it needs more, restructure |

If a file approaches its limit, the right response is to move content to the SPEC.md or
a design-decisions log — not to raise the limit.

---

*This guideline is part of the Architecture Canon.*
*Referenced by: Phase 5 agent (creates module CLAUDE.md), Phase 8 agent (updates Exports)*
*Companion: `agent-token-discipline.md` (included in every coding agent's instructions)*
