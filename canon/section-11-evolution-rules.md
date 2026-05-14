# Architecture Canon
## Section 11 — Evolution Rules
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

How to change a running application safely. Most architecture documentation covers how to build the first version. This section covers what happens on day 50, day 200, and day 500 — when requirements change, modules grow, new use cases emerge, and the codebase needs to evolve without breaking what already works.

Every rule in this section is designed to answer one question: **how do I add this without touching code that doesn't need to change?**

---

### The evolution principles

These four principles guide every decision in this section.

**1. Extend, don't modify.**
Adding is safer than changing. A new field is safer than renaming one. A new service method is safer than changing an existing one's signature. When in doubt, add alongside — deprecate and remove later.

**2. The contract is the boundary.**
The `{ data }` / `{ error }` response shape, the Zod schema types, and the service method signatures are contracts. Callers depend on them. Changing a contract is a breaking change — adding to it is not.

**3. Refactor only when you're already in the file.**
Never refactor working code that isn't involved in the current change. The right time to clean up a service method is when you're adding a feature to it — not as a standalone task. This keeps PRs focused and keeps unrelated risk contained.

**4. The canon evolves with the codebase.**
When a new pattern is introduced — a background job, a real-time subscription, a new tool — the canon is updated before the code is merged. Undocumented patterns become invisible debt.

---

### Pattern 1 — Field addition

Adding a field to an existing module is the most common evolution. A client wants to add "phone number" to branches.

**Step 1: Classify the field**

| Is the new field required? | Does the table have existing rows? | Approach |
|---|---|---|
| Optional (nullable) | Any | Add as nullable — safest |
| Required (NOT NULL) | No rows yet | Add as NOT NULL directly |
| Required (NOT NULL) | Has existing rows | Add as NOT NULL with a default — remove default in a follow-up migration |

**Step 2: Update the Drizzle schema**

```typescript
// db/schema/branches.ts
export const branches = pgTable('branches', {
  id:        uuid('id').defaultRandom().primaryKey(),
  orgId:     uuid('org_id').notNull(),
  name:      text('name').notNull(),
  region:    text('region').notNull(),
  phone:     text('phone'),              // ← nullable — no default needed
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})
```

**Step 3: Generate and review the migration**

```bash
npx drizzle-kit generate
# Review db/migrations/XXXX_add_phone_to_branches.sql
npx drizzle-kit migrate
```

**Step 4: Update the Zod schemas**

Only add the field to schemas where it makes sense for callers to provide it:

```typescript
// modules/branches/branches.schema.ts

export const createBranchSchema = z.object({
  name:   z.string().min(1).max(100),
  region: z.string().min(1),
  phone:  z.string().regex(/^\+?[\d\s\-()]{7,20}$/, 'Invalid phone format').optional(), // ← added
})

export const updateBranchSchema = createBranchSchema.partial()
```

**Step 5: Update tests — only the affected ones**

Add the field to the happy path test. The org isolation tests do not need to change — they are not affected by a new optional field.

```typescript
// modules/branches/branches.schema.test.ts
it('accepts a valid phone number', () => {
  const result = createBranchSchema.safeParse({
    name:   'Downtown',
    region: 'North',
    phone:  '+1 555 123 4567',
  })
  expect(result.success).toBe(true)
})

it('rejects an invalid phone number', () => {
  const result = createBranchSchema.safeParse({
    name:   'Downtown',
    region: 'North',
    phone:  'not-a-phone',
  })
  expect(result.success).toBe(false)
})
```

**Step 6: Update the UI form — only if the field should be user-editable**

Add the input to the form component. The Server Action and service require no changes unless the field has business rules attached to it.

**What does NOT need to change:**
- The service method signatures (they receive the schema type, which now includes `phone?`)
- The actions (they pass `parsed.data` to the service — the new field is included automatically)
- The org isolation tests
- Any other module

---

### Pattern 2 — Module addition

