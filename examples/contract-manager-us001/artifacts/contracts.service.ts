// modules/contracts/contracts.service.ts
//
// Phase 5: service interface with throwing stubs (shown first)
// Phase 7: full implementation (shown second — replaces Phase 5 content)
//
// This file shows BOTH versions so you can see the diff
// the code agent produces in Phase 7.

// ═══════════════════════════════════════════════════════════════
// PHASE 5 VERSION — throwing stubs, no implementation
// ═══════════════════════════════════════════════════════════════

/*

import type { CallerContext } from '@/lib/auth/caller-context'
import type { Contract } from '@/db/schema'
import type {
  CreateContractInput,
  CreateDraftContractInput,
  UpdateContractInput,
  ListContractsInput,
} from './contracts.schema'

type ServiceResult<T> = { data: T } | { error: string }

export const contractService = {
  async listByOrg(
    _args: { ctx: CallerContext; filters?: ListContractsInput }
  ): Promise<ServiceResult<Contract[]>> {
    throw new Error('contractService.listByOrg not implemented')
  },

  async getById(
    _args: { contractId: string; ctx: CallerContext }
  ): Promise<Contract | null> {
    throw new Error('contractService.getById not implemented')
  },

  async create(
    _args: { data: CreateContractInput; ctx: CallerContext }
  ): Promise<ServiceResult<Contract>> {
    throw new Error('contractService.create not implemented')
  },

  async createDraft(
    _args: { data: CreateDraftContractInput; ctx: CallerContext }
  ): Promise<ServiceResult<Contract>> {
    throw new Error('contractService.createDraft not implemented')
  },

  async update(
    _args: { contractId: string; data: UpdateContractInput; ctx: CallerContext }
  ): Promise<ServiceResult<Contract>> {
    throw new Error('contractService.update not implemented')
  },

  async delete(
    _args: { contractId: string; ctx: CallerContext }
  ): Promise<ServiceResult<Contract>> {
    throw new Error('contractService.delete not implemented')
  },
}

*/

// ═══════════════════════════════════════════════════════════════
// PHASE 7 VERSION — full implementation
// ═══════════════════════════════════════════════════════════════

import { and, eq } from 'drizzle-orm'

import { db } from '@/db'
import { contracts, type Contract } from '@/db/schema'
import { audit } from '@/lib/audit'
import { requirePermission } from '@/lib/auth'
import type { CallerContext } from '@/lib/auth/caller-context'
import { PERMISSIONS } from '@/lib/auth/permissions'
import { logger } from '@/lib/logger'

import {
  createContractSchema,
  createDraftContractSchema,
  updateContractSchema,
  type CreateContractInput,
  type CreateDraftContractInput,
  type ListContractsInput,
  type UpdateContractInput,
} from './contracts.schema'

// ── Result type ───────────────────────────────────────────────────────
// Services return data or error — never throw in business-logic paths.
// Exception: permission errors throw (ForbiddenError) — the action boundary
// catches them and returns { error: 'Forbidden' }.

type ServiceResult<T> = { data: T } | { error: string }

// ── Org scope helper ──────────────────────────────────────────────────
// Every query on the contracts table MUST include this condition.
// Forgetting it is what the org isolation tests catch.

function ownedByOrg(ctx: CallerContext) {
  return eq(contracts.orgId, ctx.orgId)
}

// ── Service ──────────────────────────────────────────────────────────

