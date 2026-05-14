# RBAC Implementation Guideline
## Dynamic Roles, Static Permissions
*Version 1.0 | Last updated: April 2026*

---

### What this document covers

A complete implementation guide for the default authorization model used across all projects. Roles are stored in the database and can be created and managed by org admins at runtime. The set of available permissions is defined in code and never changes without a deployment. This document covers the permission enum, database schema, policy helpers, seeding, the roles management module, and how to extend the system.

---

### Core concept

```
Code defines:   what permissions exist (a fixed, typed enum)
Database stores: what roles exist per org (created and named by org admins)
Database stores: which permissions each role has (assigned from the enum)
Database stores: which role each user has within an org
```

The result: org admins can create a "Regional Supervisor" role and assign it exactly the permissions that role needs — but they cannot invent a permission that does not exist in the system.

---

### Step 1 — The permission enum

This is the authoritative list of everything that can be permitted or denied in the system. It lives in `lib/auth/permissions.ts` and is the first file to update when a new capability is added to a module.

```typescript
// lib/auth/permissions.ts

export const PERMISSIONS = {
  branches: {
    read:   'branches:read',
    create: 'branches:create',
    update: 'branches:update',
    delete: 'branches:delete',
  },
  users: {
    read:       'users:read',
    invite:     'users:invite',
    deactivate: 'users:deactivate',
  },
  reports: {
    read:   'reports:read',
    create: 'reports:create',
    export: 'reports:export',
  },
  inventory: {
    read:  'inventory:read',
    write: 'inventory:write',
  },
  roles: {
    read:   'roles:read',
    manage: 'roles:manage', // create, update, delete roles and assign permissions
  },
} as const

// ── Derived types ────────────────────────────────────────────────────

// Recursively extracts all leaf string values from the nested object
type PermissionValues<T> = T extends Record<string, infer V>
  ? V extends string
    ? V
    : PermissionValues<V>
  : never

// The union of all valid permission strings
// e.g. 'branches:read' | 'branches:create' | 'users:invite' | ...
export type Permission = PermissionValues<typeof PERMISSIONS>

// A flat array of all permission strings — used for seeding and UI
export const ALL_PERMISSIONS: Permission[] = Object.values(PERMISSIONS).flatMap(
  (group) => Object.values(group) as Permission[]
)
```

**The type safety this provides:**

```typescript
// ✅ Correct — TypeScript confirms this is a valid permission
await requirePermission(PERMISSIONS.branches.create)

// ❌ Compile error — catches typos before they reach production
await requirePermission('branches:craete')

// ❌ Compile error — catches invented permissions
await requirePermission('dashboard:view')
```

**Rule:** Never write permission strings as raw strings in actions or pages. Always reference `PERMISSIONS.*`. Raw strings bypass type checking and break silently when permissions are renamed.

---

### Step 2 — Database schema

Two new tables: `roles` and `user_roles`. These live alongside BetterAuth's own tables (which manage user identity and org membership).

```typescript
// db/schema/roles.ts
import {
  pgTable, uuid, text, boolean,
  timestamp, unique
} from 'drizzle-orm/pg-core'

// A role belongs to one org and holds an array of permission strings
export const roles = pgTable('roles', {
  id:          uuid('id').defaultRandom().primaryKey(),
  orgId:       uuid('org_id').notNull(),
  name:        text('name').notNull(),
  description: text('description'),
  permissions: text('permissions').array().notNull().default([]),
  isDefault:   boolean('is_default').notNull().default(false),
  isSystem:    boolean('is_system').notNull().default(false), // seeded, not deletable
  createdAt:   timestamp('created_at').defaultNow().notNull(),
  updatedAt:   timestamp('updated_at').defaultNow().notNull(),
}, (table) => ({
  // Role names must be unique within an org
  uniqueNamePerOrg: unique().on(table.orgId, table.name),
}))

export type Role    = typeof roles.$inferSelect
export type NewRole = typeof roles.$inferInsert

// ─────────────────────────────────────────────────────────────────────

// Assigns exactly one role to a user within an org
export const userRoles = pgTable('user_roles', {
  id:        uuid('id').defaultRandom().primaryKey(),
  userId:    text('user_id').notNull(),   // FK to BetterAuth user.id
  orgId:     uuid('org_id').notNull(),
  roleId:    uuid('role_id').notNull(),   // FK to roles.id
  createdAt: timestamp('created_at').defaultNow().notNull(),
}, (table) => ({
  // A user has one role per org
  uniqueUserPerOrg: unique().on(table.userId, table.orgId),
}))

export type UserRole    = typeof userRoles.$inferSelect
export type NewUserRole = typeof userRoles.$inferInsert
```