Adding a new business domain. See Section 3 for the 9-step checklist. This section adds guidance on what "not breaking existing code" means in practice.

**The module boundary rule:**
A new module must not import from any existing module. It can import from:
- `db/schema` — for table definitions and types
- `lib/` — for auth, logger, audit, schemas, utils
- `components/` — for shared UI components

If the new module needs data from an existing module, that composition happens at the page level — not inside the module.

**The test database rule:**
Before writing any service code for the new module, confirm the migration runs cleanly against the test database. A migration error discovered before any application code is written is far cheaper to fix than one discovered after.

**The naming rule:**
Choose the module name carefully before creating any files. Module names appear in file names, function names, permission strings, audit events, and log messages. Renaming a module later is a large, error-prone refactor. Take the time to name it correctly the first time.

---

### Pattern 3 — Cross-cutting use case

A new requirement that involves data or logic from multiple existing modules. Example: "We need a dashboard showing branches alongside their inventory levels and recent reports."

#### Case A: Composition at the page level (most common)

The page calls multiple services and passes the results to a composite component. No modules are changed.

```tsx
// app/(dashboard)/overview/page.tsx
export default async function OverviewPage() {
  const ctx = await requireOrgAccess()

  const [branches, inventory, recentReports] = await Promise.all([
    branchService.listByOrg({ orgId: ctx.orgId }),
    inventoryService.summaryByOrg({ orgId: ctx.orgId }),
    reportService.listByOrg({ orgId: ctx.orgId, filters: { pageSize: 5 } }),
  ])

  return (
    <OrgOverviewDashboard
      branches={branches.data}
      inventory={inventory.data}
      reports={recentReports.data}
    />
  )
}
```

Nothing inside `modules/branches`, `modules/inventory`, or `modules/reports` changes. The composition is the page's responsibility.

#### Case B: A shared query (when the same join is needed in multiple places)

If the same cross-module join is needed in more than one place, extract it to `lib/queries/`:

```typescript
// lib/queries/branch-overview.ts
// Joins branches with their inventory summary — no business logic

import { db } from '@/db'
import { branches, inventory } from '@/db/schema'
import { eq } from 'drizzle-orm'

export async function getBranchesWithInventory(orgId: string) {
  return db
    .select({
      branchId:    branches.id,
      branchName:  branches.name,
      region:      branches.region,
      totalItems:  inventory.totalItems,
      lowStockFlag: inventory.lowStockFlag,
    })
    .from(branches)
    .leftJoin(inventory, eq(inventory.branchId, branches.id))
    .where(eq(branches.orgId, orgId))
}
```

This query belongs to neither the branches module nor the inventory module. It lives in `lib/queries/` because no single module owns it.

#### Case C: A new business operation that spans modules (create a coordinating service)

If a new business operation requires writing to two modules — for example, "transfer inventory from one branch to another" — create a coordinating service in `lib/services/`:

```typescript
// lib/services/inventory-transfer.service.ts
// Coordinates across modules — lives in lib/ because it owns no single domain

import { branchService } from '@/modules/branches/branches.service'
import { inventoryService } from '@/modules/inventory/inventory.service'
import { db } from '@/db'
import type { CallerContext } from '@/lib/auth/caller-context'

export const inventoryTransferService = {
  async transfer({
    fromBranchId,
    toBranchId,
    itemId,
    quantity,
    ctx,
  }: {
    fromBranchId: string
    toBranchId:   string
    itemId:       string
    quantity:     number
    ctx:          CallerContext
  }) {
    // Verify both branches belong to this org
    const [fromBranch, toBranch] = await Promise.all([
      branchService.getById({ branchId: fromBranchId, orgId: ctx.orgId }),
      branchService.getById({ branchId: toBranchId,   orgId: ctx.orgId }),
    ])

    if (!fromBranch) return { error: 'Source branch not found' }
    if (!toBranch)   return { error: 'Destination branch not found' }

    // Execute the transfer in a transaction
    return db.transaction(async (tx) => {
      await inventoryService.deduct({ branchId: fromBranchId, itemId, quantity, ctx })
      await inventoryService.add({    branchId: toBranchId,   itemId, quantity, ctx })
      return { data: { transferred: quantity } }
    })
  },
}
```

