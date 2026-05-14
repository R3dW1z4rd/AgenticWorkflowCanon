// lib/audit.ts
//
// Audit logging. Called by every service method that writes data.
//
// Canon rule (Section 9): audit.record() is called after every successful write,
// before returning { data: ... }. It is not optional.
//
// CURRENT IMPLEMENTATION (v1.0 — structured log):
//   Writes a structured log entry tagged with audit: true.
//   Log aggregation (Datadog, Logtail, etc.) can filter on this field.
//
// UPGRADE PATH:
//   When AC-008 (or equivalent) is implemented for a module, the service
//   will also insert a row into an `audit_log` table. The log entry here
//   remains as a secondary record. See the US-002 worked example in
//   examples/contract-manager-us001/ for the pattern.
//
// Canon reference: Section 9 (Testing & Observability)

import type { CallerContext } from './auth/caller-context'
import { logger } from './logger'

// ── Types ────────────────────────────────────────────────────────────────────

export type AuditAction =
  | `${string}.created`
  | `${string}.updated`
  | `${string}.deleted`
  | `${string}.status_changed`
  | `${string}.draft_created`
  | (string & {}) // allow arbitrary action strings — the pattern above is a guide

export type AuditEntry = {
  /** What happened — convention: '[module].[verb]' e.g. 'contract.created' */
  action:       AuditAction
  /** The ID of the resource that was affected */
  resourceId:   string
  /** The type of resource — matches the module slug e.g. 'contract' */
  resourceType: string
  /** The caller who performed the action */
  ctx:          CallerContext
  /** Any additional structured fields to include in the audit record */
  metadata?:    Record<string, unknown>
}

// ── Implementation ───────────────────────────────────────────────────────────

export const audit = {
  /**
   * Record an audit event. Call after every successful write in a service method.
   *
   * @example
   * const [record] = await db.insert(contracts).values({...}).returning()
   * await audit.record({
   *   action:       'contract.created',
   *   resourceId:   record.id,
   *   resourceType: 'contract',
   *   ctx,
   * })
   */
  async record(entry: AuditEntry): Promise<void> {
    logger.info(
      {
        audit:        true,        // tag for log filtering
        action:       entry.action,
        resourceId:   entry.resourceId,
        resourceType: entry.resourceType,
        userId:       entry.ctx.userId,
        orgId:        entry.ctx.orgId,
        orgUnitId:    entry.ctx.orgUnitId,
        ipAddress:    entry.ctx.ipAddress,
        ...entry.metadata,
      },
      `audit: ${entry.action}`,
    )

    // TODO (US-002 pattern): also insert into audit_log table when that
    // module is implemented. The DB write goes here, in the same transaction
    // as the service write that triggered this record.
  },
}
