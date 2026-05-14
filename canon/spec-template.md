# SPEC.md Template & Structure
*The structural definition of the consolidated spec. This is what `generate_spec.py` produces and what coding agents consume.*

---

## What SPEC.md is

`SPEC.md` is the consolidated, agent-consumable specification for an entire project. It is generated from the five discovery artifacts (`00-discovery-notes.md`, `01-module-X.md`, `02-data-dictionary.md`, `03-acceptance-criteria.md`, `04-behavioral-test-specs.md`) by the `generate_spec.py` script.

It is the **single source of truth** that crosses the handoff between discovery (Codex) and coding (Claude Code). Once signed off in Phase 4, it is copied into the project repo at `docs/specs/SPEC.md` and tagged in git. Coding agents reference the tagged version, not the discovery workspace.

**Audience:**
- Implementation agents need the complete picture in one document
- Tech leads use it as the review artifact
- Future BAs reading it as part of an "update spec" workflow

It is not the only document — the five source artifacts remain as the human-readable working files in the discovery workspace. SPEC.md is the agent contract.

---

## Structure

The document has **seven required sections** in this exact order:

```
1. Header & Sign-offs       — version, dates, who approved
2. Project Overview          — what this is, who it's for
3. Organizational Context    — org_context block, the foundational decision
4. System Map                — actors, integrations, core flow
5. Module Index              — table of contents with status
6. Modules                   — one detailed section per module
7. Cross-Module Relationships — data and operations crossing module boundaries
```

Each section has a defined structure that the generator script follows exactly. Coding agents read these sections in this order.

---

## Section 1 — Header & Sign-offs

The first thing in the document. Establishes version, project identity, and approvals.

```markdown
# SPEC — [Project Name]
*Project slug: `[project-slug]` | Version: [v1.0] | Status: [Approved | Draft | Under Review]*

## Sign-offs

| Role | Name | Date | Status |
|---|---|---|---|
| Business Analyst | [Name] | [YYYY-MM-DD] | ✅ Approved |
| Designer | [Name] | [YYYY-MM-DD] | ✅ Approved |
| Dev Lead | [Name] | [YYYY-MM-DD] | ✅ Approved |

## Version History

| Version | Date | Summary | Generated from |
|---|---|---|---|
| v1.0 | [YYYY-MM-DD] | Initial spec | discovery workspace at [commit] |
```

The Phase 4 gate cannot be passed without all three sign-offs filled. The script writes the table; humans fill the names, dates, and status.

---

## Section 2 — Project Overview

A 1–2 paragraph summary of what the project is, who it's for, and what it solves. Aggregated from `00-discovery-notes.md`'s Discovery Summary block.

```markdown
## Project Overview

**Problem:** [The problem this system solves, in one sentence]

**Users:** [Primary actors / personas]

**Solution:** [What the system does, in one paragraph]

**Business model:** [How value is generated — relevant for customer-facing apps]

**Success criteria:** [What "this worked" looks like in 3 months]
```

This section is always short. It exists to give an agent the project context in 30 seconds.

---

## Section 3 — Organizational Context

The single most important architectural decision from discovery. Drives the data model, auth model, and isolation rules for every module.

```markdown
## Organizational Context

**Pattern:** `org-only` | `org-with-units` | `customer-account`

**Description:**
[Brief paragraph explaining how data ownership is structured for this project]

### Structured definition

\`\`\`yaml
org_context:
  type: org-with-units
  notes: |
    Brief description of how the user expressed it
  hierarchy: |
    region → branch → store
  user_assignment: |
    Each user belongs to exactly one branch.
    Regional managers can see all branches in their region.
\`\`\`

### Implications for the architecture

- Every entity in the data model has an `orgId` column.
- [If org-with-units]: Some entities also have an `orgUnitId` column for branch/region scoping.
- [If customer-account]: Each customer's data is fully isolated; no cross-account queries except through admin tools.
- The Auth model uses BetterAuth's organization plugin (with org units modeled as data per Section 6 + RBAC guideline).
```

This section is non-negotiable. The Phase 4 gate fails if `org_context.type` is not one of the three values.

---

## Section 4 — System Map

