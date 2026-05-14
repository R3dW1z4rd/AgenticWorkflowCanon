# Architecture Canon
## Section 4 — Data Flow
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

Every request in this architecture follows one of two flows. Understanding both — step by step, layer by layer — is required before writing any feature code. This section traces each flow with annotated code at every step and documents the error handling contract.

---

### The two flows

**Mutation flow (~70% of cases)**
A user submits a form or triggers an action that changes data. The primary pattern. Uses Server Actions.

```
UI (client component)
  → server boundary
    → Server Action
      → Zod validates
        → requireOrgAccess()
          → Service
            → Drizzle → PostgreSQL
          ← typed row returned
        ← { data } or { error }
      ← response to client
    ← UI updates, toast shown
```

**Query flow (~30% of cases)**
A page loads and needs to display data. Uses Server Components with direct service calls.

```
page.tsx (server component)
  → requireOrgAccess()
    → Service
      → Drizzle → PostgreSQL
    ← Branch[] returned
  ← passed as props to components
← HTML rendered and sent to browser
```

---

### Mutation flow — step by step

#### Step 1 — UI: the client component

The form lives in a Client Component. It handles submission state and calls the Server Action. It contains no business logic and no validation beyond basic HTML `required` attributes.

```tsx
// modules/branches/components/CreateBranchForm.tsx
'use client'

import { useTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { createBranchAction } from '../branches.actions'
import { toast } from '@/components/ui/use-toast'

export function CreateBranchForm() {
  const [isPending, startTransition] = useTransition()

  function handleSubmit(formData: FormData) {
    const input = {
      name: formData.get('name') as string,
      region: formData.get('region') as string,
    }

    startTransition(async () => {
      const result = await createBranchAction(input)

      if (result.error) {
        toast({ title: 'Error', description: result.error, variant: 'destructive' })
        return
      }

      toast({ title: 'Branch created' })
    })
  }

  return (
    <form action={handleSubmit}>
      <div className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="name">Branch name</Label>
          <Input id="name" name="name" required />
        </div>
        <div className="space-y-1">
          <Label htmlFor="region">Region</Label>
          <Input id="region" name="region" required />
        </div>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Creating...' : 'Create branch'}
        </Button>
      </div>
    </form>
  )
}
```

**What this step owns:**
- Submission state (`isPending`)
- Reading form values from `FormData`
- Calling the Server Action
- Showing success/error feedback to the user

**What this step does not do:**
- Validate the input shape (Zod does this on the server)
- Check permissions
- Touch the database
- Contain business logic

---

#### Step 2 — Server Action: the API boundary

The Server Action is the entry point to the server. It is thin by design: validate, check auth, call service, return.

```typescript
// modules/branches/branches.actions.ts
'use server'

import { createBranchSchema } from './branches.schema'
import { branchService } from './branches.service'
import { requireOrgAccess } from '@/lib/auth/policy'

export async function createBranchAction(input: unknown) {
  // 1. Validate
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) {
    return {
      error: 'Invalid input',
      issues: parsed.error.issues,
    }
  }

  // 2. Auth + org context
  const { orgId, userId } = await requireOrgAccess()

  // 3. Call service
  return branchService.create({
    data: parsed.data,
    orgId,
    userId,
  })
}
```

**What this step owns:**
- Calling `safeParse` and returning early on validation failure
- Calling `requireOrgAccess()` and extracting `{ orgId, userId }`
- Calling the service with typed, validated, org-scoped input
- Returning the service result directly

**What this step does not do:**
- Contain business logic — not even one `if` that isn't about input shape or auth
- Call Drizzle directly
- Catch errors from the service (errors bubble up and are handled by Next.js)

---

#### Step 3 — Zod schema: the validation contract

The schema is written before the action. It is the source of truth for what valid input looks like.

```typescript
// modules/branches/branches.schema.ts
import { z } from 'zod'

export const createBranchSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  region: z.string().min(1, 'Region is required'),
})

// The TypeScript type is inferred — not written by hand
export type CreateBranchInput = z.infer<typeof createBranchSchema>
```

**What the schema owns:**
- Shape validation (required fields, types)
- Format validation (min/max length, regex patterns)
- The TypeScript type for valid input

**What the schema does not validate:**
- Whether a branch name is already taken (service concern)
- Whether the user has permission to create branches (auth concern)
- Whether the org exists (service/auth concern)

