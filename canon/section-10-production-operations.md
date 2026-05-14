# Architecture Canon
## Section 10 — Production Operations
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

The infrastructure layer that keeps a running application observable, debuggable, and maintainable: structured logging, the audit trail, database migration workflow, environment configuration validation, error boundaries, and health checks. These are not optional production concerns — they are required parts of every project from day one.

---

### Logging

The logger provides structured, contextual output for operational visibility. It is not the audit trail — the logger is for developers and operations teams. The audit trail is for the business and compliance.

**The library:** `pino` — fast, structured JSON output in production, human-readable output in development. Installed once, configured once, imported everywhere.

```bash
npm install pino pino-pretty
```

#### `lib/logger.ts` — the canonical implementation

```typescript
// lib/logger.ts
import pino from 'pino'

const isDev = process.env.NODE_ENV !== 'production'

export const logger = pino({
  level: isDev ? 'debug' : 'info',
  ...(isDev && {
    transport: {
      target:  'pino-pretty',
      options: { colorize: true, ignore: 'pid,hostname' },
    },
  }),
  // Standard fields on every log entry
  base: {
    env: process.env.NODE_ENV,
    app: process.env.NEXT_PUBLIC_APP_NAME ?? 'app',
  },
})
```

#### Log levels — when to use each

| Level | Use for | Example |
|---|---|---|
| `error` | Unexpected failures that need immediate attention | DB connection failure, unhandled exception |
| `warn` | Recoverable problems, deprecations, suspicious activity | Audit write failed, missing optional config |
| `info` | Business events — the standard level for service operations | `branch.created`, `user.deactivated`, `report.exported` |
| `debug` | Detailed flow information — development only | Request params, query results, internal state |

#### The logging convention in services

```typescript
// Every successful write operation logs at info level
// Format: 'resource.event'
// Context: always include resourceId, orgId, userId at minimum

logger.info('branch.created',   { branchId: branch.id, orgId: ctx.orgId, userId: ctx.userId })
logger.info('branch.updated',   { branchId,            orgId: ctx.orgId, userId: ctx.userId })
logger.info('branch.deleted',   { branchId,            orgId: ctx.orgId, userId: ctx.userId })

// Errors include the error message and stack if available
logger.error('payment.failed',  { orderId, orgId, error: err.message, stack: err.stack })

// Warnings for recoverable issues
logger.warn('audit.write.failed', { action, resourceId, error: err.message })
```

**What never goes in a log:**
- Passwords, tokens, secrets, API keys
- Full request or response bodies (may contain PII)
- PII — names, emails, phone numbers in plain text

---

### Audit trail

The audit trail is a permanent, queryable record of who did what to which resource and when. It lives in the database and is never deleted. It differs from the logger in purpose and destination:

| | Logger | Audit trail |
|---|---|---|
| Destination | Log aggregation service / stdout | Application database |
| Primary consumer | Developers, ops team, alerting | Business users, compliance, security |
| Retention | Days to weeks (configurable) | Permanent |
| Query pattern | Full-text search, time range | By resource, by user, by org |
| Write failure | Logged as a warning | Non-blocking, logged as a warning |

#### The audit log table

```typescript
// db/schema/audit-log.ts
import { pgTable, uuid, text, jsonb, timestamp } from 'drizzle-orm/pg-core'

export const auditLog = pgTable('audit_log', {
  id:         uuid('id').defaultRandom().primaryKey(),

  // The event that occurred — 'branch.created', 'user.deactivated'
  action:     text('action').notNull(),

  // The primary record that was affected
  resourceId: text('resource_id').notNull(),

  // Org context — always present
  orgId:      uuid('org_id').notNull(),

  // The user ultimately responsible for the action
  userId:     text('user_id').notNull(),

  // Whether the caller was a human or an agent
  callerType: text('caller_type').notNull(), // 'user' | 'agent'

  // Present when callerType is 'agent'
  agentId:    text('agent_id'),

  // Present when callerType is 'user'
  sessionId:  text('session_id'),

  // Optional additional context — before/after values, related IDs
  metadata:   jsonb('metadata'),

  createdAt:  timestamp('created_at').defaultNow().notNull(),
})

export type AuditLogEntry    = typeof auditLog.$inferSelect
export type NewAuditLogEntry = typeof auditLog.$inferInsert
```

