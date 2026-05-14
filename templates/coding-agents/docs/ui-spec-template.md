# [Module Name] — UI Specification
*Source: [docs/wireframes/contracts-v1.2.pdf | generated from SPEC.md]*
*Generated: [YYYY-MM-DD]*
*Status: [approved | draft]*
*Wireframe version: [v1.2 — increment when the underlying design changes]*

---

## Module overview

*(1–2 sentences from SPEC.md describing what this module does. Gives the code agent quick visual-design context without forcing it to re-read the full SPEC.)*

The contracts module captures client agreements through a multi-step creation flow, supports browsing and editing existing contracts, and manages status transitions from draft through expiry. Visual design emphasizes form clarity and validation feedback on the creation flow.

---

## Screen inventory

*Every screen visible in the wireframe gets an entry, even if not in scope for the current sprint. The Story coverage column may say "deferred" or "not planned" for screens beyond the current sprint horizon.*

| Screen ID | Name | Purpose | Story coverage |
|---|---|---|---|
| LIST | Contracts list | Browse all contracts in user's org | _to be assigned_ |
| NEW-1 | New Contract — Step 1 | Capture required step-1 fields | _to be assigned_ |
| NEW-2 | New Contract — Step 2 | Display Forex exchange rate | _to be assigned_ |
| NEW-3 | New Contract — Step 3 | Add referrals (up to 5) | _to be assigned_ |
| NEW-4 | New Contract — Step 4 | Submit confirmation | _to be assigned_ |
| DETAIL | Contract detail | Read-only view of a single contract | _to be assigned_ |
| EDIT | Contract edit form | Update an existing contract | _to be assigned_ |
| TRANS | Status transition modal | Move contract between states | _to be assigned_ |

---

## Story-to-screen mapping

*Populated by the orchestrator during sprint planning. Each user story is mapped to one or more screens. The mapping informs which screen detail sections each issue body needs to embed.*

| Story | Screen(s) | Sprint | Notes |
|---|---|---|---|
| US-001 | NEW-1 | sprint-1 | Required fields only; bypass for draft save |
| US-002 | (none) | sprint-1 | Backend-only audit log |
| US-003 | NEW-2 | sprint-2 | Forex API integration |
| US-004 | LIST, DETAIL | sprint-2 | Read paths |
| US-005 | NEW-3 | sprint-3 | Referrals complexity |
| US-006 | EDIT, TRANS | sprint-4 | State machine |

---

## Screen detail

*One section per screen. The code agent reads only the sections relevant to its assigned story.*

---

### NEW-1 — New Contract, Step 1

**Purpose:** Allow an Account Manager to start a new contract by entering the three required fields.

**Layout:** Full-page form (not a modal). Centered single-column layout on desktop, full-width on mobile.

**Entry point:** "New Contract" button on the LIST screen (top-right of the table).

**Exit points:**
- Save as Draft button → returns to LIST screen with new draft visible
- Continue button → advances to NEW-2
- Browser back / breadcrumb → returns to LIST without saving (warn if dirty)

**Components:**

| Component | Variant | Notes |
|---|---|---|
| Page header | Standard | Title "New Contract" + breadcrumb to Contracts |
| Progress indicator | Steps 1–4, highlighted on 1 | shadcn/ui Stepper or equivalent |
| Form card | Card with sections | Contains the three fields below |
| Date picker | Calendar popover | Min date = today, format MM/DD/YYYY |
| Searchable dropdown | Combobox | For Account Manager field |
| Segmented control | 3 options | For Contract Type field |
| Primary button | "Continue" | Bottom right of card |
| Secondary button | "Save as Draft" | Bottom left of card |

**Fields:**

| Field | Component | Label | Validation | Helper text |
|---|---|---|---|---|
| Start Date | Date picker | Start Date | Future date or today | "When does this contract begin?" |
| Account Manager | Searchable dropdown | Account Manager | Required for full save; auto-filled with current user | (none) |
| Contract Type | Segmented control | Contract Type | Required for full save; default unselected | (none) |

