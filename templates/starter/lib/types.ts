// lib/types.ts
//
// Shared types used across the application.
// Import from here — do not re-declare these in individual modules.

// ── ServiceResult ────────────────────────────────────────────────────────────
//
// The return type of every service write method.
// Service methods return either data or a business-logic error — never throw
// for expected failure cases (validation failures, not-found, business rule
// violations). ForbiddenError is the only exception (literally thrown).
//
// Usage:
//   async create(...): Promise<ServiceResult<Contract>> {
//     ...
//     if (validationFailed) return { error: 'Start date cannot be in the past' }
//     return { data: contract }
//   }
//
// Callers check with 'error' in result:
//   const result = await contractService.create({ data, ctx })
//   if ('error' in result) { /* show error */ }
//   else { /* use result.data */ }
//
// Note: getById returns T | null, NOT ServiceResult — not-found is not
// a business failure, it is an expected absence.

export type ServiceResult<T> = { data: T } | { error: string }

// ── PaginatedResult ───────────────────────────────────────────────────────────
//
// Used by list methods that support pagination.

export type PaginatedResult<T> = {
  data:  T[]
  total: number
  page:  number
  pageSize: number
}
