# MIRO AI PROTOTYPE PROMPT
## Module: Contract Creation

---

## CONTEXT

Allows Account Managers to create and manage contracts with clients. Without this module, contracts are tracked in spreadsheets, creating version conflicts and audit risk.

**Primary actors:** Account Manager, Finance, System

**Target device:** desktop
**Visual style:** enterprise
**Layout density:** comfortable

---

## SCREEN INVENTORY

Generate **exactly** these screens, with these exact names. Do not add extra screens.
Do not merge screens. Every screen listed must appear as a separate frame in the prototype.

1. **Create / New** — Account Manager clicks New Contract → system creates draft record
2. **Form — Step 3** — AM fills Step 2: exchange rate displayed from Forex API
3. **Review & Confirm** — AM submits → system validates and changes status to Pending
4. **List View**
5. **Detail View**
6. **Error State** — Required by: AC-003; AC-005

---

## FLOW MAP

Connect the screens using these **exact transitions**. Every arrow listed must exist in the prototype.
Do not add connections that are not listed here.

**[Create / New]** --[clicks new contract]--> **[Form — Step 3]**
**[Form — Step 3]** --[fills step 2: exchange rate displayed from forex a…]--> **[Review & Confirm]**
**[Review & Confirm]** --[submits]--> **[List View]**
**[List View]** --[Continue →]--> **[Detail View]**
**[Detail View]** --[Continue →]--> **[Error State]**
**[Create / New]** --[Submit (validation fails)]--> **[Error State]**  ← CONDITION: required fields empty or invalid
**[Create / New]** --[Submit (validation passes)]--> **[Form — Step 3]**  ← CONDITION: all required fields valid
**[List View]** --[Submit (validation fails)]--> **[Error State]**  ← CONDITION: required fields empty or invalid
**[List View]** --[Submit (validation passes)]--> **[Detail View]**  ← CONDITION: all required fields valid
**[Detail View]** --[Submit (validation fails)]--> **[Error State]**  ← CONDITION: required fields empty or invalid
**[Detail View]** --[Submit (validation passes)]--> **[Error State]**  ← CONDITION: all required fields valid
**[Create / New]** --[Cancel / Back]--> **[Create / New]**  ← No data saved
**[Form — Step 3]** --[Cancel / Back]--> **[Create / New]**  ← No data saved
**[Review & Confirm]** --[Cancel / Back]--> **[Create / New]**  ← No data saved

---

## SCREEN DETAILS

For each screen, build exactly the layout described. No additional sections or panels.

### Create / New
_Account Manager clicks New Contract → system creates draft record_

**Fields / elements to show:**
- Start Date `[date]` *(required)*
- Account Manager `[reference]` *(required)*
- Referral Type `[enum]` — options: none · employee · external
- Exchange Rate `[decimal]` *(required)* ⚠ read-only (from Forex API (every 30s))
- Commission Rate `[decimal]`

**Integration displays (read-only, auto-updating):**
- Exchange Rate — fetched from Forex API (every 30s) · Show loading state while fetching · Show error state if unavailable

**Layout:** Single-column form. Group related fields. Show required field indicators. Primary action button at bottom.
**Progress indicator:** Show step progress if this is part of a multi-step flow.

### Form — Step 3
_AM fills Step 2: exchange rate displayed from Forex API_

**Layout:** Single-column form. Group related fields. Show required field indicators. Primary action button at bottom.
**Progress indicator:** Show step progress if this is part of a multi-step flow.

### Review & Confirm
_AM submits → system validates and changes status to Pending_

**Layout:** Two-column detail view. Labels on left, values on right. Action buttons in header.

### List View

**Fields / elements to show:**
- Contract ID `[string]` *(required)* ⚠ read-only (from system_generated)
- Status `[enum]` *(required)* — options: draft · pending · active · expired · cancelled ⚠ read-only (from system_generated)
- Account Manager `[reference]` *(required)*

**Layout:** Table or card list with column headers. Include search/filter bar at top. Empty state if no records.

### Detail View

**Fields / elements to show:**
- Start Date `[date]` *(required)*
- Exchange Rate `[decimal]` *(required)* ⚠ read-only (from Forex API (every 30s))
- Commission Rate `[decimal]`

**Integration displays (read-only, auto-updating):**
- Exchange Rate — fetched from Forex API (every 30s) · Show loading state while fetching · Show error state if unavailable

**Layout:** Two-column detail view. Labels on left, values on right. Action buttons in header.

### Error State
_Required by: AC-003; AC-005_

**Layout:** Inline error messages below affected fields. Do not replace the form — show errors in context.

---

## INTERACTION RULES

Apply these rules to the relevant screens:

- "Contract ID": Auto-generated UUID
- "Start Date": Must not be in the past
- "Account Manager": Must be active AM user
- "Referral Type" must be one of: none , employee , external
- "Exchange Rate": 4 decimal places
- "Status" must be one of: draft , pending , active , expired , cancelled
- "Commission Rate": 0–100%
- "Commission Rate" is sensitive — restrict visibility to authorized roles only
- [AC-011] Role-based visibility: display commission rate only to Account Manager and Finance roles

---

## INTEGRATION & LOADING STATES

For every field sourced from an external API, show three states:

**Exchange Rate** (from: Forex API (every 30s))
- Loading state: skeleton/spinner in the field area
- Loaded state: value displayed as read-only with timestamp if relevant
- Error state: inline error message + retry action. Rest of form remains usable.

---

## ROLE-BASED VISIBILITY

Show these variations in the prototype (use annotations or separate frames):

- [AC-011] display commission rate only to Account Manager and Finance roles

---

## DO NOT INCLUDE

The following are explicitly out of scope. Do not add screens or flows for these:

- Contract renewal, payment processing, and document signing are not in scope for v1.

---

## PROTOTYPE QUALITY CHECKLIST

Before finishing, verify:

- [ ] Exactly 6 screens exist — one for each item in the Screen Inventory
- [ ] Every transition in the Flow Map has a visible connector with a label
- [ ] Every screen with a form shows field labels, input types, and required indicators
- [ ] Every integration field has a loading state visible
- [ ] Error states are shown in context (inline), not as separate replacement screens
- [ ] Empty states are included for list views
- [ ] Role-restricted fields are annotated
- [ ] No screens were added beyond the inventory list

---

_Generated from workspace artifacts. Module: Contract Creation. 
Source files: 01-module-*.md + 02-data-dictionary.md + 03-acceptance-criteria.md_