# Architecture Canon
## Section 3 — Folder & File Structure
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

Where every file lives, what every file is named, and what the rules are for cross-module dependencies. Read this before creating any file. When you are unsure where something belongs, this section is the answer.

---

### Top-level project structure

```
/
├── app/                    # Next.js App Router — routes only
├── modules/                # Domain modules — one per business area
├── db/                     # Database schema, client, and migrations
├── lib/                    # Shared code — utilities, auth, logger
├── components/             # Shared UI components
├── public/                 # Static assets
├── tests/                  # E2E tests (Playwright)
├── drizzle.config.ts
├── next.config.ts
└── tsconfig.json
```

Each top-level folder has exactly one responsibility. Nothing crosses this boundary without a documented reason.

---

### The four zones and what belongs in each

#### Zone 1 — `app/` (Routes only)

The `app/` directory is owned by Next.js. It defines the URL structure of the application. It contains pages, layouts, and route handlers — nothing else. No business logic, no service calls, no database queries.

Pages in `app/` import from `modules/` to get components and call services. They do not contain logic themselves.

```
app/
├── (auth)/
│   ├── layout.tsx              # Auth shell (no sidebar, centered layout)
│   └── login/
│       └── page.tsx
│
├── (dashboard)/
│   ├── layout.tsx              # Dashboard shell — auth guard + sidebar
│   ├── branches/
│   │   ├── page.tsx            # /branches — list all branches
│   │   ├── new/
│   │   │   └── page.tsx        # /branches/new — create form
│   │   └── [branchId]/
│   │       ├── page.tsx        # /branches/[branchId] — detail view
│   │       └── edit/
│   │           └── page.tsx    # /branches/[branchId]/edit
│   ├── users/
│   ├── reports/
│   └── inventory/
│
└── api/
    └── webhooks/               # Route Handlers for external consumers only
        └── [provider]/
            └── route.ts
```

**Rules for `app/`:**
- `page.tsx` files are Server Components that fetch data and pass it as props
- `layout.tsx` files define shared shells and section-level auth guards
- Route Handlers (`route.ts`) live in `app/api/` and are only created for external consumers
- No Drizzle calls directly in `app/` — all data comes through module services
- No business logic — pages compose and display, they do not compute

---

#### Zone 2 — `modules/` (Domain modules)

This is where the application lives. Every business domain gets its own module folder. Each module owns its schema, service, actions, and components.

```
modules/
├── branches/
│   ├── branches.schema.ts
│   ├── branches.service.ts
│   ├── branches.actions.ts
│   └── components/
│       ├── BranchList.tsx
│       ├── BranchCard.tsx
│       ├── BranchDetail.tsx
│       └── CreateBranchForm.tsx
│
├── users/
│   ├── users.schema.ts
│   ├── users.service.ts
│   ├── users.actions.ts
│   └── components/
│       ├── UserTable.tsx
│       └── InviteUserForm.tsx
│
├── reports/
│   ├── reports.schema.ts
│   ├── reports.service.ts
│   ├── reports.actions.ts
│   └── components/
│       ├── ReportList.tsx
│       └── ReportFilters.tsx
│
└── inventory/
    ├── inventory.schema.ts
    ├── inventory.service.ts
    ├── inventory.actions.ts
    └── components/
        ├── InventoryTable.tsx
        └── StockUpdateForm.tsx
```

**The four files every module has:**

| File | Contains | Rules |
|---|---|---|
| `[module].schema.ts` | All Zod schemas for this module | Written first. No imports from other modules. |
| `[module].service.ts` | All business logic for this module | Only caller of Drizzle. Receives org context explicitly. |
| `[module].actions.ts` | All Server Actions for this module | Thin. Validate → auth → call service → return. |
| `components/` | All UI components for this module | Render only. No service calls. No business logic. |

**When a module grows — the optional fifth file:**

When a service becomes large because of complex queries, extract them into a queries file inside the same module:

```
modules/branches/
├── branches.schema.ts
├── branches.service.ts
├── branches.actions.ts
├── branches.queries.ts     ← added only when service queries become complex
└── components/
```

`branches.queries.ts` contains only Drizzle queries that read or write the branches table. No business logic. The service calls it. Nothing else does. Do not create this file preemptively — add it when the service file is genuinely hard to read because of query complexity.

