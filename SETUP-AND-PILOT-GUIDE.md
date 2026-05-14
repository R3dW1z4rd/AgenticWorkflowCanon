# Setup & Pilot Guide

*A step-by-step walkthrough from zero to your first shipped user story using the agentic pipeline. Allow 4-6 hours for the full pilot. Stop at any "✓ Validation checkpoint" and verify before continuing.*

---

## Before you start

### What you need

| Requirement | Why |
|---|---|
| Node.js 20+ and npm | Next.js 15, Drizzle Kit, Vitest, Playwright |
| PostgreSQL 14+ running locally | Database for development and testing |
| Git | Version control, branch management for phases |
| GitHub or Gitea account with a token | Issue tracking + Actions for state updates |
| Claude Code CLI installed and authenticated | The agent runtime |
| Codex CLI installed and authenticated | The discovery agent runtime |
| A real or pretend client brief | Input to the discovery agent |

### What you'll have at the end

A Next.js project with one user story (US-001) shipped end-to-end through the four-phase agent pipeline. Real schema, real tests, real implementation, real E2E coverage. Issue auto-closed by Actions. State file updated. The exact rhythm you'll use on every subsequent project.

### What this guide covers

| Section | What happens |
|---|---|
| Phase A | Set up the canon repo and discovery agent |
| Phase B | Bootstrap a new project from the starter template |
| Phase C | Configure BetterAuth and the database |
| Phase D | Run discovery — produce SPEC.md |
| Phase E | Run /wireframe — produce UI specification |
| Phase F | Run /plan-sprint — create issues |
| Phase G | Walk US-001 through Phases 5-8 |
| Phase H | Verify everything end-to-end |

---

# Phase A — Canon setup (one-time, ~15 minutes)

This is done once per machine. After this, you can bootstrap any number of projects.

## A.1 — Clone the canon

```bash
cd ~/work     # or wherever you keep code
git clone [your-canon-repo-url] architecture-canon
cd architecture-canon
```

Inspect the structure:

```bash
ls -la
# You should see:
#   canon/                    ← architecture rules
#   templates/starter/        ← project bootstrap files
#   templates/coding-agents/  ← agent definitions
#   templates/discovery-agent-codex/  ← discovery agent
#   tools/                    ← Python scripts
#   examples/                 ← worked examples
#   README.md  STATUS.md  CHANGELOG.md  OPEN-ISSUES.md
```

## A.2 — Verify Python scripts run

The discovery agent's helper scripts live alongside the agent itself, at `templates/discovery-agent-codex/scripts/`. Verify they're runnable:

```bash
python3 templates/discovery-agent-codex/scripts/generate_spec.py --help
python3 templates/discovery-agent-codex/scripts/generate_test_shells.py --help
python3 templates/discovery-agent-codex/scripts/generate_change_manifest.py --help
```

Each should print usage information. If any fails with "No such file", confirm you cloned the canon correctly — the scripts should appear in the directory listing above.

The scripts use only the Python standard library, so no `pip install` is needed. Python 3.9+ is required.

You'll typically not invoke these scripts directly — the discovery agent calls them on your behalf during its conversation. This step just confirms they're present and your Python version is compatible.

## A.3 — Verify install scripts are executable

```bash
ls -la templates/coding-agents/install-coding-agents.sh
ls -la templates/starter/install-starter.sh
```

Both should show `-rwxr-xr-x` permissions. If they show `-rw-r--r--` instead, make them executable:

```bash
chmod +x templates/coding-agents/install-coding-agents.sh
chmod +x templates/starter/install-starter.sh
chmod +x templates/coding-agents/.agent/scripts/*.sh
```

Quick sanity check — this should print a usage error (not "No such file"):

```bash
bash templates/coding-agents/install-coding-agents.sh /nonexistent
# Expected: ❌ Canon repo not found at /nonexistent
```

## A.4 — Set up the Codex discovery agent

Codex is a separate runtime from Claude Code. The discovery agent is configured in its own directory:

```bash
cd templates/discovery-agent-codex
ls
# Should contain:
#   AGENTS.md           ← the discovery agent's system prompt
#   guides/             ← guides for each discovery artifact
#   tools/              ← Python helpers
```

Start a Codex session in this directory to confirm it loads:

```bash
codex
# Inside Codex, type: hello
# The agent should respond as the Discovery Agent and list its commands.
```

Exit Codex (`Ctrl-D` or `exit`).

**✓ Validation checkpoint A:**
- `~/work/architecture-canon/` exists with all expected subdirectories
- The install scripts are executable
- A Codex session in `templates/discovery-agent-codex/` loads the discovery agent

---

# Phase B — Project bootstrap (~10 minutes)

Now create a real project. For this guide, we'll use a small example project. Substitute your own client name if you have one.