Add to `db/schema/index.ts` and generate the migration.

#### `lib/audit.ts` — the canonical implementation

```typescript
// lib/audit.ts
import { db } from '@/db'
import { auditLog } from '@/db/schema'
import { logger } from './logger'
import type { CallerContext } from './auth/caller-context'

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
  }): void {
    // Non-blocking — a failed audit write must never break the primary operation
    // The error is logged as a warning so it can be investigated
    db.insert(auditLog)
      .values({
        action,
        resourceId,
        orgId:      ctx.orgId,
        userId:     ctx.userId,
        callerType: ctx.callerType,
        agentId:    ctx.agentId    ?? null,
        sessionId:  ctx.sessionId  ?? null,
        metadata:   metadata       ?? null,
      })
      .catch((err) => {
        logger.warn('audit.write.failed', {
          action,
          resourceId,
          orgId:  ctx.orgId,
          error:  err.message,
        })
      })
  },
}
```

**Why non-blocking:**
The audit write happens after the primary operation succeeds. If the audit write fails, the primary operation has already succeeded and cannot be rolled back. Blocking on the audit write would cause the API to return an error even though the user's action completed successfully. The warning log ensures the failure is visible without breaking the user experience.

**When a strict audit is required:**
If a compliance requirement demands that every operation has a guaranteed audit record, wrap the primary operation and the audit write in a transaction. This makes the audit write blocking and atomic:

```typescript
// Strict audit — operation and audit are atomic
async create({ data, ctx }) {
  return db.transaction(async (tx) => {
    const [branch] = await tx.insert(branches).values({ ...data, orgId: ctx.orgId }).returning()

    // If this insert fails, the branch insert is also rolled back
    await tx.insert(auditLog).values({
      action:     'branch.created',
      resourceId: branch.id,
      orgId:      ctx.orgId,
      userId:     ctx.userId,
      callerType: ctx.callerType,
    })

    return { data: branch }
  })
}
```

Use this pattern only when the compliance requirement explicitly demands it — it adds latency to every write operation.

#### Querying the audit trail

A standard query for "what happened to this record":

```typescript
// modules/audit/audit.service.ts
export const auditService = {
  async getHistory({
    resourceId,
    orgId,
    limit = 50,
  }: {
    resourceId: string
    orgId:      string
    limit?:     number
  }) {
    return db
      .select()
      .from(auditLog)
      .where(and(
        eq(auditLog.resourceId, resourceId),
        eq(auditLog.orgId,      orgId),
      ))
      .orderBy(desc(auditLog.createdAt))
      .limit(limit)
  },
}
```

---

### Database migrations — the complete workflow

Migrations are the mechanism for evolving the database schema safely. Every schema change — adding a table, adding a column, modifying a constraint — goes through this workflow.

#### `drizzle.config.ts` — the canonical configuration

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema:    './db/schema/index.ts',
  out:       './db/migrations',
  dialect:   'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  // Generate verbose migration names — easier to read in git history
  verbose: true,
})
```

#### The migration workflow — step by step

```
1. Edit the Drizzle schema file
   → db/schema/[table].ts

2. Generate the migration
   → npx drizzle-kit generate
   → Creates db/migrations/XXXX_[description].sql

3. Review the generated SQL
   → Open the .sql file and confirm it does what you intended
   → Pay special attention to: DROP statements, column renames, constraint changes

4. Apply locally
   → npx drizzle-kit migrate
   → Confirms the SQL runs without error on your local database

5. Commit both files
   → git add db/schema/[table].ts db/migrations/XXXX_[description].sql
   → Never commit a schema change without its migration

6. CI/CD runs migrations on deployment
   → Production migrations are automated — never run manually