**Validation failure response shape:**
```typescript
// When safeParse fails, the action returns:
{
  error: 'Invalid input',
  issues: [
    { path: ['name'], message: 'Name is required' }
  ]
}
```

---

#### Step 4 — Auth + org context: the policy check

`requireOrgAccess()` is called immediately after validation. It reads the current session from BetterAuth, confirms the user belongs to an org, and returns the context the service needs.

```typescript
// lib/auth/policy.ts

export async function requireOrgAccess() {
  const session = await auth.getSession()

  if (!session?.user) {
    throw new Error('UNAUTHORIZED')
  }

  const orgId = session.user.orgId

  if (!orgId) {
    throw new Error('NO_ORG_CONTEXT')
  }

  return {
    userId: session.user.id,
    orgId,
  }
}
```

**What this step owns:**
- Confirming an authenticated session exists
- Extracting and returning `{ userId, orgId }`
- Throwing (not returning) on failure — failures here are not recoverable in the action

**Why it throws instead of returning an error:**
When auth fails, there is nothing to do in the action. Throwing causes Next.js to handle the error at the boundary (returning a 401 or redirecting to login). Returning `{ error: 'unauthorized' }` would require every action to check for it — that is the kind of implicit contract that leads to auth bypasses.

**Org context invariant:**
After `requireOrgAccess()` returns, `orgId` is guaranteed to be present and valid. Every subsequent step receives it explicitly. No service or query ever fetches the org context itself — it is always passed in.

---

#### Step 5 — Service layer: business logic

The service receives typed, validated input and explicit org context. It enforces business rules, executes the database operation, logs the event, and returns a result.

```typescript
// modules/branches/branches.service.ts
import { db } from '@/db'
import { branches } from '@/db/schema'
import { eq } from 'drizzle-orm'
import { logger } from '@/lib/logger'
import type { CreateBranchInput } from './branches.schema'

export const branchService = {
  async create({
    data,
    orgId,
    userId,
  }: {
    data: CreateBranchInput
    orgId: string
    userId: string
  }) {
    // Business rule: check for duplicate name within the org
    const existing = await db
      .select()
      .from(branches)
      .where(eq(branches.name, data.name))
      .limit(1)

    if (existing.length > 0) {
      return { error: 'A branch with this name already exists' }
    }

    // Execute the insert
    const [branch] = await db
      .insert(branches)
      .values({
        name: data.name,
        region: data.region,
        orgId,
      })
      .returning()

    // Log the event (non-blocking)
    logger.info('branch.created', {
      branchId: branch.id,
      orgId,
      userId,
    })

    return { data: branch }
  },

  async listByOrg({ orgId }: { orgId: string }) {
    return db
      .select()
      .from(branches)
      .where(eq(branches.orgId, orgId))
  },
}
```

**What the service owns:**
- Business rule enforcement (duplicate check)
- The Drizzle query
- Logging and audit events
- The return value: `{ data: T }` on success, `{ error: string }` on business failure

**What the service does not do:**
- Validate input shape — already done by Zod
- Read the session or check auth — already done by policy helpers
- Format data for the UI — returns plain typed data

---

#### Step 6 — Drizzle: the query layer

Drizzle executes SQL against PostgreSQL and returns typed results. It is the only layer that touches the database.

```typescript
// Inside the service — what Drizzle does:

// INSERT — returns the inserted row as a Branch type
const [branch] = await db
  .insert(branches)
  .values({ name, region, orgId })
  .returning()
// branch is typed as Branch (from $inferSelect)

// SELECT with org scope — always filtered
const results = await db
  .select()
  .from(branches)
  .where(eq(branches.orgId, orgId))
// results is typed as Branch[]
```

**The org scope rule at the query level:**
Every SELECT query that returns application data must include a `.where()` condition on `orgId`. A query without an org scope filter is a bug — it would return data across organizational boundaries.

```typescript
// ✅ Correct — scoped to org
db.select().from(branches).where(eq(branches.orgId, orgId))

// ❌ Wrong — returns all branches from all orgs
db.select().from(branches)
```

---

### Query flow — step by step

The query flow is simpler because there is no mutation, no form submission, and no Server Action. Data flows in one direction: server fetches, passes as props, components render.

#### Step 1 — page.tsx: fetch and pass props

