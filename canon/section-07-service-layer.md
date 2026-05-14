# Architecture Canon
## Section 7 — Service Layer
*Version 2.1 | Last updated: April 2026*

---

### What this section covers

What a service owns, what it never does, how to structure every method, error handling patterns, transaction management, when to extract a queries file, and how to keep services readable as they grow. The service layer is where the application's business logic lives. Everything else in the architecture exists to deliver clean, validated, authenticated input to this layer and to carry its output back to the caller.

---

### What a service owns

A service is responsible for exactly these things:

1. **Business rule enforcement** — duplicate checks, state validation, constraint checks, anything that requires reasoning about the data
2. **All Drizzle queries** for its module — SELECT, INSERT, UPDATE, DELETE
3. **Transaction management** — when multiple DB operations must succeed or fail together
4. **Logging and audit events** — recording that something happened, who did it, and when
5. **The return value** — typed data on success, a descriptive error string on business failure

Nothing else belongs here. If you find yourself doing something not on this list inside a service method, it belongs in a different layer.

---

### What a service never does

| Never | Why |
|---|---|
| Validate input shape | Already done by Zod at the API boundary. The service receives data that is already confirmed valid. |
| Read the session or call auth helpers | Auth is already confirmed. Services receive a `CallerContext` as an explicit parameter. A service that reads the session cannot be tested without faking one. |
| Construct a `CallerContext` itself | Context is always produced by `requireOrgAccess()`, `requirePermission()`, or `authorizeAgent()`. Never by the service. |
| Call another module's service directly | Cross-module data composition belongs in `app/` pages. Module services are isolated by design. |
| Format data for the UI | Services return plain typed database rows. Presentation logic belongs in components. |
| Throw for business failures | A duplicate name or an invalid state transition is an expected outcome. Return `{ error: string }`. Only system errors throw. |

---

### CallerContext — the service's trust anchor

Every service method that writes data receives a `CallerContext`. This is the verified object produced by the policy helpers or `authorizeAgent()`. It carries:

```typescript
type CallerContext = {
  userId:            string          // who is responsible for this action
  orgId:             string          // which org is being acted upon
  callerType:        'user' | 'agent'
  sessionId?:        string          // present for human callers
  agentId?:          string          // present for agent callers
  agentPermissions?: Permission[]    // present for agent callers
}
```

Services extract `orgId` and `userId` from the context. They never receive them as separate loose strings for write operations. Read operations that don't need a full audit trail may receive `{ orgId }` directly — but write operations always receive `ctx`.

**Why this matters for agents:** A service that accepts a loose `orgId` string can be called by an agent passing any `orgId` it wants. A service that requires a `CallerContext` can only be called after going through an authorized construction path — `requireOrgAccess()` for humans, `authorizeAgent()` for agents. The context is the proof that authorization happened.

---

### The standard service structure

Every service is a named object exported from `[module].service.ts`. Read methods receive `orgId` directly for simplicity. Write methods always receive the full `CallerContext`.

