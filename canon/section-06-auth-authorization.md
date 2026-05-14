# Architecture Canon
## Section 6 — Auth & Authorization
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

How authentication and authorization work in this architecture: BetterAuth setup, the session shape, the three policy helpers, the `CallerContext` pattern, the org hierarchy model, and where every check happens in the request lifecycle. Every rule in this section is a hard requirement.

The full `CallerContext` and agent authorization implementation is documented in the **Caller Context & Agent Authorization Guideline**. This section covers the concepts and the human-caller flow. Read the guideline before implementing agent callers.

---

### Core concepts — auth vs authorization

These two words are often confused. In this architecture they are distinct responsibilities:

**Authentication** — confirms who the user is. Handled by BetterAuth. Produces a session with a verified user identity.

**Authorization** — confirms what the user is allowed to do. Handled by the policy helpers. Uses the session to confirm org membership and permissions before any data operation.

Authentication always happens first. Authorization always happens at the API boundary, before the service is called.

---

### BetterAuth setup

BetterAuth is initialized once in `lib/auth/index.ts`. This file is the single source of truth for the auth configuration across the entire application.

```typescript
// lib/auth/index.ts
import { betterAuth } from 'better-auth'
import { drizzleAdapter } from 'better-auth/adapters/drizzle'
import { organization } from 'better-auth/plugins'
import { db } from '@/db'
import * as schema from '@/db/schema'

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: 'pg',
    schema,
  }),
  plugins: [
    organization({
      // Controls which roles exist in the system
      roles: {
        admin: {
          permissions: ['*'], // full access
        },
        manager: {
          permissions: [
            'branches:read',
            'branches:create',
            'branches:update',
            'users:read',
            'reports:read',
            'reports:create',
          ],
        },
        member: {
          permissions: [
            'branches:read',
            'reports:read',
            'reports:create',
          ],
        },
      },
    }),
  ],
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24,      // refresh if older than 1 day
  },
  emailAndPassword: {
    enabled: true,
  },
})

export type Auth = typeof auth
```

**What BetterAuth manages automatically:**
- User creation and login
- Session creation, storage, and expiry
- Password hashing
- Organization membership records
- Role assignments per org

**What BetterAuth does not manage:**
- Business logic
- Data access patterns
- The org hierarchy below the org level (branches, regions, stores — that is a module concern)

---

### The session shape

After login, BetterAuth creates a session. The policy helpers read this session on every request. Understanding the session shape is required to understand how org context flows through the system.

```typescript
// What the session contains after a successful login:
{
  user: {
    id: 'usr_01jx...',        // user's ID
    email: 'user@example.com',
    name: 'Jane Smith',
  },
  session: {
    id: 'ses_01jx...',
    expiresAt: '2026-05-15T...',
  },
  // Added by the organization plugin:
  activeOrganization: {
    id: 'org_01jx...',        // the org the user is currently acting within
    name: 'Acme Corp',
    role: 'manager',          // the user's role in this org
    permissions: [            // permissions derived from the role
      'branches:read',
      'branches:create',
      'reports:read',
    ],
  }
}
```

**The `activeOrganization` is the org context.** Its `id` is the `orgId` that flows through every service call. Its `role` and `permissions` are what the policy helpers check.

---

### The org hierarchy model

Your applications serve corporations with multiple organizational units (regions, branches, stores). This is not the same as multi-tenancy — there is one database, and the hierarchy is modelled as data, not as separate schemas.

**The hierarchy:**

```
Organization (top level — the corporation)
  └── OrgUnit (branches, regions, stores, departments)
        └── Users belong to one org and optionally one org unit
```

**How this maps to the database:**

```typescript
// db/schema/org-units.ts
export const orgUnits = pgTable('org_units', {
  id: uuid('id').defaultRandom().primaryKey(),
  orgId: uuid('org_id').notNull(),           // which org this unit belongs to
  parentId: uuid('parent_id'),               // null = top-level unit
  type: text('type').notNull(),              // 'region' | 'branch' | 'store'
  name: text('name').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

// Users have an optional org unit assignment
// db/schema/users.ts (BetterAuth manages the base user table,
// this is an extension for org-unit scoping)
export const userProfiles = pgTable('user_profiles', {
  id: uuid('id').defaultRandom().primaryKey(),
  userId: text('user_id').notNull(),          // FK to BetterAuth user
  orgId: uuid('org_id').notNull(),
  orgUnitId: uuid('org_unit_id'),             // null = org-wide access
  createdAt: timestamp('created_at').defaultNow().notNull(),
})
```

**How org unit context flows through the system:**

The policy helpers return a `CallerContext` containing `orgId` — the top-level org. Services that need to scope further to an org unit receive `orgUnitId` as an additional parameter, fetched from the user's profile at the API boundary:

```typescript
// In a Server Action that needs org-unit scope:
const ctx = await requireOrgAccess()

// Fetch the user's org unit assignment
const profile = await userProfileService.getByUserId({
  userId: ctx.userId,
  orgId:  ctx.orgId,
})

// Pass both to the service
return branchService.listForUser({
  ctx,
  orgUnitId: profile.orgUnitId ?? undefined,
})
```