## B.1 — Create the project directory

```bash
cd ~/work
mkdir contract-pilot && cd contract-pilot
git init
```

## B.2 — Bootstrap a Next.js 15 app

```bash
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --src-dir=false \
  --import-alias="@/*" \
  --eslint

# When asked about Turbopack: yes
# When asked about React Compiler: optional, your call
```

After this, you should have a working Next.js project. Test it:

```bash
npm run dev
# Open http://localhost:3000 — you should see the Next.js welcome page
# Stop the server (Ctrl-C)
```

## B.3 — Run the starter install

This adds the agentic scaffolding: lib/auth, lib/audit, lib/logger, db/, tests/helpers/, the CLAUDE.md, and config files. It also calls the coding-agents installer automatically.

```bash
bash ~/work/architecture-canon/templates/starter/install-starter.sh \
  --canon ~/work/architecture-canon \
  --name "Contract Pilot" \
  --slug contract-pilot \
  --org-context org-with-units
```

Watch the output. You should see:

```
📁 Copying lib/ files...
📁 Copying db/ scaffold...
📁 Copying tests/ helpers...
📁 Copying config files...
📄 Setting up root CLAUDE.md...
📦 package.json exists — merging scripts section...
📚 Syncing architecture canon sections...
📦 Installing coding agents...
✅ Contract Pilot bootstrapped.
```

## B.4 — Install dependencies

```bash
npm install \
  better-auth \
  drizzle-orm \
  drizzle-kit \
  pg \
  zod \
  pino \
  pino-pretty

npm install -D \
  @types/pg \
  vitest \
  @vitest/coverage-v8 \
  @playwright/test \
  playwright
```

## B.5 — Verify the structure

```bash
ls -la
# You should see:
#   .claude/agents/      ← orchestrator, schema, test, code, ship, wireframe
#   .claude/commands/    ← all slash commands
#   .agent/scripts/      ← preflight scripts
#   .github/workflows/   ← state update workflow
#   .work/               ← (empty — created by agents)
#   app/                 ← Next.js app dir
#   db/                  ← Drizzle scaffold
#   docs/                ← architecture, specs, wireframes, project-state
#   lib/                 ← auth, audit, logger, types
#   modules/             ← (empty — populated per story)
#   tests/               ← helpers, e2e, setup
#   CLAUDE.md            ← root context, customised for Contract Pilot
#   drizzle.config.ts
#   vitest.config.ts
#   .env.example
```

## B.6 — Configure environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_pilot
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_pilot_test
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development

# Generate a real secret: openssl rand -base64 64
BETTER_AUTH_SECRET=paste-the-output-of-openssl-rand-here
BETTER_AUTH_URL=http://localhost:3000

LOG_LEVEL=debug
SERVICE_NAME=contract-pilot
DATABASE_POOL_MAX=10
```

Generate the secret:

```bash
openssl rand -base64 64
# Copy the output, paste it as BETTER_AUTH_SECRET in .env.local
```

## B.7 — Create the databases

```bash
createdb contract_pilot
createdb contract_pilot_test

# If using Docker:
# docker exec -it [postgres-container] psql -U postgres -c "CREATE DATABASE contract_pilot;"
# docker exec -it [postgres-container] psql -U postgres -c "CREATE DATABASE contract_pilot_test;"
```

## B.8 — Initial git commit

```bash
git add .
git commit -m "chore: bootstrap project from canon starter"
```

**✓ Validation checkpoint B:**
- `npm run dev` starts the dev server without errors
- `ls .claude/agents/` shows 6 agent files
- `psql contract_pilot -c "SELECT 1"` succeeds
- `npx tsc --noEmit` passes (no TypeScript errors)

---

# Phase C — BetterAuth setup (~30 minutes)

The one part the agents can't generate for you. This is one-time per project.

## C.1 — Create the BetterAuth instance

Create `lib/auth/auth.ts`:

```bash
cat > lib/auth/auth.ts << 'EOF'
// lib/auth/auth.ts
//
// BetterAuth instance. Extends the default session to include orgId,
// orgUnitId, and permissions — required by CallerContext.
//
// Canon reference: Section 8 (Authorization)

import { betterAuth } from 'better-auth'
import { drizzleAdapter } from 'better-auth/adapters/drizzle'
import { db } from '@/db'
import * as schema from '@/db/schema/auth'

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: 'pg',
    schema,
  }),

  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false,  // for pilot — enable for production
  },

  // ── Session extension — required by CallerContext ────────────────────────
  user: {
    additionalFields: {
      orgId: {
        type: 'string',
        required: true,
        defaultValue: '',
      },
      orgUnitId: {
        type: 'string',
        required: true,
        defaultValue: '',
      },
      permissions: {
        type: 'string[]',
        required: false,
        defaultValue: [],
      },
    },
  },

  // ── Session caching ──────────────────────────────────────────────────────
  session: {
    expiresIn: 60 * 60 * 24 * 7,   // 7 days
    updateAge: 60 * 60 * 24,        // refresh daily
    cookieCache: {
      enabled: true,
      maxAge:  60 * 5,              // 5 minutes — for fast permission checks
    },
  },

  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.BETTER_AUTH_URL!,
})

