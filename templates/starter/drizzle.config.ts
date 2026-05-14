// drizzle.config.ts
//
// Drizzle Kit configuration. Used by:
//   npm run db:generate   — generate SQL migration from schema changes
//   npm run db:migrate    — apply pending migrations
//   npm run db:migrate:down — roll back last migration
//
// The schema agent runs these commands during Phase 5 gate checks.
// If this file is missing or misconfigured, Phase 5 will fail.

import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema:    './db/schema/index.ts',
  out:       './db/migrations',
  dialect:   'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  // Naming convention for migration files: XXXX_description.sql
  migrations: {
    prefix: 'supabase',   // change to 'timestamp' or 'index' per your preference
  },
  verbose: true,
  strict:  true,
})
