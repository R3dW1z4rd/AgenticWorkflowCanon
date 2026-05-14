# Architecture Canon
## Section 8 — API Layer
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

The API layer is the boundary between the outside world and the server. It covers two mechanisms — Server Actions and Route Handlers — their canonical structures, when to use each, how auth works in each, the response shape contract, and error propagation rules. This section formalizes patterns introduced in Section 4 (Data Flow) and adds the complete Route Handler specification, which has not been fully covered until now.

---

### The decision — Server Action or Route Handler

This is the first question to answer before writing any API boundary code.

```
Who is calling this endpoint?

  A Next.js component or page in this application
    → Server Action

  An external service, a webhook, a mobile app,
  a third-party integration, or an AI agent via HTTP
    → Route Handler

Does the response need specific HTTP semantics?
(status codes, binary data, custom headers, redirects)
    → Route Handler

Everything else
    → Server Action
```

In practice: ~70% of operations in this stack are Server Actions. Route Handlers are for external consumers and HTTP-specific requirements — not for internal application logic.

| Use a Server Action | Use a Route Handler |
|---|---|
| Form submissions and mutations from the UI | External API consumers (mobile apps, third-party services) |
| Any operation called from a Next.js component | Webhook receivers |
| Any mutation that changes data | File downloads |
| Reading data in a Server Component (direct service call — no action needed) | Responses requiring specific status codes or headers |
| Operations where the caller is always this application | Agent HTTP access via bearer token |

---

### Server Actions — the complete specification

#### The canonical structure

Every Server Action follows this exact structure, in this exact order. No step is skipped. No step is reordered.

```typescript
// modules/branches/branches.actions.ts
'use server'

import { createBranchSchema } from './branches.schema'
import { branchService } from './branches.service'
import { requireOrgAccess, requirePermission } from '@/lib/auth/policy'
import { PERMISSIONS } from '@/lib/auth/permissions'

export async function createBranchAction(input: unknown) {
  // ── Step 1: Validate input ──────────────────────────────────────
  // input is typed as unknown — it comes from the browser and is untrusted.
  // safeParse never throws — it returns success or failure.
  const parsed = createBranchSchema.safeParse(input)
  if (!parsed.success) {
    return {
      error: 'Invalid input',
      issues: parsed.error.issues,
    }
  }

  // ── Step 2: Auth + org context ──────────────────────────────────
  // Returns a CallerContext — verified userId and orgId from the session.
  // Use requirePermission when the operation is restricted to a role.
  // Use requireOrgAccess when any org member can perform the operation.
  const ctx = await requirePermission(PERMISSIONS.branches.create)

  // ── Step 3: Call the service ────────────────────────────────────
  // Pass validated data and verified context. Nothing else.
  // Return the service result directly — actions do not transform it.
  return branchService.create({ data: parsed.data, ctx })
}
```

**The invariant:** Every Server Action is exactly three steps. Validate → auth → service. An action with business logic in it is a violation of this structure.

#### Input is always typed as `unknown`

Server Actions receive data from the browser. The TypeScript type at the call site does not make it safe — the browser can send anything. Always type the parameter as `unknown` and run it through Zod.

```typescript
// ✅ Correct — unknown forces explicit validation
export async function createBranchAction(input: unknown) {
  const parsed = createBranchSchema.safeParse(input)
  // ...
}

// ❌ Wrong — trusting the TypeScript type does not validate at runtime
export async function createBranchAction(input: CreateBranchInput) {
  // input could be anything — no runtime check
}
```

#### Multi-parameter actions

Some actions receive an ID from the URL and a body from the form — two separate pieces of input that are validated separately:

```typescript
export async function updateBranchAction(
  branchId: unknown,
  body:      unknown
) {
  // Validate both separately
  const parsedId   = branchIdSchema.safeParse({ branchId })
  const parsedBody = updateBranchSchema.safeParse(body)

  if (!parsedId.success || !parsedBody.success) {
    return { error: 'Invalid input' }
  }

  const ctx = await requirePermission(PERMISSIONS.branches.update)

  return branchService.update({
    branchId: parsedId.data.branchId,
    data:     parsedBody.data,
    ctx,
  })
}
```