**Query placement rule — where every query lives:**

| Query type | Lives in | Reason |
|---|---|---|
| Queries that read/write one module's tables | `modules/[module]/[module].queries.ts` | Locality — the module owns its data |
| Queries that join across two or more modules | `lib/queries/[descriptive-name].ts` | No single module owns cross-module data |
| No queries of any kind | `db/` | `db/` owns schema, client, and migrations only |

This rule keeps `db/` minimal, modules self-contained, and cross-module complexity visible and explicit. A developer working inside `modules/branches/` finds everything they need in that folder. A query that no module owns goes to `lib/queries/` — the explicit escape hatch for cross-domain joins.

**Module naming conventions:**

| What | Convention | Example |
|---|---|---|
| Module folder | kebab-case, plural | `branches/`, `inventory-items/` |
| Module files | `[module-name].[type].ts` | `branches.schema.ts` |
| Zod schemas | camelCase, descriptive suffix | `createBranchSchema`, `updateBranchSchema` |
| Inferred Zod types | PascalCase with `Input` suffix | `CreateBranchInput`, `UpdateBranchInput` |
| Service export | camelCase object | `branchService` |
| Service methods | camelCase verbs | `create`, `update`, `listByOrg`, `getById` |
| Actions | camelCase with `Action` suffix | `createBranchAction`, `deleteBranchAction` |
| Components | PascalCase | `BranchList`, `CreateBranchForm` |

---

#### Zone 3 — `db/` (Database layer)

The database layer contains the Drizzle client, all Drizzle table definitions, and migrations. It is the only place that defines what the database looks like.

```
db/
├── index.ts                # Drizzle client — single export, used by all services
├── schema/
│   ├── branches.ts         # branches table definition
│   ├── users.ts            # users table definition
│   ├── reports.ts          # reports table definition
│   ├── inventory.ts        # inventory table definition
│   └── index.ts            # re-exports all tables — import from here
└── migrations/             # Generated by drizzle-kit — never edited by hand
    ├── 0001_initial.sql
    └── 0002_add_regions.sql
```

**Rules for `db/`:**
- `db/index.ts` exports one thing: the Drizzle `db` client. All services import from here.
- `db/schema/` contains only table definitions and the types inferred from them
- `db/schema/index.ts` re-exports every table — services always import from `@/db/schema` not from individual schema files
- `db/migrations/` is owned by `drizzle-kit`. Never create or edit migration files manually.
- Nothing in `db/` contains business logic, validation, or query functions
- Queries belong in modules or in `lib/queries/` — never in `db/`

**`db/index.ts` — canonical form:**
```typescript
import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import * as schema from './schema'

const client = postgres(process.env.DATABASE_URL!)

export const db = drizzle(client, { schema })
```

**`db/schema/index.ts` — canonical form:**
```typescript
export * from './branches'
export * from './users'
export * from './reports'
export * from './inventory'
```

---

#### Zone 4 — `lib/` (Shared code)

`lib/` is for code that is shared across modules but does not belong to any one module. Auth helpers, the logger, shared Zod schemas, and utility functions live here.

```
lib/
├── auth/
│   ├── index.ts            # BetterAuth instance and config
│   └── policy.ts           # requireUser, requireOrgAccess, requirePermission
├── logger.ts               # Structured logger (used by services)
├── audit.ts                # Audit event emitter (used by services)
├── schemas/
│   └── common.ts           # Shared Zod schemas: pagination, org context, id params
├── queries/                # Cross-module Drizzle queries (joins across two+ modules)
│   └── reports-with-branches.ts
└── utils/
    └── dates.ts            # Pure utility functions (formatting, parsing, etc.)
```

**Rules for `lib/`:**
- `lib/` code may be imported by anything — modules, app, components
- `lib/` code may NOT import from `modules/` — that would create a circular dependency
- `lib/` code may import from `db/` only in `lib/auth/` (for session/org lookups) and `lib/queries/` (for cross-module joins)
- Add to `lib/` when: two or more modules need the same logic and it has no clear module owner
- `lib/queries/` is specifically for Drizzle queries that join across two or more module tables — not for single-module queries, which belong in the module itself

---

#### Zone 5 — `components/` (Shared UI)

