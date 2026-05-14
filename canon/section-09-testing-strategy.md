# Architecture Canon
## Section 9 — Testing Strategy
*Version 2.0 | Last updated: April 2026*

---

### What this section covers

What gets tested, at which layer, with which tool, and how. This section covers the testing pyramid for this architecture, the canonical patterns for schema tests, service tests, and E2E tests, the test helpers that make this architecture easy to test, and the division of responsibility between agents and developers.

---

### The testing pyramid

```
              ┌─────────────────────┐
              │   E2E (Playwright)  │  ← Critical user journeys,
              │   tests/e2e/        │    permission boundaries,
              └─────────────────────┘    auth flows
            ┌───────────────────────────┐
            │  Service tests (Vitest)   │  ← Business logic,
            │  [module].service.test.ts │    org isolation,
            └───────────────────────────┘    error cases
          ┌─────────────────────────────────┐
          │    Schema tests (Vitest)         │  ← Validation contracts,
          │    [module].schema.test.ts       │    error messages,
          └─────────────────────────────────┘    boundary values
```

Most tests live in the middle two layers. Schema tests are fast and mechanical. Service tests cover the business logic that actually matters. E2E tests cover the flows a user cares about — not every permutation.

---

### Where tests live

Tests are co-located with the code they test. When a module is deleted, its tests go with it.

```
modules/branches/
├── branches.schema.ts
├── branches.schema.test.ts     ← schema tests
├── branches.service.ts
├── branches.service.test.ts    ← service tests
├── branches.actions.ts         ← actions are thin, tested via service + E2E
└── components/                 ← components tested via E2E

tests/
└── e2e/
    ├── fixtures/
    │   ├── auth.ts             ← shared auth fixtures
    │   └── db.ts              ← shared test data helpers
    ├── branches.spec.ts
    ├── users.spec.ts
    └── auth.spec.ts
```

---

### Vitest setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    environment: 'node',
    globals:     true,

    // Run tests in a single thread to avoid DB connection pool exhaustion
    pool:        'forks',
    poolOptions: { forks: { singleFork: true } },

    // Path aliases matching tsconfig
    alias: {
      '@': path.resolve(__dirname, './'),
    },

    // Global setup/teardown for the test database
    globalSetup: './tests/setup/global.ts',
  },
})
```

```typescript
// tests/setup/global.ts
import { db } from '@/db'

export async function setup() {
  // Run migrations on the test database before the test suite
  await migrate(db, { migrationsFolder: './db/migrations' })
}

export async function teardown() {
  // Clean up after the full suite
  await db.$client.end()
}
```

The test database URL is set in `.env.test`:

```bash
# .env.test
DATABASE_URL=postgresql://localhost:5432/myapp_test
```

Vitest picks this up automatically when `NODE_ENV=test`.

---

### The test CallerContext helper

This is the most important test helper in the architecture. Every service test needs a `CallerContext` — but tests have no session. This helper creates a valid context without going through auth:

```typescript
// tests/helpers/caller-context.ts
import { randomUUID } from 'crypto'
import type { CallerContext } from '@/lib/auth/caller-context'

// Creates a CallerContext for a human caller in tests
export function makeUserContext(
  overrides?: Partial<CallerContext>
): CallerContext {
  return {
    userId:     `user-${randomUUID()}`,
    orgId:      `org-${randomUUID()}`,
    callerType: 'user',
    sessionId:  `session-${randomUUID()}`,
    ...overrides,
  }
}

// Creates a CallerContext for an agent caller in tests
export function makeAgentContext(
  overrides?: Partial<CallerContext>
): CallerContext {
  return {
    userId:           `user-${randomUUID()}`,
    orgId:            `org-${randomUUID()}`,
    callerType:       'agent',
    agentId:          'test-agent',
    agentPermissions: [],
    ...overrides,
  }
}

// Creates a shared context for a suite where multiple operations
// need to happen within the same org
export function makeOrgContext(): {
  orgId:      string
  userId:     string
  ctx:        CallerContext
} {
  const orgId  = `org-${randomUUID()}`
  const userId = `user-${randomUUID()}`
  const ctx    = makeUserContext({ orgId, userId })
  return { orgId, userId, ctx }
}
```

---

### Schema tests — the pattern

Every Zod schema gets a test file. Schema tests are fast, mechanical, and fully generatable by agents.

```typescript
// modules/branches/branches.schema.test.ts
import { describe, it, expect } from 'vitest'
import {
  createBranchSchema,
  updateBranchSchema,
  branchIdSchema,
} from './branches.schema'

