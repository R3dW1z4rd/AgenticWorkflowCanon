# Architecture Canon
## Section 2 — Stack
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

Every technology in the stack is listed here with three things: what it does in this architecture, what it explicitly does not do, and how it connects to the layers around it. Read this section before writing any code. When you are unsure which tool to reach for, the answer is in this section.

---

### Next.js (App Router)

**Role:** The framework anchor. Next.js provides the file-based routing system, the server/client component model, Server Actions for mutations, and Route Handlers for HTTP endpoints. It is the container that holds everything else.

**What it does not do:**
- Does not contain business logic. Pages and layouts render — they do not compute.
- Does not manage database connections directly. That is Drizzle's job.
- Does not validate input. That is Zod's job.
- Does not enforce auth. That is the policy helpers' job.

**Connects to:** shadcn/ui (renders components), Zod (passes validated input to Server Actions), BetterAuth (reads session from the server), Service layer (calls services via Server Actions or Route Handlers).

**Why it is never replaced:** Next.js is the platform anchor for all projects on this stack. Its App Router model — server components, Server Actions, co-located layouts — is deeply aligned with this architecture's explicit, boundary-respecting design. Replacing it would require re-evaluating every layer below it.

---

### TypeScript

**Role:** The connective tissue of the entire stack. Every file, every function, every boundary is typed. TypeScript is not a layer — it runs through all of them. Zod infers TypeScript types from schemas. Drizzle infers TypeScript types from table definitions. Services accept and return typed values. This means type errors at one layer surface immediately at every layer that depends on it.

**What it does not do:**
- Does not validate at runtime. TypeScript types disappear at compile time. Runtime validation is Zod's job.
- Does not replace Zod schemas. A TypeScript type is not a contract — it is a description. A Zod schema is a contract — it enforces.

**Why it is non-negotiable:** Without TypeScript, the architecture loses its self-auditing property. Renaming a field in a Drizzle schema should break every service and component that references it — and TypeScript is what makes that happen. No TypeScript means no type safety at boundaries, which means bugs that should be caught at build time only surface in production.

---

### BetterAuth

**Role:** Authentication provider and session manager. BetterAuth handles user login, session creation, token management, and session retrieval. In this architecture, it is the source of truth for who the current user is.

**What it does not do:**
- Does not define org context. BetterAuth tells you who the user is. The policy helpers derive org context from that identity and the request.
- Does not enforce permissions. That is the job of `requireOrgAccess()` and `requirePermission()`.
- Does not contain business logic of any kind.

**Connects to:** API boundary (session is read at the start of every Server Action and Route Handler), Auth policy helpers (which receive the session and derive org context from it).

**Configuration:** BetterAuth is initialized once in `lib/auth.ts` and imported wherever the session is needed. It is never called from components or from the service layer — session retrieval happens at the API boundary and the extracted context is passed down explicitly.

**Why it is the standard:** Building authentication from scratch introduces significant security risk and ongoing maintenance cost. BetterAuth is production-proven, actively maintained, and designed for Next.js. A custom auth system requires a documented business case explaining what BetterAuth cannot do.

---

### Zod

**Role:** Validation layer and contract system. A Zod schema is a runtime-enforced description of what a piece of data must look like. Zod schemas are written first — before the function, before the form, before the database call. The schema is the contract that every layer agrees to.

**What it does not do:**
- Does not describe the database. That is Drizzle's job.
- Does not replace TypeScript types — it produces them. `z.infer<typeof mySchema>` gives you the TypeScript type. The Zod schema itself enforces the shape at runtime.
- Does not contain business logic. A Zod schema validates shape and format. It does not validate whether a branch exists, whether a user has permission, or whether a name is already taken. Those are service-layer concerns.

**Where schemas live:**
- Feature schemas: `features/[feature]/[feature].schema.ts`
- Shared/global schemas (common field types, pagination, etc.): `lib/schemas/`

**Connects to:** UI layer (schema used for client-side type hints and optional client validation), API boundary (schema enforced server-side before the service is called), Service layer (service functions accept types inferred from Zod schemas).

**Why it is never replaced:** Zod is the single most important architectural discipline tool in the stack. It enforces the schema-first principle at runtime, produces TypeScript types, and gives agents a reliable, machine-readable contract to work with. Every other tool depends on Zod schemas being present and correct.

---