```

#### Migration rules — non-negotiable

**Never edit a migration file after it has been committed.**
Drizzle tracks which migrations have been applied via a `__drizzle_migrations` table. Editing an applied migration causes a hash mismatch and breaks the migration chain. If a migration contains an error, generate a new migration to fix it.

**Never apply migrations to production manually.**
Production migrations run automatically on deployment. Manual intervention is the leading cause of schema drift between environments.

**Never delete migration files.**
Migration files are the audit history of the database schema. They are the source of truth for how the database evolved over time. Deleting them makes it impossible to recreate the database from scratch.

**Column renames require explicit two-step migrations.**
A column rename generates a DROP and ADD, which loses data. Use Drizzle's `.rename()` helper to generate a proper ALTER TABLE RENAME COLUMN:

```typescript
// ❌ This generates DROP + ADD (data loss in production)
// Before: name: text('name')
// After:  branchName: text('branch_name')

// ✅ This generates ALTER TABLE RENAME COLUMN
import { text } from 'drizzle-orm/pg-core'
branchName: text('name').rename('branch_name')
// Then: npx drizzle-kit generate
```

**Adding a NOT NULL column to an existing table requires a default.**
Without a default, the migration fails if the table has existing rows:

```typescript
// ❌ Fails on tables with existing rows
status: text('status').notNull()

// ✅ Provides a default for existing rows
status: text('status').notNull().default('active')

// After the migration, if you want to remove the default:
// Generate another migration that drops the default constraint
```

#### Useful migration commands

```bash
# Generate a new migration from schema changes
npx drizzle-kit generate

# Apply pending migrations
npx drizzle-kit migrate

# View migration status (which have been applied)
npx drizzle-kit status

# Open Drizzle Studio — visual DB browser (development only)
npx drizzle-kit studio

# Push schema directly to DB without generating files (development only, never production)
npx drizzle-kit push
```

---

### Environment configuration

Environment variables are validated at application startup using Zod. This means a deployment with a missing or malformed environment variable fails immediately with a clear error — rather than failing later at runtime when a specific feature is used.

#### `lib/env.ts` — the canonical implementation

```typescript
// lib/env.ts
import { z } from 'zod'

const envSchema = z.object({
  // Database
  DATABASE_URL: z.string().url('DATABASE_URL must be a valid URL'),

  // Auth
  BETTER_AUTH_SECRET: z.string().min(32, 'BETTER_AUTH_SECRET must be at least 32 characters'),
  BETTER_AUTH_URL:    z.string().url('BETTER_AUTH_URL must be a valid URL'),

  // Application
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  NEXT_PUBLIC_APP_NAME: z.string().default('App'),

  // Optional integrations — add as needed
  WEBHOOK_SECRET:   z.string().optional(),
  RESEND_API_KEY:   z.string().optional(),
  STORAGE_BUCKET:   z.string().optional(),
})

// Parse and validate at import time
// If validation fails, the application throws with a clear error message
const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error('❌ Invalid environment configuration:')
  console.error(parsed.error.flatten().fieldErrors)
  throw new Error('Invalid environment configuration — see errors above')
}

export const env = parsed.data
```

#### Using env throughout the codebase

```typescript
// ✅ Always import from lib/env — never access process.env directly
import { env } from '@/lib/env'

const client = postgres(env.DATABASE_URL)

export const auth = betterAuth({
  secret: env.BETTER_AUTH_SECRET,
  baseURL: env.BETTER_AUTH_URL,
})
```

**Why not `process.env` directly:**
- `process.env.X` returns `string | undefined` — requires `!` assertions everywhere
- `env.X` returns the validated, typed value — no assertions needed
- Missing variables are caught at startup, not at the point of use
- Typos in variable names are caught by TypeScript

#### `.env` file structure

```bash
# .env.local — local development (never committed)
DATABASE_URL=postgresql://localhost:5432/myapp_dev
BETTER_AUTH_SECRET=your-secret-at-least-32-characters-long
BETTER_AUTH_URL=http://localhost:3000