describe('createBranchSchema', () => {
  // ── Valid inputs ────────────────────────────────────────────────
  it('accepts valid input', () => {
    const result = createBranchSchema.safeParse({
      name:   'Downtown Office',
      region: 'North',
    })
    expect(result.success).toBe(true)
  })

  // ── Required fields ─────────────────────────────────────────────
  it('rejects missing name', () => {
    const result = createBranchSchema.safeParse({ region: 'North' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toContain('name')
  })

  it('rejects missing region', () => {
    const result = createBranchSchema.safeParse({ name: 'Downtown' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toContain('region')
  })

  // ── Format and boundary validation ─────────────────────────────
  it('rejects empty name', () => {
    const result = createBranchSchema.safeParse({ name: '', region: 'North' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].message).toBe('Name is required')
  })

  it('rejects name over 100 characters', () => {
    const result = createBranchSchema.safeParse({
      name:   'A'.repeat(101),
      region: 'North',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].message).toBe('Name too long')
  })

  // ── Fields that must not exist ──────────────────────────────────
  // These confirm the schema does not allow fields
  // that should be set by the DB or service
  it('strips id if provided', () => {
    const result = createBranchSchema.safeParse({
      name:   'Downtown',
      region: 'North',
      id:     'some-uuid', // should be stripped
    })
    expect(result.success).toBe(true)
    expect((result.data as any).id).toBeUndefined()
  })
})

describe('updateBranchSchema', () => {
  it('accepts partial updates', () => {
    // Only name — region not required
    expect(updateBranchSchema.safeParse({ name: 'New Name' }).success).toBe(true)
    // Only region — name not required
    expect(updateBranchSchema.safeParse({ region: 'South' }).success).toBe(true)
    // Empty object is valid — caller provides only what changed
    expect(updateBranchSchema.safeParse({}).success).toBe(true)
  })
})

describe('branchIdSchema', () => {
  it('accepts a valid UUID', () => {
    const result = branchIdSchema.safeParse({ branchId: '550e8400-e29b-41d4-a716-446655440000' })
    expect(result.success).toBe(true)
  })

  it('rejects a non-UUID string', () => {
    const result = branchIdSchema.safeParse({ branchId: 'not-a-uuid' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].message).toBe('Invalid branch ID')
  })
})
```

---

### Service tests — the pattern

Service tests are the most important tests in the architecture. They verify business logic, org isolation, and error handling against a real test database.

```typescript
// modules/branches/branches.service.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { branchService } from './branches.service'
import { makeOrgContext, makeUserContext } from '@/tests/helpers/caller-context'
import { db } from '@/db'
import { branches } from '@/db/schema'

// Clean the branches table before each test
// Each test creates its own isolated org context
beforeEach(async () => {
  await db.delete(branches)
})

describe('branchService.create', () => {
  it('creates a branch and returns it', async () => {
    const { orgId, ctx } = makeOrgContext()

    const result = await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx,
    })

    expect(result.data).toMatchObject({
      name:   'Downtown',
      region: 'North',
      orgId,
    })
    expect(result.data?.id).toBeDefined()
  })

  it('returns an error when the name already exists in the org', async () => {
    const { ctx } = makeOrgContext()

    await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx,
    })

    const result = await branchService.create({
      data: { name: 'Downtown', region: 'South' }, // same name, same org
      ctx,
    })

    expect(result.error).toBe('A branch with this name already exists')
  })

  // ── The org isolation test ──────────────────────────────────────
  // This is the most important test in the architecture.
  // A name that exists in org A must not block creation in org B.
  it('allows the same name in a different org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx:  orgA.ctx,
    })

    // Same name, different org — must succeed
    const result = await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx:  orgB.ctx,
    })

    expect(result.data).toBeDefined()
    expect(result.error).toBeUndefined()
  })
})

describe('branchService.getById', () => {
  it('returns the branch when it exists', async () => {
    const { orgId, ctx } = makeOrgContext()

    const created = await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx,
    })

    const found = await branchService.getById({
      branchId: created.data!.id,
      orgId,
    })

    expect(found?.name).toBe('Downtown')
  })

  it('returns null when the branch does not exist', async () => {
    const { orgId } = makeOrgContext()

    const found = await branchService.getById({
      branchId: '550e8400-e29b-41d4-a716-446655440000',
      orgId,
    })

    expect(found).toBeNull()
  })

  // ── Cross-org access test ───────────────────────────────────────
  // A branch created in org A must not be retrievable by org B.
  it('returns null when the branch belongs to a different org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    const created = await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx:  orgA.ctx,
    })

    // Org B tries to fetch a branch that belongs to org A
    const found = await branchService.getById({
      branchId: created.data!.id,
      orgId:    orgB.orgId, // different org
    })

    // Must return null — not the branch, and not an error
    expect(found).toBeNull()
  })
})