```typescript
// modules/branches/branches.service.ts
import { db } from '@/db'
import { branches } from '@/db/schema'
import { and, eq, ilike, count } from 'drizzle-orm'
import { logger } from '@/lib/logger'
import { audit } from '@/lib/audit'
import type { CallerContext } from '@/lib/auth/caller-context'
import type {
  CreateBranchInput,
  UpdateBranchInput,
  ListBranchesInput,
} from './branches.schema'

export const branchService = {

  // ── READ ─────────────────────────────────────────────────────────
  // Read methods receive orgId directly — no audit trail needed

  async listByOrg({
    orgId,
    filters,
  }: {
    orgId:    string
    filters?: ListBranchesInput
  }) {
    const page     = filters?.page     ?? 1
    const pageSize = filters?.pageSize ?? 20
    const offset   = (page - 1) * pageSize

    const whereClause = and(
      eq(branches.orgId, orgId),
      filters?.region ? eq(branches.region,  filters.region)         : undefined,
      filters?.search ? ilike(branches.name, `%${filters.search}%`) : undefined,
    )

    const [items, [{ total }]] = await Promise.all([
      db.select().from(branches).where(whereClause).limit(pageSize).offset(offset),
      db.select({ total: count() }).from(branches).where(whereClause),
    ])

    return {
      data: items,
      pagination: {
        page,
        pageSize,
        total,
        totalPages: Math.ceil(total / pageSize),
      },
    }
  },

  async getById({
    branchId,
    orgId,
  }: {
    branchId: string
    orgId:    string
  }) {
    const result = await db
      .select()
      .from(branches)
      .where(and(
        eq(branches.id,    branchId),
        eq(branches.orgId, orgId)
      ))
      .limit(1)

    return result[0] ?? null
  },

  // ── WRITE ─────────────────────────────────────────────────────────
  // Write methods always receive ctx — the verified CallerContext

  async create({
    data,
    ctx,
  }: {
    data: CreateBranchInput
    ctx:  CallerContext
  }) {
    const { orgId, userId } = ctx

    // Business rule: branch names must be unique within the org
    const existing = await db
      .select({ id: branches.id })
      .from(branches)
      .where(and(
        eq(branches.name,  data.name),
        eq(branches.orgId, orgId)
      ))
      .limit(1)

    if (existing.length > 0) {
      return { error: 'A branch with this name already exists' }
    }

    const [branch] = await db
      .insert(branches)
      .values({ ...data, orgId })
      .returning()

    logger.info('branch.created', { branchId: branch.id, orgId, userId })
    audit.record({ action: 'branch.created', resourceId: branch.id, ctx })

    return { data: branch }
  },

  async update({
    branchId,
    data,
    ctx,
  }: {
    branchId: string
    data:     UpdateBranchInput
    ctx:      CallerContext
  }) {
    const { orgId, userId } = ctx

    // Fetch before write — confirms existence AND org ownership
    const existing = await db
      .select()
      .from(branches)
      .where(and(
        eq(branches.id,    branchId),
        eq(branches.orgId, orgId)
      ))
      .limit(1)

    if (!existing[0]) return { error: 'Branch not found' }

    // Business rule: if renaming, confirm the new name is not taken
    if (data.name && data.name !== existing[0].name) {
      const nameConflict = await db
        .select({ id: branches.id })
        .from(branches)
        .where(and(
          eq(branches.name,  data.name),
          eq(branches.orgId, orgId)
        ))
        .limit(1)

      if (nameConflict.length > 0) {
        return { error: 'A branch with this name already exists' }
      }
    }

    const [updated] = await db
      .update(branches)
      .set({
        ...(data.name   !== undefined && { name:   data.name }),
        ...(data.region !== undefined && { region: data.region }),
        updatedAt: new Date(),
      })
      .where(and(
        eq(branches.id,    branchId),
        eq(branches.orgId, orgId)
      ))
      .returning()

    logger.info('branch.updated', { branchId, orgId, userId })
    audit.record({ action: 'branch.updated', resourceId: branchId, ctx })

    return { data: updated }
  },

  async delete({
    branchId,
    ctx,
  }: {
    branchId: string
    ctx:      CallerContext
  }) {
    const { orgId, userId } = ctx

    const existing = await db
      .select()
      .from(branches)
      .where(and(
        eq(branches.id,    branchId),
        eq(branches.orgId, orgId)
      ))
      .limit(1)

    if (!existing[0]) return { error: 'Branch not found' }

    await db
      .delete(branches)
      .where(and(
        eq(branches.id,    branchId),
        eq(branches.orgId, orgId)
      ))

    logger.info('branch.deleted', { branchId, orgId, userId })
    audit.record({ action: 'branch.deleted', resourceId: branchId, ctx })

    return { data: { id: branchId } }
  },
}
```

---

### How Server Actions pass CallerContext to services

```typescript
// modules/branches/branches.actions.ts
'use server'

import { createBranchSchema } from './branches.schema'
import { branchService } from './branches.service'
import { requireOrgAccess, requirePermission } from '@/lib/auth/policy'
import { PERMISSIONS } from '@/lib/auth/permissions'

export async function createBranchAction(input: unknown) {
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input', issues: parsed.error.issues }

  // ctx is CallerContext — constructed by the policy helper, passed to the service
  const ctx = await requirePermission(PERMISSIONS.branches.create)

  return branchService.create({ data: parsed.data, ctx })
}
```

---

### How agent entry points pass CallerContext to services

Agents bypass Server Actions entirely. They call `authorizeAgent()` and pass the resulting context directly to services — the service code is identical:

```typescript
// lib/agents/branch-sync.agent.ts
import { authorizeAgent } from '@/lib/auth/agent-context'
import { requireAgentPermission } from '@/lib/auth/policy'
import { PERMISSIONS } from '@/lib/auth/permissions'
import { branchService } from '@/modules/branches/branches.service'

export async function runBranchSyncAgent(token: string) {
  const ctx = await authorizeAgent(token)
  requireAgentPermission(ctx, PERMISSIONS.branches.create)

  return branchService.create({
    data: { name: 'Synced Branch', region: 'North' },
    ctx, // same CallerContext shape — service does not know the caller type
  })
}
```

---

### Service method naming — the convention

| Operation | Method name | Parameters |
|---|---|---|
| Fetch all for an org | `listByOrg` | `{ orgId, filters? }` |
| Fetch one by ID | `getById` | `{ [resource]Id, orgId }` |
| Fetch one by unique field | `getByEmail`, `getByName` | `{ field, orgId }` |
| Create | `create` | `{ data, ctx }` |
| Update | `update` | `{ [resource]Id, data, ctx }` |
| Delete | `delete` | `{ [resource]Id, ctx }` |
| Domain operation | `archive`, `activate`, `transfer` | `{ [resource]Id, ctx, ...extras }` |