### Server Actions (primary) and Route Handlers (secondary)

**Role:** The API boundary. This is the layer where the outside world meets the server. Server Actions handle form submissions and mutations — they are the primary pattern. Route Handlers handle cases where HTTP semantics are required.

**When to use a Server Action (default — ~70% of cases):**
- Any mutation triggered from a form or a user interaction
- Any operation that modifies data (create, update, delete)
- Any action that needs to be called from a Next.js component

**When to use a Route Handler instead (~30% of cases):**
- External consumers need to call the endpoint (a third-party service, a mobile app, a webhook receiver)
- The response must be a specific HTTP format (file download, redirect, specific status codes)
- A GET request that fetches data for non-component consumers

**What the API boundary does not do:**
- Does not contain business logic. Its job is to receive, validate, check auth, call the service, and return.
- Does not talk to the database. The service does that.
- Does not perform its own validation beyond calling the Zod schema.

**Standard Server Action structure:**
```typescript
// features/branches/branches.actions.ts
'use server'

import { createBranchSchema } from './branches.schema'
import { branchService } from './branches.service'
import { requireOrgAccess } from '@/lib/auth/policy'

export async function createBranchAction(input: unknown) {
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) {
    return { error: 'Invalid input', issues: parsed.error.issues }
  }

  const { orgId, userId } = await requireOrgAccess()

  return branchService.create({
    data: parsed.data,
    orgId,
    userId,
  })
}
```

This is the complete pattern. The action validates, checks auth, calls the service, and returns. Nothing more.

**Connects to:** Zod (validates input at the boundary), BetterAuth policy helpers (enforces auth and org context), Service layer (calls the service with typed, validated, org-scoped input).

---

### Auth Policy Helpers

**Role:** Three small functions that enforce who can do what in which org context. These are not a framework — they are explicit function calls in every API boundary.

```typescript
// lib/auth/policy.ts

requireUser()
// Returns the current session user or throws.
// Use when: the user must be logged in but org scope is not yet needed.

requireOrgAccess(orgId?: string)
// Returns { userId, orgId } after confirming the user belongs to the org.
// Use when: the action touches org-scoped data (which is almost always).

requirePermission(permission: string)
// Returns { userId, orgId } after confirming the user has a specific permission.
// Use when: the action is restricted to a subset of org members.
```

**What they do not do:**
- Do not contain business logic
- Do not talk to the database directly (they read the session and org membership, which is cached in the session or fetched once per request)
- Do not silently pass — they throw with a typed error if the check fails, which the API boundary catches and returns as an error response

**Why not a full RBAC framework:** A policy engine adds a framework layer that must be learned, configured, and debugged. Three explicit helper functions are readable, testable, and immediately understandable by any developer. If the permission model becomes complex enough to justify a policy engine, that decision is made explicitly and documented.

---

### Service Layer

**Role:** The owner of all business logic. Services are plain TypeScript functions (or classes, consistently applied per project). They receive typed, validated input and an explicit org context. They enforce business rules. They call Drizzle for data. They emit audit events and logs.

**What services do not do:**
- Do not validate input shape — that is already done by Zod at the boundary
- Do not check auth or permissions — that is already done by the policy helpers
- Do not render or format output for the UI — they return plain typed data

**Standard service structure:**
```typescript
// features/branches/branches.service.ts

import { db } from '@/db'
import { branches } from '@/db/schema/branches'
import { eq, and } from 'drizzle-orm'
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
    const branch = await db
      .insert(branches)
      .values({ ...data, orgId })
      .returning()

    logger.info('branch.created', { branchId: branch[0].id, orgId, userId })

    return branch[0]
  },

  async listByOrg({ orgId }: { orgId: string }) {
    return db
      .select()
      .from(branches)
      .where(eq(branches.orgId, orgId))
  },
}
```

**Connects to:** API boundary (called by Server Actions and Route Handlers), Drizzle (queries the database), `lib/logger` and `lib/audit` (emits side effects).

---

### Drizzle ORM

**Role:** The database query layer. Drizzle defines the database schema as TypeScript and provides a type-safe query builder that maps directly to SQL. It is the only layer that talks to PostgreSQL.

**What Drizzle does not do:**
- Does not validate user input — that is Zod's job
- Does not contain business logic — that is the service layer's job
- Does not get called from anywhere except the service layer (and, in rare justified cases, a repository)

