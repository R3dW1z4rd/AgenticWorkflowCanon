# Architecture Quick Reference
*Version 1.0 | Read this first. Read this often. The full canon is for edge cases.*

---

## The flow — every feature follows this path

```
UI form submit → Server Action → Zod parse → requireOrgAccess()
  → service.method({ data, ctx }) → Drizzle → PostgreSQL → returns up
```

The five layers, in order: **UI → Schema → Action → Service → Drizzle.** Nothing skips.

---

## The stack — what to reach for

| Need | Use |
|---|---|
| Framework | Next.js (App Router) |
| Language | TypeScript (no `any`) |
| Validation | Zod — written first, before any function |
| Database ORM | Drizzle — explicit SQL via TypeScript |
| Database | PostgreSQL |
| Auth | BetterAuth |
| UI components | shadcn/ui — solve here first, build custom only if forced |
| Unit/integration tests | Vitest |
| E2E tests | Playwright |
| Logging | pino |

To replace any default: document what business requirement the default cannot meet. Familiarity with an alternative is not a justification.

---

## Folder structure — where everything lives

```
app/             ← routes only (page.tsx, layout.tsx, route.ts)
modules/         ← domain modules — your application
db/              ← Drizzle schema + migrations only (no queries)
lib/             ← shared code (auth, logger, audit, env, joins)
components/      ← shared UI (shadcn/ui in components/ui)
tests/e2e/       ← Playwright tests
```

**Modules cannot import from each other.** Cross-module composition happens in `app/` pages, or in `lib/joins/` for shared queries, or in `lib/services/` for cross-module operations.

---

## The four files of every module

```
modules/branches/
├── branches.schema.ts      ← Zod schemas (write FIRST)
├── branches.service.ts     ← business logic
├── branches.actions.ts     ← Server Actions
└── components/             ← UI for this module
```

Optional fifth: `branches.queries.ts` when queries grow complex.

---

## The order of writing a feature — never deviate

```
1. db/schema/[table].ts          (Drizzle table)
2. drizzle-kit generate          (migration)
3. modules/[mod]/[mod].schema.ts (Zod schemas)
4. modules/[mod]/[mod].service.ts
5. modules/[mod]/[mod].actions.ts
6. modules/[mod]/components/
7. app/(dashboard)/[mod]/page.tsx
8. tests/e2e/[mod].spec.ts
```

---

## Canonical patterns — copy these exactly

### Drizzle table

```typescript
// db/schema/branches.ts
export const branches = pgTable('branches', {
  id:        uuid('id').defaultRandom().primaryKey(),
  orgId:     uuid('org_id').notNull(),         // every table has orgId
  name:      text('name').notNull(),
  region:    text('region').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export type Branch    = typeof branches.$inferSelect
export type NewBranch = typeof branches.$inferInsert
```

### Zod schema

```typescript
// modules/branches/branches.schema.ts
export const createBranchSchema = z.object({
  name:   z.string().min(1, 'Name is required').max(100, 'Name too long'),
  region: z.string().min(1, 'Region is required'),
  // NEVER include: id, orgId, createdAt, updatedAt
})
export type CreateBranchInput = z.infer<typeof createBranchSchema>

export const updateBranchSchema = createBranchSchema.partial()
export type UpdateBranchInput = z.infer<typeof updateBranchSchema>

export const branchIdSchema = z.object({
  branchId: z.string().uuid('Invalid branch ID'),
})
```

### Service method (write)

```typescript
// modules/branches/branches.service.ts
async create({ data, ctx }: { data: CreateBranchInput; ctx: CallerContext }) {
  const { orgId, userId } = ctx

  // Business rule check
  const existing = await db.select({ id: branches.id }).from(branches)
    .where(and(eq(branches.name, data.name), eq(branches.orgId, orgId)))
    .limit(1)
  if (existing.length > 0) return { error: 'Name already exists' }

  // Insert
  const [branch] = await db.insert(branches).values({ ...data, orgId }).returning()

  // Log + audit
  logger.info('branch.created', { branchId: branch.id, orgId, userId })
  audit.record({ action: 'branch.created', resourceId: branch.id, ctx })

  return { data: branch }
}
```

### Service method (read)

```typescript
async getById({ branchId, ctx }: { branchId: string; ctx: CallerContext }) {
  const result = await db.select().from(branches)
    .where(and(
      eq(branches.id,    branchId),
      eq(branches.orgId, ctx.orgId)   // ALWAYS filter by orgId
    ))
    .limit(1)
  return result[0] ?? null   // null = not found, caller decides what to do
}
```

### Server Action — exactly three steps, in order

```typescript
// modules/branches/branches.actions.ts
'use server'

export async function createBranchAction(input: unknown) {
  // 1. Validate
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input', issues: parsed.error.issues }

  // 2. Auth + context
  const ctx = await requirePermission(PERMISSIONS.branches.create)

  // 3. Call service, return result
  return branchService.create({ data: parsed.data, ctx })
}
```

### Page (Server Component) — fetches and passes props

