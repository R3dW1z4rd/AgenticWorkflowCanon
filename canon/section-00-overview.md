# Architecture Canon
## Section 0 — Overview: How Everything Fits Together
*Version 2.0 | Last updated: April 2026*

---

Every application built on this architecture follows the same vertical data flow. A request enters at the top, passes through each layer in sequence, and data flows back up the same path. No layer skips another. No layer reaches past its neighbor.

---

### The seven layers, in order

```
┌─────────────────────────────────────┐
│  UI layer                           │  Next.js App Router + shadcn/ui
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Zod schema                         │  Validates every input before it moves
└──────────────┬──────────────────────┘  ← UI + API contract. Written before any function.
               │
┌──────────────▼──────────────────────┐
│  API boundary                       │  Server action or route handler
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Auth + org context                 │  BetterAuth + org-scoped policy helpers
└──────────────┬──────────────────────┘  ← Org scope enforced at every request.
               │
┌──────────────▼──────────────────────┐
│  Service layer                      │  All business logic lives here
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Drizzle ORM                        │  Explicit SQL queries via TypeScript
└──────────────┬──────────────────────┘  ← DB schema + types. Separate from Zod.
               │
┌──────────────▼──────────────────────┐
│  PostgreSQL                         │  Persistent data store
└─────────────────────────────────────┘
```

**UI layer** — Next.js App Router pages and components built with shadcn/ui. This layer renders and collects input. It knows nothing about business rules. It calls Server Actions or submits to Route Handlers.

**Zod schema** — Before any input moves anywhere, it passes through a Zod schema. The schema is the written contract for what the data must look like. It is defined first, before the function that uses it. It is shared between the UI (for client-side hints) and the API boundary (for server-side enforcement). Zod owns the *shape of communication* between layers.

**API boundary** — A Server Action or Route Handler receives the validated input and acts as the entry point to the server side. It does not contain business logic. Its job is to receive, confirm authentication and org context, call the service, and return a response.

**Auth + org context** — BetterAuth provides the session. Three policy helpers — `requireUser()`, `requireOrgAccess()`, and `requirePermission()` — enforce who can do what in which org context. Every request passes through this layer. There are no exceptions.

**Service layer** — This is where the application actually lives. Business rules, conditional logic, side effects, audit events — all of it belongs here. Services receive typed, validated input and an explicit org context. They call Drizzle directly for simple features, and a repository for complex ones. Nothing outside the service layer is allowed to contain business logic.

**Drizzle ORM** — The query layer. Drizzle defines the database schema as TypeScript, which also provides the TypeScript types for database rows. This is *separate and deliberate* from Zod: Drizzle owns the shape of the database. Zod owns the shape of validation contracts. They are both "schemas" but they answer different questions at different layers and are never merged.

**PostgreSQL** — The database. Drizzle talks to it. Nothing else does.

---

### The two schema layers explained

This is the most common source of confusion for new developers, so it is stated plainly here.

Zod and Drizzle both define "shapes," but they are not the same thing and they are never substituted for each other.

| | Drizzle schema | Zod schema |
|---|---|---|
| **Describes** | Database table structure | What a function/form/endpoint accepts |
| **Lives in** | `db/schema/` | `features/[feature]/[feature].schema.ts` |
| **Used by** | Drizzle ORM to query the DB | Server actions, route handlers, services |
| **Types produced** | Row types from the database | Validated input types for functions |
| **Includes** | `createdAt`, `id`, internal fields | Only what the user/caller provides |

**Concrete example:** A `users` table has a `createdAt` column set by the database. A `createUserSchema` does not include `createdAt` — the database sets it. The Zod schema validates what the caller submits. The Drizzle schema defines what the database stores. They overlap in some fields and differ in others. That is by design.

---

### What TypeScript does across all of this

TypeScript is not a layer — it is the connective tissue. Every boundary between layers is a TypeScript type boundary. Zod schemas produce inferred types. Drizzle schemas produce inferred types. Service functions are typed. This means a mistake at the UI layer is caught before it reaches the service, and a database schema change propagates as a type error immediately. TypeScript makes the architecture self-auditing.

---

### What org context does across all of this

Org context is not a feature — it is a system-wide invariant. The Auth layer extracts the current user's org context from the session and passes it explicitly to every service call. Services scope all queries to that org context. A query that returns data without an org filter is treated as a bug, not a feature.

Whether the current user is an internal employee at a branch or a customer of a client org, there is always an org context. The shape of that context may vary; its presence never does.

---

### How to use this document

- **Developers**: Read this before writing any code. This is the map of the whole system. When you are unsure where something belongs, trace the request lifecycle and find the layer that owns your concern.
- **Agents**: This section defines the canonical data flow. Every code generation decision must be consistent with the layer boundaries described here. No layer may be skipped or merged with another without explicit documented justification.
- **Tech leads**: Use this diagram as the reference when reviewing where new code is being placed. If a PR puts business logic in a route handler or a query in a component, this document is the basis for the correction.

---

*Next: Section 1 — Philosophy*
*Then: Section 2 — Stack*