#### What actions never do

- **Contain business logic.** Not a single `if` that isn't about input shape or auth.
- **Call Drizzle directly.** All database access goes through the service.
- **Transform the service result.** Return it as-is. Transformation belongs in the component.
- **Catch service errors.** Business failures return `{ error }` — let them propagate. System errors throw — let Next.js handle them at the error boundary.
- **Call other actions.** Actions are entry points, not utilities.

---

### Route Handlers — the complete specification

Route Handlers live in `app/api/[path]/route.ts`. They handle HTTP requests directly and return `Response` objects with explicit status codes.

#### When to create a Route Handler

Create a Route Handler only when:
1. The caller is external to this application (a third party, a mobile app, an agent via HTTP)
2. The response requires specific HTTP semantics (binary data, status codes, headers)
3. A webhook receiver is needed

Do not create a Route Handler for internal application operations. Server Actions are always preferred for those.

#### The canonical Route Handler structure

```typescript
// app/api/branches/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { listBranchesSchema } from '@/modules/branches/branches.schema'
import { branchService } from '@/modules/branches/branches.service'
import type { CallerContext } from '@/lib/auth/caller-context'

// ── GET — list branches (external API consumer) ────────────────────
export async function GET(request: NextRequest) {
  // ── Step 1: Auth ───────────────────────────────────────────────
  // In Route Handlers, headers come from the request object — not next/headers
  const ctx = await resolveCallerContext(request)
  if (!ctx) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // ── Step 2: Validate query params ─────────────────────────────
  const { searchParams } = request.nextUrl
  const parsed = listBranchesSchema.safeParse({
    region:   searchParams.get('region')   ?? undefined,
    page:     Number(searchParams.get('page')     ?? 1),
    pageSize: Number(searchParams.get('pageSize') ?? 20),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Invalid parameters', issues: parsed.error.issues },
      { status: 400 }
    )
  }

  // ── Step 3: Call the service ───────────────────────────────────
  const result = await branchService.listByOrg({
    orgId:   ctx.orgId,
    filters: parsed.data,
  })

  return NextResponse.json({ data: result.data, pagination: result.pagination })
}
```

#### Auth in Route Handlers — three patterns

Auth in Route Handlers is different from Server Actions because there is no Next.js request context providing headers automatically. The handler receives the `Request` object and must resolve auth from it.

**Pattern 1 — Session cookie (user is logged in via a browser)**

```typescript
async function resolveCallerContext(
  request: NextRequest
): Promise<CallerContext | null> {
  try {
    // Pass request headers to BetterAuth
    const session = await auth.api.getSession({
      headers: request.headers,
    })

    if (!session?.user || !session.activeOrganization) return null

    return {
      userId:     session.user.id,
      orgId:      session.activeOrganization.id,
      callerType: 'user',
      sessionId:  session.session.id,
    }
  } catch {
    return null
  }
}
```

**Pattern 2 — Bearer token (agent or external API consumer)**

```typescript
async function resolveCallerContext(
  request: NextRequest
): Promise<CallerContext | null> {
  const authHeader = request.headers.get('Authorization')
  const token = authHeader?.startsWith('Bearer ')
    ? authHeader.slice(7)
    : null

  if (!token) return null

  try {
    return await authorizeAgent(token) // from lib/auth/agent-context
  } catch {
    return null
  }
}
```

**Pattern 3 — Both (accept either session or bearer token)**

Most API endpoints exposed to external consumers should accept either. Resolve session first, fall back to bearer:

```typescript
async function resolveCallerContext(
  request: NextRequest
): Promise<CallerContext | null> {
  // Try session first
  try {
    const session = await auth.api.getSession({ headers: request.headers })
    if (session?.user && session.activeOrganization) {
      return {
        userId:     session.user.id,
        orgId:      session.activeOrganization.id,
        callerType: 'user',
        sessionId:  session.session.id,
      }
    }
  } catch { /* no session */ }

  // Fall back to bearer token
  const authHeader = request.headers.get('Authorization')
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : null
  if (!token) return null

  try {
    return await authorizeAgent(token)
  } catch {
    return null
  }
}
```

Place this helper in `lib/auth/resolve-caller.ts` and import it in any Route Handler that needs it.

---

### The webhook pattern

Webhooks from external services (payment processors, communication platforms, third-party APIs) do not use session auth or bearer tokens. They use signature verification — a shared secret is used to confirm the request genuinely came from the expected service.

```typescript
// app/api/webhooks/[provider]/route.ts

import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

export async function POST(
  request: NextRequest,
  { params }: { params: { provider: string } }
) {
  // ── Step 1: Read the raw body ──────────────────────────────────
  // Must read as text before parsing — signature is computed against raw body
  const rawBody  = await request.text()
  const signature = request.headers.get('x-webhook-signature') ?? ''

  // ── Step 2: Verify the signature ──────────────────────────────
  const secret   = process.env.WEBHOOK_SECRET ?? ''
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex')

  const isValid = crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  )

  if (!isValid) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }

  // ── Step 3: Parse and process ──────────────────────────────────
  const event = JSON.parse(rawBody)

  // Route to the appropriate handler based on event type
  switch (event.type) {
    case 'payment.completed':
      await handlePaymentCompleted(event)
      break
    case 'subscription.cancelled':
      await handleSubscriptionCancelled(event)
      break
    default:
      // Acknowledge unknown events without error — external services retry on failure
      break
  }

  // ── Step 4: Acknowledge immediately ───────────────────────────
  // Always return 200 promptly — external services time out and retry otherwise
  return NextResponse.json({ received: true })
}
```

**Webhook rules:**
- Always verify the signature before processing any data
- Use `crypto.timingSafeEqual` — not `===` — to prevent timing attacks
- Always return 200 promptly — put long processing in a background job if needed
- Acknowledge first, process second if the operation is time-consuming
- Each provider gets its own route file — never share webhook receivers

---

### The response shape contract

This contract is identical for both Server Actions and Route Handlers. Every response is one of these shapes — nothing else.

```typescript
// Success — the operation completed
{ data: T }

// Success with pagination — list operations
{ data: T[], pagination: { page, pageSize, total, totalPages } }

// Business failure — an expected outcome the caller can handle
{ error: string, issues?: ZodIssue[] }
```

**For Route Handlers**, wrap in `NextResponse.json()` with an appropriate status code:

```typescript
// 200 — success
NextResponse.json({ data: branch })

// 200 with pagination
NextResponse.json({ data: items, pagination })

// 400 — validation failure
NextResponse.json({ error: 'Invalid input', issues }, { status: 400 })

// 401 — not authenticated
NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

// 403 — authenticated but not permitted
NextResponse.json({ error: 'Forbidden' }, { status: 403 })

// 404 — not found
NextResponse.json({ error: 'Not found' }, { status: 404 })

// 409 — conflict (business rule violation involving existing state)
NextResponse.json({ error: 'A branch with this name already exists' }, { status: 409 })

// 500 — unexpected system error (let Next.js handle these — do not return 500 manually)
```

**Server Actions do not set HTTP status codes.** They return plain objects. The `{ error }` shape is how business failures are communicated — not a 400 status code.

---

### Error propagation rules

The error handling rules differ slightly between the two mechanisms.

| Error type | Server Action | Route Handler |
|---|---|---|
| Validation failure | Return `{ error, issues }` | Return 400 with `{ error, issues }` |
| Not authenticated | `requireOrgAccess()` throws → Next.js redirects | Return 401 |
| Not permitted | `requirePermission()` throws → Next.js error boundary | Return 403 |
| Not found (service returns null) | Return `{ error: 'Not found' }` or call `notFound()` | Return 404 |
| Business rule violation | Return `{ error: string }` | Return 409 |
| Unexpected system error | Let it throw → Next.js error boundary | Let it throw → Next.js returns 500 |

