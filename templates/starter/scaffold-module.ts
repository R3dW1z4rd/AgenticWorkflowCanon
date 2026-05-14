#!/usr/bin/env tsx
/**
 * Module Scaffolder
 *
 * Generates a complete module following the architecture canon.
 *
 * Usage:
 *   npm run scaffold:module <module-name>
 *
 * Examples:
 *   npm run scaffold:module branches
 *   npm run scaffold:module inventory-items
 *
 * Generates:
 *   - db/schema/<module>.ts                    (Drizzle table)
 *   - modules/<module>/<module>.schema.ts      (Zod schemas)
 *   - modules/<module>/<module>.service.ts     (Service layer)
 *   - modules/<module>/<module>.actions.ts     (Server Actions)
 *   - modules/<module>/<module>.schema.test.ts (Schema tests)
 *   - modules/<module>/<module>.service.test.ts (Service tests + 4 isolation tests)
 *   - modules/<module>/components/<Module>List.tsx
 *   - modules/<module>/components/Create<Module>Form.tsx
 *   - app/(dashboard)/<module>/page.tsx         (List page)
 *
 * Updates:
 *   - db/schema/index.ts                       (Adds export)
 *   - components/layout/Sidebar.tsx            (Adds nav link)
 *
 * After running: npm run db:generate && npm run db:migrate
 */

import { mkdirSync, writeFileSync, existsSync, readFileSync } from 'fs'
import { join } from 'path'

// ─── Name normalization ──────────────────────────────────────────────

interface ModuleNames {
  /** kebab-case, plural — e.g. 'inventory-items' */
  kebab:    string
  /** kebab-case, singular — e.g. 'inventory-item' */
  kebabSingular: string
  /** camelCase, plural — used for table/service names — e.g. 'inventoryItems' */
  camel:    string
  /** camelCase, singular — e.g. 'inventoryItem' */
  camelSingular: string
  /** PascalCase, singular — e.g. 'InventoryItem' */
  pascal:   string
  /** PascalCase, plural — e.g. 'InventoryItems' */
  pascalPlural: string
  /** snake_case, plural — used for DB column references e.g. 'inventory_items' */
  snake:    string
  /** Human-readable singular for UI text — 'Inventory item' */
  humanSingular: string
  /** Human-readable plural — 'Inventory items' */
  humanPlural:   string
}

/** Crude singularization — strip 's' or 'es'. Override for irregular words below. */
const IRREGULAR_SINGULARS: Record<string, string> = {
  'inventory':  'inventory-item', // example of irregular handling
  'people':     'person',
  'children':   'child',
  'series':     'series',
}

function singularize(word: string): string {
  if (IRREGULAR_SINGULARS[word]) return IRREGULAR_SINGULARS[word]
  if (word.endsWith('ies'))      return word.slice(0, -3) + 'y'
  if (word.endsWith('es') && (word.endsWith('ses') || word.endsWith('xes'))) return word.slice(0, -2)
  if (word.endsWith('s'))        return word.slice(0, -1)
  return word
}

function kebabToCamel(s: string): string {
  return s.replace(/-([a-z])/g, (_, c) => c.toUpperCase())
}

function kebabToPascal(s: string): string {
  const camel = kebabToCamel(s)
  return camel.charAt(0).toUpperCase() + camel.slice(1)
}

function kebabToSnake(s: string): string {
  return s.replace(/-/g, '_')
}

