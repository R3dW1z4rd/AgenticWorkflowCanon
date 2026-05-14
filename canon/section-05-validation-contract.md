# Architecture Canon
## Section 5 — Validation Contract (Zod)
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

How to write Zod schemas correctly, where they live, what they own, and what they do not own. The schema file is always the first file written for any new feature. This section is the complete reference for how to do that.

---

### The schema-first rule

A Zod schema is written before any function, form, or database call that depends on it.

This is not a style preference. It is the rule that makes the architecture work:

- The service function signature is derived from the schema type
- The Server Action validates against the schema before calling the service
- The UI form fields correspond to the schema fields
- Agents generating code for a feature start by reading the schema

If the schema does not exist yet, nothing else can be correctly written. The schema is the contract. Everything else implements it.

**The order is always:**
```
1. db/schema/[module].ts      — Drizzle table (what the database stores)
2. modules/[module]/[module].schema.ts  — Zod schemas (what callers provide)
3. modules/[module]/[module].service.ts — Service (uses Zod types as input types)
4. modules/[module]/[module].actions.ts — Actions (validates with Zod before calling service)
5. modules/[module]/components/         — UI (fields match Zod schema fields)
```

---

### What a schema file contains

Every module schema file contains three things per operation: the schema, the inferred type, and nothing else.

```typescript
// modules/branches/branches.schema.ts
import { z } from 'zod'

// CREATE — what a caller provides to create a branch
export const createBranchSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  region: z.string().min(1, 'Region is required'),
})
export type CreateBranchInput = z.infer<typeof createBranchSchema>

// UPDATE — what a caller provides to update a branch
export const updateBranchSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long').optional(),
  region: z.string().min(1, 'Region is required').optional(),
})
export type UpdateBranchInput = z.infer<typeof updateBranchSchema>

// GET BY ID — what a caller provides to fetch a single branch
export const branchIdSchema = z.object({
  branchId: z.string().uuid('Invalid branch ID'),
})
export type BranchIdInput = z.infer<typeof branchIdSchema>

// LIST — what a caller provides to list branches (with filters/pagination)
export const listBranchesSchema = z.object({
  region: z.string().optional(),
  page: z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(100).default(20),
})
export type ListBranchesInput = z.infer<typeof listBranchesSchema>
```

**Naming convention:**
- Schema: `[verb][Module]Schema` — `createBranchSchema`, `updateBranchSchema`
- Type: `[Verb][Module]Input` — `CreateBranchInput`, `UpdateBranchInput`
- Exception: ID and list schemas use `[module]IdSchema` and `list[Module]Schema`

---

### What schemas validate — and what they do not

**Schemas validate shape and format. Nothing else.**

| Schemas validate | Schemas do not validate |
|---|---|
| Required fields are present | Whether a branch name is already taken |
| String length limits | Whether the user has permission |
| Number ranges | Whether the org exists |
| Valid UUID format | Whether a referenced record exists |
| Allowed enum values | Any rule that requires a database query |
| Email format | Any rule that requires business context |

Everything in the right column is a service-layer concern. A schema that reaches for the database or applies business context is a schema that has crossed its boundary.

**Concrete example — what belongs where:**

```typescript
// ✅ In the schema — format and shape
export const createBranchSchema = z.object({
  name: z.string().min(1).max(100),
  region: z.enum(['north', 'south', 'east', 'west']), // allowed values
  email: z.string().email().optional(),               // format
})

// ✅ In the service — business rules that need context
async create({ data, orgId }) {
  const existing = await db
    .select()
    .from(branches)
    .where(and(
      eq(branches.name, data.name),
      eq(branches.orgId, orgId)
    ))
    .limit(1)

  if (existing.length > 0) {
    return { error: 'A branch with this name already exists in this org' }
  }
  // ...
}
```

---

### Schema patterns for every common scenario

#### Create schema

Only the fields the caller provides. Never `id`, `createdAt`, `updatedAt`, or `orgId` — these are set by the database or the service.

```typescript
export const createBranchSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  region: z.string().min(1, 'Region is required'),
  managerId: z.string().uuid().optional(), // optional FK reference
})
export type CreateBranchInput = z.infer<typeof createBranchSchema>
```

#### Update schema

Fields are optional — a partial update only sends what changed. The `id` of the record being updated comes from the URL params, not the request body.

```typescript
export const updateBranchSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  region: z.string().min(1).optional(),
  managerId: z.string().uuid().nullable().optional(), // nullable = can be cleared
})
export type UpdateBranchInput = z.infer<typeof updateBranchSchema>
```

**Why `id` is not in the update schema:**
The record ID comes from the URL (`/branches/[branchId]`), is validated by `branchIdSchema`, and is passed to the service separately from the update body. Keeping ID out of the update schema prevents a caller from updating a different record than the URL specifies.

```typescript
// In the action:
const parsedId = branchIdSchema.safeParse({ branchId: params.branchId })
const parsedBody = updateBranchSchema.safeParse(input)

// Both validated separately, both passed to the service
branchService.update({
  branchId: parsedId.data.branchId,
  data: parsedBody.data,
  orgId,
  userId,
})
```

#### ID param schema

URL parameters come in as strings. Validate them explicitly before using them.

```typescript
export const branchIdSchema = z.object({
  branchId: z.string().uuid('Invalid branch ID'),
})
export type BranchIdInput = z.infer<typeof branchIdSchema>
```

#### List / filter schema

Pagination and filter parameters. Always provide safe defaults with `.default()`.

