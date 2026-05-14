# Permission Extraction Guideline
*How to convert natural-language access rules from discovery into structured permission strings the canon's RBAC system understands.*

---

## What this document is for

During discovery, clients express access rules in natural language:
- *"Only Account Managers can create contracts"*
- *"Finance and Branch Managers can review commissions"*
- *"Customers can only edit their own records"*

The canon's RBAC system (see `guidelines/rbac.md`) requires structured permission strings:
- `contracts:create`
- `contracts:viewCommission`
- `customers:editOwn`

This guideline is the bridge. Use it during Phase 2 (Module Definition) and Phase 3 (Acceptance Criteria) to convert what the client said into what the code will enforce.

---

## The permission string format

```
[module-slug]:[action]
```

**Rules:**
- `module-slug` matches the module's kebab-case slug exactly (`contracts`, `customer-management`, `inventory-items`)
- `action` is lowercase camelCase, describes the operation (not the role)
- No nested colons, no spaces, no underscores in the action

**Standard actions** (use these by default):

| Action | Meaning |
|---|---|
| `create` | Add a new record |
| `read` | View a record (use only when read access is restricted; default reads need no permission) |
| `update` | Modify an existing record |
| `delete` | Remove a record |
| `list` | View the collection (when listing is restricted beyond read) |
| `approve` | Move a record forward in a workflow |
| `reject` | Block or reverse a workflow step |
| `export` | Download data |
| `import` | Upload data in bulk |
| `archive` | Soft-disable without deleting |

**Field-scoped actions** (when restriction is at the field level, not the record level):

| Action | Format | Example |
|---|---|---|
| View a sensitive field | `viewFieldName` | `contracts:viewCommissionRate` |
| Edit a sensitive field | `editFieldName` | `contracts:editApprovedAmount` |

**Ownership-scoped actions** (when "own" vs "any" matters):

| Action | Format | Example |
|---|---|---|
| Modify own record | `updateOwn` | `customers:updateOwn` |
| Modify any record | `updateAny` | `customers:updateAny` |

When the rule is "users can edit their own profile but only admins can edit anyone's," that becomes two permissions: `users:updateOwn` (everyone) and `users:updateAny` (admin only).

---

## The extraction process

### Step 1 — Read every "The system must…" outcome

The desired outcomes in the module card are the primary source of permissions. Re-read each one and ask: *does this outcome involve a role distinction?*

| Outcome | Role distinction? |
|---|---|
| "The system must allow AMs to create contracts" | Yes — AM only |
| "The system must reject Start Date in the past" | No — universal validation |
| "The system must show commission rate to AM and Finance" | Yes — AM, Finance only |
| "The system must auto-generate the contract ID" | No — system action |

If yes, that outcome produces a permission. If no, it doesn't.

### Step 2 — Read every Sensitive/PII field's Restricted To column

The data dictionary's Restricted To column is the secondary source. Each unique value there produces a permission.

```
field:        commission_rate
Restricted To: Account Manager, Finance
              ──────────────────┬────────
                                ▼
            Permission:  contracts:viewCommissionRate
            Default roles:  Account Manager, Finance
```

### Step 3 — Map each rule to a single permission

Aim for one permission per distinct access rule, not one per role.

**Wrong (too granular):**
```
contracts:createByAccountManager
contracts:createByAdmin
```

**Right (one permission, multiple roles):**
```
contracts:create  →  Account Manager, Admin
```

The role-to-permission mapping happens at runtime through the RBAC system. The permission string itself does not encode the role.

### Step 4 — Write the permission table on the module card

Section 6b of the module card has the canonical permission table. Fill it for every module. The default roles column is a starting point; the actual role assignment happens during BetterAuth org seeding.

---

## Patterns by org_context type

The `org_context.type` from discovery shapes which permissions are typical:

### org-only

Internal tool, single tenant. Permissions are role-based within the org.

```
[module]:create        → typical: Manager, Admin
[module]:approve       → typical: Manager (with department scope)
[module]:export        → typical: Admin only
```

### org-with-units

Multi-branch / multi-region. Add unit-scoped variants for cross-unit operations.

```
[module]:create              → Branch Manager, Admin (within own unit)
[module]:viewCrossUnit       → Regional Manager, Admin (across all units)
[module]:approveCrossUnit    → Admin only (highest-privilege operation)
```

The `:viewCrossUnit` and similar suffixes are how the canon expresses unit-hierarchy restrictions.

### customer-account

Per-customer accounts. Most operations are owner-scoped.