# .env.test — test environment (committed, no secrets)
DATABASE_URL=postgresql://localhost:5432/myapp_test
BETTER_AUTH_SECRET=test-secret-at-least-32-characters-long
BETTER_AUTH_URL=http://localhost:3000
NODE_ENV=test

# .env.example — documents all required variables (committed)
DATABASE_URL=
BETTER_AUTH_SECRET=
BETTER_AUTH_URL=
NEXT_PUBLIC_APP_NAME=
WEBHOOK_SECRET=
```

`.env.example` is committed and kept up to date. New developers copy it to `.env.local` and fill in values. CI/CD injects the production values from the secrets manager.

---

### Error boundaries

Next.js catches unhandled errors at route segment boundaries. Every route group should have an `error.tsx` file that renders a user-facing error page.

```tsx
// app/(dashboard)/error.tsx
'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { logger } from '@/lib/logger'

export default function DashboardError({
  error,
  reset,
}: {
  error:  Error & { digest?: string }
  reset:  () => void
}) {
  useEffect(() => {
    // Log to the server-side logger
    logger.error('unhandled.client.error', {
      message: error.message,
      digest:  error.digest,
    })
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
      <h2 className="text-lg font-medium">Something went wrong</h2>
      <p className="text-sm text-muted-foreground">
        An unexpected error occurred. Our team has been notified.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

The `digest` field is a unique error ID generated by Next.js. It appears in the server logs, making it possible to find the exact error from a user report without exposing stack traces to the browser.

---

### Health check endpoint

A simple endpoint that confirms the application is running and the database connection is healthy. Used by load balancers, uptime monitors, and deployment pipelines.

```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server'
import { db } from '@/db'
import { sql } from 'drizzle-orm'

export async function GET() {
  try {
    // Confirm the database connection is alive
    await db.execute(sql`SELECT 1`)

    return NextResponse.json({
      status:    'ok',
      timestamp: new Date().toISOString(),
    })
  } catch (err) {
    return NextResponse.json(
      {
        status:  'error',
        message: 'Database connection failed',
      },
      { status: 503 }
    )
  }
}
```

The health endpoint:
- Returns 200 when healthy
- Returns 503 when the database is unreachable
- Never requires authentication — load balancers call it without a session
- Never returns sensitive information — status and timestamp only

---

### Production operations checklist — before going live

**Logging:**
- [ ] `lib/logger.ts` is implemented with `pino`
- [ ] All service write operations call `logger.info` with event name and context
- [ ] No passwords, tokens, or PII in any log call

**Audit trail:**
- [ ] `audit_log` table migration is applied
- [ ] `lib/audit.ts` is implemented
- [ ] All service write operations call `audit.record({ action, resourceId, ctx })`
- [ ] At least one audit history query is implemented and accessible to org admins

**Migrations:**
- [ ] `drizzle.config.ts` is configured
- [ ] All migrations committed alongside schema changes
- [ ] Migration run is part of the CI/CD deployment pipeline
- [ ] `.env.example` documents all required variables

**Environment:**
- [ ] `lib/env.ts` validates all required variables
- [ ] All `process.env` references replaced with `env.*` imports
- [ ] Production secrets are in the secrets manager — not in `.env` files in the repository

**Error handling:**
- [ ] `error.tsx` exists for every route group
- [ ] `global-error.tsx` exists at the root
- [ ] Health check endpoint is live and monitored

---

### How to use this document

- **Developers:** Add `logger.info` and `audit.record` calls to every service write method before marking a feature complete. Never reference `process.env` directly — always use `lib/env`. Never write or edit migration files manually — always use `drizzle-kit generate`.
- **Agents:** When generating a service module, include `logger.info` and `audit.record` calls in every write method. Use `ctx` for the audit call. Do not generate audit records for read operations. When generating a new environment variable usage, add it to `lib/env.ts` first and import from there.
- **Tech leads:** Before any production deployment, run through the checklist above. A service that writes data without audit records is incomplete. An application that reads `process.env` directly in service or library code is bypassing the validation layer.

---

*Previous: Section 9 — Testing Strategy*
*Next: Section 11 — Evolution Rules*