function humanize(s: string): string {
  const words = s.split('-').join(' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function normalizeName(input: string): ModuleNames {
  const kebab = input.trim().toLowerCase()

  if (!/^[a-z][a-z0-9-]*$/.test(kebab)) {
    throw new Error(`Invalid module name "${input}". Use kebab-case lowercase letters, numbers, and hyphens.`)
  }

  const kebabSingular = singularize(kebab)

  return {
    kebab,
    kebabSingular,
    camel:         kebabToCamel(kebab),
    camelSingular: kebabToCamel(kebabSingular),
    pascal:        kebabToPascal(kebabSingular),
    pascalPlural:  kebabToPascal(kebab),
    snake:         kebabToSnake(kebab),
    humanSingular: humanize(kebabSingular),
    humanPlural:   humanize(kebab),
  }
}

// ─── Templates ──────────────────────────────────────────────────────

function dbSchemaTemplate(n: ModuleNames): string {
  return `import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core'

export const ${n.camel} = pgTable('${n.snake}', {
  id:        uuid('id').defaultRandom().primaryKey(),
  orgId:     uuid('org_id').notNull(),
  name:      text('name').notNull(),
  // Add your fields here
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export type ${n.pascal}    = typeof ${n.camel}.$inferSelect
export type New${n.pascal} = typeof ${n.camel}.$inferInsert
`
}

function moduleSchemaTemplate(n: ModuleNames): string {
  return `import { z } from 'zod'

// CREATE — what a caller provides to create a ${n.humanSingular.toLowerCase()}
export const create${n.pascal}Schema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  // Add your fields here — never include id, orgId, createdAt, updatedAt
})
export type Create${n.pascal}Input = z.infer<typeof create${n.pascal}Schema>

// UPDATE — partial updates, all fields optional
export const update${n.pascal}Schema = create${n.pascal}Schema.partial()
export type Update${n.pascal}Input = z.infer<typeof update${n.pascal}Schema>

// ID PARAM — for routes like /${n.kebab}/[${n.camelSingular}Id]
export const ${n.camelSingular}IdSchema = z.object({
  ${n.camelSingular}Id: z.string().uuid('Invalid ${n.humanSingular.toLowerCase()} ID'),
})
export type ${n.pascal}IdInput = z.infer<typeof ${n.camelSingular}IdSchema>

// LIST — pagination and filters
export const list${n.pascalPlural}Schema = z.object({
  search:   z.string().max(100).optional(),
  page:     z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(100).default(20),
})
export type List${n.pascalPlural}Input = z.infer<typeof list${n.pascalPlural}Schema>
`
}

function moduleServiceTemplate(n: ModuleNames): string {
  return `import { db } from '@/db'
import { ${n.camel} } from '@/db/schema'
import { and, eq, ilike, count } from 'drizzle-orm'
import { logger } from '@/lib/logger'
import { audit } from '@/lib/audit'
import type { CallerContext } from '@/lib/auth/caller-context'
import type {
  Create${n.pascal}Input,
  Update${n.pascal}Input,
  List${n.pascalPlural}Input,
} from './${n.kebab}.schema'

export const ${n.camelSingular}Service = {

  // ── READ ──────────────────────────────────────────────────────────

  async listByOrg({
    ctx,
    filters,
  }: {
    ctx:      CallerContext
    filters?: List${n.pascalPlural}Input
  }) {
    const page     = filters?.page     ?? 1
    const pageSize = filters?.pageSize ?? 20
    const offset   = (page - 1) * pageSize

    const whereClause = and(
      eq(${n.camel}.orgId, ctx.orgId),
      filters?.search ? ilike(${n.camel}.name, \`%\${filters.search}%\`) : undefined,
    )

    const [items, [{ total }]] = await Promise.all([
      db.select().from(${n.camel}).where(whereClause).limit(pageSize).offset(offset),
      db.select({ total: count() }).from(${n.camel}).where(whereClause),
    ])

    return {
      data: items,
      pagination: { page, pageSize, total, totalPages: Math.ceil(total / pageSize) },
    }
  },

  async getById({
    ${n.camelSingular}Id,
    ctx,
  }: {
    ${n.camelSingular}Id: string
    ctx:                  CallerContext
  }) {
    const result = await db
      .select()
      .from(${n.camel})
      .where(and(
        eq(${n.camel}.id,    ${n.camelSingular}Id),
        eq(${n.camel}.orgId, ctx.orgId)
      ))
      .limit(1)

    return result[0] ?? null
  },

  // ── WRITE ─────────────────────────────────────────────────────────

  async create({
    data,
    ctx,
  }: {
    data: Create${n.pascal}Input
    ctx:  CallerContext
  }) {
    const { orgId, userId } = ctx

    // Business rule: name must be unique within the org
    const existing = await db
      .select({ id: ${n.camel}.id })
      .from(${n.camel})
      .where(and(
        eq(${n.camel}.name,  data.name),
        eq(${n.camel}.orgId, orgId)
      ))
      .limit(1)

    if (existing.length > 0) {
      return { error: 'A ${n.humanSingular.toLowerCase()} with this name already exists' }
    }

    const [created] = await db
      .insert(${n.camel})
      .values({ ...data, orgId })
      .returning()

    logger.info('${n.kebabSingular}.created', { ${n.camelSingular}Id: created.id, orgId, userId })
    audit.record({ action: '${n.kebabSingular}.created', resourceId: created.id, ctx })

    return { data: created }
  },

  async update({
    ${n.camelSingular}Id,
    data,
    ctx,
  }: {
    ${n.camelSingular}Id: string
    data:                 Update${n.pascal}Input
    ctx:                  CallerContext
  }) {
    const { orgId, userId } = ctx

    // Fetch before write — confirms existence AND org ownership
    const existing = await db
      .select()
      .from(${n.camel})
      .where(and(
        eq(${n.camel}.id,    ${n.camelSingular}Id),
        eq(${n.camel}.orgId, orgId)
      ))
      .limit(1)

    if (!existing[0]) return { error: '${n.humanSingular} not found' }

    // Business rule: if renaming, confirm new name is not taken
    if (data.name && data.name !== existing[0].name) {
      const conflict = await db
        .select({ id: ${n.camel}.id })
        .from(${n.camel})
        .where(and(
          eq(${n.camel}.name,  data.name),
          eq(${n.camel}.orgId, orgId)
        ))
        .limit(1)

      if (conflict.length > 0) {
        return { error: 'A ${n.humanSingular.toLowerCase()} with this name already exists' }
      }
    }

    const [updated] = await db
      .update(${n.camel})
      .set({
        ...(data.name !== undefined && { name: data.name }),
        updatedAt: new Date(),
      })
      .where(and(
        eq(${n.camel}.id,    ${n.camelSingular}Id),
        eq(${n.camel}.orgId, orgId)
      ))
      .returning()

    logger.info('${n.kebabSingular}.updated', { ${n.camelSingular}Id, orgId, userId })
    audit.record({ action: '${n.kebabSingular}.updated', resourceId: ${n.camelSingular}Id, ctx })

    return { data: updated }
  },

  async delete({
    ${n.camelSingular}Id,
    ctx,
  }: {
    ${n.camelSingular}Id: string
    ctx:                  CallerContext
  }) {
    const { orgId, userId } = ctx

    const existing = await db
      .select()
      .from(${n.camel})
      .where(and(
        eq(${n.camel}.id,    ${n.camelSingular}Id),
        eq(${n.camel}.orgId, orgId)
      ))
      .limit(1)

    if (!existing[0]) return { error: '${n.humanSingular} not found' }

    await db
      .delete(${n.camel})
      .where(and(
        eq(${n.camel}.id,    ${n.camelSingular}Id),
        eq(${n.camel}.orgId, orgId)
      ))

    logger.info('${n.kebabSingular}.deleted', { ${n.camelSingular}Id, orgId, userId })
    audit.record({ action: '${n.kebabSingular}.deleted', resourceId: ${n.camelSingular}Id, ctx })

    return { data: { id: ${n.camelSingular}Id } }
  },
}
`
}

function moduleActionsTemplate(n: ModuleNames): string {
  return `'use server'

import {
  create${n.pascal}Schema,
  update${n.pascal}Schema,
  ${n.camelSingular}IdSchema,
  list${n.pascalPlural}Schema,
} from './${n.kebab}.schema'
import { ${n.camelSingular}Service } from './${n.kebab}.service'
import { requireOrgAccess, requirePermission } from '@/lib/auth/policy'
// import { PERMISSIONS } from '@/lib/auth/permissions'
// Uncomment and use specific permissions when RBAC is set up:
//   await requirePermission(PERMISSIONS.${n.camel}.create)

export async function create${n.pascal}Action(input: unknown) {
  const parsed = create${n.pascal}Schema.safeParse(input)
  if (!parsed.success) return { error: 'Invalid input', issues: parsed.error.issues }

  const ctx = await requireOrgAccess()

  return ${n.camelSingular}Service.create({ data: parsed.data, ctx })
}

export async function update${n.pascal}Action(${n.camelSingular}Id: unknown, body: unknown) {
  const parsedId   = ${n.camelSingular}IdSchema.safeParse({ ${n.camelSingular}Id })
  const parsedBody = update${n.pascal}Schema.safeParse(body)

  if (!parsedId.success || !parsedBody.success) {
    return { error: 'Invalid input' }
  }

  const ctx = await requireOrgAccess()

  return ${n.camelSingular}Service.update({
    ${n.camelSingular}Id: parsedId.data.${n.camelSingular}Id,
    data:                 parsedBody.data,
    ctx,
  })
}

export async function delete${n.pascal}Action(${n.camelSingular}Id: unknown) {
  const parsed = ${n.camelSingular}IdSchema.safeParse({ ${n.camelSingular}Id })
  if (!parsed.success) return { error: 'Invalid ID' }

  const ctx = await requireOrgAccess()

  return ${n.camelSingular}Service.delete({
    ${n.camelSingular}Id: parsed.data.${n.camelSingular}Id,
    ctx,
  })
}
`
}

function schemaTestTemplate(n: ModuleNames): string {
  return `import { describe, it, expect } from 'vitest'
import {
  create${n.pascal}Schema,
  update${n.pascal}Schema,
  ${n.camelSingular}IdSchema,
} from './${n.kebab}.schema'

describe('create${n.pascal}Schema', () => {
  it('accepts valid input', () => {
    const result = create${n.pascal}Schema.safeParse({ name: 'Valid name' })
    expect(result.success).toBe(true)
  })

  it('rejects missing name', () => {
    const result = create${n.pascal}Schema.safeParse({})
    expect(result.success).toBe(false)
  })

  it('rejects empty name', () => {
    const result = create${n.pascal}Schema.safeParse({ name: '' })
    expect(result.success).toBe(false)
  })

  it('rejects name over 100 characters', () => {
    const result = create${n.pascal}Schema.safeParse({ name: 'a'.repeat(101) })
    expect(result.success).toBe(false)
  })
})

describe('update${n.pascal}Schema', () => {
  it('accepts partial updates', () => {
    expect(update${n.pascal}Schema.safeParse({ name: 'New' }).success).toBe(true)
    expect(update${n.pascal}Schema.safeParse({}).success).toBe(true)
  })
})

describe('${n.camelSingular}IdSchema', () => {
  it('accepts valid UUID', () => {
    const result = ${n.camelSingular}IdSchema.safeParse({
      ${n.camelSingular}Id: '550e8400-e29b-41d4-a716-446655440000',
    })
    expect(result.success).toBe(true)
  })

  it('rejects non-UUID', () => {
    const result = ${n.camelSingular}IdSchema.safeParse({ ${n.camelSingular}Id: 'not-a-uuid' })
    expect(result.success).toBe(false)
  })
})
`
}

function serviceTestTemplate(n: ModuleNames): string {
  return `import { describe, it, expect, beforeEach } from 'vitest'
import { ${n.camelSingular}Service } from './${n.kebab}.service'
import { ${n.camel} } from '@/db/schema'
import { db } from '@/db'
import { makeOrgContext } from '@/tests/helpers/caller-context'

beforeEach(async () => {
  await db.delete(${n.camel})
})

describe('${n.camelSingular}Service.create', () => {
  it('creates and returns the record', async () => {
    const { ctx } = makeOrgContext()
    const result = await ${n.camelSingular}Service.create({
      data: { name: 'Test ${n.humanSingular}' },
      ctx,
    })
    expect(result.data).toBeDefined()
    expect(result.data?.name).toBe('Test ${n.humanSingular}')
  })

  it('returns error when name already exists in the org', async () => {
    const { ctx } = makeOrgContext()
    await ${n.camelSingular}Service.create({ data: { name: 'Same' }, ctx })
    const result = await ${n.camelSingular}Service.create({ data: { name: 'Same' }, ctx })
    expect(result.error).toMatch(/already exists/)
  })

  it('allows the same name in a different org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()
    await ${n.camelSingular}Service.create({ data: { name: 'Same' }, ctx: orgA.ctx })
    const result = await ${n.camelSingular}Service.create({ data: { name: 'Same' }, ctx: orgB.ctx })
    expect(result.data).toBeDefined()
  })
})

// ── The four required org isolation tests ──────────────────────────

describe('${n.camelSingular}Service — org isolation', () => {
  it('cannot fetch a record from another org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    const created = await ${n.camelSingular}Service.create({
      data: { name: 'Org A record' },
      ctx:  orgA.ctx,
    })

    const found = await ${n.camelSingular}Service.getById({
      ${n.camelSingular}Id: created.data!.id,
      ctx:                  orgB.ctx,
    })

    expect(found).toBeNull()
  })

  it('cannot update a record from another org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    const created = await ${n.camelSingular}Service.create({
      data: { name: 'Org A record' },
      ctx:  orgA.ctx,
    })

    const result = await ${n.camelSingular}Service.update({
      ${n.camelSingular}Id: created.data!.id,
      data:                 { name: 'Hijacked' },
      ctx:                  orgB.ctx,
    })

    expect(result.error).toBe('${n.humanSingular} not found')
  })

  it('cannot delete a record from another org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    const created = await ${n.camelSingular}Service.create({
      data: { name: 'Org A record' },
      ctx:  orgA.ctx,
    })

    const result = await ${n.camelSingular}Service.delete({
      ${n.camelSingular}Id: created.data!.id,
      ctx:                  orgB.ctx,
    })

    expect(result.error).toBe('${n.humanSingular} not found')
  })

  it('list returns only records from the requesting org', async () => {
    const orgA = makeOrgContext()
    const orgB = makeOrgContext()

    await ${n.camelSingular}Service.create({ data: { name: 'A1' }, ctx: orgA.ctx })
    await ${n.camelSingular}Service.create({ data: { name: 'A2' }, ctx: orgA.ctx })
    await ${n.camelSingular}Service.create({ data: { name: 'B1' }, ctx: orgB.ctx })

    const result = await ${n.camelSingular}Service.listByOrg({ ctx: orgA.ctx })

    expect(result.data).toHaveLength(2)
    expect(result.data.every(r => r.orgId === orgA.ctx.orgId)).toBe(true)
  })
})
`
}

function listComponentTemplate(n: ModuleNames): string {
  return `import type { ${n.pascal} } from '@/db/schema'

export function ${n.pascal}List({ ${n.camel} }: { ${n.camel}: ${n.pascal}[] }) {
  if (${n.camel}.length === 0) {
    return <p className="text-sm text-muted-foreground">No ${n.humanPlural.toLowerCase()} found.</p>
  }

  return (
    <ul className="divide-y border rounded">
      {${n.camel}.map((item) => (
        <li key={item.id} className="p-4 flex items-center justify-between">
          <span className="font-medium">{item.name}</span>
          <span className="text-xs text-muted-foreground">
            {new Date(item.createdAt).toLocaleDateString()}
          </span>
        </li>
      ))}
    </ul>
  )
}
`
}

function formComponentTemplate(n: ModuleNames): string {
  return `'use client'

import { useTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { create${n.pascal}Action } from '../${n.kebab}.actions'
import { toast } from '@/components/ui/use-toast'

export function Create${n.pascal}Form() {
  const [isPending, startTransition] = useTransition()

  function handleSubmit(formData: FormData) {
    const input = { name: formData.get('name') as string }

    startTransition(async () => {
      const result = await create${n.pascal}Action(input)
      if (result.error) {
        toast({ title: 'Error', description: result.error, variant: 'destructive' })
      } else {
        toast({ title: '${n.humanSingular} created' })
      }
    })
  }

  return (
    <form action={handleSubmit} className="space-y-4 max-w-md">
      <div className="space-y-1">
        <Label htmlFor="name">Name</Label>
        <Input id="name" name="name" required />
      </div>
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create ${n.humanSingular.toLowerCase()}'}
      </Button>
    </form>
  )
}
`
}

function pageTemplate(n: ModuleNames): string {
  return `import { ${n.camelSingular}Service } from '@/modules/${n.kebab}/${n.kebab}.service'
import { requireOrgAccess } from '@/lib/auth/policy'
import { ${n.pascal}List } from '@/modules/${n.kebab}/components/${n.pascal}List'
import { Create${n.pascal}Form } from '@/modules/${n.kebab}/components/Create${n.pascal}Form'

export default async function ${n.pascalPlural}Page() {
  const ctx = await requireOrgAccess()
  const result = await ${n.camelSingular}Service.listByOrg({ ctx })

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">${n.humanPlural}</h1>
        <p className="text-sm text-muted-foreground">
          Manage your ${n.humanPlural.toLowerCase()}.
        </p>
      </header>

      <section>
        <h2 className="text-sm font-medium mb-3">Add new</h2>
        <Create${n.pascal}Form />
      </section>

      <section>
        <h2 className="text-sm font-medium mb-3">All ${n.humanPlural.toLowerCase()}</h2>
        <${n.pascal}List ${n.camel}={result.data} />
      </section>
    </div>
  )
}
`
}

// ─── File operations ────────────────────────────────────────────────

interface FileSpec {
  path:    string
  content: string
}

function writeFiles(files: FileSpec[]): void {
  for (const file of files) {
    const dir = file.path.substring(0, file.path.lastIndexOf('/'))
    mkdirSync(dir, { recursive: true })
    writeFileSync(file.path, file.content)
    console.log(`  ✓ ${file.path}`)
  }
}

function checkNoConflicts(files: FileSpec[]): void {
  const conflicts = files.filter(f => existsSync(f.path))
  if (conflicts.length > 0) {
    console.error('❌ Cannot scaffold — files already exist:')
    conflicts.forEach(c => console.error(`   ${c.path}`))
    console.error('\nDelete or rename these files and try again.')
    process.exit(1)
  }
}

function updateSchemaIndex(n: ModuleNames): void {
  const path    = 'db/schema/index.ts'
  if (!existsSync(path)) {
    console.warn(`  ⚠ ${path} not found — add 'export * from "./${n.kebab}"' manually`)
    return
  }

  const content  = readFileSync(path, 'utf-8')
  const exportLine = `export * from './${n.kebab}'`

  if (content.includes(exportLine)) {
    console.log(`  ⚪ ${path} (already has export)`)
    return
  }

  // Insert before the scaffold:export anchor, or at the end
  const updated = content.includes('// scaffold:export')
    ? content.replace('// scaffold:export', `${exportLine}\n// scaffold:export`)
    : content + `\n${exportLine}\n`

  writeFileSync(path, updated)
  console.log(`  ✓ ${path} (added export)`)
}

function updateSidebar(n: ModuleNames): void {
  const path = 'components/layout/Sidebar.tsx'
  if (!existsSync(path)) {
    console.warn(`  ⚠ ${path} not found — add nav link manually`)
    return
  }

  const content = readFileSync(path, 'utf-8')
  const navLine = `        <li><Link href="/${n.kebab}" className="block px-3 py-2 rounded hover:bg-accent">${n.humanPlural}</Link></li>`

  if (content.includes(`href="/${n.kebab}"`)) {
    console.log(`  ⚪ ${path} (nav link exists)`)
    return
  }

  if (!content.includes('// scaffold:nav')) {
    console.warn(`  ⚠ ${path} has no // scaffold:nav anchor — add nav link manually`)
    return
  }

  const updated = content.replace('{/* scaffold:nav', `${navLine}\n        {/* scaffold:nav`)
  writeFileSync(path, updated)
  console.log(`  ✓ ${path} (added nav link)`)
}

// ─── Main ───────────────────────────────────────────────────────────

function main(): void {
  const arg = process.argv[2]

  if (!arg) {
    console.error('Usage: npm run scaffold:module <module-name>')
    console.error('Example: npm run scaffold:module branches')
    process.exit(1)
  }

  let names: ModuleNames
  try {
    names = normalizeName(arg)
  } catch (err: any) {
    console.error('❌', err.message)
    process.exit(1)
  }

  console.log(`\n📦 Scaffolding module: ${names.kebab}`)
  console.log(`   Singular: ${names.humanSingular}`)
  console.log(`   Plural:   ${names.humanPlural}\n`)

  const files: FileSpec[] = [
    { path: `db/schema/${names.kebab}.ts`,                                          content: dbSchemaTemplate(names) },
    { path: `modules/${names.kebab}/${names.kebab}.schema.ts`,                      content: moduleSchemaTemplate(names) },
    { path: `modules/${names.kebab}/${names.kebab}.service.ts`,                     content: moduleServiceTemplate(names) },
    { path: `modules/${names.kebab}/${names.kebab}.actions.ts`,                     content: moduleActionsTemplate(names) },
    { path: `modules/${names.kebab}/${names.kebab}.schema.test.ts`,                 content: schemaTestTemplate(names) },
    { path: `modules/${names.kebab}/${names.kebab}.service.test.ts`,                content: serviceTestTemplate(names) },
    { path: `modules/${names.kebab}/components/${names.pascal}List.tsx`,            content: listComponentTemplate(names) },
    { path: `modules/${names.kebab}/components/Create${names.pascal}Form.tsx`,      content: formComponentTemplate(names) },
    { path: `app/(dashboard)/${names.kebab}/page.tsx`,                              content: pageTemplate(names) },
  ]

  checkNoConflicts(files)

  console.log('Generating files:')
  writeFiles(files)

  console.log('\nUpdating shared files:')
  updateSchemaIndex(names)
  updateSidebar(names)

  console.log(`\n✅ Module "${names.kebab}" scaffolded successfully.\n`)
  console.log('Next steps:')
  console.log('  1. Review the generated files and adjust the table fields if needed')
  console.log('  2. Run: npm run db:generate')
  console.log('  3. Run: npm run db:migrate')
  console.log('  4. Run: npm test')
  console.log('  5. Run: npm run dev — visit http://localhost:3000/' + names.kebab + '\n')
}

main()
