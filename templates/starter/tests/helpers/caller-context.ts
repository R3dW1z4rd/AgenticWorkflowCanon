// tests/helpers/caller-context.ts
//
// Test factory for CallerContext. Used in every service test file.
//
// makeOrgContext() creates a CallerContext with randomised IDs so that
// each test is fully isolated — no test can accidentally share an org with
// another. This is the foundation of the org isolation test pattern.
//
// USAGE:
//
//   // Basic — all permissions granted (suitable for most tests)
//   const { ctx } = makeOrgContext()
//   const result = await contractService.create({ data: validData(), ctx })
//
//   // Org isolation tests — two separate orgs
//   const orgA = makeOrgContext()
//   const orgB = makeOrgContext()
//   // orgA.ctx.orgId !== orgB.ctx.orgId — guaranteed by randomUUID()
//
//   // Permission boundary tests — specific permission denied
//   const { ctx } = makeOrgContext({ permissions: [] })
//   const result = await contractService.create({ data: validData(), ctx })
//   expect(result).toHaveProperty('error') // or catch ForbiddenError
//
//   // Specific user identity
//   const userId = randomUUID()
//   const { ctx } = makeOrgContext({ userId })
//
// Canon reference: Section 9 (Testing Strategy)

import { randomUUID } from 'crypto'
import type { CallerContext } from '@/lib/auth/caller-context'

// ── Factory ──────────────────────────────────────────────────────────────────

/**
 * Creates a fresh CallerContext with randomised IDs.
 * By default grants all permissions ('*') so tests focus on business logic,
 * not permission setup. Override `permissions` for permission boundary tests.
 */
export function makeOrgContext(
  overrides: Partial<CallerContext> = {}
): { ctx: CallerContext } {
  return {
    ctx: {
      userId:      randomUUID(),
      orgId:       randomUUID(),
      orgUnitId:   randomUUID(),
      permissions: ['*'],         // all permissions by default — override for SB-2 tests
      ipAddress:   '127.0.0.1',
      ...overrides,
    },
  }
}

// ── Permission boundary helper ────────────────────────────────────────────────

/**
 * Creates a CallerContext with NO permissions.
 * Use for SB-2 (missing permission) tests.
 *
 * @example
 * const { ctx } = makeRestrictedContext()
 * await expect(() =>
 *   contractService.create({ data: validData(), ctx })
 * ).rejects.toThrow('Forbidden')
 */
export function makeRestrictedContext(
  overrides: Partial<CallerContext> = {}
): { ctx: CallerContext } {
  return makeOrgContext({ permissions: [], ...overrides })
}

// ── Shared org helper ─────────────────────────────────────────────────────────

/**
 * Creates two CallerContexts that share the same orgId but have different userIds.
 * Use when testing that two users in the same org can see each other's records
 * (as opposed to the org isolation tests, which use different orgIds).
 *
 * @example
 * const { ctxA, ctxB } = makeSameOrgContexts()
 * const { data: record } = await service.create({ data: validData(), ctx: ctxA })
 * const found = await service.getById({ id: record.id, ctx: ctxB })
 * expect(found).not.toBeNull() // same org — should be visible
 */
export function makeSameOrgContexts(): { ctxA: CallerContext; ctxB: CallerContext } {
  const orgId    = randomUUID()
  const orgUnitId = randomUUID()

  return {
    ctxA: {
      userId:      randomUUID(),
      orgId,
      orgUnitId,
      permissions: ['*'],
    },
    ctxB: {
      userId:      randomUUID(),
      orgId,
      orgUnitId,
      permissions: ['*'],
    },
  }
}
