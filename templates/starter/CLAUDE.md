# [Project Name] — Claude Code Context

*This file is auto-loaded at the start of every Claude Code session. Keep it accurate and current.*
*Agents read this before any other file. Every section here has a purpose.*

---

## Stack

Next.js 15 (App Router) · TypeScript (strict) · Drizzle ORM · PostgreSQL · BetterAuth · shadcn/ui · Vitest · Playwright · Zod · pino

All defaults from the architecture canon. Do not deviate without documenting the reason in the relevant module CLAUDE.md.

---

## Org context

**Pattern:** `[org-only | org-with-units | customer-account]`

*(Fill this in at project initialization. It determines column structure in every table and query patterns in every service. See docs/architecture/section-03-org-context.md for the pattern details.)*

- `org-only`: every record has `org_id`. Services scope queries by `ctx.orgId`.
- `org-with-units`: every record has `org_id` AND `org_unit_id`. Services scope by both.
- `customer-account`: records have `account_id` with optional `org_id`. Confirm pattern with SPEC.

---

## Canon rules — 7 invariants

Every agent and every developer follows these. They are not preferences.

1. **Boundaries over cleverness** — UI renders, schemas validate, services own business logic, DB persists. Nothing crosses its boundary.
2. **Schema-first** — A Zod schema is written before any function, form, or DB call.
3. **The service layer is sacred** — Business rules live in services. Never in components, route handlers, or DB queries.
4. **Explicit over implicit** — No magic. Auth checks, org scoping, validation, logging — all visible function calls.
5. **Org-aware by default** — Every account belongs to an org context. Queries that don't scope to org are wrong.
6. **Best practices, not opinions** — Follow established patterns. Consistency is a professional standard.
7. **Don't reinvent the wheel** — Use the standard library. Build domain logic, not infrastructure.

---

## Build commands

```bash
npm run dev           # start dev server
npm run build         # production build
npm test              # unit + integration tests (Vitest)
npm run test:e2e      # E2E tests (Playwright)
npm run db:generate   # generate Drizzle migration from schema changes
npm run db:migrate    # apply pending migrations
npm run db:migrate:down  # roll back last migration
npm run lint          # ESLint
npx tsc --noEmit      # TypeScript type check (no output = pass)
```

---

## Key file locations

| What | Where |
|---|---|
| Architecture canon | `docs/architecture/section-N-*.md` |
| SPEC (locked) | `docs/specs/SPEC.md` |
| Wireframes and UI specs | `docs/wireframes/` |
| Project state | `docs/project-state.md` |
| Drizzle schema | `db/schema/[module].ts` |
| Migrations | `db/migrations/` |
| Zod schemas | `modules/[slug]/[slug].schema.ts` |
| Service layer | `modules/[slug]/[slug].service.ts` |
| Server Actions | `modules/[slug]/[slug].actions.ts` |
| Unit tests | `modules/[slug]/[slug].service.test.ts` |
| E2E tests | `tests/e2e/` |
| Components | `modules/[slug]/components/` |
| Pages | `app/(dashboard)/[slug]/` |
| Auth context | `lib/auth/caller-context.ts` |
| Permissions | `lib/auth/permissions.ts` |
| Audit log | `lib/audit.ts` |
| Logger | `lib/logger.ts` |
| Shared types | `lib/types.ts` |
| Test helpers | `tests/helpers/` |

---

## Module registry

*(Updated by the orchestrator during sprint planning when a new module is introduced. Ship agent updates Exports after Phase 8.)*

| Module | Slug | Status | CLAUDE.md |
|---|---|---|---|
| *(empty — populated as modules are built)* | | | |

---

## Cross-cutting patterns

**CallerContext** — every service method receives `ctx: CallerContext`. Never accept raw `orgId: string`.

**ServiceResult** — write methods return `{ data: T } | { error: string }`. `getById` returns `T | null`. Permission failures throw `ForbiddenError` — the Server Action boundary catches and converts.

**Org scope** — `ownedByOrg(ctx)` helper on every table. The org condition is always first in `where()`. This is what the org isolation tests enforce.

**Audit** — `audit.record()` on every successful write. Required, not optional.

**Logger** — `logger.info()` on every successful write. Never `console.log`.

---

*For agent use: read this file first. Read module CLAUDE.md files on demand. Read canon sections on demand. Do not bulk-read.*
