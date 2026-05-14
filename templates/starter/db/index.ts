// db/index.ts
//
// Drizzle ORM database instance. Import `db` in service files.
//
// All queries go through this instance — never use the raw `pool` outside this file.
// All schema types are available via the second argument to drizzle() so that
// Drizzle's relational query API (`db.query.[table].findMany(...)`) works correctly.
//
// Canon reference: Section 4 (Database Layer)

import { drizzle } from 'drizzle-orm/node-postgres'
import { Pool }    from 'pg'

import * as schema from './schema'

// Connection pool — shared across all requests in the Node.js process.
// Pool size is controlled by DATABASE_POOL_MAX (default: 10).
// In serverless environments (Vercel), use @vercel/postgres or Neon instead.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max:              parseInt(process.env.DATABASE_POOL_MAX ?? '10', 10),
  idleTimeoutMillis: 30_000,
})

export const db = drizzle(pool, { schema })

// ── Type re-exports ───────────────────────────────────────────────────────────
// Convenience: import inferred types from db without knowing the schema path.
// Usage: import { type Contract } from '@/db/schema'
export * from './schema'