A high-level view of who interacts with the system and how it connects to the outside world. Aggregated from `00-discovery-notes.md` actors section + `02-data-dictionary.md` integrations.

```markdown
## System Map

### Actors

| Role | Side | Actions | Visibility |
|---|---|---|---|
| Account Manager | Internal | Create / edit / submit contracts | All fields except commission rate |
| Finance | Internal | Review commission rates | All fields |
| Customer | External | View own account, request changes | Own data only |

### Core business loop

The single most important process this system supports:

[Trigger] → [Step 1] → [Step 2] → [Decision?] → [Outcome]

Example: Customer requests contract → AM drafts → Finance reviews → AM submits → Active

### External integrations

| System / Service | Purpose | Direction | Auth |
|---|---|---|---|
| Forex API | Exchange rate lookup | Inbound (read) | Public, refresh every 30s |
| Stripe | Payment processing | Outbound | API key in vault |

### Internal integrations

| System | Purpose | Direction |
|---|---|---|
| (Existing CRM) | Pull customer records | Inbound, sync nightly |
```

This section answers "who and what touches this system" without yet going into module detail.

---

## Section 5 — Module Index

The table of contents. Every module identified in discovery, with priority and status.

```markdown
## Module Index

| # | Module | Slug | Priority | Status | LOC estimate |
|---|---|---|---|---|---|
| 5.1 | Contract Creation | `contract-creation` | Must | 🟢 Specified | 800 |
| 5.2 | Contract Review | `contract-review` | Must | 🟢 Specified | 600 |
| 5.3 | Customer Management | `customer-management` | Should | 🟢 Specified | 1200 |
| 5.4 | Reporting Dashboard | `reporting-dashboard` | Could | 🟡 Partial | TBD |

**Status legend:**
- 🟢 Specified — module fully defined, ready for implementation
- 🟡 Partial — module defined but has open questions
- 🔴 Blocked — module cannot proceed without external decision

**Priority legend:**
- Must — required for v1.0 launch
- Should — important but not blocking launch
- Could — nice to have, may defer to v1.1+
```

The numbered references (5.1, 5.2) are the section numbers within Section 6 — Modules. This makes navigation predictable.

---

## Section 6 — Modules

The longest section. One detailed sub-section per module. Each follows the same structure exactly.

### Per-module structure