```
[module]:updateOwn            → Account-owner (default for all customers)
[module]:viewAny              → CustomerSupport, Admin (back-office)
[module]:updateAny            → Admin only
[module]:exportOwn            → Account-owner
[module]:exportAny            → Admin only
```

The `:Own` / `:Any` distinction is the customer-account pattern's signature.

---

## Worked example — Contract Creation

Source material from discovery:

> *"Account Managers create contracts. Finance reviews commission rates. The commission rate field should only be visible to AMs and Finance — sales reps shouldn't see it. Admins can do everything. Once a contract is approved, it can only be cancelled by Finance or Admin."*

Mapping each clause:

| Clause | Permission | Default roles |
|---|---|---|
| "AMs create contracts" | `contracts:create` | Account Manager, Admin |
| "Finance reviews commission rates" | `contracts:approveCommission` | Finance, Admin |
| "Commission rate visible to AMs and Finance" | `contracts:viewCommissionRate` | Account Manager, Finance, Admin |
| "Approved contracts cancellable only by Finance or Admin" | `contracts:cancelApproved` | Finance, Admin |
| "Admins can do everything" | (implicit — admin has all module permissions) | Admin |

The permission table on the module card:

```markdown
## 6b. Permissions

| # | Natural-language rule | Permission string | Default roles |
|---|-----------------------|-------------------|---------------|
| 1 | AMs create contracts | `contracts:create` | Account Manager, Admin |
| 2 | Finance reviews commission rates | `contracts:approveCommission` | Finance, Admin |
| 3 | Commission rate visible to AM and Finance | `contracts:viewCommissionRate` | Account Manager, Finance, Admin |
| 4 | Approved contracts cancellable only by Finance/Admin | `contracts:cancelApproved` | Finance, Admin |
```

These same strings appear in:
- The data dictionary's Restricted To column for `commission_rate`
- The Acceptance Criteria's Permission column for the relevant ACs
- The behavioral specs' SB-2 (missing permission) scenarios
- The canon's `lib/auth/permissions.ts` PERMISSIONS enum at implementation time (Phase 5)

The same string crossing all four artifacts is what makes the workflow traceable end-to-end.

---

## Anti-patterns — do not do these

**Roles in permission strings:**
```
❌  contracts:createByAccountManager
✅  contracts:create  (with default role: Account Manager)
```

**Module name mismatch:**
```
❌  contract-creation:create   (module slug is `contracts`, not `contract-creation`)
✅  contracts:create
```

**Generic verbs that lose meaning:**
```
❌  contracts:do
✅  contracts:approve
```

**Snake_case or kebab-case in actions:**
```
❌  contracts:view_commission_rate
❌  contracts:view-commission-rate
✅  contracts:viewCommissionRate
```

**Permissions for universal operations:**
```
❌  contracts:read   (when everyone with module access can read)
✅  (no permission needed)  (use `requireOrgAccess` instead of `requirePermission`)
```

The canon's auth model uses `requireOrgAccess` for "any authenticated org member can do this" and `requirePermission` for "only specific roles can do this." If everyone in the org can do an operation, it does not need a permission string.

---

## When to add a permission vs not

Ask this question for every action:

> *"If a regular member of the org performs this action, is the system supposed to allow it?"*

- **Yes, always allow** → no permission needed (`requireOrgAccess` is sufficient)
- **Only some members** → permission needed (`requirePermission(PERMISSIONS.module.action)`)
- **Different rules per ownership of the record** → ownership-scoped permission (`updateOwn` vs `updateAny`)

A common mistake is to add permissions defensively ("we might want to restrict this later"). Don't. Add permissions only for actual restrictions identified in discovery. Adding a permission later is a small change; removing one once roles depend on it is much harder.

---

## How agents use this

The discovery agent uses this guideline during Phase 2 (Module Definition) when filling Section 6b of the module card. The agent walks through the steps above with the BA, generating each permission string and confirming it matches the natural-language rule.

The Schema & Contracts agent (Phase 5) reads SPEC.md's permission tables and emits matching entries into `lib/auth/permissions.ts` per the canon's RBAC pattern.

The Test agent (Phase 6) reads the same permission tables to generate the SB-2 (missing permission) scenarios in the behavioral test specs.

Same strings, same source of truth, four agents reading the same data.

---

*Companion documents:*
*- `guidelines/rbac.md` (in canon) — full RBAC implementation*
*- `module-definition-card.md` — where the permission table lives during discovery*
*- `behavioral-test-spec-template.md` — where SB-2 scenarios are written*