export type Auth = typeof auth
EOF
```

## C.2 — Create the BetterAuth Drizzle schema

This is the schema BetterAuth needs for sessions, accounts, etc. Plus the org/org-unit structure.

```bash
cat > db/schema/auth.ts << 'EOF'
// db/schema/auth.ts
//
// BetterAuth tables + org structure tables.
// BetterAuth manages user, session, account, verification.
// We add: organisations, org_units, memberships, roles.

import {
  boolean,
  pgTable,
  text,
  timestamp,
  uuid,
} from 'drizzle-orm/pg-core'

// ── Organisations (the top-level scope) ──────────────────────────────────

export const organisations = pgTable('organisations', {
  id:        uuid('id').defaultRandom().primaryKey(),
  name:      text('name').notNull(),
  slug:      text('slug').notNull().unique(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
})

// ── Org units (branches, stores, regions — per org-with-units pattern) ───

export const orgUnits = pgTable('org_units', {
  id:        uuid('id').defaultRandom().primaryKey(),
  orgId:     uuid('org_id').notNull().references(() => organisations.id),
  name:      text('name').notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
})

// ── BetterAuth core tables ───────────────────────────────────────────────

export const user = pgTable('user', {
  id:            text('id').primaryKey(),
  name:          text('name').notNull(),
  email:         text('email').notNull().unique(),
  emailVerified: boolean('email_verified').notNull().default(false),
  image:         text('image'),
  createdAt:     timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt:     timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),

  // Extended fields per BetterAuth additionalFields config:
  orgId:       uuid('org_id'),                     // nullable to allow signup before org assignment
  orgUnitId:   uuid('org_unit_id'),
  permissions: text('permissions').array().default([]).notNull(),
})

export const session = pgTable('session', {
  id:        text('id').primaryKey(),
  userId:    text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
  token:     text('token').notNull().unique(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
  ipAddress: text('ip_address'),
  userAgent: text('user_agent'),
})

export const account = pgTable('account', {
  id:                    text('id').primaryKey(),
  accountId:             text('account_id').notNull(),
  providerId:            text('provider_id').notNull(),
  userId:                text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  accessToken:           text('access_token'),
  refreshToken:          text('refresh_token'),
  idToken:               text('id_token'),
  accessTokenExpiresAt:  timestamp('access_token_expires_at', { withTimezone: true }),
  refreshTokenExpiresAt: timestamp('refresh_token_expires_at', { withTimezone: true }),
  scope:                 text('scope'),
  password:              text('password'),
  createdAt:             timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt:             timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
})

export const verification = pgTable('verification', {
  id:         text('id').primaryKey(),
  identifier: text('identifier').notNull(),
  value:      text('value').notNull(),
  expiresAt:  timestamp('expires_at', { withTimezone: true }).notNull(),
  createdAt:  timestamp('created_at', { withTimezone: true }).defaultNow(),
  updatedAt:  timestamp('updated_at', { withTimezone: true }).defaultNow(),
})
EOF
```

Update `db/schema/index.ts` to export this:

```bash
cat > db/schema/index.ts << 'EOF'
// db/schema/index.ts
// Schema barrel. The schema agent adds new module exports below.

export * from './auth'
EOF
```

## C.3 — Generate and apply the auth migration

```bash
npm run db:generate
# Should output: "1 migration generated: db/migrations/0000_*.sql"

npm run db:migrate
# Should output: "Migration applied successfully"
```

Verify in PostgreSQL:

```bash
psql contract_pilot -c "\\dt"
# You should see tables: account, organisations, org_units, session, user, verification
```

## C.4 — Add the auth API route

Create the catch-all auth route:

```bash
mkdir -p app/api/auth/[...all]
cat > "app/api/auth/[...all]/route.ts" << 'EOF'
// app/api/auth/[...all]/route.ts
// BetterAuth API handler. Routes all /api/auth/* requests to the auth instance.

import { auth } from '@/lib/auth/auth'
import { toNextJsHandler } from 'better-auth/next-js'

export const { POST, GET } = toNextJsHandler(auth)
EOF
```

## C.5 — Create middleware for authentication

```bash
cat > middleware.ts << 'EOF'
// middleware.ts
// Redirects unauthenticated requests to /login.
// SB-3 requirement: unauthenticated visitor at protected routes → /login

import { NextResponse, type NextRequest } from 'next/server'
import { getSessionCookie } from 'better-auth/cookies'

export async function middleware(request: NextRequest) {
  const sessionCookie = getSessionCookie(request)

  // Protect everything under (dashboard) — i.e. the authenticated app
  if (!sessionCookie && request.nextUrl.pathname.startsWith('/(dashboard)')) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match all dashboard routes and anything else that needs auth
    '/(dashboard)/:path*',
  ],
}
EOF
```

## C.6 — Create minimal login/signup pages

These are placeholder pages for the pilot. Real projects would replace these with branded versions.

```bash
mkdir -p app/login app/signup

