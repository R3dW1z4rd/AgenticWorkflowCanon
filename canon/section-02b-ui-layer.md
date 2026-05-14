# Architecture Canon
## Section 2 — Supplement: How the UI Layer Is Built
*Version 2.0 | Last updated: April 2026*

---

This supplement expands the UI Layer entry in Section 2. It covers the core concepts every developer needs to understand before writing any interface code: what a component is, how layouts wrap pages, what props are, how data flows down, and how the UI connects to Server Actions.

---

### What a component is

A component is a TypeScript function that returns UI. That is all it is. You write a function, it returns some JSX (HTML-like syntax), and Next.js renders it on the screen.

```tsx
// The simplest possible component
export function BranchName({ name }: { name: string }) {
  return <h1>{name}</h1>
}
```

Every piece of the UI — a button, a table row, an entire page — is a component. Components can be nested inside each other. A page is a component that contains other components.

---

### The two types of component

Next.js App Router has two kinds of component. Understanding the difference is the most important concept in the UI layer.

#### Server Components (the default)

Every component in this architecture is a Server Component unless explicitly marked otherwise. Server Components run on the server before being sent to the browser. They can fetch data directly and they produce plain HTML.

```tsx
// app/(dashboard)/branches/page.tsx
// No 'use client' — this is a Server Component by default

import { branchService } from '@/features/branches/branches.service'
import { requireOrgAccess } from '@/lib/auth/policy'
import { BranchList } from './components/BranchList'

export default async function BranchesPage() {
  const { orgId } = await requireOrgAccess()
  const branches = await branchService.listByOrg({ orgId })

  return (
    <div>
      <h1>Branches</h1>
      <BranchList branches={branches} />
    </div>
  )
}
```

What to notice:
- The function is `async` — Server Components can `await` data directly
- Auth is checked at the top before anything else
- The service is called directly — no fetch, no API call needed
- Data is passed down to child components as props

#### Client Components

A Client Component runs in the browser. It can hold state, respond to user interactions, and use browser APIs. You mark it with `'use client'` at the top of the file.

```tsx
// features/branches/components/BranchSearchInput.tsx
'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'

export function BranchSearchInput({
  onSearch,
}: {
  onSearch: (query: string) => void
}) {
  const [value, setValue] = useState('')

  return (
    <Input
      value={value}
      onChange={(e) => {
        setValue(e.target.value)
        onSearch(e.target.value)
      }}
      placeholder="Search branches..."
    />
  )
}
```

What to notice:
- `'use client'` is on the very first line — this is the signal to Next.js
- `useState` is used — this is only possible in Client Components
- It receives `onSearch` as a prop — a function passed down from a parent

**When to use `'use client'`:**

| The component needs... | Use |
|---|---|
| `useState`, `useEffect`, or any other hook | Client Component |
| An `onClick`, `onChange`, or similar event handler | Client Component |
| Access to `window`, `localStorage`, or browser APIs | Client Component |
| To fetch data on load or display server-rendered content | Server Component |
| To call a service or read from the database | Server Component |

**The rule:** Keep as many components as possible as Server Components. Move to `'use client'` only when you genuinely need interactivity or browser APIs. A common pattern is to have a Server Component page that fetches data and passes it to a small Client Component that handles the interactive parts.

---

### Layouts — the children pattern

A layout is a component that wraps every page under a certain route. It receives the page as a special prop called `children`. You do not call `children` explicitly — Next.js passes it automatically.

```tsx
// app/layout.tsx — Root layout, wraps the entire application
import type { ReactNode } from 'react'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}
```

```tsx
// app/(dashboard)/layout.tsx — Dashboard layout, wraps all dashboard pages
import type { ReactNode } from 'react'
import { Sidebar } from '@/components/Sidebar'
import { requireOrgAccess } from '@/lib/auth/policy'

export default async function DashboardLayout({
  children,
}: {
  children: ReactNode
}) {
  await requireOrgAccess() // Protect the entire section

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>
    </div>
  )
}
```

**What is `{children}`?**

When a user visits `/branches`, Next.js renders the page like this:

```
RootLayout
  └── DashboardLayout
        ├── Sidebar
        └── {children} ← this slot is filled by BranchesPage
              └── BranchesPage
                    └── BranchList
```

The `children` prop is Next.js filling in whatever page matches the current URL. The layout does not know or care which page is inside it — it just renders its shell and puts `{children}` where the page content should appear.

**Why layouts matter for this architecture:**
- Auth checks that protect an entire section (like all dashboard pages) go in the layout — written once, applied everywhere
- Shared UI like sidebars, headers, and navigation live in layouts, not repeated in every page
- Layouts are Server Components, so they can fetch shared data (like the current user's org name) once for the whole section

---

### Pages

A page is the leaf of a route. It is the component that matches the URL. Every page lives in a file called `page.tsx` inside the `app/` directory.

```tsx
// app/(dashboard)/branches/[branchId]/page.tsx
// The [branchId] folder makes this a dynamic route
// The branchId value comes from the URL

import { branchService } from '@/features/branches/branches.service'
import { requireOrgAccess } from '@/lib/auth/policy'
import { BranchDetail } from '../components/BranchDetail'
import { notFound } from 'next/navigation'

export default async function BranchDetailPage({
  params,
}: {
  params: { branchId: string }
}) {
  const { orgId } = await requireOrgAccess()

  const branch = await branchService.getById({
    branchId: params.branchId,
    orgId,
  })

  if (!branch) notFound()

  return <BranchDetail branch={branch} />
}
```

What to notice:
- Pages receive `params` from the URL — `params.branchId` is the value from the `[branchId]` folder name
- Pages are async Server Components — they fetch data directly
- Auth is checked again even though the layout checked it — the page may need a more specific permission check
- The page's job is to fetch data and pass it to components. It renders as little markup as possible itself.

---

### Props — how data flows down through components

Props are how a parent component passes data to a child component. You define what props a component accepts using a TypeScript type or interface.

```tsx
// The Branch type comes from Drizzle — it describes a database row
import type { Branch } from '@/db/schema/branches'

// This component accepts an array of Branch objects as a prop
export function BranchList({ branches }: { branches: Branch[] }) {
  return (
    <ul>
      {branches.map((branch) => (
        <BranchCard key={branch.id} branch={branch} />
      ))}
    </ul>
  )
}

// This component accepts a single Branch object
export function BranchCard({ branch }: { branch: Branch }) {
  return (
    <li>
      <span>{branch.name}</span>
      <span>{branch.region}</span>
    </li>
  )
}
```

**The data flow pattern for this architecture:**

```
page.tsx (Server Component)
  → fetches data from the service
  → passes data as props to components
    → components render the data
      → if interaction is needed, a Client Component handles it
```

Data flows in one direction: down. A child component never fetches its own data unless there is a documented reason. Data fetching happens at the page level and flows down through props.

**TypeScript and props:** Every component's props must be typed. You get this for free when you use the types produced by Drizzle (`Branch`, `NewBranch`, etc.) or the types inferred from Zod schemas. Never use `any` for props.

---

### Using shadcn/ui components

shadcn/ui components are building blocks. You add them to your project once with the CLI and then own the code — they are in your `components/ui/` folder and you can modify them freely.

```tsx
// Using shadcn/ui components to build a branch form
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function BranchFormShell() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>New Branch</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="name">Branch name</Label>
            <Input id="name" name="name" placeholder="Downtown Office" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="region">Region</Label>
            <Input id="region" name="region" placeholder="North" />
          </div>
          <Button type="submit">Create branch</Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

**Resolution rule:** Before building any UI element from scratch, check if shadcn/ui has it. It covers buttons, inputs, dialogs, dropdowns, tables, toasts, cards, badges, and much more. Only build a custom component when shadcn/ui genuinely cannot meet the requirement.

**Adding a new shadcn/ui component:**
```bash
npx shadcn@latest add dialog
npx shadcn@latest add data-table
```

---

### Connecting the UI to a Server Action (the primary pattern)

This is the most important flow in the architecture — how a user fills out a form and triggers a mutation. Because 70% of this stack is action-heavy, this pattern appears constantly.

```tsx
// features/branches/components/CreateBranchForm.tsx
'use client'

import { useTransition } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { createBranchAction } from '../branches.actions'
import { toast } from '@/components/ui/use-toast'

export function CreateBranchForm() {
  const [isPending, startTransition] = useTransition()

  function handleSubmit(formData: FormData) {
    const input = {
      name: formData.get('name') as string,
      region: formData.get('region') as string,
    }

    startTransition(async () => {
      const result = await createBranchAction(input)

      if (result.error) {
        toast({ title: 'Error', description: result.error, variant: 'destructive' })
        return
      }

      toast({ title: 'Branch created' })
    })
  }

  return (
    <form action={handleSubmit}>
      <div className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="name">Branch name</Label>
          <Input id="name" name="name" required />
        </div>
        <div className="space-y-1">
          <Label htmlFor="region">Region</Label>
          <Input id="region" name="region" required />
        </div>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Creating...' : 'Create branch'}
        </Button>
      </div>
    </form>
  )
}
```

**What is happening here:**

1. The form is a Client Component (`'use client'`) because it needs to handle submission state
2. `useTransition` gives us `isPending` — a boolean that is `true` while the Server Action is running. We use it to disable the button and show a loading state.
3. `handleSubmit` reads the form data, constructs the input object, and calls the Server Action
4. The Server Action (`createBranchAction`) runs on the server — it validates, checks auth, calls the service. The client never touches the database.
5. The result comes back and we show a toast notification

**The complete picture — one full flow:**

```
User fills out form
  → clicks "Create branch"
    → handleSubmit reads form values
      → calls createBranchAction(input) [crosses to server]
        → Zod validates the input
          → requireOrgAccess() checks auth and extracts orgId
            → branchService.create({ data, orgId, userId })
              → Drizzle inserts the row into PostgreSQL
            → service returns the new branch
          → action returns { data: branch }
        → Client receives the result
      → toast notification shown
    → UI updates
```

Every step has one job. Nothing is skipped. Nothing is duplicated.

---

### The component decision tree

When you need to build something, ask these questions in order:

```
1. Does it need state, hooks, or event handlers?
   YES → Client Component ('use client')
   NO  → Server Component (default, no directive needed)

2. Does it wrap a section of the app with shared UI?
   YES → Layout (layout.tsx)
   NO  → Continue

3. Does it match a URL route?
   YES → Page (page.tsx) — fetch data here, pass as props
   NO  → Component — receive data as props, render UI

4. Does shadcn/ui already have this component?
   YES → Use it from @/components/ui/
   NO  → Build it in features/[feature]/components/ or components/
```

---

### Rules for the UI layer

These are not suggestions — they are the invariants that keep the architecture clean.

1. **Pages fetch, components render.** A page fetches data from a service and passes it as props. Components render what they receive. A component that calls a service directly is a violation.

2. **Auth in pages and layouts, not components.** The auth check happens once in the layout (for section-level protection) and once in the page (for specific permission needs). Not inside individual components.

3. **Client Components are as small as possible.** If only a button needs interactivity, only the button is a Client Component. The surrounding card, title, and layout remain as Server Components. This is called "pushing the client boundary down."

4. **No business logic in components.** A component formats and displays. If it needs to compute something from the data, that computation belongs in the service, not in `useMemo` inside a component.

5. **Props are typed.** Every component's props interface is explicit TypeScript. No `any`, no untyped props objects.

---

### How to use this document

- **Developers:** Read this before writing any component. When you are unsure whether something should be a Server or Client Component, use the decision tree above. When you are unsure where data fetching belongs, the answer is: in the page, passed down as props.
- **Agents:** When generating UI code, default to Server Components. Only add `'use client'` when the component explicitly requires hooks or event handlers. All data fetching must happen in `page.tsx` and be passed to child components as props. Never generate a component that calls a service directly.

---

*Part of Section 2 — Stack*
*Next: Section 3 — Folder & File Structure*