Add both exports to `db/schema/index.ts`:

```typescript
// db/schema/index.ts
export * from './branches'
export * from './users'
export * from './reports'
export * from './inventory'
export * from './roles'      // ← add
```

Then generate and run the migration:

```bash
npx drizzle-kit generate
npx drizzle-kit migrate
```

---

### Step 3 — Permission resolution with per-request caching

The policy helpers need to fetch a user's permissions from the database on every request. To avoid multiple round-trips when several server components or actions call a helper in the same request, use React's `cache()` — it memoizes the result for the duration of a single server render.

```typescript
// lib/auth/get-user-permissions.ts
import { cache } from 'react'
import { db } from '@/db'
import { roles, userRoles } from '@/db/schema'
import { and, eq } from 'drizzle-orm'
import type { Permission } from './permissions'

// Fetches and caches permissions for one (userId, orgId) pair per request.
// cache() ensures this DB query runs at most once per request,
// even if multiple helpers call it.
export const getUserPermissions = cache(
  async (userId: string, orgId: string): Promise<Permission[]> => {
    const result = await db
      .select({ permissions: roles.permissions })
      .from(userRoles)
      .innerJoin(roles, eq(userRoles.roleId, roles.id))
      .where(
        and(
          eq(userRoles.userId, userId),
          eq(userRoles.orgId, orgId)
        )
      )
      .limit(1)

    if (result.length === 0) return []

    return result[0].permissions as Permission[]
  }
)
```

---

### Step 4 — Updated policy helpers

```typescript
// lib/auth/policy.ts
import { auth } from './index'
import { headers } from 'next/headers'
import { getUserPermissions } from './get-user-permissions'
import type { Permission } from './permissions'

// ─── requireUser ──────────────────────────────────────────────────────
// Use when: operation requires login, no org scope needed.

export async function requireUser() {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user) throw new Error('UNAUTHORIZED')

  return {
    userId: session.user.id,
    email:  session.user.email,
  }
}

// ─── requireOrgAccess ────────────────────────────────────────────────
// Use when: operation reads or writes org-scoped data.
// Default for almost all operations.

export async function requireOrgAccess() {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user) throw new Error('UNAUTHORIZED')

  const orgId = session.activeOrganization?.id
  if (!orgId) throw new Error('NO_ORG_CONTEXT')

  return {
    userId: session.user.id,
    orgId,
  }
}

// ─── requirePermission ───────────────────────────────────────────────
// Use when: operation is restricted to users with a specific permission.
// Accepts a typed Permission value — raw strings are a compile error.

export async function requirePermission(permission: Permission) {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user) throw new Error('UNAUTHORIZED')

  const orgId = session.activeOrganization?.id
  if (!orgId) throw new Error('NO_ORG_CONTEXT')

  // Fetch from DB — cached per request via React cache()
  const permissions = await getUserPermissions(session.user.id, orgId)

  if (!permissions.includes(permission)) {
    throw new Error('FORBIDDEN')
  }

  return {
    userId: session.user.id,
    orgId,
  }
}

// ─── hasPermission ───────────────────────────────────────────────────
// Non-throwing variant. Use when you need to conditionally render UI
// based on permissions — not to protect an operation.
//
// Example: show/hide a "Delete" button based on whether the user
// has the delete permission. The actual delete action still calls
// requirePermission() — this is display-only.

export async function hasPermission(
  permission: Permission,
  context: { userId: string; orgId: string }
): Promise<boolean> {
  const permissions = await getUserPermissions(context.userId, context.orgId)
  return permissions.includes(permission)
}
```

**The `hasPermission` helper — why it exists:**

Some UI elements should only appear for users who have the right to use them. Hiding a "Create Branch" button from a `member` role is good UX. But hiding the button is not the security control — `requirePermission()` in the action is. `hasPermission()` is for display logic only. Never use it as the sole gate on a data operation.