```tsx
// app/(dashboard)/branches/page.tsx
import { branchService } from '@/modules/branches/branches.service'
import { requireOrgAccess } from '@/lib/auth/policy'
import { BranchList } from '@/modules/branches/components/BranchList'
import { notFound } from 'next/navigation'

export default async function BranchesPage() {
  // Auth + org context — same pattern as mutation flow
  const { orgId } = await requireOrgAccess()

  // Direct service call — no Server Action needed for reads
  const branches = await branchService.listByOrg({ orgId })

  return (
    <div>
      <h1>Branches</h1>
      <BranchList branches={branches} />
    </div>
  )
}
```

#### Step 2 — components receive props and render

```tsx
// modules/branches/components/BranchList.tsx
import type { Branch } from '@/db/schema'
import { BranchCard } from './BranchCard'

export function BranchList({ branches }: { branches: Branch[] }) {
  if (branches.length === 0) {
    return <p>No branches found.</p>
  }

  return (
    <ul className="space-y-3">
      {branches.map((branch) => (
        <BranchCard key={branch.id} branch={branch} />
      ))}
    </ul>
  )
}
```

Components receive typed data as props. They render. They do not fetch.

---

### The response shape contract

Every Server Action returns one of two shapes. This is the contract between server and client. It never deviates.

```typescript
// Success
{ data: T }

// Failure (validation or business rule)
{ error: string, issues?: ZodIssue[] }
```

**Why not throw on business failures?**
Throwing from a Server Action causes Next.js to treat it as an unhandled error (500). Business failures — duplicate name, insufficient stock, invalid state transition — are expected outcomes, not exceptions. They return `{ error }` so the client can display a meaningful message. Only auth failures and unexpected system errors throw.

```typescript
// In the client component:
const result = await createBranchAction(input)

if (result.error) {
  // Business failure — show message, stay on form
  toast({ title: result.error, variant: 'destructive' })
  return
}

// Success — result.data is the created branch, fully typed
console.log(result.data.id)
```

---

### Error handling — the complete picture

| Error type | Where it originates | How it is handled |
|---|---|---|
| Invalid input shape | Zod `safeParse` | Returns `{ error, issues }` — action exits early |
| Auth failure (no session) | `requireOrgAccess()` | Throws — Next.js redirects to login |
| Business rule violation | Service returns `{ error }` | Action passes it to client — displayed as message |
| Database error | Drizzle throws | Caught in service, logged, re-thrown as generic error |
| Not found | Service returns `null` | Page calls `notFound()` — renders 404 |

**Not found pattern in pages:**
```tsx
const branch = await branchService.getById({ branchId, orgId })

if (!branch) notFound() // Next.js renders the nearest not-found.tsx

return <BranchDetail branch={branch} />
```

---

### What TypeScript guarantees across both flows

At every step, TypeScript enforces the contract:

1. `createBranchSchema.safeParse(input)` → `parsed.data` is typed as `CreateBranchInput`
2. `branchService.create({ data: parsed.data, ... })` → TypeScript confirms `parsed.data` matches what the service expects
3. `db.insert(branches).returning()` → returns `Branch[]` — the type inferred from the Drizzle schema
4. `result.data` in the client → typed as `Branch` if `result.error` is absent

A type error at any step surfaces immediately at build time. Renaming a field in the Drizzle schema breaks every query and service that references it. Removing a required field from a Zod schema breaks every action that passes its output to the service.

---

### What org context guarantees across both flows

In both flows, `orgId` is extracted from the authenticated session before any data operation occurs. It is passed explicitly to every service call. It is applied in every Drizzle query as a filter.

This means:
- A user cannot access another org's data by manipulating a URL parameter
- A service cannot accidentally return cross-org data because the filter is in the service, not in the UI
- An agent generating a new service method that omits the org filter will produce a TypeScript error (the `orgId` parameter is required in the function signature)

---

### How to use this document

- **Developers:** When building a new feature, use the mutation flow for any operation that changes data and the query flow for any operation that reads data. Both flows are complete — do not skip steps. The annotated code examples above are canonical templates.
- **Agents:** When generating a Server Action, always follow the exact structure: `safeParse` → `requireOrgAccess` → service call → return. Never generate a service that calls `requireOrgAccess` itself — org context is always passed in. Never generate a SELECT query without a `.where(eq(table.orgId, orgId))` filter.
- **Tech leads:** When reviewing code, check that every mutation goes through a Server Action (not a Route Handler unless there is a documented reason), every query in the query flow is org-scoped, and every action is thin — no business logic inside it.

---

*Previous: Section 3 — Folder & File Structure*
*Next: Section 5 — Validation Contract (Zod)*
