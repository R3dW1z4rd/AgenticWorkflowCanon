# Data Dictionary — Reference Guide
> Agent reference file. Use this as the template and rules when writing data dictionaries to workspace/.

## File naming
`workspace/[project-slug]/02-data-dictionary.md`
One file per project. All modules share the same dictionary — use entity grouping to separate them.

## Status header
```
## Status: In Progress 🔄  |  Last updated: YYYY-MM-DD
```

---

## Column Definitions

| Column | Description |
|--------|-------------|
| **Entity** | The object this field belongs to. e.g. `contract`, `user`, `referral` |
| **field_name** | Database column / internal class name. Always **snake_case**. e.g. `contract_start_date` |
| **fieldName** | JavaScript / API field name. Always **camelCase**. e.g. `contractStartDate` |
| **Display Label** | The label shown to the user in the UI. e.g. `Contract Start Date` |
| **Type** | One of: `string` `integer` `decimal` `boolean` `date` `datetime` `enum` `reference` `file` `json` |
| **Required** | `Yes` / `No` / `Conditional` — if Conditional, document the condition in Validation Rules |
| **Validation Rules** | Constraints on the value. e.g. `Must not be in the past` / `Max 255 chars` / `0–100` |
| **Default** | Default value if not supplied. e.g. `null` / `Today` / `false` / `[]` |
| **Source** | `user_input` / `system_generated` / `integration` / `derived` |
| **Integration / Module Ref** | If source = `integration`: name the API and refresh behavior. If source = `derived`: name the source module and field |
| **Enum Values** | If type = `enum`: list all allowed values separated by ` · ` |
| **Used In** | Which screens or views use this field. e.g. `Create Form · Detail View · List` |
| **Sensitive / PII** | **MANDATORY**. `Yes` / `No`. Mark `Yes` for: personal identifiers (email, phone, full name in some jurisdictions), financial data (commission rates, salaries, bank accounts), health data, government IDs, location data, and any field whose unauthorized disclosure would harm the user, customer, or business. When `Yes`, populate the **Restricted To** column. |
| **Restricted To** | When Sensitive/PII = Yes, list the role names or permission strings that may read/write this field. e.g. `Account Manager, Finance` or `contracts:viewCommission`. Empty when Sensitive/PII = No. |
| **Notes** | Extra context, business rules, open questions, or cross-module dependencies |

---

## Naming Convention Rules

- **DB and internal classes:** always `snake_case` → `contract_start_date`, `account_manager_id`
- **JavaScript and API:** always `camelCase` → `contractStartDate`, `accountManagerId`
- Both columns must be filled for every field — no exceptions
- Entity names are singular and lowercase: `contract` not `contracts`, `user` not `users`
- Foreign key fields end in `_id`: `account_manager_id`, `referral_id`
- Boolean fields start with `is_` or `has_`: `is_active`, `has_referral`
- Timestamp fields end in `_at`: `created_at`, `updated_at`, `approved_at`

---

## Source Types — Rules

### user_input
Value is entered directly by a user in a form or UI control.
No special documentation required beyond validation rules.

### system_generated
Value is created automatically by the system.
Always document: what generates it and when.
Examples: `contract_id` (UUID on creation), `created_at` (timestamp on insert), `status` (set by workflow)

### integration
Value is fetched from a third-party API or external service.
**Must document:**
- The name of the API or service
- How often the value is refreshed (on load / every N seconds / daily / on-demand)
- What happens if the source is unavailable (error state, cached value, block submission?)
- The field that stores the fetch timestamp (always required alongside the value)

Example:
```
exchange_rate     | integration | Forex API — refreshed every 30s
exchange_rate_at  | system_generated | Timestamp of last successful Forex API fetch
```

### derived
Value is computed from another field or module.
**Must document:**
- The source module and field_name it is derived from
- The computation logic (if non-trivial)