```tsx
// app/(dashboard)/branches/page.tsx
export default async function BranchesPage() {
  const { orgId, userId } = await requireOrgAccess()

  const [branches, canCreate] = await Promise.all([
    branchService.listByOrg({ orgId }),
    hasPermission(PERMISSIONS.branches.create, { userId, orgId }),
  ])

  return (
    <div>
      <BranchList branches={branches} />
      {canCreate && <CreateBranchButton />}
    </div>
  )
}
```

---

### Step 5 — Seeding default roles

Every new org must have a set of default roles created when the org is first set up. Default roles cover the common use cases so org admins have a working starting point.

```typescript
// lib/auth/seed-default-roles.ts
import { db } from '@/db'
import { roles } from '@/db/schema'
import { PERMISSIONS, ALL_PERMISSIONS } from './permissions'

// Define the default role set for every new org.
// isSystem = true means the role cannot be deleted by org admins.
// isDefault = true means new users get this role automatically.

const DEFAULT_ROLES = [
  {
    name: 'Admin',
    description: 'Full access to all features',
    permissions: ALL_PERMISSIONS,
    isSystem: true,
    isDefault: false,
  },
  {
    name: 'Manager',
    description: 'Can manage branches, users, and create reports',
    permissions: [
      PERMISSIONS.branches.read,
      PERMISSIONS.branches.create,
      PERMISSIONS.branches.update,
      PERMISSIONS.users.read,
      PERMISSIONS.users.invite,
      PERMISSIONS.reports.read,
      PERMISSIONS.reports.create,
      PERMISSIONS.reports.export,
      PERMISSIONS.inventory.read,
      PERMISSIONS.inventory.write,
      PERMISSIONS.roles.read,
    ],
    isSystem: false,
    isDefault: false,
  },
  {
    name: 'Member',
    description: 'Standard access — read and create reports',
    permissions: [
      PERMISSIONS.branches.read,
      PERMISSIONS.reports.read,
      PERMISSIONS.reports.create,
      PERMISSIONS.inventory.read,
    ],
    isSystem: false,
    isDefault: true, // new users get Member by default
  },
]

export async function seedDefaultRoles(orgId: string) {
  const rows = DEFAULT_ROLES.map((role) => ({
    orgId,
    name: role.name,
    description: role.description,
    permissions: role.permissions,
    isSystem: role.isSystem,
    isDefault: role.isDefault,
  }))

  await db.insert(roles).values(rows)
}
```

Call `seedDefaultRoles` inside a BetterAuth organization creation hook or in an `onOrgCreated` handler in your org setup flow:

```typescript
// lib/auth/index.ts
export const auth = betterAuth({
  // ...
  plugins: [
    organization({
      async onOrganizationCreated({ organization }) {
        await seedDefaultRoles(organization.id)
      },
    }),
  ],
})
```

---

### Step 6 — The roles management module

This is a standard module following the architecture pattern. It gives org admins a UI to create custom roles, assign permissions, and assign roles to users.

```
modules/roles/
├── roles.schema.ts
├── roles.service.ts
├── roles.actions.ts
└── components/
    ├── RoleList.tsx
    ├── RoleForm.tsx
    ├── PermissionsCheckboxGroup.tsx
    └── AssignRoleForm.tsx
```

**`roles.schema.ts`:**

```typescript
// modules/roles/roles.schema.ts
import { z } from 'zod'
import { ALL_PERMISSIONS } from '@/lib/auth/permissions'
import type { Permission } from '@/lib/auth/permissions'

export const createRoleSchema = z.object({
  name: z.string().min(1, 'Name is required').max(50, 'Name too long'),
  description: z.string().max(200).optional(),
  permissions: z.array(
    z.enum(ALL_PERMISSIONS as [Permission, ...Permission[]])
  ).min(1, 'At least one permission is required'),
})
export type CreateRoleInput = z.infer<typeof createRoleSchema>

export const updateRoleSchema = createRoleSchema.partial()
export type UpdateRoleInput = z.infer<typeof updateRoleSchema>

export const assignRoleSchema = z.object({
  userId: z.string().min(1),
  roleId: z.string().uuid('Invalid role ID'),
})
export type AssignRoleInput = z.infer<typeof assignRoleSchema>

export const roleIdSchema = z.object({
  roleId: z.string().uuid('Invalid role ID'),
})
export type RoleIdInput = z.infer<typeof roleIdSchema>
```