**Schema structure:**
```typescript
// db/schema/branches.ts
import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core'

export const branches = pgTable('branches', {
  id: uuid('id').defaultRandom().primaryKey(),
  orgId: uuid('org_id').notNull(),
  name: text('name').notNull(),
  region: text('region').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

// These are the types you use when working with database rows
export type Branch = typeof branches.$inferSelect
export type NewBranch = typeof branches.$inferInsert
```

**Drizzle vs Zod — side by side:**

```typescript
// db/schema/branches.ts  — Drizzle owns the DB shape
export const branches = pgTable('branches', {
  id: uuid('id').defaultRandom().primaryKey(), // set by DB
  orgId: uuid('org_id').notNull(),              // set by service from auth context
  name: text('name').notNull(),
  region: text('region').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(), // set by DB
  updatedAt: timestamp('updated_at').defaultNow().notNull(), // set by DB
})

// features/branches/branches.schema.ts  — Zod owns the validation contract
export const createBranchSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  region: z.string().min(1, 'Region is required'),
  // id → not here, the database generates it
  // orgId → not here, the service sets it from auth context
  // createdAt / updatedAt → not here, the database sets them
})
```

The Zod schema only contains what the caller provides. The Drizzle schema contains everything the database stores. They overlap in some fields and intentionally differ in others.

**Migrations:** Drizzle manages schema migrations via `drizzle-kit`. Migration workflow is covered in Section 10 (Production Operations). Migrations are never written by hand and never applied manually in production.

**Connects to:** Service layer (only caller), PostgreSQL (only target), TypeScript type system (Drizzle types flow into service function signatures).

---

### PostgreSQL

**Role:** The persistent data store. PostgreSQL holds all application data. It is the only source of truth for data at rest.

**What PostgreSQL does not do in this architecture:**
- Does not contain application logic (no stored procedures, no triggers that encode business rules)
- Is not called directly by anything except Drizzle

**Why it is the default:** PostgreSQL is mature, well-documented, and capable of handling the relational, org-scoped data model that all projects on this stack use. It is not swapped without a specific, documented infrastructure requirement. "We want to try a different database" is not sufficient justification.

---

### shadcn/ui

**Role:** The UI component library. shadcn/ui provides composable, accessible components (forms, buttons, dialogs, tables, etc.) that are copied into the project — not installed as a black-box dependency. You own the component code.

**What it does not do:**
- Does not manage state or data
- Does not connect to the server
- Does not contain business logic

**Resolution rule:** When a UI requirement arises, solve it with shadcn/ui first. Only if a strong case can be documented that shadcn/ui cannot meet the requirement do you consider another library or building from scratch.

**Connects to:** Next.js App Router (used in Server and Client Components), forms (paired with Zod for type hints and validation feedback).

---

### Vitest

**Role:** Unit and integration test runner. Vitest tests Zod schemas (valid and invalid inputs), service functions (business logic correctness), and utility functions.

**What it does not do:**
- Does not test the UI or user flows — that is Playwright's job
- Does not test against a live database in unit tests (services are tested with an in-memory or test database)

**What gets tested with Vitest:**
- Every Zod schema (valid input passes, invalid input returns the right error)
- Every service function (given this input and org context, returns this output or error)
- Utility functions in `lib/`

---

### Playwright

**Role:** End-to-end test runner. Playwright tests complete user flows in a real browser against a real running application.

**What it does not do:**
- Does not replace Vitest for unit/integration tests
- Does not test individual functions or schemas in isolation

**What gets tested with Playwright:**
- Critical user journeys (login, create, edit, delete, permission boundaries)
- Any flow that crosses multiple layers end to end

---

### How to use this document

- **Developers**: Before using any technology, confirm its role and boundaries in this section. If you are unsure whether something belongs in a service or an action, the role descriptions above are the answer.
- **Agents**: Every code file you generate must use only the technologies listed here in the roles described here. If a file requires a technology not in this section, flag it before generating. The standard structures shown above are canonical — follow them exactly.
- **Tech leads**: When reviewing a PR, check that each technology is being used in its defined role. A Drizzle call in a route handler, a Zod schema that includes `id` or `createdAt`, or a service that reads a session directly are all violations of this section.

---

*Previous: Section 1 — Philosophy*
*Next: Section 3 — Folder & File Structure*