cat > app/login/page.tsx << 'EOF'
'use client'

import { useState } from 'react'
import { authClient } from '@/lib/auth/client'

export default function LoginPage() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const result = await authClient.signIn.email({
      email,
      password,
      callbackURL: '/contracts',
    })
    if (result.error) setError(result.error.message ?? 'Login failed')
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: '2rem' }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input type="email"    value={email}    onChange={e => setEmail(e.target.value)}    placeholder="Email" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
        <button type="submit">Sign in</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
      <p>No account? <a href="/signup">Sign up</a></p>
    </div>
  )
}
EOF

cat > app/signup/page.tsx << 'EOF'
'use client'

import { useState } from 'react'
import { authClient } from '@/lib/auth/client'

export default function SignupPage() {
  const [name,     setName]     = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const result = await authClient.signUp.email({
      name, email, password,
      callbackURL: '/contracts',
    })
    if (result.error) setError(result.error.message ?? 'Signup failed')
  }

  return (
    <div style={{ maxWidth: 400, margin: '4rem auto', padding: '2rem' }}>
      <h1>Sign up</h1>
      <form onSubmit={handleSubmit}>
        <input type="text"     value={name}     onChange={e => setName(e.target.value)}     placeholder="Name" required />
        <input type="email"    value={email}    onChange={e => setEmail(e.target.value)}    placeholder="Email" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password (8+ chars)" required minLength={8} />
        <button type="submit">Create account</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  )
}
EOF
```

## C.7 — Create the auth client

```bash
cat > lib/auth/client.ts << 'EOF'
// lib/auth/client.ts
// BetterAuth React client. Use in client components for signIn, signUp, signOut.

import { createAuthClient } from 'better-auth/react'

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_APP_URL!,
})
EOF
```

## C.8 — Seed an initial organisation and user for the pilot

For the pilot, we need at least one org with one org-unit and one test user. Create a seed script:

```bash
mkdir -p scripts
cat > scripts/seed-pilot.ts << 'EOF'
// scripts/seed-pilot.ts
// Run once: npx tsx scripts/seed-pilot.ts
//
// Creates:
//   - 1 organisation (Acme Corp)
//   - 2 org units (London Branch, Manchester Branch)
//   - 2 test users with different permissions

import { auth } from '@/lib/auth/auth'
import { db } from '@/db'
import { organisations, orgUnits, user } from '@/db/schema/auth'
import { sql } from 'drizzle-orm'

async function seed() {
  console.log('🌱 Seeding pilot data...')

  // Org + org units
  const [org] = await db
    .insert(organisations)
    .values({ name: 'Acme Corp', slug: 'acme' })
    .returning()

  const [london]     = await db.insert(orgUnits).values({ orgId: org.id, name: 'London Branch'     }).returning()
  const [manchester] = await db.insert(orgUnits).values({ orgId: org.id, name: 'Manchester Branch' }).returning()

  console.log(`  Org: ${org.name} (${org.id})`)
  console.log(`  Units: ${london.name}, ${manchester.name}`)

  // Test users via BetterAuth (so passwords are hashed correctly)
  const am = await auth.api.signUpEmail({
    body: {
      name: 'Alice AM',
      email: 'alice@acme.test',
      password: 'pilotpass123',
    },
  })

  if (am.user?.id) {
    await db.update(user).set({
      orgId:       org.id,
      orgUnitId:   london.id,
      permissions: ['contracts:create', 'contracts:update', 'contracts:delete'],
    }).where(sql`id = ${am.user.id}`)
    console.log(`  User: ${am.user.email} (AM, London Branch)`)
  }

  const viewer = await auth.api.signUpEmail({
    body: {
      name: 'Bob Viewer',
      email: 'bob@acme.test',
      password: 'pilotpass123',
    },
  })

  if (viewer.user?.id) {
    await db.update(user).set({
      orgId:       org.id,
      orgUnitId:   london.id,
      permissions: [],   // no contracts:create — for SB-2 testing
    }).where(sql`id = ${viewer.user.id}`)
    console.log(`  User: ${viewer.user.email} (Viewer, no permissions)`)
  }

  console.log('\n✅ Seed complete.\n')
  console.log('Login as:')
  console.log('  Alice (full permissions): alice@acme.test / pilotpass123')
  console.log('  Bob   (no permissions):    bob@acme.test   / pilotpass123')

  process.exit(0)
}