```typescript
export const listBranchesSchema = z.object({
  region: z.string().optional(),
  search: z.string().max(100).optional(),
  page: z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(100).default(20),
})
export type ListBranchesInput = z.infer<typeof listBranchesSchema>
```

#### Delete schema

Delete operations only need the ID. Use the shared `branchIdSchema` directly — no separate delete schema needed.

```typescript
// In the action:
const parsed = branchIdSchema.safeParse({ branchId: params.branchId })
```

---

### Shared schemas — what lives in lib/schemas/

Some schemas appear across multiple modules. They live in `lib/schemas/common.ts` and are imported wherever needed.

```typescript
// lib/schemas/common.ts

import { z } from 'zod'

// Pagination — used by every list endpoint
export const paginationSchema = z.object({
  page: z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(100).default(20),
})
export type PaginationInput = z.infer<typeof paginationSchema>

// UUID param — used by any route with an ID segment
export const uuidParamSchema = z.object({
  id: z.string().uuid('Invalid ID'),
})
export type UuidParamInput = z.infer<typeof uuidParamSchema>

// Date range — used by reports and filtered list views
export const dateRangeSchema = z.object({
  from: z.string().datetime().optional(),
  to: z.string().datetime().optional(),
})
export type DateRangeInput = z.infer<typeof dateRangeSchema>
```

**When to add something to `lib/schemas/common.ts`:**
- The same schema shape appears in two or more modules
- The pattern is general enough that any future module would likely need it

**When not to:**
- The schema is specific to one module's domain, even if it shares field names with another module

---

### Composing schemas

Zod's composition tools keep schemas DRY without coupling modules to each other.

#### Extending a base schema

```typescript
// A base address schema used by branches and users both
const addressSchema = z.object({
  street: z.string().min(1),
  city: z.string().min(1),
  country: z.string().length(2), // ISO country code
})

// Branch extends the base
export const createBranchSchema = z.object({
  name: z.string().min(1).max(100),
  region: z.string().min(1),
}).merge(addressSchema) // merge adds address fields to branch
```

#### Reusing pagination

```typescript
import { paginationSchema } from '@/lib/schemas/common'

export const listBranchesSchema = paginationSchema.extend({
  region: z.string().optional(),
  search: z.string().max(100).optional(),
})
export type ListBranchesInput = z.infer<typeof listBranchesSchema>
```

#### Deriving a partial update schema from a create schema

```typescript
export const createBranchSchema = z.object({
  name: z.string().min(1).max(100),
  region: z.string().min(1),
})

// All fields become optional — safe starting point for update schemas
export const updateBranchSchema = createBranchSchema.partial()
export type UpdateBranchInput = z.infer<typeof updateBranchSchema>
```

Use `.partial()` with care — it makes every field optional, which is correct for most updates but may hide required fields that should always be present when updating.

---

### Zod error messages — the convention

Error messages in schemas are user-facing. They appear in toast notifications and form validation feedback. Write them as if a user will read them.

```typescript
// ✅ User-facing messages
z.string().min(1, 'Name is required')
z.string().max(100, 'Name must be 100 characters or fewer')
z.string().uuid('Invalid ID format')
z.string().email('Enter a valid email address')
z.number().min(0, 'Value must be 0 or greater')

// ❌ Developer-facing messages (wrong for this layer)
z.string().min(1, 'name_required')
z.string().max(100, 'STRING_TOO_LONG')
z.string().uuid() // no message — defaults to technical Zod output
```

---

### How agents use schemas

The schema file is the first file an agent reads when working on a module. It is the contract from which everything else is derived.

**What an agent does with a schema:**

1. **Reads `CreateBranchInput`** → knows exactly what fields the service's `create` method accepts
2. **Reads `UpdateBranchInput`** → knows which fields are optional vs required for updates
3. **Reads field names and types** → generates matching form inputs with correct `name` attributes
4. **Reads validation rules** → generates matching `required`, `maxLength` HTML attributes for basic client hints
5. **Reads the schema before generating service code** → service function signature matches schema type exactly

**The agent contract for schemas:**

- Never generate a service function whose input type is not derived from a Zod schema
- Never add `id`, `createdAt`, `updatedAt`, or `orgId` to a create schema
- Never add database-checking logic to a schema
- If a field appears in the Drizzle table but not in the Zod create schema, that is intentional — the database or service sets it

---

### Schema checklist — before committing

Before committing a schema file, verify:

- [ ] Schema is written before the service that uses it
- [ ] Create schema excludes `id`, `createdAt`, `updatedAt`, `orgId`
- [ ] Update schema fields are `.optional()` or derived via `.partial()`
- [ ] Every required field has a user-facing error message
- [ ] Types are exported alongside schemas (`export type CreateBranchInput = ...`)
- [ ] No database queries or service calls inside schema validation
- [ ] Shared patterns (pagination, UUID params) imported from `lib/schemas/common.ts`

---

### How to use this document

- **Developers:** Write the schema file first, always. Use the patterns in this section for every operation type. When in doubt about whether a rule belongs in the schema or the service, check the "What schemas validate" table above.
- **Agents:** The schema file is your source of truth for a module's input contracts. Read it before generating any service, action, or component code. Never generate code that bypasses schema validation. If a schema for an operation does not exist, generate it first before generating the function that depends on it.
- **Tech leads:** When reviewing PRs, check that every new service method has a corresponding Zod schema and that the schema type is used as the input type. A service method that accepts a plain object with no Zod type is a contract violation.

---

*Previous: Section 4 — Data Flow*
*Next: Section 6 — Auth & Authorization*