Example:
```
referral_type | derived | Inherited from contract.referral_type
total_amount  | derived | Calculated: unit_price × quantity, updated on save
```

---

## Type Reference

| Type | Use for | Notes |
|------|---------|-------|
| `string` | Text values | Specify max length in Validation Rules |
| `integer` | Whole numbers | Specify min/max if relevant |
| `decimal` | Prices, rates, percentages | Specify decimal places in Validation Rules |
| `boolean` | True/false flags | Default should always be specified |
| `date` | Calendar dates without time | Format: YYYY-MM-DD |
| `datetime` | Timestamps with time | Store as UTC, display in user's locale |
| `enum` | Fixed set of allowed values | List all values in Enum Values column |
| `reference` | Foreign key to another entity | Note the target entity and field in Integration/Module Ref |
| `file` | File attachments | Note allowed types and size limits in Validation |
| `json` | Arrays or nested objects | Describe the expected shape in Notes |

---

## Template

```markdown
# Data Dictionary — [Project Name]
Last updated: YYYY-MM-DD

---

## Entity: [entity_name]

| field_name | fieldName | Display Label | Type | Required | Validation Rules | Default | Source | Integration / Module Ref | Enum Values | Used In | Sensitive / PII | Restricted To | Notes |
|------------|-----------|---------------|------|----------|-----------------|---------|--------|--------------------------|-------------|---------|-----------------|---------------|-------|
| entity_id | entityId | — | string | Yes | UUID v4, auto-generated | UUID v4 | system_generated | | | All views | No | | Primary key — never shown to end user |
| created_at | createdAt | — | datetime | Yes | | now() | system_generated | | | — | No | | Set on insert, never updated |
| updated_at | updatedAt | — | datetime | Yes | | now() | system_generated | | | — | No | | Updated on every write |

---

## Entity: [next_entity_name]
...
```

---

## Security Boundaries — when to flag a field

A field is **Sensitive / PII = Yes** when at least one of these is true:

- **Personal identifier:** full name, email, phone, government ID, date of birth in jurisdictions that classify it
- **Financial data:** salary, commission rate, bank account, transaction amount, credit card last-4
- **Health / medical:** diagnoses, medications, appointments, biometric measurements
- **Location data:** home address, GPS coordinates, IP at the time of action
- **Behavioral signals:** browsing history, search queries, message content
- **Authentication:** passwords (never stored in plain), security questions, recovery codes, session tokens
- **Business confidential:** internal pricing strategy, supplier costs, unsigned contracts, any field whose disclosure to a competitor would cause harm

When in doubt, flag it. The Restricted To column then names the roles or permission strings that gate access.

**Common patterns by org_context:**

| `org_context.type` | Typical sensitive fields | Typical Restricted To |
|---|---|---|
| org-only | Salaries, performance reviews, internal contracts | HR, Finance, Manager |
| org-with-units | Branch P&L, inter-branch commissions, regional targets | Branch Manager, Regional Manager, Finance |
| customer-account | All customer PII (email, address, payment), billing data | Account-owner, customer-support (read-only) |

---

## Discovery Questions to Derive the Data Model

Use these to extract fields from the user during Phase 3:

**Front-end first:**
- "Walk me through the creation form for this module. What fields does the user fill in?"
- "What does the user see when they open the detail view of this record?"
- "What columns appear in the list view?"

**Backend expansion:**
- "For [field], what type of value is that — text, a number, a date, a choice from a list?"
- "Is [field] entered by the user or does the system generate it?"
- "Can [field] have more than one value? Could it be an array?"
- "Does [field] point to something else — like another record in the system?"

**Integration probing:**
- "Where does [field] come from? Is it entered manually or pulled from somewhere?"
- "If it comes from [external source] — how often is it updated? What shows if the source fails?"

**Catalog discovery:**
- "You mentioned [field] has different types. What are all the possible types?"
- "Are those types fixed, or can an admin add new ones?"
- "Does the type change what other fields are required?" (conditional fields)
