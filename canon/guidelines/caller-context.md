# Architecture Guideline
## Caller Context & Agent Authorization
*Version 1.0 | Last updated: April 2026*

---

### What this document covers

The `CallerContext` pattern — a typed, verified object that every service method receives instead of loose `orgId` and `userId` strings. This pattern strengthens the service layer's security model and makes it ready to be consumed by AI agents without bypassing authentication or audit controls.

---

### The problem this solves

The basic service contract — receive `orgId` and `userId`, filter by org, log the actor — works correctly when the only caller is a Server Action that has run `requireOrgAccess()` first. It breaks down when services are called from AI agents, background jobs, or other non-HTTP contexts, because those callers have no session to validate against.

Without this pattern:
- An agent can pass any `orgId` it wants — there is no enforcement
- Agent actions appear in the audit log as a human user with no indication an agent was involved
- A compromised or misconfigured agent can access any org's data if it knows or guesses a valid `orgId`
- There is no way to revoke an agent's access without code changes

With this pattern:
- `orgId` is locked to the token at creation time — agents cannot change it
- Every audit record carries `callerType` and `agentId` — full traceability
- Agent tokens can be revoked immediately with one database update
- Agents carry only the permissions their token grants — principle of least privilege

---

### The CallerContext type

```typescript
// lib/auth/caller-context.ts
import type { Permission } from './permissions'

export type CallerType = 'user' | 'agent'

export type CallerContext = {
  // Who is ultimately responsible for this action
  userId: string

  // Which org is being acted upon
  orgId: string

  // Whether this call came from a human session or an agent token
  callerType: CallerType

  // Present when callerType is 'user'
  sessionId?: string

  // Present when callerType is 'agent'
  agentId?: string

  // Present when callerType is 'agent'
  // The specific permissions this token grants — a subset of the owner's permissions
  agentPermissions?: Permission[]
}
```

`CallerContext` is never constructed by a service. It is never constructed by a component. It is only produced by two functions: `requireOrgAccess()` (for human callers) and `authorizeAgent()` (for agent callers). These are the only two authorized construction paths.

---

### Construction path 1 — human callers

`requireOrgAccess()` reads the BetterAuth session and returns a `CallerContext`. The service receives it without knowing or caring that it came from a session.

```typescript
// lib/auth/policy.ts
export async function requireOrgAccess(): Promise<CallerContext> {
  const session = await auth.api.getSession({ headers: await headers() })

  if (!session?.user)              throw new Error('UNAUTHORIZED')
  if (!session.activeOrganization) throw new Error('NO_ORG_CONTEXT')

  return {
    userId:     session.user.id,
    orgId:      session.activeOrganization.id,
    callerType: 'user',
    sessionId:  session.session.id,
  }
}
```

---

### Construction path 2 — agent callers

`authorizeAgent()` validates a bearer token against the `agentTokens` table and returns a `CallerContext` scoped to that token's org and permissions.

```typescript
// lib/auth/agent-context.ts
import { db } from '@/db'
import { agentTokens } from '@/db/schema'
import { and, eq, gt } from 'drizzle-orm'
import type { CallerContext } from './caller-context'
import type { Permission } from './permissions'

export async function authorizeAgent(token: string): Promise<CallerContext> {
  if (!token) throw new Error('INVALID_AGENT_TOKEN')

  const result = await db
    .select()
    .from(agentTokens)
    .where(and(
      eq(agentTokens.tokenHash, hashToken(token)),
      eq(agentTokens.revoked,   false),
      gt(agentTokens.expiresAt, new Date())
    ))
    .limit(1)

  if (!result[0]) throw new Error('INVALID_AGENT_TOKEN')

  const agentToken = result[0]

  return {
    userId:           agentToken.ownerUserId,
    orgId:            agentToken.orgId,
    callerType:       'agent',
    agentId:          agentToken.agentId,
    agentPermissions: agentToken.permissions as Permission[],
  }
}

// Tokens are stored as hashes — raw tokens are never stored
function hashToken(token: string): string {
  const crypto = require('crypto')
  return crypto.createHash('sha256').update(token).digest('hex')
}
```

---

### The agent token table