```markdown
## 6.1 Contract Creation

*Module slug: `contract-creation` | Priority: Must | AC range: AC-001 to AC-018*

### 6.1.1 Business purpose

[Aggregated from 01-module-contract-creation.md, section "Business Purpose"]

Allows Account Managers to create and manage contracts with clients. Without
this module, contracts are tracked in spreadsheets, creating version conflicts
and audit risk.

### 6.1.2 Actors

| Role | Actions | What they see |
|---|---|---|
| Account Manager | Create, edit, submit contracts | All fields except commission rate (restricted to AM + Finance) |
| Finance | Review commission rates | Commission rate field visible |
| System | Auto-generate IDs, timestamps, audit log | — |

### 6.1.3 Entry & exit points

- **Entry:** User clicks "New Contract" from the Contracts list view
- **Pre-conditions:** User must be authenticated with Account Manager role
- **Exit:** Contract status changes to Active and notifications are sent
- **Post-conditions:** Contract is stored, audit log entry created, AM notified

### 6.1.4 Core flow

1. Account Manager clicks New Contract → system creates draft record
2. AM fills Step 1: Start Date, Account Manager, Contract Type
3. AM fills Step 2: exchange rate displayed from Forex API
4. AM adds referrals (0–5) with type and details
5. AM submits → system validates and changes status to Pending
6. System sends notification to AM, creates audit log entry

### 6.1.5 States & transitions

States: `draft` → `pending` → `active` → `expired` | `cancelled`

| From | To | Trigger | Actor |
|---|---|---|---|
| draft | pending | submit clicked | AM |
| pending | active | review approved | Finance |
| pending | draft | review rejected | Finance |
| active | expired | expiry date reached | System |
| any | cancelled | cancel clicked | AM, Finance |

### 6.1.6 Data dictionary (this module)

[Filtered from 02-data-dictionary.md — only the entities for this module]

#### Entity: Contract

| field_name | fieldName | Type | Required | Source | Sensitive | Validation |
|---|---|---|---|---|---|---|
| id | id | uuid | Yes | system_generated | No | — |
| start_date | startDate | date | Yes | user_input | No | not in past |
| account_manager_id | accountManagerId | uuid | Yes | user_input | No | must be active AM |
| referral_type | referralType | enum | No | user_input | No | one of: none, employee, external |
| exchange_rate | exchangeRate | decimal | Yes | integration | No | 4 decimal places, from Forex API |
| commission_rate | commissionRate | decimal | No | user_input | **Yes** | 0–100% |
| status | status | enum | Yes | system_generated | No | one of: draft, pending, active, expired, cancelled |

[For org-with-units patterns: include `org_id` and `org_unit_id` (orgId, orgUnitId)]
[For all patterns: include `created_at`, `updated_at` if relevant for the schema]

### 6.1.7 Acceptance criteria

[Filtered from 03-acceptance-criteria.md — only the ACs for this module]

| AC ID | Priority | The system must… | Permission | Behavior IDs |
|---|---|---|---|---|
| AC-001 | Must | Allow AM to create a new contract from the list view | `contracts:create` | B-001, B-002 |
| AC-002 | Must | Reject a past Start Date with an inline error | (none) | B-003 |
| AC-003 | Must | Display Forex exchange rate and refresh every 30 seconds | (none) | B-004, B-005 |
| AC-004 | Must | Enforce maximum of 5 referrals per contract | (none) | B-006 |
| AC-005 | Must | Restrict commission rate visibility to AM and Finance | `contracts:viewCommission` | B-007 |

### 6.1.8 Behavioral specs

[Filtered from 04-behavioral-test-specs.md — only the behaviors for this module]

#### B-001 [AC-001 happy path]
- **Layer:** e2e
- **Actor:** Account Manager
- **Setup:** AM is logged in, on the Contracts list view, has `contracts:create` permission
- **Action:** Click "New Contract" button
- **Expect:** Contract creation form is shown with Start Date and Account Manager pre-filled

#### B-002 [AC-001 failure / cross-org isolation]
- **Layer:** e2e
- **Actor:** Member from another org
- **Setup:** Member from org B is logged in, with a known contract ID belonging to org A
- **Action:** Navigate directly to /contracts/[orgA-contract-id]
- **Expect:** 404 Not Found is rendered (NOT "forbidden" — the resource appears to not exist)

[... continues for every behavior in this module ...]

### 6.1.9 Permissions required

| Permission string | Required by | Default roles |
|---|---|---|
| `contracts:create` | AC-001 | Account Manager, Admin |
| `contracts:viewCommission` | AC-005 | Account Manager, Finance, Admin |
| `contracts:approve` | AC-007 | Finance, Admin |
| `contracts:cancel` | AC-012 | Account Manager (own only), Finance, Admin |

### 6.1.10 Out of scope

Contract renewal, payment processing, and document signing are not in this module.
- Contract renewal → `contract-renewal` module (v2.0+)
- Payment processing → external Stripe integration, separate module
- Document signing → external DocuSign integration, separate module

### 6.1.11 Open questions

- 🚩 Is contract type a fixed catalog or user-defined? *(Owner: PM, blocking AC-006)*
- ❓ Should expired contracts be archivable or hard-deletable? *(Owner: client)*
```

This pattern repeats for every module in the project. The numbering (6.1, 6.2, 6.3...) corresponds to the order in the Module Index.

---

## Section 7 — Cross-Module Relationships

The section that makes a single SPEC.md genuinely more valuable than per-module specs. Documents the data and operations that cross module boundaries.