describe('branchService.listByOrg', () => {
  it('returns only branches belonging to the requesting org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    // Create branches in both orgs
    await branchService.create({ data: { name: 'A Branch 1', region: 'North' }, ctx: orgA.ctx })
    await branchService.create({ data: { name: 'A Branch 2', region: 'South' }, ctx: orgA.ctx })
    await branchService.create({ data: { name: 'B Branch 1', region: 'North' }, ctx: orgB.ctx })

    const result = await branchService.listByOrg({ orgId: orgA.orgId })

    // Org A gets exactly its two branches
    expect(result.data).toHaveLength(2)
    expect(result.data.every(b => b.orgId === orgA.orgId)).toBe(true)
  })
})

describe('branchService.update', () => {
  it('updates the branch and returns the updated record', async () => {
    const { orgId, ctx } = makeOrgContext()

    const created = await branchService.create({
      data: { name: 'Old Name', region: 'North' },
      ctx,
    })

    const result = await branchService.update({
      branchId: created.data!.id,
      data:     { name: 'New Name' },
      ctx,
    })

    expect(result.data?.name).toBe('New Name')
    expect(result.data?.region).toBe('North') // unchanged
  })

  it('returns an error when updating to a name that already exists', async () => {
    const { ctx } = makeOrgContext()

    await branchService.create({ data: { name: 'Branch A', region: 'North' }, ctx })
    const b = await branchService.create({ data: { name: 'Branch B', region: 'North' }, ctx })

    const result = await branchService.update({
      branchId: b.data!.id,
      data:     { name: 'Branch A' }, // name taken
      ctx,
    })

    expect(result.error).toBe('A branch with this name already exists')
  })

  it('returns an error when the branch belongs to a different org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    const created = await branchService.create({
      data: { name: 'Downtown', region: 'North' },
      ctx:  orgA.ctx,
    })

    // Org B tries to update org A's branch
    const result = await branchService.update({
      branchId: created.data!.id,
      data:     { name: 'Hijacked' },
      ctx:      orgB.ctx, // different org
    })

    expect(result.error).toBe('Branch not found')
  })
})
```

---

### The org isolation tests — why they matter

The tests marked "Cross-org access test" in the examples above are the most important tests in the entire test suite. They verify the fundamental security property of the architecture: **data from one org cannot be accessed or modified by another org**.

Every module must have at least these three org isolation tests:

```typescript
// The three required isolation tests for every module:

// 1. getById returns null for a record from a different org
it('cannot fetch a record from another org', ...)

// 2. update returns an error for a record from a different org
it('cannot update a record from another org', ...)

// 3. delete returns an error for a record from a different org
it('cannot delete a record from another org', ...)

// 4. list returns only records belonging to the requesting org
it('list returns only own org records', ...)
```

These tests are non-negotiable. If a PR adds a new module without these tests, it is incomplete regardless of whether the feature works correctly.

---

### Playwright E2E tests — the pattern

E2E tests cover complete user flows from the browser. They are slower than unit tests and should cover critical journeys, not every permutation.

#### Auth fixtures

Log in once per role, save the session state, reuse it across all tests. This avoids repeated login flows that slow the suite down significantly.

```typescript
// tests/e2e/fixtures/auth.ts
import { test as base, type Page, type BrowserContext } from '@playwright/test'

// Run this script once to create the saved session files:
// playwright test tests/e2e/setup/auth.setup.ts
// Output: tests/e2e/.auth/admin.json, member.json

type AuthFixtures = {
  adminPage:  Page
  memberPage: Page
}

export const test = base.extend<AuthFixtures>({
  adminPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({
      storageState: 'tests/e2e/.auth/admin.json',
    })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },

  memberPage: async ({ browser }, use) => {
    const ctx = await browser.newContext({
      storageState: 'tests/e2e/.auth/member.json',
    })
    const page = await ctx.newPage()
    await use(page)
    await ctx.close()
  },
})

export { expect } from '@playwright/test'
```

```typescript
// tests/e2e/setup/auth.setup.ts
// Runs once before the full E2E suite to create session files

import { test as setup } from '@playwright/test'

setup('create admin session', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[name=email]',    'admin@testorg.com')
  await page.fill('[name=password]', 'test-password')
  await page.click('[type=submit]')
  await page.waitForURL('/dashboard')
  await page.context().storageState({ path: 'tests/e2e/.auth/admin.json' })
})