---

### Error handling inside services

**Business failures → return `{ error: string }`**
```typescript
if (existing.length > 0) return { error: 'A branch with this name already exists' }
if (branch.status === 'archived') return { error: 'Archived branches cannot be updated' }
```

**Not found → return `null`**
```typescript
return result[0] ?? null  // caller decides: notFound() or { error: '...' }
```

**System errors → let them throw**
```typescript
try {
  await db.insert(branches).values(data)
} catch (e) {
  if (isUniqueConstraintError(e)) return { error: 'Name already exists' }
  throw e  // re-throw everything unexpected
}
```

**The decision tree:**
```
Business rule violated?  → return { error }
Record not found?        → return null
Unexpected system error? → throw
```

---

### The org context invariant

Every query that reads or writes data filters by `orgId`. This is extracted from `ctx` in write methods and passed directly in read methods. It is never a user-supplied value.

```typescript
// ✅ Both conditions on every query — existence AND ownership
.where(and(eq(branches.id, branchId), eq(branches.orgId, orgId)))

// ❌ ID alone — any org can access any record by guessing the ID
.where(eq(branches.id, branchId))
```

---

### Transactions

Use a transaction when two or more database writes in the same method must succeed or fail together:

```typescript
async create({ data, ctx }) {
  return db.transaction(async (tx) => {
    const [branch] = await tx.insert(branches).values({ ...data, orgId: ctx.orgId }).returning()
    await tx.insert(auditLog).values({ action: 'branch.created', resourceId: branch.id })
    return { data: branch }
  })
}
```

Single-table writes are atomic by default — no transaction needed.

---

### Logging and audit

Every successful write calls both before returning:

```typescript
logger.info('branch.created', { branchId: branch.id, orgId: ctx.orgId })
audit.record({ action: 'branch.created', resourceId: branch.id, ctx })
```

`audit.record` receives `ctx` — not loose strings. This is what populates `callerType` and `agentId` in the audit trail, making human and agent actions fully distinguishable. Full audit implementation is in Section 10 (Production Operations).

---

### When to extract a queries file

Add `[module].queries.ts` when:
- The service file exceeds ~150 lines and most of the bulk is query code
- A query has multiple joins or conditional clauses that obscure business logic
- The same complex query is needed in more than one service method

```typescript
// modules/reports/reports.queries.ts — queries only
export const reportsQueries = {
  async listWithDetails({ orgId, filters }) {
    return db
      .select({ id: reports.id, title: reports.title, branchName: branches.name })
      .from(reports)
      .innerJoin(branches, eq(reports.branchId, branches.id))
      .where(eq(reports.orgId, orgId))
  },
}

// modules/reports/reports.service.ts — business logic only
import { reportsQueries } from './reports.queries'
export const reportService = {
  async listByOrg({ orgId, filters }) {
    const items = await reportsQueries.listWithDetails({ orgId, filters })
    return { data: items }
  },
}
```

---

### Keeping services readable as they grow

1. Extract complex queries to `[module].queries.ts` first — solves 80% of cases
2. Group methods with section comments — READ / WRITE / DOMAIN OPERATIONS
3. Split into sub-services only when there are genuinely distinct concerns — not just length

---

### Service checklist — before committing

- [ ] Write methods receive `ctx: CallerContext` — not loose `orgId`/`userId` strings
- [ ] Read methods filter by `orgId` on every query
- [ ] Every UPDATE and DELETE filters by both `id` AND `orgId`
- [ ] Business failures return `{ error: string }` — not thrown
- [ ] Not found returns `null`
- [ ] Successful writes call `logger.info` and `audit.record({ ..., ctx })`
- [ ] No session reads inside the service
- [ ] No calls to other module services
- [ ] No Zod validation inside the service
- [ ] Input types are derived from Zod schemas
- [ ] Transactions used when two or more tables are written in one method
- [ ] Service never constructs a `CallerContext` — it only receives one

---

### How to use this document

- **Developers:** Every write method receives `ctx`. Extract `orgId` and `userId` from it — never pass them as separate strings. When a business rule check is needed, it goes in the service, never in the action or component.
- **Agents:** Generate write method signatures as `{ data, ctx: CallerContext }`. Generate read method signatures with `{ orgId: string }` directly. Every successful write emits `audit.record({ action, resourceId, ctx })`. Never generate a service that constructs its own `CallerContext`.
- **Tech leads:** When reviewing a PR, verify that write methods accept `ctx`, that no query is missing the `orgId` filter, and that no service constructs its own context or reads the session. The checklist above is the review checklist.

---

*Previous: Section 6 — Auth & Authorization*
*Next: Section 8 — API Layer*
*See also: Caller Context & Agent Authorization Guideline*
