// lib/auth/permissions.ts
//
// Central registry of every permission string in the application.
// Permission strings follow the format '[module]:[action]'.
//
// RULES:
//   1. Every permission used by requirePermission() must be declared here.
//   2. Services import from PERMISSIONS — they never write string literals.
//   3. The schema agent adds entries when a new module is scaffolded (Phase 5).
//   4. The ship agent verifies the Exports section in CLAUDE.md lists permissions.
//
// HOW ROLES RELATE TO PERMISSIONS:
//   Roles are stored in the database and assigned to users.
//   Permissions are static strings defined here.
//   The mapping (which role grants which permissions) lives in BetterAuth
//   configuration and is documented per-module in SPEC.md section 6.X.9.
//   This file is the canonical list of what permissions EXIST — not who has them.
//
// Canon reference: Section 8 (Authorization), canon/guidelines/rbac.md

export const PERMISSIONS = {

  // ── Add module permission groups below as modules are scaffolded ──────────
  //
  // Pattern (added by schema-agent during Phase 5):
  //
  // [module-slug]: {
  //   create: '[module-slug]:create',
  //   update: '[module-slug]:update',
  //   delete: '[module-slug]:delete',
  //   // Field-level permissions for Sensitive/PII fields:
  //   viewCommissionRate: '[module-slug]:viewCommissionRate',
  // },
  //
  // Example (contracts module, added when US-001 Phase 5 ran):
  //
  // contracts: {
  //   create: 'contracts:create',
  //   update: 'contracts:update',
  //   delete: 'contracts:delete',
  // },

} as const

// ── Type helpers ─────────────────────────────────────────────────────────────

/** Union of all permission strings in the registry */
export type Permission = typeof PERMISSIONS extends Record<string, infer Module>
  ? Module extends Record<string, infer P>
    ? P
    : never
  : never