setup('create member session', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[name=email]',    'member@testorg.com')
  await page.fill('[name=password]', 'test-password')
  await page.click('[type=submit]')
  await page.waitForURL('/dashboard')
  await page.context().storageState({ path: 'tests/e2e/.auth/member.json' })
})
```

#### The E2E test pattern

```typescript
// tests/e2e/branches.spec.ts
import { test, expect } from './fixtures/auth'

test.describe('branches — admin', () => {
  test('can create a branch', async ({ adminPage: page }) => {
    await page.goto('/branches/new')

    await page.fill('[name=name]',   'Test Branch')
    await page.fill('[name=region]', 'North')
    await page.click('[type=submit]')

    // Confirm the success toast appears
    await expect(page.getByText('Branch created')).toBeVisible()

    // Confirm the branch appears in the list
    await page.goto('/branches')
    await expect(page.getByText('Test Branch')).toBeVisible()
  })

  test('sees a validation error for an empty name', async ({ adminPage: page }) => {
    await page.goto('/branches/new')
    await page.click('[type=submit]')

    await expect(page.getByText('Name is required')).toBeVisible()
  })
})

test.describe('branches — permission boundaries', () => {
  // This is the E2E equivalent of the org isolation test —
  // confirms that role-based restrictions are enforced in the UI
  test('member cannot see the Create Branch button', async ({ memberPage: page }) => {
    await page.goto('/branches')
    await expect(page.getByRole('link', { name: 'New Branch' })).not.toBeVisible()
  })

  test('member cannot access the create branch page directly', async ({ memberPage: page }) => {
    await page.goto('/branches/new')
    // Should be redirected or see a forbidden message
    await expect(page).not.toHaveURL('/branches/new')
  })
})
```

#### What E2E tests cover

| Always test | Do not test in E2E |
|---|---|
| The happy path for every major feature | Every validation error (test in schema tests) |
| Auth flows — login, logout, session expiry | Every business rule variation (test in service tests) |
| Permission boundaries — role A can, role B cannot | Pagination edge cases |
| Critical multi-step flows | Internal data transformations |
| Navigation — does clicking X go to Y | |

The E2E suite should be fast enough to run in under 5 minutes. If it takes longer, reduce scope or parallelize.

---

### What agents generate vs what developers write

| Test type | Agent generates | Developer writes |
|---|---|---|
| Schema tests | All of them — mechanical derivation from the schema | Edge cases the schema description didn't cover |
| Service happy-path tests | The structure and basic assertions | Business rule tests, complex state tests |
| Org isolation tests | The four required patterns per module | Module-specific variations |
| Action tests | Not needed — actions are thin and covered by service + E2E | — |
| E2E flows | The fixture setup | Actual user journey tests |
| E2E permission boundaries | The structure | The specific roles and permissions being tested |

**The agent contract for tests:**
When an agent generates a new module (schema, service, actions), it also generates:
- The schema test file with valid/invalid/boundary cases for every schema
- The service test file with happy path, not found, and all four org isolation tests
- It does NOT generate E2E tests — those require knowledge of the actual UI flows

---

### The testing checklist — before a PR is ready

**Schema tests:**
- [ ] Valid input passes for every schema
- [ ] Each required field is tested for absence
- [ ] Each format rule is tested at the boundary (min length, max length, format)
- [ ] Fields that must not exist (id, orgId, createdAt) are confirmed absent from output

**Service tests:**
- [ ] Happy path for every public service method
- [ ] Business failure cases for every business rule
- [ ] Not found returns null (getById, getByX methods)
- [ ] The four org isolation tests: getById, update, delete, list

**E2E tests:**
- [ ] Happy path for the primary user journey of the feature
- [ ] Permission boundary: the restricted operation fails for an unauthorized role

---

### How to use this document

- **Developers:** Write schema tests first — they are fast and confirm the contract before any service code is written. Write service tests before marking a feature complete. Write E2E tests for the happy path and at least one permission boundary per new feature.
- **Agents:** When generating a new module, always generate the schema test file and the service test file alongside the implementation files. Use `makeOrgContext()` from the test helper for every service test. Always include the four org isolation tests. Do not generate E2E tests.
- **Tech leads:** A PR that adds a new module without org isolation tests in the service test file is incomplete. This is a non-negotiable review gate. The four required patterns are documented above.

---

*Previous: Section 8 — API Layer*
*Next: Section 10 — Production Operations*
