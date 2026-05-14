# Worked Example — Orchestrator Wireframe Discussion

*This excerpt shows the wireframe check step during a `/plan-sprint` session for the contract-manager project. It picks up mid-session, after the preflight has passed and the orchestrator has loaded the project state and SPEC.md. The `contracts-ui-spec.md` was produced by `/wireframe contracts` before this session.*

---

## Context

Sprint 1 planning is underway. The orchestrator has read:
- `docs/project-state.md` — sprint-1, target v1.0.0
- `docs/specs/SPEC.md` — contracts module, spec-v1.0

Now performing the wireframe check for the contracts module.

---

## The orchestrator's wireframe check

> Let me check what's in `docs/wireframes/` for the contracts module before I propose stories.

```bash
ls docs/wireframes/ | grep contracts
```

Output:
```
contracts-v1.2.pdf
contracts-ui-spec.md
```

> Found both the source PDF and a `ui-spec.md`. I'll read the spec — it's already been structured by the wireframe agent so I don't need to re-read the full PDF.

*(Reads `docs/wireframes/contracts-ui-spec.md`)*

> Here's what the wireframe covers for the contracts module:
>
> **Screen inventory — 6 screens:**
>
> | Screen | Name | Purpose |
> |---|---|---|
> | LIST | Contracts list | Browse org contracts, entry point for creation |
> | NEW-1 | Create — Step 1 | Start Date, Account Manager, Contract Type |
> | NEW-2 | Create — Step 2 | Forex exchange rate display |
> | NEW-3 | Create — Step 3 | Referrals (up to 5) |
> | NEW-4 | Create — Step 4 | Review and submit |
> | DETAIL | Contract detail | Read-only view |
>
> **A few things I noticed comparing the wireframe to the SPEC:**
>
> 1. The wireframe shows a "Duplicate Contract" button on the DETAIL screen. ACs 001–012 don't mention this action — is it intentional, or was it added to the wireframe without a corresponding AC?
>
> 2. The commission rate field (AC-011) is not visible in any wireframe screen. The SPEC says it's finance-gated. I'll assume it's intentionally absent from the wireframe and will appear in a future Finance-role screen.
>
> 3. NEW-2 (Forex step) and NEW-3 (Referrals) look like they add meaningful complexity. I'd recommend scoping sprint 1 to just NEW-1 and LIST — the team can validate the creation flow end-to-end before tackling the multi-step form.
>
> **Quick question before I propose the sprint:** On the "Duplicate Contract" button — is that in scope for any sprint, or is it something the UX added speculatively?

### Developer responds

> Good catch. Duplicate contract is a future nice-to-have — UX added it without a backing AC. Not in scope for any current sprint. Also confirmed: commission rate doesn't appear in the wireframe because Finance sets it through the back-office admin, which is a separate module.

### Orchestrator acknowledges and proposes

> Got it — logging both of those as design decisions in my plan notes.
>
> Given that context, here's how I'd map the wireframe screens to sprint 1 stories:
>
> **In scope for sprint 1:**
>
> | Story | Wireframe screens | Rationale |
> |---|---|---|
> | US-001 | NEW-1, LIST | Core creation flow and list view — validates the module end-to-end |
> | US-002 | (none) | Audit log — backend only, no UI |
>
> **Deferred — will be backlog entries:**
>
> | Screen | Deferred to | Notes |
> |---|---|---|
> | NEW-2 | Sprint 2 | Forex API integration — separate story |
> | NEW-3 | Sprint 3 | Referrals — significant form complexity |
> | NEW-4 | Sprint 3 | Submission step — depends on referrals |
> | DETAIL | Sprint 2 | Read-only view — natural next step after list |
>
> **What US-001's UI Specification section will contain:**
>
> For the issue body, I'll embed the NEW-1 screen detail (full-page form, date picker + combobox + segmented control, Save as Draft + Continue footer) and the LIST screen detail (table with New Contract button). The NEW-2 through NEW-4 screens will be referenced as "visible in wireframe but out of scope for this story" — this tells the code agent explicitly not to build them.
>
> Does this mapping match your intent?

### Developer confirms

> Yes, exactly right. Let's proceed.

### Orchestrator continues with sprint proposal

> Good. Here's the full sprint 1 proposal with the wireframe mapping locked in...

*(The session continues to the standard APPROVE PLAN gate and artifact generation)*

---

## What changed in the issue body

Because the orchestrator found and read the ui-spec.md, US-001's issue body now contains a populated `## UI Specification` section instead of a bare wireframe link:

```markdown
## UI Specification
Source: docs/wireframes/contracts-ui-spec.md
Screens: NEW-1 (Create Contract — Step 1), LIST (Contracts list)

**LIST screen:**
Layout: Full page — data table
Components: DataTable with columns (ID, AM, Type, Status, Start Date, Actions),
  "New Contract" button (primary, top-right)
Entry point: /contracts route, sidebar nav link
States: Empty state ("No contracts yet — create your first one"), Loading skeleton,
  Populated table

**NEW-1 screen:**
Layout: Full-page form (not a modal)
Entry point: "New Contract" button on LIST
Components:
  - Page header: "New Contract" + breadcrumb to Contracts
  - Progress indicator: Steps 1–4, Step 1 highlighted
  - Form card with three fields:
      Start Date — date picker (min: today, format MM/DD/YYYY)
      Account Manager — searchable combobox, pre-filled with current user
      Contract Type — segmented control (Standard | Premium | Enterprise)
  - Footer: "Save as Draft" (secondary, left) | "Continue" (primary, right, disabled until fields filled)

States this story handles:
  - Default: form empty, AM pre-filled, Continue disabled
  - Filled: all three fields populated, Continue enabled
  - Validation error: Start Date red underline + "Start date cannot be in the past"
  - Saving: both buttons spinner + disabled
  - Success (draft): redirect to LIST + "Draft saved" toast
  - Network error: "Couldn't save. Please try again." toast

**Out of scope for US-001 (visible in wireframe, not in this story):**
  NEW-2 (Forex rate display), NEW-3 (Referrals), NEW-4 (Submission)
  DETAIL (Contract detail view)
  "Duplicate Contract" button (no backing AC — future consideration)
```

Compare this to what US-001's issue body would have contained without the wireframe integration:

```markdown
## Attachments
- Wireframe: docs/wireframes/contracts-v1.2.pdf
```

The code agent receiving the wireframe-integrated issue body knows:
- The form is full-page, not a modal
- AM field is a combobox (not a regular select)
- Contract Type is a segmented control (not a dropdown)
- Continue is disabled until all fields are filled
- "Duplicate Contract" should NOT be built

The code agent receiving only the PDF link would have to infer all of this — or ask.

---

## What success looks like for the wireframe check

The orchestrator's wireframe discussion is successful when:

1. The developer is asked about — and answers — any conflicts between the wireframe and the SPEC before stories are proposed
2. The screen-to-story mapping is explicit and agreed on before `APPROVE PLAN`
3. Out-of-scope screens are named in every issue body (not just omitted)
4. The UI Specification section in each issue body is specific enough that the code agent doesn't need to ask what kind of component to use

The 10-minute wireframe discussion in the orchestrator session replaces the ambiguity that would otherwise surface as questions during Phase 7 — or worse, as a mismatch at UAT.
