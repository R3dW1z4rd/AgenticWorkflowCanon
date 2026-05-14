// tests/setup.ts
//
// Runs before each Vitest test file (configured in vitest.config.ts setupFiles).
// Handles database state between test files.
//
// STRATEGY: clean the database before each TEST FILE (not each test).
// Individual tests that need isolation call db.delete() in their own beforeEach.
// This keeps the suite fast while preventing state leakage between files.

import { afterAll, beforeAll } from 'vitest'
import { db } from '@/db'
import { sql } from 'drizzle-orm'

beforeAll(async () => {
  // Verify database connection
  await db.execute(sql`SELECT 1`)
})

afterAll(async () => {
  // Clean up after the full test file completes.
  // Order matters — FK constraints require deleting child tables first.
  // Add your tables here in the correct order as modules are built.
  //
  // Example (after contracts + audit modules are built):
  //   await db.execute(sql`TRUNCATE audit_log, contracts CASCADE`)
  //
  // For now: no-op (no tables exist yet)
})
