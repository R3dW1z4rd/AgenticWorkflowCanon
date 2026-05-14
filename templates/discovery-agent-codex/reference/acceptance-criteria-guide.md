# Acceptance Criteria — Reference Guide
> Agent reference file. Use this as the template and rules when writing acceptance criteria to workspace/.

## File naming
`workspace/[project-slug]/03-acceptance-criteria.md`
One file per project. IDs are sequential across all modules: AC-001, AC-002 … AC-NNN.

---

## The Format

Every criterion follows this pattern:

> **The system must** [observable outcome]

The outcome must be:
- **Observable** — a tester can verify it without reading source code
- **Specific** — it describes one thing, not several
- **Outcome-focused** — what the system does, not how it does it

### Good vs Bad

| ✅ Good | ❌ Bad |
|---------|--------|
| "The system must reject a Start Date set in the past and display an inline error" | "The system must validate the date field" |
| "The system must allow saving a contract as Draft without triggering required field validation" | "The system must have a Save as Draft button" |
| "The system must display the commission rate field only to Account Manager and Finance roles" | "The system must implement role-based access control" |
| "The system must send an email to the assigned AM within 60 seconds of a status change to Pending" | "The system must notify users of status changes" |

---

## Priority Definitions

| Priority | Meaning |
|----------|---------|
| **Must** | Required for launch. The feature does not ship without this. |
| **Should** | Important and expected. A workaround exists but it degrades the experience. |
| **Could** | Enhancement. Valuable but not blocking. Candidate for a later sprint. |

**Rule:** If everything is a Must, nothing is a Must. Be disciplined — a typical module should have 40–60% Must, 30–40% Should, 10–20% Could.

---

## Template

```markdown
# Acceptance Criteria — [Project Name]
Last updated: YYYY-MM-DD

---

## Module: [Module Name]

| ID | Module | Flow Step | Actor | The system must… | Priority | Status | Gitea Issue | Linked Fields | Notes |
|----|--------|-----------|-------|-----------------|----------|--------|-------------|---------------|-------|
| AC-001 | | Step 1 | | | Must | Draft | | | |
| AC-002 | | Step 2 | | | Must | Draft | | | |

---

## Module: [Next Module Name]
...

---

## Summary

| Priority | Count |
|----------|-------|
| Must | |
| Should | |
| Could | |
| **Total** | |
```

---

## Status Lifecycle

```
Draft → Reviewed → Approved → In Dev → Done
```

- **Draft** — written but not yet reviewed with designer or dev lead
- **Reviewed** — discussed, edge cases confirmed
- **Approved** — signed off, ready to be ticketed
- **In Dev** — Gitea issue created, work in progress
- **Done** — implemented and verified

---

## Linked Fields Column

Fill this with the `field_name` values from the Data Dictionary that this criterion exercises.
This creates traceability: Data Dictionary → Acceptance Criteria → Test Spec → Gitea Issue.

Example:
```
AC-003 | Contract Creation | Step 1 | AM | reject a Start Date in the past | Must | Draft | | contract_start_date |
```

---

## Derivation Process

Use this sequence to derive criteria from the Module Definition Card:

1. **For each step in the Core Flow:**
   - "What must be true for this step to be considered working correctly?"
   - "What would a tester verify at this step?"

2. **For each edge case in Section 5:**
   - Turn each edge case into a criterion
   - "The system must [handle this edge case in this specific way]"

3. **For each desired outcome in Section 6:**
   - These are already written as criteria — copy them and refine
   - Assign an AC-XXX ID and link to the flow step

4. **For each field in the Data Dictionary with validation rules:**
   - Each validation rule should generate at least one criterion
   - "The system must [enforce this validation rule] and [show this specific feedback]"

5. **For each role in the Actors table:**
   - "The system must [allow/prevent] [role] from [action]"
   - Check: is every role's access to every sensitive field explicitly stated?

6. **For each integration field:**
   - "The system must [show loading state / error state / refresh behavior]"
   - These are frequently missed and always important

---

## Questions to Ask the User During This Phase

- "For step [N] in the flow — what would a tester check to confirm this is working?"
- "What should happen if [actor] tries to [action] without the right permissions?"
- "Is there anything the system should explicitly prevent a user from doing?"
- "What's the most likely thing to go wrong in this module? How should the system handle it?"
- "Are there any timing or performance expectations? (e.g. 'must load within 3 seconds')"
