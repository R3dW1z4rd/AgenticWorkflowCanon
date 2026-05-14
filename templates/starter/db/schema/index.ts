// db/schema/index.ts
//
// Schema barrel file. Every Drizzle table definition is exported from here.
// The schema agent adds a new export line during Phase 5 of each module.
//
// Pattern added by schema-agent:
//   export * from './[module]'
//
// Example (after contracts module Phase 5):
//   export * from './contracts'
//
// The db/index.ts imports this file as `import * as schema from './schema'`
// to give Drizzle's relational API knowledge of all tables.
//
// NOTE: Do not import individual table files directly in service code.
// Import from '@/db/schema' (via the path alias in tsconfig.json) to ensure
// you always get the full schema context.

// ── Module schema exports ─────────────────────────────────────────────────────
// (schema-agent adds entries below during Phase 5 of each story)