**States:**

- **Default**: Empty form, AM field pre-filled with current user, Continue button disabled until required fields filled
- **Filled**: All three fields populated, Continue button enabled
- **Validation error on Start Date**: Red underline on field + inline message below: "Start date cannot be in the past"
- **Validation error on missing required field**: Red underline + inline message: "[Field name] is required"
- **Saving (Draft or Continue clicked)**: Both buttons show spinner, both disabled, form fields read-only
- **Network error**: Toast notification at top: "Couldn't save. Please try again."
- **Success (Save as Draft)**: Redirect to LIST with success toast: "Draft saved"

**Permissions:**
- Page accessible only to users with `contracts:create`
- Account Manager dropdown limited to users with AM role in same org/org-unit

**Accessibility notes:**
- All fields labeled with `<label>` elements
- Validation errors announced via aria-live regions
- Continue button disabled state communicated to screen readers
- Tab order: Start Date → AM → Contract Type → Save as Draft → Continue

**Out of scope for stories that only cover this screen:**
- Forex rate display (handled by NEW-2)
- Referrals input (handled by NEW-3)
- Approval submission (handled by NEW-4)
- Commission rate field gating (future story — field not visible in this screen at all)
- Auto-save (Could priority, deferred)

---

### NEW-2 — New Contract, Step 2

**Purpose:** Display the current Forex exchange rate for the AM to confirm before proceeding.

**Layout:** Full-page, same chrome as NEW-1.

**Entry point:** Continue button on NEW-1.

**Exit points:**
- Back button → returns to NEW-1 with values preserved
- Continue button → advances to NEW-3
- Save as Draft → returns to LIST

**Components:**
- Page header (same as NEW-1)
- Progress indicator (Step 2 of 4 highlighted)
- Rate display card showing current rate + last-updated timestamp + currency pair
- Loading spinner overlay on rate display
- Error state component with retry button

**States:**
- **Loading**: Spinner over rate display, "Fetching current rate..." text
- **Loaded**: Rate displayed prominently with timestamp "Updated [N] seconds ago"
- **Refreshing**: Rate stays visible, small spinner adjacent to timestamp
- **Error**: Error icon + "Rate unavailable. Retry?" with retry button
- **Stale**: If rate is older than 30 seconds and refresh fails, banner "Rate may be outdated"

**Permissions:**
- Same as NEW-1 (`contracts:create`)

**Out of scope for stories that only cover this screen:**
- Manual rate override (future story)
- Currency selection (always uses project default in v1.0)

---

*(Additional screen detail sections — DETAIL, EDIT, LIST, NEW-3, NEW-4, TRANS — follow the same pattern. Omitted here for brevity.)*

---

## Design system notes

*Project-specific design tokens or component conventions the code agent should know about. Filled from the project's existing visual language.*

- Primary color: project's brand blue (defined in tailwind.config.ts)
- Button heights: 40px standard, 32px small
- Form field spacing: 16px between fields
- Error message styling: red-600 text, 14px, mt-1
- Card padding: 24px
- Component library: shadcn/ui (canon Section 6 — solve with shadcn first)

---

## Wireframe revision history

*When the underlying design changes, increment the version and add an entry.*

| Version | Date | Changes | Triggered by |
|---|---|---|---|
| v1.0 | 2026-04-28 | Initial wireframe approved by client | discovery + design pass |
| v1.1 | 2026-05-05 | Forex display moved from inline to dedicated step | client feedback |
| v1.2 | 2026-05-10 | AC-008 audit step not visualized (backend-only) | dev review |

---

*This document is the canonical UI specification for the contracts module. The orchestrator extracts per-screen excerpts into issue bodies during sprint planning. The code agent reads issue body sections, not this file directly — but Phase 8 may consult this file to verify completeness of implementation.*