**The rule:** `orgId` is always present. `orgUnitId` is optional and only fetched when the feature requires scoping below the org level.

---

### The three policy helpers

All three live in `lib/auth/policy.ts`. They are the only functions in the codebase that read the session. Services never read the session — they receive a `CallerContext` as a parameter.

All three helpers return a `CallerContext` — the verified, typed object every service method accepts. This is what makes the service layer safe to call from both human sessions and agent tokens without changing the service code.

```typescript
// lib/auth/policy.ts
import { auth } from './index'
import { headers } from 'next/headers'
import { getUserPermissions } from './get-user-permissions'
import type { CallerContext } from './caller-context'
import type { Permission } from './permissions'

// ─── Helper 1: requireUser ────────────────────────────────────────────
// Confirms a session exists and returns a CallerContext.
// Use when: the operation requires login but no org scope yet.
// Example: profile pages, account settings.

export async function requireUser(): Promise<CallerContext> {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user) throw new Error('UNAUTHORIZED')

  return {
    userId:     session.user.id,
    orgId:      '',           // no org scope at this level
    callerType: 'user',
    sessionId:  session.session.id,
  }
}

// ─── Helper 2: requireOrgAccess ───────────────────────────────────────
// Confirms a session exists and the user belongs to an active org.
// Returns a CallerContext with userId and orgId verified from the session.
// Use when: the operation reads or writes org-scoped data.
// This is the default for almost all operations.

export async function requireOrgAccess(): Promise<CallerContext> {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user)              throw new Error('UNAUTHORIZED')
  if (!session.activeOrganization) throw new Error('NO_ORG_CONTEXT')

  return {
    userId:     session.user.id,
    orgId:      session.activeOrganization.id,
    callerType: 'user',
    sessionId:  session.session.id,
  }
}

// ─── Helper 3: requirePermission ─────────────────────────────────────
// Confirms a session, org membership, and a specific permission.
// Returns a CallerContext — the same shape as requireOrgAccess().
// Use when: the operation is restricted to a subset of org members.
// Example: creating users, deleting records, exporting reports.

export async function requirePermission(
  permission: Permission
): Promise<CallerContext> {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user)              throw new Error('UNAUTHORIZED')
  if (!session.activeOrganization) throw new Error('NO_ORG_CONTEXT')

  const ctx: CallerContext = {
    userId:     session.user.id,
    orgId:      session.activeOrganization.id,
    callerType: 'user',
    sessionId:  session.session.id,
  }

  // Fetch from DB — cached per request via React cache()
  const permissions = await getUserPermissions(ctx.userId, ctx.orgId)
  if (!permissions.includes(permission)) throw new Error('FORBIDDEN')

  return ctx
}

// ─── hasPermission ───────────────────────────────────────────────────
// Non-throwing variant. Use for conditional UI rendering only.
// Never use as the sole gate on a data operation.

export async function hasPermission(
  permission: Permission,
  ctx: CallerContext
): Promise<boolean> {
  if (ctx.callerType === 'agent') {
    return (ctx.agentPermissions ?? []).includes(permission)
  }
  const permissions = await getUserPermissions(ctx.userId, ctx.orgId)
  return permissions.includes(permission)
}

// ─── requireAgentPermission ──────────────────────────────────────────
// For agent entry points — confirms the token grants a specific permission.
// Call after authorizeAgent() returns a CallerContext.

export function requireAgentPermission(
  ctx: CallerContext,
  permission: Permission
): void {
  if (ctx.callerType !== 'agent') throw new Error('CALLER_TYPE_MISMATCH')
  const agentPerms = ctx.agentPermissions ?? []
  if (!agentPerms.includes(permission)) throw new Error('AGENT_FORBIDDEN')
}
```

---

### Which helper to use — decision rule

```
Does the operation require login?
  NO  → No auth check (public routes only — login page, marketing pages)
  YES → Continue

Does the operation touch org-scoped data?
  NO  → requireUser()
        Example: GET /profile, PUT /account/settings

  YES → Continue

Is the operation restricted to specific roles/permissions?
  NO  → requireOrgAccess()
        Example: GET /branches, GET /reports (any org member can read)

  YES → requirePermission('resource:action')
        Example: POST /branches (managers+), DELETE /users (admin only)
```

**Permission naming convention:** `resource:action` in lowercase.

```typescript
// Examples of well-named permissions:
'branches:create'
'branches:update'
'branches:delete'
'users:invite'
'users:deactivate'
'reports:export'
'inventory:write'
```

---

### Where checks happen — the invariants

**Rule 1: Auth is always checked at the API boundary, never inside the service.**