```markdown
## Cross-Module Relationships

### Data relationships

| Entity in module | References | Relationship | Notes |
|---|---|---|---|
| Contract (6.1) | Customer (6.3) | Many-to-one | A contract belongs to one customer |
| Contract (6.1) | Account Manager (User) | Many-to-one | AM assignment, also touches User module |
| Report (6.4) | Contract (6.1) | Many-to-many | Reports may span multiple contracts |

### Cross-module operations

Operations that write to multiple modules' tables atomically. Per Section 11 of the canon,
these belong in `lib/services/` as coordinating services, not inside any single module.

| Operation | Modules touched | Suggested location |
|---|---|---|
| Cancel contract → cancel related reports | 6.1 + 6.4 | `lib/services/contract-cancellation.service.ts` |
| Transfer customer between AMs | 6.3 + (User) | `lib/services/customer-transfer.service.ts` |

### Cross-module queries

Read-only queries that join across multiple modules. Per Section 3 of the canon, these
belong in `lib/joins/`, not inside any single module.

| Query | Modules joined | Suggested file |
|---|---|---|
| Contracts with their customer details | 6.1 + 6.3 | `lib/joins/contracts-with-customer.ts` |
| Reports with contract and customer details | 6.4 + 6.1 + 6.3 | `lib/joins/reports-with-context.ts` |

### Shared validation

| Validation | Used by | Suggested location |
|---|---|---|
| Phone number format | 6.3 (Customer), 6.5 (Branch) | `lib/schemas/phone.ts` |
| Currency amount with 2 decimals | 6.1 (Contract), 6.4 (Report) | `lib/schemas/money.ts` |
```

This section is what an implementation agent reads to understand "is what I'm about to build standalone, or does it need a coordinating service?"

If there are no cross-module relationships in the project, the section explicitly states "None — modules are fully independent in this version."

---

## Generation rules

The `generate_spec.py` script enforces these rules:

1. **Sections appear in the exact order above.** No reordering.
2. **Section 1 sign-offs are blank in v1.0 generation** — humans fill them at Phase 4 gate review.
3. **Sections 2–4 are aggregated from `00-discovery-notes.md`** — the discovery summary, actors, and integrations.
4. **Section 5 is built from the list of `01-module-*.md` files** found in the workspace.
5. **Section 6 is generated by iterating over each module file** and pulling the relevant data dictionary entries, ACs, and behaviors.
6. **Section 7 is the only section not auto-generated** — the script writes a placeholder with structured sub-sections, and the discovery agent fills it during Phase 4 review.

If any of the source artifacts are missing or malformed, the script fails with a clear error message identifying which artifact and which section.

---

## Versioning rules

Every generated SPEC.md has version metadata. The script reads the existing SPEC.md (if any) to determine the next version:

- No existing SPEC.md → v1.0 (initial generation)
- Existing v1.x with new content → v1.x+1
- Existing version with major restructuring (modules removed, org_context changed) → next major (v2.0)

The version bump decision can be overridden via CLI flag: `python3 generate_spec.py [project] --version v2.0`

The version history table (in Section 1) accumulates entries across versions. It is never overwritten — only appended to.

---

## What the generator does NOT do

- It does not validate the *content* of the spec. A poorly written AC will still be included.
- It does not enforce sign-offs. That is a human gate.
- It does not auto-detect new modules. Every module must have its own `01-module-*.md` file.
- It does not generate Section 7 (Cross-Module Relationships). This requires architectural judgment that only the discovery agent + dev lead can apply.

---

## Reading SPEC.md as an agent

For coding agents, the standard read sequence is:

1. Read **Section 3 (Organizational Context)** — determines schema patterns
2. Read **Section 5 (Module Index)** — locate the assigned module
3. Read the **specific module section in Section 6** — the working specification
4. Read **Section 7 (Cross-Module Relationships)** — check for shared concerns
5. Reference the **canon's relevant sections** based on the agent's role (per the integrated workflow)

Agents do not need to read Sections 1, 2, or 4 unless context requires it. The structure makes selective reading possible.

---

## Reading SPEC.md as a human

For developers and BAs, the natural read order is top-to-bottom. The document is structured to flow from "what is this project" (Section 2) to "what are the building blocks" (Sections 5–6) to "how do they connect" (Section 7).

For Phase 4 gate review:
- Section 1 — confirm sign-off table is present
- Section 3 — verify `org_context.type` is one of three values
- Section 5 — verify every module from discovery is listed
- Section 6 — spot-check 2-3 modules for AC coverage and behavior coverage
- Section 7 — verify cross-module relationships are filled (or "None" stated)

---

*Companion documents:*
*- `generate_spec.py` — the script that produces SPEC.md*
*- `phase-handoffs.md` — what each phase consumes and produces*
*- `section-12-integrated-workflow.md` — the full workflow*
