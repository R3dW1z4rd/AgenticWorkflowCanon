// lib/auth/caller-context.ts
//
// CallerContext is the single object that carries authentication and authorization
// information through every service call. Services never accept raw strings like
// `orgId: string` or `userId: string` — they always receive a CallerContext.
//
// This enforces two things:
//   1. Org isolation — orgId always comes from the verified session, never from user input
//   2. Permission enforcement — permissions are verified by the session, not passed by callers
//
// Canon reference: Section 7 (Service Layer), Section 8 (Authorization)

import { headers } from 'next/headers'
import { auth } from './auth'   // your BetterAuth instance — see lib/auth/auth.ts

// ── Type ────────────────────────────────────────────────────────────────────

export type CallerContext = {
  /** Authenticated user's ID */
  userId: string

  /** The organisation this user belongs to */
  orgId: string

  /**
   * The sub-unit (branch, region, store) this user belongs to.
   * Empty string for projects using org-only context.
   * Non-empty for org-with-units and customer-account contexts.
   */
  orgUnitId: string

  /**
   * The permission strings this user holds, e.g. ['contracts:create', 'contracts:view'].
   * Set by BetterAuth based on the user's roles. Services check individual strings
   * via requirePermission() rather than inspecting this array directly.
   */
  permissions: string[]

  /** IP address for audit records. Optional. */
  ipAddress?: string
}

// ── Server-side constructor ──────────────────────────────────────────────────
//
// Used in Server Actions to build a CallerContext from the current session.
// Called once per Server Action at the top of the function — before any
// service call.
//
// Example usage (in a Server Action):
//   export async function createContractAction(data: CreateContractInput) {
//     const ctx = await getCallerContext()
//     return contractService.create({ data, ctx })
//   }

export async function getCallerContext(): Promise<CallerContext> {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user) {
    // This should not reach here in practice — Next.js middleware redirects
    // unauthenticated requests to /login before Server Actions execute.
    // If you see this error, check your middleware configuration.
    throw new Error('getCallerContext: no active session')
  }

  return {
    userId:      session.user.id,
    orgId:       session.user.orgId        ?? '',
    orgUnitId:   session.user.orgUnitId    ?? '',
    permissions: session.user.permissions  ?? [],
    ipAddress:   (await headers()).get('x-forwarded-for') ?? undefined,
  }
}

// ── BetterAuth session extension ────────────────────────────────────────────
//
// The fields above (orgId, orgUnitId, permissions) are not part of BetterAuth's
// default session schema. You must extend it in your BetterAuth configuration:
//
//   // lib/auth/auth.ts
//   export const auth = betterAuth({
//     ...
//     session: {
//       additionalFields: {
//         orgId:       { type: 'string', required: true  },
//         orgUnitId:   { type: 'string', required: false },
//         permissions: { type: 'string[]', required: false },
//       }
//     }
//   })
//
// These fields are populated when the user logs in based on their org membership
// and role assignments. See docs/architecture/section-08-authorization.md for
// the full pattern.

// ── Test factory ────────────────────────────────────────────────────────────
//
// For unit tests — use makeOrgContext() from tests/helpers/caller-context.ts
// instead of importing this directly. The helper creates isolated org/unit IDs
// for each test, which is what the org isolation tests depend on.