UI components that are used across multiple modules and do not belong to any one of them.

```
components/
├── ui/                     # shadcn/ui components — auto-generated, owned by you
│   ├── button.tsx
│   ├── input.tsx
│   ├── dialog.tsx
│   └── ...
├── layout/                 # App shell components
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   └── PageHeader.tsx
└── shared/                 # Custom shared components used in multiple modules
    ├── OrgBadge.tsx
    ├── EmptyState.tsx
    └── DataTable.tsx
```

**Rules for `components/`:**
- `components/ui/` is managed by the shadcn CLI — do not reorganize it
- `components/layout/` contains the app shell — sidebar, header, navigation
- `components/shared/` is for custom components needed by two or more modules
- If a component is only used by one module, it lives in `modules/[module]/components/`, not here
- Components in `components/` receive data as props — they do not call services

---

### The cross-module dependency rule

**Modules cannot import from each other directly.**

This is the rule that keeps the codebase from becoming a dependency tangle. It is not optional.

```
✅ Allowed imports:
  modules/branches  →  lib/
  modules/branches  →  db/schema
  modules/branches  →  components/ui
  modules/branches  →  components/shared

❌ Forbidden imports:
  modules/reports   →  modules/branches
  modules/inventory →  modules/users
```

**But what if `reports` needs branch data?**

This is the most common question about cross-module dependencies. The answer depends on the situation:

**Case 1: The page needs data from two modules (most common)**

The page in `app/` calls both services and passes both results as props. The page is the only place where cross-module data composition is allowed.

```tsx
// app/(dashboard)/reports/page.tsx
import { branchService } from '@/modules/branches/branches.service'
import { reportService } from '@/modules/reports/reports.service'
import { requireOrgAccess } from '@/lib/auth/policy'

export default async function ReportsPage() {
  const { orgId } = await requireOrgAccess()

  // Both services called at the page level — not inside each other
  const [branches, reports] = await Promise.all([
    branchService.listByOrg({ orgId }),
    reportService.listByOrg({ orgId }),
  ])

  return <ReportListWithFilters branches={branches} reports={reports} />
}
```

**Case 2: A shared query is needed by multiple modules**

If the same cross-module join is needed in more than one place, extract it to `lib/queries/`:

```
lib/
└── queries/
    └── reports-with-branches.ts    # Used by reports page and reports export
```

This file contains a Drizzle query that joins across tables. It is not a service — it has no business logic. It is a reusable query helper that lives in `lib/` because no single module owns it.

**Case 3: A module needs a type from another module**

If `reports` needs the `Branch` type for a component prop, import the Drizzle-inferred type from `db/schema`, not from the branches module:

```typescript
// ✅ Correct — importing the type from db/schema (shared source of truth)
import type { Branch } from '@/db/schema'

// ❌ Wrong — importing from another module
import type { Branch } from '@/modules/branches/branches.service'
```

---

### Naming conventions — complete reference

