// lib/auth/index.ts
//
// Permission enforcement. Imported by every service method that writes data.
//
// Canon rule (Section 8): requirePermission() is ALWAYS the first line of
// every write method — before validation, before DB access, before anything.
//
// Pattern:
//   async create({ data, ctx }: { data: CreateInput; ctx: CallerContext }) {
//     requirePermission(ctx, PERMISSIONS.contracts.create)  // ← first line
//     const parsed = createSchema.safeParse(data)           // ← then validate
//     ...
//   }

import type { CallerContext } from './caller-context'

// ── ForbiddenError ──────────────────────────────────────────────────────────
//
// Thrown by requirePermission when the caller lacks a permission.
// Server Actions catch this and return { error: 'Forbidden' } to the client.
// Services do NOT catch it — they let it propagate.
//
// This is intentional: permission failures are exceptional (should not happen
// in a correctly built UI), so throwing is appropriate. Business validation
// failures (missing field, invalid date) are expected and return { error }.

export class ForbiddenError extends Error {
  public readonly permission: string

  constructor(permission: string) {
    super(`Forbidden: missing permission '${permission}'`)
    this.name  = 'ForbiddenError'
    this.permission = permission
    // Maintains proper prototype chain in transpiled environments
    Object.setPrototypeOf(this, ForbiddenError.prototype)
  }
}

// ── requirePermission ───────────────────────────────────────────────────────
//
// Checks that ctx.permissions includes the specified permission string.
// Throws ForbiddenError if not. Returns void if yes (no try/catch needed).
//
// Permission strings follow the format '[module]:[action]', e.g.:
//   'contracts:create'
//   'contracts:viewCommissionRate'
//   'reports:export'
//
// These strings are declared in lib/auth/permissions.ts and referenced by
// PERMISSIONS.[module].[action] — never written as string literals in service code.

export function requirePermission(ctx: CallerContext, permission: string): void {
  if (!ctx.permissions.includes(permission)) {
    throw new ForbiddenError(permission)
  }
}

// ── Server Action boundary pattern ──────────────────────────────────────────
//
// Server Actions that call services should wrap in try/catch for ForbiddenError:
//
//   export async function createContractAction(data: CreateContractInput) {
//     try {
//       const ctx = await getCallerContext()
//       return contractService.create({ data, ctx })
//     } catch (err) {
//       if (err instanceof ForbiddenError) {
//         return { error: 'Forbidden' }
//       }
//       throw err  // re-throw unexpected errors — Next.js error boundary handles them
//     }
//   }
//
// The scaffold-module.ts helper generates this pattern for every action stub.