```tsx
// app/(dashboard)/branches/page.tsx
export default async function BranchesPage() {
  const ctx = await requireOrgAccess()
  const branches = await branchService.listByOrg({ ctx })
  return <BranchList branches={branches.data} />
}
```

### Form (Client Component) — calls the action

```tsx
'use client'
export function CreateBranchForm() {
  const [isPending, startTransition] = useTransition()

  function handleSubmit(formData: FormData) {
    const input = {
      name:   formData.get('name')   as string,
      region: formData.get('region') as string,
    }
    startTransition(async () => {
      const result = await createBranchAction(input)
      if (result.error) toast({ title: result.error, variant: 'destructive' })
      else              toast({ title: 'Branch created' })
    })
  }

  return (
    <form action={handleSubmit}>
      <Input name="name"   required />
      <Input name="region" required />
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create branch'}
      </Button>
    </form>
  )
}
```

### Service test — the four required isolation tests per module

```typescript
describe('branchService', () => {
  it('cannot fetch a record from another org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()
    const created = await branchService.create({ data, ctx: orgA.ctx })
    const found = await branchService.getById({ branchId: created.data!.id, ctx: orgB.ctx })
    expect(found).toBeNull()
  })

  it('cannot update a record from another org', /* ... */)
  it('cannot delete a record from another org', /* ... */)
  it('list returns only own org records',       /* ... */)
})
```

---

## The contract — never break these

| Layer | Returns |
|---|---|
| Service success | `{ data: T }` |
| Service business failure | `{ error: string }` |
| Service not found | `null` |
| Service system error | throws |
| Server Action | passes service result through unchanged |

---

## Auth — three helpers, decision rule

| Use | When |
|---|---|
| `requireUser()` | Login required, no org needed (profile pages) |
| `requireOrgAccess()` | Read operations (default for reads) |
| `requirePermission(P)` | Write operations and restricted reads |

All three return `CallerContext`:
```typescript
{ userId, orgId, callerType: 'user' | 'agent', sessionId?, agentId?, agentPermissions? }
```

Never read the session inside a service. Always receive `ctx` as a parameter.

---

## The non-negotiable rules — ranked by severity

1. **Every query filters by `orgId`** — the security boundary
2. **Every write method receives `ctx: CallerContext`** — no loose strings
3. **Zod schema written before service code** — no exceptions
4. **No business logic in Server Actions** — three steps only
5. **No service calls inside components** — pages fetch, components render
6. **No cross-module imports** — composition happens in pages or `lib/`
7. **Every module has the four org isolation tests** — non-negotiable PR gate
8. **Every successful write calls `logger.info` + `audit.record`** — operational + compliance
9. **`process.env` accessed only via `lib/env.ts`** — startup-validated
10. **Migrations never edited after commit** — generate a new one to fix

---

## Common confusion — quick answers

| Question | Answer |
|---|---|
| Drizzle schema or Zod schema for input validation? | Zod. Drizzle defines DB shape, Zod defines what callers can send. |
| Server Action or Route Handler? | Server Action — unless caller is external (mobile, webhook, agent over HTTP). |
| Where does this query go? | Single module → in the module. Cross-module → `lib/joins/`. |
| Throw or return error? | Business failure → return `{ error }`. Not found → return `null`. System error → throw. |
| `requireOrgAccess` or `requirePermission`? | Reads → `requireOrgAccess`. Writes → `requirePermission`. |
| Field belongs in create schema? | Yes if the user provides it. No if the DB or service sets it (id, orgId, createdAt). |
| Update should require all fields? | No. Use `.partial()` — callers send only what changes. |
| Repository layer? | Not by default. Add `[module].queries.ts` only when service methods grow query-heavy. |

---

## Daily commands

```bash
# Database
npx drizzle-kit generate    # generate migration from schema changes
npx drizzle-kit migrate     # apply pending migrations
npx drizzle-kit studio      # visual DB browser (dev only)

# Tests
npm test                    # run Vitest
npm run test:e2e            # run Playwright

# Scaffold a new module
npm run scaffold:module     # generates schema, service, actions, components, tests
```

---

## Where to read more

| Topic | Document |
|---|---|
| **The end-to-end workflow (daily reference)** | **`workflow-quick-reference.md`** |
| **The full integrated workflow** | **Section 12 — Integrated Workflow** |
| **The SPEC.md structure** | **`spec-template.md`** |
| **Contract between phases (for agent design)** | **`phase-handoffs.md`** |
| **CLAUDE.md file structure + limits** | **`guidelines/claude-md-structure.md`** |
| **Token discipline for coding agents** | **`guidelines/agent-token-discipline.md`** |
| Why these decisions | Section 1 — Philosophy |
| Full layer details | Section 0 — Overview |
| UI / React fundamentals | Onboarding Primer |
| Folder structure rules | Section 3 — Folder & File Structure |
| Schema patterns | Section 5 — Validation Contract |
| RBAC implementation | `guidelines/rbac.md` |
| Agent authorization | `guidelines/caller-context.md` |
| Adding a new field / module | Section 11 — Evolution Rules |

---

*If this page answers your question, you don't need the full canon.*
*If it doesn't, the linked sections go deep.*