**`roles.service.ts`:**

```typescript
// modules/roles/roles.service.ts
import { db } from '@/db'
import { roles, userRoles } from '@/db/schema'
import { and, eq } from 'drizzle-orm'
import { logger } from '@/lib/logger'
import type {
  CreateRoleInput,
  UpdateRoleInput,
  AssignRoleInput,
} from './roles.schema'

export const rolesService = {
  async listByOrg({ orgId }: { orgId: string }) {
    return db
      .select()
      .from(roles)
      .where(eq(roles.orgId, orgId))
  },

  async create({
    data,
    orgId,
    userId,
  }: {
    data: CreateRoleInput
    orgId: string
    userId: string
  }) {
    const [role] = await db
      .insert(roles)
      .values({ ...data, orgId })
      .returning()

    logger.info('role.created', { roleId: role.id, orgId, userId })
    return { data: role }
  },

  async update({
    roleId,
    data,
    orgId,
    userId,
  }: {
    roleId: string
    data: UpdateRoleInput
    orgId: string
    userId: string
  }) {
    // Cannot update system roles
    const existing = await db
      .select()
      .from(roles)
      .where(and(eq(roles.id, roleId), eq(roles.orgId, orgId)))
      .limit(1)

    if (!existing[0]) return { error: 'Role not found' }
    if (existing[0].isSystem) return { error: 'System roles cannot be modified' }

    const [updated] = await db
      .update(roles)
      .set({ ...data, updatedAt: new Date() })
      .where(and(eq(roles.id, roleId), eq(roles.orgId, orgId)))
      .returning()

    logger.info('role.updated', { roleId, orgId, userId })
    return { data: updated }
  },

  async delete({
    roleId,
    orgId,
    userId,
  }: {
    roleId: string
    orgId: string
    userId: string
  }) {
    const existing = await db
      .select()
      .from(roles)
      .where(and(eq(roles.id, roleId), eq(roles.orgId, orgId)))
      .limit(1)

    if (!existing[0]) return { error: 'Role not found' }
    if (existing[0].isSystem) return { error: 'System roles cannot be deleted' }

    await db
      .delete(roles)
      .where(and(eq(roles.id, roleId), eq(roles.orgId, orgId)))

    logger.info('role.deleted', { roleId, orgId, userId })
    return { data: { id: roleId } }
  },

  async assignToUser({
    data,
    orgId,
    userId: actorId,
  }: {
    data: AssignRoleInput
    orgId: string
    userId: string
  }) {
    // Upsert — a user can only have one role per org
    const [assignment] = await db
      .insert(userRoles)
      .values({
        userId: data.userId,
        orgId,
        roleId: data.roleId,
      })
      .onConflictDoUpdate({
        target: [userRoles.userId, userRoles.orgId],
        set: { roleId: data.roleId },
      })
      .returning()

    logger.info('role.assigned', {
      targetUserId: data.userId,
      roleId: data.roleId,
      orgId,
      actorId,
    })

    return { data: assignment }
  },
}
```

**`roles.actions.ts`:**

```typescript
// modules/roles/roles.actions.ts
'use server'

import {
  createRoleSchema,
  updateRoleSchema,
  assignRoleSchema,
  roleIdSchema,
} from './roles.schema'
import { rolesService } from './roles.service'
import { requirePermission } from '@/lib/auth/policy'
import { PERMISSIONS } from '@/lib/auth/permissions'

export async function createRoleAction(input: unknown) {
  const parsed = createRoleSchema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input', issues: parsed.error.issues }

  const { orgId, userId } = await requirePermission(PERMISSIONS.roles.manage)

  return rolesService.create({ data: parsed.data, orgId, userId })
}

export async function updateRoleAction(roleId: unknown, input: unknown) {
  const parsedId = roleIdSchema.safeParse({ roleId })
  const parsedBody = updateRoleSchema.safeParse(input)

  if (!parsedId.success || !parsedBody.success) {
    return { error: 'Invalid input' }
  }

  const { orgId, userId } = await requirePermission(PERMISSIONS.roles.manage)

  return rolesService.update({
    roleId: parsedId.data.roleId,
    data: parsedBody.data,
    orgId,
    userId,
  })
}

export async function deleteRoleAction(roleId: unknown) {
  const parsed = roleIdSchema.safeParse({ roleId })
  if (!parsed.success) return { error: 'Invalid role ID' }

  const { orgId, userId } = await requirePermission(PERMISSIONS.roles.manage)

  return rolesService.delete({ roleId: parsed.data.roleId, orgId, userId })
}

export async function assignRoleAction(input: unknown) {
  const parsed = assignRoleSchema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input', issues: parsed.error.issues }

  const { orgId, userId } = await requirePermission(PERMISSIONS.roles.manage)

  return rolesService.assignToUser({ data: parsed.data, orgId, userId: actorId })
}
```