| Item | Convention | Examples |
|---|---|---|
| Module folders | kebab-case, plural | `branches/`, `inventory-items/` |
| Module files | `[module].[type].ts` | `branches.schema.ts`, `branches.service.ts` |
| Page files | Always `page.tsx` | — |
| Layout files | Always `layout.tsx` | — |
| Route Handler files | Always `route.ts` | — |
| Zod schemas | camelCase + descriptive suffix | `createBranchSchema`, `listBranchesSchema` |
| Zod inferred types | PascalCase + `Input` | `CreateBranchInput` |
| Service export | camelCase object named after module | `branchService`, `reportService` |
| Service methods | verb + context | `create`, `update`, `listByOrg`, `getById`, `deleteById` |
| Server Actions | camelCase + `Action` suffix | `createBranchAction`, `updateBranchAction` |
| Components | PascalCase, descriptive | `BranchList`, `CreateBranchForm`, `BranchCard` |
| Drizzle tables | camelCase, plural | `branches`, `inventoryItems` |
| Drizzle types | PascalCase from `$inferSelect` | `Branch`, `Report`, `InventoryItem` |
| Utility functions | camelCase | `formatDate`, `parseOrgId` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_BRANCHES_PER_ORG` |

---

### The full project map

```
/
├── app/
│   ├── (auth)/
│   │   ├── layout.tsx
│   │   └── login/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── branches/
│   │   │   ├── page.tsx
│   │   │   ├── new/page.tsx
│   │   │   └── [branchId]/
│   │   │       ├── page.tsx
│   │   │       └── edit/page.tsx
│   │   ├── users/
│   │   │   ├── page.tsx
│   │   │   └── [userId]/page.tsx
│   │   ├── reports/
│   │   │   ├── page.tsx
│   │   │   └── [reportId]/page.tsx
│   │   └── inventory/
│   │       ├── page.tsx
│   │       └── [itemId]/page.tsx
│   └── api/
│       └── webhooks/[provider]/route.ts
│
├── modules/
│   ├── branches/
│   │   ├── branches.schema.ts
│   │   ├── branches.service.ts
│   │   ├── branches.actions.ts
│   │   ├── branches.queries.ts      ← optional, added when queries grow complex
│   │   └── components/
│   │       ├── BranchList.tsx
│   │       ├── BranchCard.tsx
│   │       ├── BranchDetail.tsx
│   │       └── CreateBranchForm.tsx
│   ├── users/
│   │   ├── users.schema.ts
│   │   ├── users.service.ts
│   │   ├── users.actions.ts
│   │   └── components/
│   │       ├── UserTable.tsx
│   │       └── InviteUserForm.tsx
│   ├── reports/
│   │   ├── reports.schema.ts
│   │   ├── reports.service.ts
│   │   ├── reports.actions.ts
│   │   └── components/
│   │       ├── ReportList.tsx
│   │       └── ReportFilters.tsx
│   └── inventory/
│       ├── inventory.schema.ts
│       ├── inventory.service.ts
│       ├── inventory.actions.ts
│       └── components/
│           ├── InventoryTable.tsx
│           └── StockUpdateForm.tsx
│
├── db/
│   ├── index.ts
│   ├── schema/
│   │   ├── branches.ts
│   │   ├── users.ts
│   │   ├── reports.ts
│   │   ├── inventory.ts
│   │   └── index.ts
│   └── migrations/
│
├── lib/
│   ├── auth/
│   │   ├── index.ts
│   │   └── policy.ts
│   ├── logger.ts
│   ├── audit.ts
│   ├── schemas/
│   │   └── common.ts
│   ├── queries/             ← cross-module joins only
│   │   └── reports-with-branches.ts
│   └── utils/
│       └── dates.ts
│
├── components/
│   ├── ui/
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   └── shared/
│       ├── EmptyState.tsx
│       └── DataTable.tsx
│
├── tests/
│   └── e2e/
│       ├── branches.spec.ts
│       ├── users.spec.ts
│       └── auth.spec.ts
│
├── drizzle.config.ts
├── next.config.ts
└── tsconfig.json
```

---

### Adding a new module — the checklist

When a new business domain is identified, follow this order exactly:

1. Create `db/schema/[module].ts` — define the Drizzle table
2. Add the export to `db/schema/index.ts`
3. Generate and run the migration via `drizzle-kit`
4. Create `modules/[module]/[module].schema.ts` — write Zod schemas first
5. Create `modules/[module]/[module].service.ts` — implement business logic
6. Create `modules/[module]/[module].actions.ts` — implement Server Actions
7. Create `modules/[module]/components/` — build UI components
8. Create `app/(dashboard)/[module]/page.tsx` — wire up the route
9. Create `tests/e2e/[module].spec.ts` — write the E2E test

This order is not flexible. The schema (both Drizzle and Zod) is always written before the service. The service is always written before the action. The action is always written before the component.

---

### How to use this document

- **Developers:** Before creating any file, find where it belongs in the structure above. If it does not fit cleanly, ask before creating a new folder. New top-level folders require a documented architectural decision.
- **Agents:** When generating code for a module, always generate all four core files together: schema, service, actions, and at least one component. Never generate a service without its schema. Never generate a component that imports from another module. Cross-module data composition belongs in `app/` pages, not in modules.
- **Tech leads:** When reviewing PRs, flag any import that crosses the module boundary. A `modules/reports` file importing from `modules/branches` is a violation of this section regardless of how convenient it is.

---

*Previous: Section 2 — Stack*
*Next: Section 4 — Data Flow*