**Use a coordinating service in `lib/services/` when:**
- A business operation writes to two or more modules' tables
- The operation needs to be atomic (transaction)
- The logic is complex enough to warrant its own home

**Do not create a coordinating service when:**
- The composition is read-only (use a query in `lib/queries/` instead)
- The operation is only needed in one page (compose at the page level instead)

---

### Pattern 4 — Module extraction

A module has grown too large. The signals that extraction is needed:

```
signals that a module should be split:

✦ Service has 8+ methods AND they fall into 2 clearly distinct groups
✦ Schema file has 10+ schemas AND they map to 2 clearly distinct operations
✦ Two developers are regularly working in the same module at the same time
  and causing merge conflicts
✦ The module name is vague ("data", "records", "misc")
```

**What is not a signal:**
- The service file is 200 lines but all methods are about the same domain
- You want to "clean it up" without a specific pain point
- It "feels" too big

**How to split a module:**

Using `reports` as an example, split into `reports` (the report records) and `report-templates` (the reusable templates):

```
Before:
modules/reports/
├── reports.schema.ts          (report + template schemas mixed)
├── reports.service.ts         (report + template methods mixed)
└── reports.actions.ts

After:
modules/reports/
├── reports.schema.ts          (report schemas only)
├── reports.service.ts         (report methods only)
└── reports.actions.ts

modules/report-templates/
├── report-templates.schema.ts
├── report-templates.service.ts
└── report-templates.actions.ts
```

The split happens along the domain boundary — not along file size. If you can't cleanly separate the methods into two independent groups, the module should not be split.

---

### When to refactor vs extend — the decision matrix

Use this matrix when you are already working in a file and notice something that could be improved.

| What you observe | Action | When |
|---|---|---|
| A service method has grown to 60+ lines mostly of queries | Extract to `[module].queries.ts` | Now — while you're in the file |
| The same query appears in 2 service methods | Extract to `[module].queries.ts` | Now |
| The same business rule appears in 2 modules | Extract to `lib/utils/[rule].ts` | Now |
| A service method signature needs to change | Add a new method, deprecate the old | In the next release cycle |
| A module has 8+ methods in 2 distinct groups | Plan a module split | As a dedicated PR, not mid-feature |
| A schema field needs to be renamed | Two-step: add new field, migrate data, remove old | As a dedicated migration PR |
| Code "feels messy" with no specific pain | Do nothing | Not a valid trigger |

---

### Schema evolution — safe patterns

These patterns apply when you need to change the database schema for an existing, running application.

#### Adding an optional field (safest)

```typescript
// Before
export const branches = pgTable('branches', { name: text('name').notNull() })

// After — add as nullable, no migration risk
export const branches = pgTable('branches', {
  name:  text('name').notNull(),
  phone: text('phone'), // nullable by default
})
```

#### Adding a required field to a table with existing rows

Two-step process. Never combine these into one migration:

```typescript
// Migration 1: Add as nullable with a temporary default
phone: text('phone').notNull().default('NOT_SET')

// After deploying Migration 1 and backfilling real data:

// Migration 2: Remove the default (now all rows have real values)
phone: text('phone').notNull()
```

#### Renaming a field safely

Three-step process:

```
Step 1: Add the new column alongside the old one
Step 2: Backfill the new column, update all code to write to both, read from new
Step 3: Remove the old column once all code reads from the new one
```

Never rename a column in a single migration on a live database — it causes downtime for any query that references the old name before the deployment finishes.

#### Removing a field

Two-step process:

```
Step 1: Remove all code references to the field (schema, Zod, service, UI)
        Deploy. Confirm the column is no longer read or written.

Step 2: Generate a migration that drops the column
        Deploy the migration.
```

Dropping a column in the same deployment as removing code references risks a brief window where the deployed code tries to read a column that no longer exists.

---

### Deprecation and removal

When a feature is no longer needed:

**Step 1: Stop routing to it.**
Remove the page from `app/`. The feature is unreachable but the code still exists. Deploy.

**Step 2: Remove the module.**
Delete the module folder: schema, service, actions, components. Update any imports. Deploy.

**Step 3: Drop the table (optional, one release later).**
Generate a migration that drops the table. This is a separate, deliberate step — not automatic. Sometimes data needs to be retained for compliance. Make the decision consciously before generating the drop migration.

**What never gets deleted:**
- Audit log entries for the deleted feature — they are the permanent historical record
- Migration files — even migrations that created tables that are later dropped are retained

---

### Evolving the architecture itself

When a project genuinely needs something outside the standard stack — a background job queue, a real-time pub/sub system, file storage — follow this process before writing any code:

**1. Document the requirement the default cannot meet.**
Write one paragraph explaining what the existing stack cannot do. If you cannot write this clearly, the need may not be genuine.

**2. Evaluate against the architecture principles.**
Does the proposed addition require learning a new framework? Does it introduce magic or implicit behavior? Does it add a dependency that the team cannot own? These are the Section 1 questions applied to evolution.

**3. Decide where it fits in the folder structure.**
A background job runner would add a `jobs/` top-level folder and a pattern for job files. This needs to be defined before any job is written.

**4. Update the canon before the code is merged.**
The new pattern — its folder, its structure, its conventions — is documented in the relevant section before the PR is approved. Undocumented patterns are invisible to the next developer and to agents.

**5. Implement consistently.**
The first implementation of the new pattern is the canonical example. It must be clean enough to serve as the reference for every future implementation.

---

### The evolution checklist — before merging a change

**For field additions:**
- [ ] Drizzle schema updated
- [ ] Migration generated and reviewed
- [ ] Zod schema updated (only fields that callers provide)
- [ ] Tests updated (new field tested, existing isolation tests unchanged)
- [ ] UI updated if the field is user-editable

**For module additions:**
- [ ] Section 3 nine-step checklist completed
- [ ] No imports from other modules inside the new module
- [ ] Org isolation tests present in the service test file

**For cross-cutting use cases:**
- [ ] Composition happens at the page level, or in `lib/queries/`, or in `lib/services/`
- [ ] No module imports from another module directly

**For any change:**
- [ ] No working, untouched code was refactored in this PR
- [ ] The `{ data }` / `{ error }` response shape is unchanged for existing methods
- [ ] Existing service method signatures are unchanged (new parameters are optional)
- [ ] The canon is updated if a new pattern was introduced

---

### How to use this document

- **Developers:** When you receive a new requirement, identify which pattern it fits — field addition, module addition, cross-cutting, or module extraction. Follow the pattern's steps exactly. Do not combine patterns in one PR (e.g. a field addition + a module refactor). Keep changes small and focused.
- **Agents:** When asked to add a field to an existing module, follow Pattern 1. When asked to add a new module, follow the Section 3 checklist and Pattern 2. Never modify an existing service method signature to add a required parameter — make new parameters optional or create a new method. Never refactor code that isn't part of the current task.
- **Tech leads:** Use this section to evaluate PRs. A PR that adds a feature and refactors unrelated code should be split. A PR that changes an existing service method signature without adding it as an optional extension needs review against the contract principle. A PR that introduces a new pattern without updating the canon is incomplete.

---

*Previous: Section 10 — Production Operations*
*This is the final section of the Architecture Canon.*
*See also: Section 1 (Philosophy), Section 3 (Folder Structure), Guidelines (RBAC, Caller Context)*