---

### Step 7 — The PermissionsCheckboxGroup component

The UI for assigning permissions to a role groups checkboxes by resource. The structure of `PERMISSIONS` maps directly to the groups.

```tsx
// modules/roles/components/PermissionsCheckboxGroup.tsx
'use client'

import { PERMISSIONS } from '@/lib/auth/permissions'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import type { Permission } from '@/lib/auth/permissions'

export function PermissionsCheckboxGroup({
  selected,
  onChange,
}: {
  selected: Permission[]
  onChange: (permissions: Permission[]) => void
}) {
  function toggle(permission: Permission) {
    if (selected.includes(permission)) {
      onChange(selected.filter((p) => p !== permission))
    } else {
      onChange([...selected, permission])
    }
  }

  return (
    <div className="space-y-6">
      {Object.entries(PERMISSIONS).map(([resource, actions]) => (
        <div key={resource}>
          <h4 className="text-sm font-medium capitalize mb-2">{resource}</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(actions).map(([action, permission]) => (
              <div key={permission} className="flex items-center gap-2">
                <Checkbox
                  id={permission}
                  checked={selected.includes(permission as Permission)}
                  onCheckedChange={() => toggle(permission as Permission)}
                />
                <Label htmlFor={permission} className="capitalize">
                  {action}
                </Label>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
```

---

### Step 8 — Adding a new permission

When a new module or capability is added to a project, follow this checklist:

1. **Add to `lib/auth/permissions.ts`:**
   ```typescript
   invoices: {
     read:     'invoices:read',
     create:   'invoices:create',
     approve:  'invoices:approve',
   }
   ```

2. **Update default roles in `lib/auth/seed-default-roles.ts`** — decide which default roles should receive the new permission

3. **Write a migration to update existing orgs' system roles** — existing seeded roles in production will not have the new permission until updated:
   ```typescript
   // db/migrations/scripts/add-invoices-permissions.ts
   // Append new permissions to the Admin system role for all orgs
   await db.execute(sql`
     UPDATE roles
     SET permissions = permissions || ARRAY[
       'invoices:read',
       'invoices:create',
       'invoices:approve'
     ]
     WHERE is_system = true
     AND name = 'Admin'
   `)
   ```

4. **Use in the new module's action:**
   ```typescript
   await requirePermission(PERMISSIONS.invoices.approve)
   ```

5. **The `PermissionsCheckboxGroup` updates automatically** — it reads from `PERMISSIONS` directly, so the new resource appears in the UI on the next deployment with no additional changes

---

### What this gives you

| Capability | Covered |
|---|---|
| Org admins can create custom roles at runtime | ✅ |
| Org admins can assign any defined permission to a role | ✅ |
| Org admins cannot invent permissions that don't exist | ✅ |
| New permissions are type-safe — typos are compile errors | ✅ |
| System roles (Admin, Member) cannot be deleted | ✅ |
| Default role assigned to new users automatically | ✅ |
| Permission checks never add multiple DB round trips per request | ✅ via `cache()` |
| Display-only permission checks for conditional UI | ✅ via `hasPermission()` |

---

### When to move to Approach 3

You do not need Approach 3 unless a client explicitly requires that org admins define entirely new capabilities — things the system has never heard of. In practice, this almost never happens. If it does, the migration path from this model is straightforward: move the `PERMISSIONS` enum from code into a database table and add a UI to manage it. The policy helpers, service, and action patterns do not change.

---

*Part of Architecture Canon — referenced by Section 6 (Auth & Authorization)*
*See also: Section 5 (Validation Contract) for schema patterns used in this module*