seed().catch(err => {
  console.error('Seed failed:', err)
  process.exit(1)
})
EOF

npm install -D tsx
npx tsx scripts/seed-pilot.ts
```

You should see:
```
🌱 Seeding pilot data...
  Org: Acme Corp ([uuid])
  Units: London Branch, Manchester Branch
  User: alice@acme.test (AM, London Branch)
  User: bob@acme.test (Viewer, no permissions)
✅ Seed complete.
```

## C.9 — Verify auth works end-to-end

```bash
npm run dev
```

Open http://localhost:3000/login

- Log in as `alice@acme.test` / `pilotpass123`
- You should be redirected to `/contracts` (which will 404 — that's fine, the module doesn't exist yet)
- Open browser DevTools → Application → Cookies — confirm a session cookie was set

Stop the dev server.

```bash
git add .
git commit -m "feat: configure BetterAuth, org structure, and pilot seed"
```

**✓ Validation checkpoint C:**
- `npm run db:migrate` applied without errors
- Login page renders at `/login`
- Signup creates a user and assigns a session cookie
- `psql contract_pilot -c "SELECT email, org_id, permissions FROM \"user\""` shows both seeded users with their permissions

---

# Phase D — Discovery (~30-45 minutes)

Now we produce the SPEC.md that drives everything. For the pilot, we'll use a deliberately small scope: a contract management feature with two basic capabilities.

## D.1 — Prepare the project structure for discovery artifacts

```bash
mkdir -p docs/specs docs/discovery
```

## D.2 — Start the discovery agent

```bash
cd ~/work/architecture-canon/templates/discovery-agent-codex
codex
```

## D.3 — Run discovery from a brief

In the Codex session, paste this brief:

```
I want to build a small contract management feature for Acme Corp, an org-with-units
business (regions → branches). Account Managers (AMs) at each branch create client
contracts. For our pilot, we need only:

1. AMs can create a new contract with required fields: start date, AM ID, contract type
   (standard, premium, enterprise)
2. They can save as draft without completing all fields
3. Past start dates are rejected with an inline error
4. AMs can see a list of their org's contracts
5. The system logs an audit record every time a contract is created

Out of scope for the pilot: Forex rates, referrals, approval workflow, commission rates,
contract editing. We'll add these later.

Please walk me through discovery for this single module: "contracts".
```

The discovery agent will:
1. Ask clarifying questions about the org context, roles, behavioral edge cases
2. Produce 5 artifacts in conversation (module card, data dictionary, ACs, behavioral specs, permissions)
3. Save them to its working directory

When discovery is complete, the agent will run `generate_spec.py` to produce the consolidated `SPEC.md`.

## D.4 — Copy discovery artifacts into the project

The discovery agent works in its own directory. Copy the outputs to the project:

```bash
cd ~/work/contract-pilot

# Copy the consolidated SPEC.md
cp ~/work/architecture-canon/templates/discovery-agent-codex/output/SPEC.md docs/specs/SPEC.md

