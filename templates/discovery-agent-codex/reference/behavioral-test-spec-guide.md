# Behavioral Test Specifications — Reference Guide
> Agent reference file. Use this as the template and rules when writing behavioral specs to workspace/.

## File naming
`workspace/[project-slug]/04-behavioral-test-specs.md`
One file per project. Scenarios are grouped by AC ID.

---

## What This Document Is

The Behavioral Test Spec bridges the gap between plain-language acceptance criteria and
executable test code. It is written before any code exists.

It is readable by:
- **Designers** — to verify every screen state is covered by a wireframe
- **Developers** — to understand exactly what to implement
- **QA** — to know what to test and with what setup
- **AI agents (Agentic Software Factory)** — as grounding context for code generation

---

## Scenario Format

```
[AC-XXX] The system must [criterion]

  Layer:   unit | integration | e2e
  Actor:   [who triggers this]
  Priority: Must / Should / Could

  SCENARIO N — [descriptive name]
    Setup:   [Pre-conditions that must be true]
    Action:  [What the actor does]
    Expect:  [What the system does — specific, observable, unambiguous]
    Notes:   [Edge cases, data deps, open questions]
```

---

## Layer Definitions

| Layer | What it tests | Framework |
|-------|--------------|-----------|
| **unit** | Pure functions: validators, calculators, formatters, permission guards | Vitest |
| **integration** | Service layer: API calls, DB writes, external integrations, side effects | Vitest + mocks |
| **e2e** | Full user flows: from UI interaction to observable outcome | Playwright |

**Rule:** Assign the lowest layer that meaningfully tests the criterion.
- A date validation rule → `unit` (it's a pure function)
- An API error state → `integration` (needs a mocked HTTP client)
- A role-based field visibility check → `e2e` (needs a real DOM and a logged-in user)

---

## Minimum Scenarios Per Criterion

Every criterion needs at minimum:
1. **Happy path** — the correct input produces the correct outcome
2. **Failure / edge case** — the wrong input or unexpected state is handled correctly

High-risk criteria (integrations, permissions, financial calculations) should have 3–5 scenarios.

---

## Writing Precise Expect Statements

The `Expect` block is the most important part. It must be specific enough that two different
people would write the same test from it.

| ❌ Vague | ✅ Specific |
|---------|------------|
| "An error appears" | "An inline error message appears directly below the Start Date field reading: 'Start date must be today or in the future'" |
| "The user is notified" | "An email is dispatched to the AM's registered address within 60 seconds" |
| "The field is hidden" | "The commission_rate field is not present in the DOM (count = 0) — not merely visually hidden" |
| "The form saves" | "A contract record is created with status: 'draft' and a UUID v4 contract_id" |

---

## Template

```markdown
# Behavioral Test Specifications — [Project Name]
Last updated: YYYY-MM-DD
Sign-off: Designer ☐  |  Dev Lead ☐  |  PM ☐

---

## [Module Name]

---

### [AC-001] The system must [criterion]

**Layer:** unit / integration / e2e
**Actor:** [role]
**Priority:** Must / Should / Could

#### SCENARIO 1 — Happy path
\`\`\`
Setup:
Action:
Expect:
\`\`\`

#### SCENARIO 2 — [Edge case name]
\`\`\`
Setup:
Action:
Expect:
\`\`\`

**Notes:**

---

### [AC-002] The system must [criterion]
...
```

---

## Common Scenario Patterns

### Validation scenarios (unit layer)
Always write:
- Valid input → no error, proceeds
- Empty / missing required field → correct error message
- Boundary value (e.g. max length, min date, max count)
- Invalid type or format

### Permission scenarios (unit + e2e)
Always write:
- Authorized role → can perform action / sees field
- Unauthorized role → blocked / field absent from DOM
- Unauthenticated user → redirected to login

### Integration scenarios (integration layer)
Always write:
- API available, valid response → correct data displayed
- API unavailable / timeout → error state shown, form still usable
- API returns malformed data → error caught, not shown as raw data
- Refresh / polling behavior → data updates without page reload

### State transition scenarios (integration + e2e)
Always write:
- Valid transition → new state persisted, downstream effects triggered
- Invalid / duplicate transition → no change, no duplicate side effects
- Concurrent modification → last-write-wins or conflict is surfaced

---

## Checklist Before Marking Complete

- [ ] Every AC in `03-acceptance-criteria.md` has at least one scenario here
- [ ] Every scenario has Setup, Action, and Expect blocks filled
- [ ] Every integration field has an unavailability scenario
- [ ] Every permission criterion has a DOM-level check (not just visual)
- [ ] Every state transition has an idempotency scenario
- [ ] Layer is assigned to every scenario
- [ ] Designer has confirmed wireframes cover all states described in the Expect blocks
