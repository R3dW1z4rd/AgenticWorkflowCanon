// tests/helpers/dates.ts
//
// Date helpers for test data. Keeps test date logic out of test files
// and prevents the "my tests pass on Monday but fail on Tuesday" problem.
//
// All helpers return ISO date strings (YYYY-MM-DD) matching Zod's z.string().date()
// and PostgreSQL's date column type.
//
// USAGE:
//
//   import { tomorrow, yesterday, daysFromNow } from '@/tests/helpers/dates'
//
//   // Valid start date (must be today or future per AC-003)
//   const validDate = tomorrow()
//
//   // Invalid start date (past — should trigger validation error)
//   const invalidDate = yesterday()
//
//   // Specific offset
//   const nextWeek = daysFromNow(7)

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Returns tomorrow's date as YYYY-MM-DD */
export function tomorrow(): string {
  return daysFromNow(1)
}

/** Returns yesterday's date as YYYY-MM-DD */
export function yesterday(): string {
  return daysFromNow(-1)
}

/** Returns today's date as YYYY-MM-DD */
export function today(): string {
  return daysFromNow(0)
}

/** Returns a date N days from today as YYYY-MM-DD. Negative N = past. */
export function daysFromNow(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0] as string
}

/** Returns a date N months from today as YYYY-MM-DD */
export function monthsFromNow(n: number): string {
  const d = new Date()
  d.setMonth(d.getMonth() + n)
  return d.toISOString().split('T')[0] as string
}