# Copy the source artifacts (for reference)
cp -r ~/work/architecture-canon/templates/discovery-agent-codex/output/* docs/discovery/
```

(The exact paths depend on where your Codex setup writes outputs. Adjust accordingly.)

## D.5 — Tag the spec

```bash
git add docs/specs/SPEC.md docs/discovery/
git commit -m "spec(contracts): SPEC.md v1.0 — pilot scope"
git tag spec-v1.0
git push --tags     # if you've set up the remote
```

## D.6 — Update project-state.md

Open `docs/project-state.md` and fill in the Project info section:

```markdown
| **Project name** | Contract Pilot |
| **Project slug** | contract-pilot |
| **Org context** | org-with-units |
| **Current spec version** | v1.0 |
| **Current spec tag** | spec-v1.0 |
| **Current product version** | v1.0.0 (in development) |
| **Last released version** | none |
| **Current sprint** | (none yet) |
| **Repository** | git@github.com:[you]/contract-pilot.git |
| **Default branch** | main |
| **Issue provider** | github |
| **Gitea server URL** | (n/a — github) |
| **CI / state automation** | GitHub Actions |
```

```bash
git add docs/project-state.md
git commit -m "chore: configure project-state.md for sprint planning"
```

**✓ Validation checkpoint D:**
- `docs/specs/SPEC.md` exists with the contracts module section
- `git tag --list 'spec-*'` shows `spec-v1.0`
- `git diff --quiet spec-v1.0 -- docs/specs/SPEC.md` is silent (no drift)
- `docs/project-state.md` has all Project info fields filled

---

# Phase E — Wireframe (~15 minutes)

For the pilot, we'll use generation mode — no PDF wireframe exists yet.

## E.1 — Open Claude Code in the project

```bash
cd ~/work/contract-pilot
claude
```

## E.2 — Run /wireframe

In Claude Code:

```
/wireframe contracts
```

The wireframe agent will:
1. Detect there's no PDF in `docs/wireframes/` → enter generation mode
2. Read `docs/specs/SPEC.md` (contracts section)
3. List any existing screens in the project (none for pilot — fresh project)
4. Generate an HTML prototype rendered in the artifact viewer
5. Ask for `PROTOTYPE APPROVED`

Review the prototype. Look for:
- The list view layout (table with New Contract button)
- The create form layout (full-page, three fields)
- The validation error state on past-date

Iterate if needed. Once satisfied:

```
PROTOTYPE APPROVED
```

The agent commits `docs/wireframes/contracts-ui-spec.md`.

## E.3 — Verify the ui-spec.md

```bash
ls docs/wireframes/
# contracts-ui-spec.md
cat docs/wireframes/contracts-ui-spec.md | head -50
```

You should see the screen inventory with at least LIST and NEW-1 screens. Each screen should have layout, components, fields, and states sections.

```bash
git log -1 --oneline
# Should show: design(contracts): ui-spec.md v1.0 — generated
```

**✓ Validation checkpoint E:**
- `docs/wireframes/contracts-ui-spec.md` exists
- Contains at minimum a LIST screen and a NEW-1 screen
- Each screen has components, fields, and states sections

---

# Phase F — Sprint planning (~20 minutes)

## F.1 — Run /plan-sprint

In Claude Code (still in the same session or a fresh one):

```
/plan-sprint
```

The preflight runs first. You should see `PREFLIGHT_RESULT=PASS`.

The orchestrator loads, reads project state, SPEC.md, and the wireframe spec. It then:

1. Presents a screen inventory from the wireframe
2. Asks about any conflicts between the wireframe and the SPEC
3. Proposes a sprint plan

For the pilot, propose only US-001 (create draft contract) in sprint 1. Defer US-002 (audit log) to sprint 2 — even though it's listed in the SPEC, walking through one story end-to-end is enough for the first pilot.

Refine the conversation until satisfied, then:

```
APPROVE PLAN
```

The orchestrator commits and writes:
- Updated `docs/project-state.md` (sprint-1 section)
- `.work/issue-bodies/US-001.md`
- `scripts/create-sprint-1-issues.sh`
- `.work/sprint-plans/sprint-1-summary.md`

## F.2 — Review the artifacts

```bash
git log -1 -p | head -50
cat scripts/create-sprint-1-issues.sh
cat .work/issue-bodies/US-001.md | head -80
```

Check that:
- The issue body has a `## UI Specification` section populated from the wireframe spec
- The script uses `gh issue create --body-file`
- The phase breakdown lists all four phases with branch names

## F.3 — Push and create issues

```bash
git push
```

Set up GitHub Actions permissions:
1. Go to repository Settings → Actions → General
2. Under "Workflow permissions" select "Read and write permissions"
3. Save

Authenticate `gh` if you haven't:

```bash
gh auth status
# If not authenticated: gh auth login
```

Create the issues:

```bash
bash scripts/create-sprint-1-issues.sh
```

You should see:
```
Creating sprint 1 issues on GitHub...
[issue URL printed]
Done. Created 1 issues for sprint 1.
```

**✓ Validation checkpoint F:**
- A new GitHub issue exists titled "US-001: AM can create a draft contract..."
- The issue body contains the populated UI Specification section
- `docs/project-state.md` shows sprint-1 with US-001 listed
- All four phase checkboxes in the issue are unchecked

---

# Phase G — Walk US-001 through four phases (~90 minutes)

This is the main event. Stay in the same Claude Code session through all four phases — the compacted context from each phase carries to the next.

## G.1 — Phase 5: /schema

```
/schema contracts US-001
```

Preflight passes. Schema agent loads, reads the issue body, SPEC.md, and CLAUDE.md.

The agent presents a Phase 5 proposal:
- Drizzle table with explained nullability decisions
- Zod schemas with explicit exclusion table
- Service method signatures
- New permissions to register

Review carefully. Most common things to verify:
- `commission_rate` is NOT in any Zod schema
- `status` is NOT in any Zod schema (service-controlled)
- `org_id` AND `org_unit_id` are both in the table (org-with-units pattern)
- Service methods take `ctx: CallerContext`, not raw `orgId`

When satisfied:

```
SCHEMA APPROVED
```

The agent generates files, runs gate checks, commits, and opens a PR.

**Review the PR on GitHub:**

```bash
gh pr view --web
```

Check:
- All Phase 5 files present (db/schema, modules/contracts schemas + service + actions, CLAUDE.md skeleton, permissions update)
- Migration is in `db/migrations/` and looks reasonable
- Every service method throws `not implemented`

**Merge the PR:**

```bash
gh pr merge --squash --delete-branch
```

Wait ~30 seconds for the Actions workflow to run. Then:

```bash
gh issue view [issue-number]
# Phase 5 checkbox should be ticked
# Workflow comment posted
```

Pull main:

```bash
git checkout main
git pull
```

## G.2 — Phase 6: /test

```
/test contracts US-001
```

The test agent loads. It presents the behavior list — 13+ behaviors covering schema, service, isolation, and E2E stubs. Review:

```
BEHAVIORS APPROVED
```

The agent writes `BEHAVIORS.md` and commits (first commit). Then writes test files and commits (second commit). Then runs tests and reports:

```
$ npm test modules/contracts/
PASS  contracts.schema.test.ts (schemas already exist)
FAIL  contracts.service.test.ts (13 tests fail with "not implemented")
```

This is the correct state. If schema tests fail (when they should pass) or service tests pass (when they should fail), the agent investigates.

**Common Phase 6 finding:** the past-date Zod refinement bug. If the agent catches this, it commits the fix separately before the test code commit. Review the diff:

```bash
gh pr view --web
```

The PR should have 2-3 commits:
1. `test(contracts): Phase 6a — behaviors for US-001`
2. (optional) `fix(contracts): past-date comparison against midnight`
3. `test(contracts): Phase 6b — failing tests for US-001`

Merge:

```bash
gh pr merge --squash --delete-branch
git checkout main && git pull
```

## G.3 — Phase 7: /code

```
/code contracts US-001
```

The code agent loads, reads the test suite, reads the UI Specification section from the issue body, and presents an implementation plan covering both service implementation order and component structure (from the UI spec).

Review carefully. Verify:
- The proposed service implementation uses `requirePermission` first
- `orgId` and `orgUnitId` come from `ctx`, not from `data`
- Components match the wireframe (full-page form, not modal; segmented control for Contract Type)

```
IMPLEMENTATION APPROVED
```

The agent implements service methods, runs tests after each one, then builds components. Final verification:

```
$ npm test
PASS  All 18+ tests
$ grep -rn "not implemented" modules/contracts/
(no output)
$ npx tsc --noEmit
(silent)
```

Merge the PR:

```bash
gh pr merge --squash --delete-branch
git checkout main && git pull
```

## G.4 — Phase 8: /ship

```
/ship contracts US-001
```

The ship agent runs the gate checklist:

1. Unit tests still pass
2. E2E tests replaced with real assertions (no more `test.fail()` stubs)
3. A11y audit on each page (≥ 95)
4. No debug code (`console.log`, TODOs)

Then it asks you for manual smoke confirmation:

```
Please do a quick manual smoke test:
1. Log in as alice@acme.test
2. Navigate to /contracts
3. Create a draft contract
4. Verify it appears in the list
5. Log out, try /contracts/new — should redirect to /login

Confirm with SMOKE PASSED.
```

In another terminal:

```bash
npm run dev
```

Walk through the steps. When everything works:

```
SMOKE PASSED
```

The ship agent updates `modules/contracts/CLAUDE.md` with the final Exports section, commits, and opens the final PR.

Merge:

```bash
gh pr merge --squash --delete-branch
```

Wait for Actions:

```bash
gh issue view [issue-number]
# Status: closed
# All 4 phase checkboxes ticked
```

**✓ Validation checkpoint G:**
- All 4 PRs merged to main
- Issue US-001 closed automatically
- `docs/project-state.md` shows `✓ ✓ ✓ ✓` for US-001 and module status = "phase 8 done"
- `modules/contracts/CLAUDE.md` has a populated Exports section
- `npm test` and `npm run test:e2e` both pass on main

---

# Phase H — End-to-end verification (~10 minutes)

The final check that everything works together.

## H.1 — Fresh clone test

This proves the project is reproducible from git:

```bash
cd /tmp
git clone [your-contract-pilot-repo] contract-pilot-verify
cd contract-pilot-verify
npm install
cp ~/work/contract-pilot/.env.local .env.local   # or recreate
npm run db:migrate
npx tsx scripts/seed-pilot.ts
npm test
npm run test:e2e
```

If all of those pass, the agent pipeline produced a genuinely working, testable codebase.

## H.2 — Smoke test in the browser

```bash
npm run dev
```

Run through the smoke test sequence one more time. Pay attention to:
- Does the form match the wireframe?
- Are validation errors displayed in the right place?
- Does the org isolation actually hold? (You can verify by creating a second org via SQL and confirming Alice can't see Bob's contracts.)

## H.3 — Capture pilot learnings

Open `docs/pilot-learnings.md` (create it):

```markdown
# Pilot 1 — Contract Pilot Learnings

## What worked
- [Things that went smoothly]

## What needed adjustment
- [Where the agents needed manual correction]

## What's missing from the canon
- [Patterns or guidance that should be added]

## Recommended canon updates
- [Specific issues for the canon's OPEN-ISSUES.md]
```

Fill this in based on your experience. These are the inputs to the next canon revision.

**✓ Validation checkpoint H:**
- Fresh clone + install + tests passes
- Browser smoke test confirms the feature works end-to-end
- Pilot learnings captured

---

# Common issues and recovery

## "Phase 6 tests pass when they should fail"

The schema agent left a method implementation in Phase 5. Check `modules/contracts/contracts.service.ts` — every method should throw. If one has a body, that's a Phase 5 fix:

```bash
git checkout -b fix/contracts-phase5-stubs
# Restore the throwing stub
git commit -m "fix(contracts): restore throwing stub for [method] (Phase 5 correction)"
```

## "/schema preflight blocks: 'Phase 5 not complete'"

The Actions workflow may not have updated `project-state.md` yet. Check:

```bash
gh run list --workflow=update-state.yml
```

If the workflow failed, check its logs. If it succeeded but the state file isn't updated, pull main:

```bash
git pull
```

## "BetterAuth session doesn't include orgId"

The session extension in `lib/auth/auth.ts` is missing. Verify the `additionalFields` block under `user` includes `orgId`, `orgUnitId`, and `permissions`. Then sign out and sign in again (the existing session cookie was issued before the extension was added).

## "Migration fails: relation already exists"

The test database has stale state from a previous attempt. Reset:

```bash
dropdb contract_pilot_test
createdb contract_pilot_test
TEST_DATABASE_URL=postgresql://...test npm run db:migrate
```

## "E2E test can't log in"

The Playwright test needs a logged-in session. Use Playwright's storage state:

```bash
# tests/e2e/helpers/auth.ts
// Save authenticated state to a file once, reuse across tests
```

The ship agent should produce this helper when generating E2E tests. If it didn't, add it manually following the Playwright authentication recipe.

## "ForbiddenError not caught by Server Action"

The Server Action needs a try/catch. Check `modules/contracts/contracts.actions.ts`:

```ts
try {
  const ctx = await getCallerContext()
  return contractService.create({ data, ctx })
} catch (err) {
  if (err instanceof ForbiddenError) return { error: 'Forbidden' }
  throw err
}
```

If missing, this is a Phase 7 fix — the code agent should have added it.

---

# After the pilot

## What you now have

- A working agentic pipeline from client brief to shipped feature
- Hands-on experience with all six agents
- Real PRs in git history showing the four-phase pattern
- A canon you can use on the next project without modification (mostly)

## What to do next

1. **Capture every divergence** between the worked examples in the canon and what actually happened in your pilot. These are the canon's improvement backlog.

2. **Decide on the team's adoption sequence.** Will every developer learn all six agents at once, or will one team member act as the agent orchestrator while others review PRs?

3. **Decide on the first real client project.** The pilot used a synthetic example. The first real project will surface different patterns. Keep the pilot codebase available as a reference.

4. **Schedule a canon review.** After 2-3 real projects, the canon will need revisions. Set a quarterly review cycle.

5. **Build your golden example.** Pick the most complete module from your first real project, polish its CLAUDE.md and tests, and commit it to the canon's `examples/` directory as a reference implementation.

---

# Quick reference

| Phase | Command | Approval phrase | What gets committed |
|---|---|---|---|
| Design — wireframe | `/wireframe [module]` | `SPEC APPROVED` or `PROTOTYPE APPROVED` | `docs/wireframes/[module]-ui-spec.md` |
| Planning — sprint | `/plan-sprint` | `APPROVE PLAN` | `docs/project-state.md`, issue bodies, script |
| Planning — change | `/plan-change` | `APPROVE PLAN` | Same as plan-sprint, scoped to change |
| Review — status | `/status` | (none — read-only) | Nothing |
| Phase 5 — schema | `/schema [m] US-XXX` | `SCHEMA APPROVED` | Schema, Zod, service stubs, CLAUDE.md skeleton |
| Phase 6 — test | `/test [m] US-XXX` | `BEHAVIORS APPROVED` | BEHAVIORS.md (commit 1), tests (commit 2) |
| Phase 7 — code | `/code [m] US-XXX` | `IMPLEMENTATION APPROVED` | Service impl, actions, components, pages |
| Phase 8 — ship | `/ship [m] US-XXX` | `SMOKE PASSED` | E2E tests, CLAUDE.md exports |

---

*Last updated: May 2026 — for canon v2.0 and coding-agents v1.0*
