# Architecture Canon
## Section 1 — Philosophy
*Version 2.0 | Last updated: April 2026*

---

### What this architecture is

A **production-first, team-scale application framework** for building internal and client-facing business applications. It is designed to be built by beginners, maintained by small teams, extended by AI agents, and operated reliably in production across multiple organizational contexts.

It is not a starter kit. It is not a prototype framework. Every decision is made with the assumption that the application will be in production, maintained, and extended for years.

---

### Core principles

**1. Boundaries over cleverness**
Every layer has one job. UI renders. Schemas validate. Services own business logic. The database layer persists. Nothing crosses its boundary. When in doubt, the answer is always: put it in the service.

**2. Schema-first, always**
A Zod schema is written before any function, form, or database call. The schema is the contract between all layers — UI, server, agent, and database. If something doesn't have a schema, it doesn't have a contract, and it doesn't belong in the codebase yet.

**3. The service layer is sacred**
Business rules live in services. Not in components. Not in route handlers. Not in database queries. A developer who can't find where a rule is enforced should look in the service first, last, and always.

**4. Explicit over implicit**
No magic. No decorators that silently check permissions. No middleware that transforms data invisibly. Every meaningful operation — auth checks, org scoping, validation, logging — is a visible function call in a readable code path.

**5. Org-aware by default**
Every account in the system — whether an internal employee or an external customer — belongs to an organizational context: a branch, a region, a store, a client org. Queries that don't scope to an org unit are suspicious. Services always receive and enforce org context. This is not optional per feature — it is a system-wide invariant. The account type may differ; the presence of org scope never does.

**6. Best practices, not opinions**
We follow established, proven patterns — not because they are fashionable, but because they are well-understood, well-documented, and immediately recognizable by any professional developer joining the team. A developer reading any file in this codebase should recognize the pattern and know where to look next. Consistency and clarity are professional standards, not stylistic preferences.

**7. Don't reinvent the wheel**
When a well-maintained, production-proven library solves a problem, we use it. We do not build custom solutions for solved problems. Authentication, validation, testing, UI components — these have standard answers in this stack. We document those answers and treat them as defaults. A business requirement must make a strong, explicit case to justify replacing a default. The team's energy goes into solving domain problems, not infrastructure problems.

---

### What we optimize for

| Priority | What it means in practice |
|---|---|
| **Teachability** | A beginner follows the pattern and produces correct architecture without fully understanding every layer yet |
| **Agent-friendliness** | Predictable file names, clear boundaries, and Zod schemas give agents reliable structure to read and generate |
| **Production durability** | The same patterns that work on day 1 work on day 500 without rewriting the foundation |
| **Evolution safety** | Adding a new feature or use case never requires touching unrelated code |
| **Speed** | Lean stack, no unnecessary abstractions, fast to scaffold a new feature correctly |

---

### Standard library defaults

These are the default answers for their problem domain across all projects. They are not re-evaluated per project unless a documented business requirement justifies the change.

| Problem | Default | Notes |
|---|---|---|
| Authentication & Authorization | **BetterAuth** | Standard for all Next.js projects. Replaces Auth.js. |
| Validation & contracts | **Zod** | Used at every layer — schema, service, API boundary |
| Database ORM | **Drizzle** | SQL-first; team is familiar with SQL |
| Database | **PostgreSQL** | Not swapped without a strong infrastructure reason |
| UI components | **shadcn/ui** | Composable, not a dependency. Solve everything here first. |
| Testing (unit/integration) | **Vitest** | Faster than Jest, native ESM |
| Testing (E2E) | **Playwright** | More reliable than Cypress, better DX |
| Framework | **Next.js (App Router)** | Platform anchor. Not replaced. |
| Language | **TypeScript** | Non-negotiable. |

#### Default replacement rule

To replace any standard default, the team must document:
1. What specific business or technical requirement the default cannot meet
2. What the proposed replacement is
3. What the maintenance and onboarding cost of the replacement is

Preference, familiarity with an alternative, or "it's better in some ways" are not sufficient justifications.

---

### What we deliberately avoid and why

| Avoided | Why |
|---|---|
| **tRPC** | Server Actions + Route Handlers provide type-safe boundaries with less learning overhead and no additional framework layer |
| **Mandatory repository layer everywhere** | Premature abstraction for most features. Services call Drizzle directly until complexity genuinely justifies separation |
| **Heavy RBAC frameworks** | A few explicit helper functions are more readable, testable, and debuggable than a policy engine at our scale |
| **Message queues on day one** | BullMQ and Temporal solve real problems — introduced only when the need is proven, not preemptively |
| **Custom auth systems** | BetterAuth is the standard. Building auth from scratch is a security and maintenance liability requiring explicit justification |
| **Implicit middleware transformations** | All data transformations and authorization checks are explicit function calls in readable code paths |
| **Feature flag infrastructure early** | Start with environment variables. Introduce a flag system only when deployment independence between features becomes a real operational need |
| **ORM magic / active record patterns** | Drizzle is explicit SQL in TypeScript. Queries are always visible, readable, and debuggable |

---

### What this architecture is not trying to solve

- Microservices or distributed systems
- High-frequency event streaming
- Per-client database isolation (separate DB per tenant)
- Real-time collaborative editing

These are valid engineering problems. This architecture is not designed for them. If a project grows into these needs, the evolution is deliberate and documented — the core patterns remain stable.

---

### How to use this document

- **Developers**: Read this before writing any code. When you are unsure where something belongs, the principles in this section are the first place to look.
- **Agents**: This section defines the invariants you can always assume are true. Every code generation, review, or scaffolding decision must be consistent with the principles and defaults listed here.
- **Tech leads**: When a team member proposes a deviation from the defaults, use the replacement rule above to evaluate the proposal objectively.

---

*Next: Section 2 — Stack*