**The key difference:** In Server Actions, auth failures throw and are handled by Next.js globally (redirect to login, render error page). In Route Handlers, auth failures must be caught explicitly and returned as a JSON response with the correct status code — because Route Handlers are called by external consumers who need a proper HTTP response, not a redirect.

---

### Putting it together — a complete Route Handler

```typescript
// app/api/branches/[branchId]/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { branchIdSchema, updateBranchSchema } from '@/modules/branches/branches.schema'
import { branchService } from '@/modules/branches/branches.service'
import { resolveCallerContext } from '@/lib/auth/resolve-caller'
import { PERMISSIONS } from '@/lib/auth/permissions'

// GET /api/branches/:branchId
export async function GET(
  request: NextRequest,
  { params }: { params: { branchId: string } }
) {
  const ctx = await resolveCallerContext(request)
  if (!ctx) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const parsed = branchIdSchema.safeParse(params)
  if (!parsed.success) return NextResponse.json({ error: 'Invalid ID' }, { status: 400 })

  const branch = await branchService.getById({
    branchId: parsed.data.branchId,
    orgId:    ctx.orgId,
  })

  if (!branch) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  return NextResponse.json({ data: branch })
}

// PATCH /api/branches/:branchId
export async function PATCH(
  request: NextRequest,
  { params }: { params: { branchId: string } }
) {
  const ctx = await resolveCallerContext(request)
  if (!ctx) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  // Permission check — for Route Handlers this is manual, not via requirePermission()
  if (ctx.callerType === 'agent') {
    if (!ctx.agentPermissions?.includes(PERMISSIONS.branches.update)) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
  }

  const parsedId   = branchIdSchema.safeParse(params)
  const parsedBody = updateBranchSchema.safeParse(await request.json())

  if (!parsedId.success || !parsedBody.success) {
    return NextResponse.json({ error: 'Invalid input' }, { status: 400 })
  }

  const result = await branchService.update({
    branchId: parsedId.data.branchId,
    data:     parsedBody.data,
    ctx,
  })

  if (result.error) {
    return NextResponse.json({ error: result.error }, { status: 409 })
  }

  return NextResponse.json({ data: result.data })
}
```

---

### File structure for Route Handlers

Route Handlers live exclusively in `app/api/`:

```
app/api/
├── branches/
│   ├── route.ts              # GET /api/branches, POST /api/branches
│   └── [branchId]/
│       └── route.ts          # GET, PATCH, DELETE /api/branches/:branchId
├── reports/
│   └── [reportId]/
│       └── export/
│           └── route.ts      # GET /api/reports/:reportId/export (file download)
└── webhooks/
    └── [provider]/
        └── route.ts          # POST /api/webhooks/:provider
```

Internal application routes (`/dashboard`, `/branches`) live in `app/(dashboard)/`. Only external-facing HTTP endpoints live in `app/api/`.

---

### How to use this document

- **Developers:** Before writing an API boundary, use the decision tree at the top to choose the right mechanism. Server Actions for everything internal. Route Handlers for external consumers and HTTP-specific needs. Follow the canonical structure exactly — three steps for actions, four steps for handlers (auth, validate, call service, return response).
- **Agents:** When generating a Server Action, always follow: validate with `safeParse` → `requirePermission` or `requireOrgAccess` → service call → return. When generating a Route Handler, always: resolve context via `resolveCallerContext` → return 401 if null → validate params/body → call service → return `NextResponse.json`. Never generate a Route Handler for an operation that is only called from within the application.
- **Tech leads:** When reviewing a PR, check that no Route Handler exists for an internally-called operation (use a Server Action instead), that every Route Handler resolves caller context before doing anything else, and that webhook receivers verify signatures before processing data.

---

*Previous: Section 7 — Service Layer*
*Next: Section 9 — Testing Strategy*