```typescript
// ✅ Correct — auth check in the action
export async function createBranchAction(input: unknown) {
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input' }

  const { orgId, userId } = await requireOrgAccess() // ← here

  return branchService.create({ data: parsed.data, orgId, userId })
}

// ❌ Wrong — auth check inside the service
export const branchService = {
  async create({ data }) {
    const { orgId } = await requireOrgAccess() // ← never here
    // ...
  }
}
```

**Why:** Services are called from actions, which have already verified auth. If a service reads auth itself, it becomes impossible to call from tests, from other services, or from background jobs without faking a session. Explicit parameters are always testable. Hidden session reads are not.

**Rule 2: Layout-level auth guards protect sections. Page-level checks enforce specific permissions.**

```typescript
// app/(dashboard)/layout.tsx — guards the entire dashboard section
export default async function DashboardLayout({ children }) {
  await requireOrgAccess() // any org member can enter the dashboard
  return <>{children}</>
}

// app/(dashboard)/reports/page.tsx — page-level permission check
export default async function ReportsPage() {
  await requirePermission('reports:read') // only members with this permission
  const { orgId } = await requireOrgAccess()
  const reports = await reportService.listByOrg({ orgId })
  return <ReportList reports={reports} />
}
```

**Note:** Calling both `requirePermission` and `requireOrgAccess` on the same page reads the session twice. This is acceptable for clarity. If performance becomes a concern, `requirePermission` already returns `{ userId, orgId }` — use that return value instead of calling `requireOrgAccess` again.

**Rule 3: The service always receives orgId as a parameter and always filters by it.**

```typescript
// ✅ Correct — org scope is explicit and always applied
async listByOrg({ orgId }: { orgId: string }) {
  return db.select().from(branches).where(eq(branches.orgId, orgId))
}

// ❌ Wrong — no org filter means data leaks across orgs
async list() {
  return db.select().from(branches) // returns ALL branches from ALL orgs
}
```

---

### Error handling for auth failures

Auth helpers throw with a string error code. Next.js catches unhandled throws from Server Actions and Server Components at the nearest error boundary.

| Error thrown | Cause | Next.js behavior |
|---|---|---|
| `UNAUTHORIZED` | No session | Redirects to login page |
| `NO_ORG_CONTEXT` | Session exists but no active org | Redirects to org selection |
| `FORBIDDEN` | Session and org exist but permission missing | Renders 403 error page |

Configure these redirects in `middleware.ts`:

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { auth } from '@/lib/auth'

export async function middleware(request: NextRequest) {
  const session = await auth.api.getSession({
    headers: request.headers,
  })

  const isAuthRoute = request.nextUrl.pathname.startsWith('/login')
  const isDashboardRoute = request.nextUrl.pathname.startsWith('/dashboard')

  if (isDashboardRoute && !session) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (isAuthRoute && session) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/login'],
}
```

The middleware provides a first layer of route protection. The policy helpers in actions and pages provide the authoritative check. Both are needed — middleware is fast but runs before full auth context is available; policy helpers are authoritative but run after the request reaches the handler.

---

### Customer-facing apps — the account type distinction

Some applications serve external customers rather than internal employees. The auth model is identical — BetterAuth, session, org context, policy helpers. What differs is the account type and the permissions assigned to it.

```typescript
// Customer accounts are org-scoped like employee accounts.
// The session shape is the same. The role is different.

// Internal employee session:
activeOrganization: {
  id: 'org_acme',
  role: 'manager',
  permissions: ['branches:read', 'reports:create', ...]
}

// External customer session:
activeOrganization: {
  id: 'org_acme',   // ← same org — the customer belongs to the client's org
  role: 'customer',
  permissions: ['orders:create', 'orders:read', 'profile:update']
}
```

**The invariant holds:** every account belongs to an org context. The `orgId` is always present. The account type determines the role and permissions, not the presence of org scope.

---

### Adding a new permission — the checklist

When a new restricted operation is added to a module:

1. Define the permission string: `'resource:action'` (e.g. `'inventory:write'`)
2. Add it to the relevant roles in `lib/auth/index.ts` under the `organization` plugin config
3. Use `requirePermission('inventory:write')` in the Server Action or page
4. Document the permission in the module's schema file as a comment near the relevant schema
5. Add a Playwright test that confirms an unauthorized role cannot perform the operation

---

### How to use this document

- **Developers:** Always check the decision rule above before writing an auth check. Use `requireOrgAccess()` as the default. Only reach for `requirePermission()` when the operation is genuinely restricted to a subset of roles. Never read the session inside a service.
- **Agents:** Every generated Server Action must include an auth check after Zod validation. The default is `requireOrgAccess()`. If the operation is a write or a restricted read, check the module's permission list and use `requirePermission()`. Never generate a service method that calls an auth helper — auth context is always passed as a parameter.
- **Tech leads:** When reviewing PRs, check that every new action calls an auth helper, that no service reads the session, and that every new permission is registered in `lib/auth/index.ts`. A permission string used in `requirePermission()` that is not registered in the config is a silent no-op — it will always deny access.

---

*Previous: Section 5 — Validation Contract (Zod)*
*Next: Section 7 — Service Layer*