export const contractService = {

  async listByOrg({
    ctx,
    filters,
  }: {
    ctx:      CallerContext
    filters?: ListContractsInput
  }): Promise<ServiceResult<Contract[]>> {
    const rows = await db
      .select()
      .from(contracts)
      .where(
        and(
          ownedByOrg(ctx),
          filters?.status ? eq(contracts.status, filters.status) : undefined,
        )
      )

    return { data: rows }
  },

  async getById({
    contractId,
    ctx,
  }: {
    contractId: string
    ctx:        CallerContext
  }): Promise<Contract | null> {
    const [row] = await db
      .select()
      .from(contracts)
      .where(
        and(
          ownedByOrg(ctx),           // org scope first — not found if wrong org
          eq(contracts.id, contractId),
        )
      )
      .limit(1)

    return row ?? null
    // Returns null (not { error }) for not-found — canon rule:
    // not-found is null, business failures are { error }.
  },

  async create({
    data,
    ctx,
  }: {
    data: CreateContractInput
    ctx:  CallerContext
  }): Promise<ServiceResult<Contract>> {
    // 1. Authorize — throws ForbiddenError if permission is missing.
    //    The Server Action catches this and returns { error: 'Forbidden' }.
    requirePermission(ctx, PERMISSIONS.contracts.create)

    // 2. Validate — return { error } for invalid input.
    const parsed = createContractSchema.safeParse(data)
    if (!parsed.success) {
      return { error: parsed.error.errors[0].message }
    }

    // 3. Write — orgId and orgUnitId always come from CallerContext.
    //    User-provided orgId would be ignored even if someone tried to pass one.
    const [contract] = await db
      .insert(contracts)
      .values({
        ...parsed.data,
        orgId:     ctx.orgId,     // from context, not from data
        orgUnitId: ctx.orgUnitId, // from context, not from data
        status:    'draft',       // hardcoded — not from data
      })
      .returning()

    // 4. Audit — every successful write records to the audit log.
    await audit.record({
      action:       'contract.created',
      resourceId:   contract.id,
      resourceType: 'contract',
      ctx,
    })

    // 5. Log — structured log, not console.log.
    logger.info(
      { contractId: contract.id, orgId: ctx.orgId, orgUnitId: ctx.orgUnitId },
      'contract created'
    )

    return { data: contract }
  },

  async createDraft({
    data,
    ctx,
  }: {
    data: CreateDraftContractInput
    ctx:  CallerContext
  }): Promise<ServiceResult<Contract>> {
    // Same permission required for draft and full create (AC-010).
    requirePermission(ctx, PERMISSIONS.contracts.create)

    // createDraftContractSchema is fully optional — any fields provided are
    // validated for type correctness, but none are required.
    const parsed = createDraftContractSchema.safeParse(data)
    if (!parsed.success) {
      return { error: parsed.error.errors[0].message }
    }

    const [contract] = await db
      .insert(contracts)
      .values({
        ...parsed.data,
        orgId:     ctx.orgId,
        orgUnitId: ctx.orgUnitId,
        status:    'draft',
      })
      .returning()

    await audit.record({
      action:       'contract.draft_created',
      resourceId:   contract.id,
      resourceType: 'contract',
      ctx,
    })

    logger.info(
      { contractId: contract.id, orgId: ctx.orgId },
      'contract draft created'
    )

    return { data: contract }
  },

  async update({
    contractId,
    data,
    ctx,
  }: {
    contractId: string
    data:       UpdateContractInput
    ctx:        CallerContext
  }): Promise<ServiceResult<Contract>> {
    requirePermission(ctx, PERMISSIONS.contracts.update)

    const parsed = updateContractSchema.safeParse(data)
    if (!parsed.success) {
      return { error: parsed.error.errors[0].message }
    }

    const [contract] = await db
      .update(contracts)
      .set({ ...parsed.data, updatedAt: new Date() })
      .where(
        and(
          ownedByOrg(ctx),
          eq(contracts.id, contractId),
        )
      )
      .returning()

    if (!contract) return { error: 'Contract not found' }

    await audit.record({
      action: 'contract.updated', resourceId: contractId, resourceType: 'contract', ctx,
    })
    logger.info({ contractId, orgId: ctx.orgId }, 'contract updated')

    return { data: contract }
  },

  async delete({
    contractId,
    ctx,
  }: {
    contractId: string
    ctx:        CallerContext
  }): Promise<ServiceResult<Contract>> {
    requirePermission(ctx, PERMISSIONS.contracts.delete)

    const [contract] = await db
      .delete(contracts)
      .where(
        and(
          ownedByOrg(ctx),
          eq(contracts.id, contractId),
        )
      )
      .returning()

    if (!contract) return { error: 'Contract not found' }

    await audit.record({
      action: 'contract.deleted', resourceId: contractId, resourceType: 'contract', ctx,
    })
    logger.info({ contractId, orgId: ctx.orgId }, 'contract deleted')

    return { data: contract }
  },
}