```typescript
// db/schema/agent-tokens.ts
import {
  pgTable, uuid, text, boolean, timestamp
} from 'drizzle-orm/pg-core'

export const agentTokens = pgTable('agent_tokens', {
  id:          uuid('id').defaultRandom().primaryKey(),

  // The token is stored as a SHA-256 hash
  // The raw token is shown once at creation and never stored
  tokenHash:   text('token_hash').notNull().unique(),

  // Descriptive name for the agent — e.g. 'inventory-sync-agent'
  agentId:     text('agent_id').notNull(),

  // The org this token is scoped to — cannot be changed after creation
  orgId:       uuid('org_id').notNull(),

  // The human user who authorized this agent to act on their behalf
  ownerUserId: text('owner_user_id').notNull(),

  // A subset of the owner's permissions — principle of least privilege
  permissions: text('permissions').array().notNull().default([]),

  // Revoke immediately if the agent is compromised or decommissioned
  revoked:     boolean('revoked').notNull().default(false),

  // Tokens expire — they must be rotated, they do not live forever
  expiresAt:   timestamp('expires_at').notNull(),

  createdAt:   timestamp('created_at').defaultNow().notNull(),
  lastUsedAt:  timestamp('last_used_at'),
})

export type AgentToken    = typeof agentTokens.$inferSelect
export type NewAgentToken = typeof agentTokens.$inferInsert
```

Add to `db/schema/index.ts`:
```typescript
export * from './agent-tokens'
```

---

### Token security rules

**Tokens are hashed at rest.**
The raw token is generated once, shown to the operator once, and never stored. Only the SHA-256 hash is stored in the database. This means a database breach does not expose usable tokens.

```typescript
// lib/auth/create-agent-token.ts
import { db } from '@/db'
import { agentTokens } from '@/db/schema'
import crypto from 'crypto'
import type { Permission } from './permissions'

export async function createAgentToken({
  agentId,
  orgId,
  ownerUserId,
  permissions,
  expiresInDays = 90,
}: {
  agentId:     string
  orgId:       string
  ownerUserId: string
  permissions: Permission[]
  expiresInDays?: number
}) {
  // Generate a cryptographically secure random token
  const rawToken = `agt_${crypto.randomBytes(32).toString('hex')}`
  const tokenHash = crypto
    .createHash('sha256')
    .update(rawToken)
    .digest('hex')

  const expiresAt = new Date()
  expiresAt.setDate(expiresAt.getDate() + expiresInDays)

  await db.insert(agentTokens).values({
    tokenHash,
    agentId,
    orgId,
    ownerUserId,
    permissions,
    expiresAt,
  })

  // Return the raw token — this is the only time it is available
  // The caller must store it securely (secrets manager, env variable)
  return { token: rawToken, expiresAt }
}
```

**Tokens are org-scoped at creation.**
The `orgId` on a token is set once and never updated. An agent cannot escalate to a different org by changing a parameter.

**Tokens have a permission subset.**
When creating a token, the caller specifies which permissions the agent needs. The token's permission set must be a strict subset of the `ownerUserId`'s current permissions. An agent cannot be granted permissions its owner does not have.

**Tokens expire.**
Default expiry is 90 days. Long-lived tokens are a security liability — rotation forces periodic review of whether the agent still needs access.

**Tokens can be revoked immediately.**
```typescript
// lib/auth/revoke-agent-token.ts
export async function revokeAgentToken(tokenId: string, orgId: string) {
  await db
    .update(agentTokens)
    .set({ revoked: true })
    .where(and(
      eq(agentTokens.id,    tokenId),
      eq(agentTokens.orgId, orgId)   // org-scoped revocation
    ))
}
```

---

### Checking permissions for both caller types

The `requirePermission()` helper handles both humans and agents:

```typescript
// lib/auth/policy.ts

export async function requirePermission(
  permission: Permission
): Promise<CallerContext> {
  const session = await auth.api.getSession({ headers: await headers() })

  if (!session?.user)              throw new Error('UNAUTHORIZED')
  if (!session.activeOrganization) throw new Error('NO_ORG_CONTEXT')

  const ctx: CallerContext = {
    userId:     session.user.id,
    orgId:      session.activeOrganization.id,
    callerType: 'user',
    sessionId:  session.session.id,
  }

  // For human callers — fetch from DB via RBAC system
  const userPermissions = await getUserPermissions(ctx.userId, ctx.orgId)
  if (!userPermissions.includes(permission)) throw new Error('FORBIDDEN')

  return ctx
}

// ─── For agent callers — used directly in agent entry points ──────────

export function requireAgentPermission(
  ctx: CallerContext,
  permission: Permission
): void {
  if (ctx.callerType !== 'agent') {
    throw new Error('CALLER_TYPE_MISMATCH')
  }

  const agentPerms = ctx.agentPermissions ?? []
  if (!agentPerms.includes(permission)) {
    throw new Error('AGENT_FORBIDDEN')
  }
}
```

---

### How an agent entry point is structured

An agent does not call Server Actions — those require an HTTP request context. Instead, agents call a dedicated **agent entry point**: a plain async function that accepts a token, constructs a `CallerContext`, checks the required permission, and calls the service.

```typescript
// lib/agents/inventory-sync.agent.ts

import { authorizeAgent } from '@/lib/auth/agent-context'
import { requireAgentPermission } from '@/lib/auth/policy'
import { PERMISSIONS } from '@/lib/auth/permissions'
import { inventoryService } from '@/modules/inventory/inventory.service'

export async function runInventorySyncAgent(token: string) {
  // Step 1: Authorize — constructs CallerContext from token
  const ctx = await authorizeAgent(token)

  // Step 2: Confirm the token grants the required permission
  requireAgentPermission(ctx, PERMISSIONS.inventory.write)

  // Step 3: Call the service — identical to how an action would call it
  const result = await inventoryService.syncFromExternalFeed({ ctx })

  return result
}
```

This structure mirrors the Server Action pattern exactly:
- Authorize (token → CallerContext)
- Check permission
- Call service

The service receives the same `CallerContext` shape regardless of whether the caller was a human or an agent.

---

### Audit trail — distinguishing humans from agents

Because `CallerContext` carries `callerType` and `agentId`, the audit trail can distinguish human and agent actions:

```typescript
// lib/audit.ts

export const audit = {
  record({
    action,
    resourceId,
    ctx,
    metadata,
  }: {
    action:     string
    resourceId: string
    ctx:        CallerContext
    metadata?:  Record<string, unknown>
  }) {
    // Every audit record knows exactly who or what performed the action
    db.insert(auditLog).values({
      action,
      resourceId,
      orgId:      ctx.orgId,
      userId:     ctx.userId,
      callerType: ctx.callerType,
      agentId:    ctx.agentId ?? null,
      sessionId:  ctx.sessionId ?? null,
      metadata:   metadata ? JSON.stringify(metadata) : null,
      createdAt:  new Date(),
    })
  }
}
```

An audit query for "what changed this record and who authorized it" now returns a complete picture:

```
action: branch.updated
userId: usr_jane_smith
callerType: agent
agentId: inventory-sync-agent
orgId: org_acme
```

You can trace every agent action back to the human who authorized the token.

---

### Migration path

**Phase 1 — CallerContext everywhere (no new tables needed)**

Update `requireOrgAccess()`, `requireUser()`, and `requirePermission()` to return `CallerContext`. Update all service method signatures from `{ orgId, userId }` to `{ ctx }`. Update all audit calls to accept `ctx`. This is a mechanical refactor — no behavior changes.

**Phase 2 — Agent token infrastructure (before first agent)**

Add the `agentTokens` table and migration. Implement `authorizeAgent()` and `createAgentToken()`. Write the first agent entry point. At this point agents can call services through the same security model humans use.

**Phase 3 — Agent permission scoping (when principle of least privilege is needed)**

Implement `requireAgentPermission()`. Add token-level permission selection to the token creation UI. Existing tokens default to full owner permissions until explicitly restricted.

---

### The invariant this establishes

> Every service call in the system is traceable to a verified identity, a verified org, and a verified caller type. No service method can be called with unverified context.

This invariant holds whether the caller is a human using a browser, an AI agent running in a background process, or a future caller type not yet imagined.

---

*Part of Architecture Canon*
*Referenced by: Section 6 (Auth & Authorization), Section 7 (Service Layer)*
*See also: RBAC Guideline for permission definitions*
