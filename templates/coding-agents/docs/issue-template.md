# US-XXX: [User-visible title — what the user can DO after this ships]

> *This is the issue body template used by the orchestrator agent. One file per user story is written to `.work/issue-bodies/US-XXX.md`, then the issue creation script references it via `gh issue create --body-file`.*

---

## User story

**As a** _[role from SPEC, e.g. Account Manager]_
**I want to** _[action — what they can do]_
**So that** _[outcome — what value they get]_

---

## Business context

_[2-3 sentences from SPEC.md 6.X.1 — why this exists, who uses it, what business problem it solves. Copied or paraphrased from the spec; not invented here.]_

---

## SPEC reference

- **Module:** _[Module Name]_ (slug: `[slug]`)
- **Spec sections:**
  - 6.X.1 (Business purpose)
  - 6.X.4 (Core flow) — specifically steps _[N]_ through _[M]_
  - 6.X.5 (States) — _[applicable states]_
  - 6.X.6 (Data dictionary) — entities: _[Entity1, Entity2]_
  - 6.X.7 (ACs) — _[AC-NNN through AC-NNN]_
  - 6.X.8 (Behavioral specs) — _[B-NNN through B-NNN]_
- **Spec tag:** `spec-vX.Y` (the coding agents must work against this tag, not main)

---

## Acceptance criteria

*These come directly from SPEC.md 6.X.7. Do not rewrite or summarize — the wording is the contract.*

- **AC-NNN** (Must): _[The system must … verbatim from spec]_
  - Permission: `[module]:[action]` or `(none)`
- **AC-NNN** (Must): _[The system must … verbatim from spec]_
  - Permission: `(none)`
- **AC-NNN** (Should): _[The system must … verbatim from spec]_
  - Permission: `(none)`

---

## Security boundaries

*These are non-negotiable per the canon. Every story that touches a module includes these checks at minimum.*

- **SB-1** (cross-org access denied): User from Org B cannot fetch records belonging to Org A → returns 404, never 403
- **SB-2** (missing permission denied): User without required permission cannot perform the action → returns Forbidden
- **SB-3** (unauthenticated redirect): Unauthenticated visitor cannot access protected pages → redirect to /login
- _[SB-N: any sensitive-field gating from SPEC 6.X.6 — fields marked Sensitive/PII]_

---

## Files this work will touch

### New files
- `db/schema/[module].ts` (Phase 5)
- `modules/[module]/[module].schema.ts` (Phase 5)
- `modules/[module]/[module].service.ts` (Phase 5 stubs, Phase 7 implementation)
- `modules/[module]/[module].actions.ts` (Phase 5 stubs, Phase 7 implementation)
- `modules/[module]/[module].service.test.ts` (Phase 6)
- `modules/[module]/[module].schema.test.ts` (Phase 6)
- `modules/[module]/components/[Component].tsx` (Phase 7)
- `modules/[module]/components/Create[Module]Form.tsx` (Phase 7)
- `modules/[module]/BEHAVIORS.md` (Phase 6a)
- `modules/[module]/CLAUDE.md` (Phase 5 skeleton, Phase 8 final)
- `app/(dashboard)/[module]/page.tsx` (Phase 7)
- `tests/e2e/[module].spec.ts` (Phase 6 stubs, Phase 8 real)
- `db/migrations/XXXX_*.sql` (Phase 5 — auto-generated)

### Modified files
- `db/schema/index.ts` — add export (Phase 5)
- `components/layout/Sidebar.tsx` — add nav link (Phase 7, if user-facing module)
- `lib/auth/permissions.ts` — register new permission strings (Phase 5)

---

## Business rules to enforce

*Specific rules from SPEC.md that the implementation must honor. Pulled from data dictionary validation, AC text, and behavioral specs.*

- _[Rule 1 — e.g. "Start date must not be in the past"]_
- _[Rule 2 — e.g. "Commission rate field hidden from non-AM/Finance roles"]_
- _[Rule 3 — e.g. "Maximum 5 referrals per contract"]_
- _[Rule 4 — e.g. "Exchange rate is read-only, sourced from Forex API every 30 seconds"]_

---

## Permissions required

*From SPEC.md 6.X.9. These appear in `lib/auth/permissions.ts` and gate the relevant service actions.*

| Permission | Required by | Default roles |
|---|---|---|
| `[module]:[action]` | AC-NNN | _[Role1, Role2]_ |
| `[module]:view[Field]` | AC-NNN | _[Role1, Role2]_ |

---

## Cross-module dependencies

- **Depends on:**
  - _[Module X, must be Phase 8 done — provides type Y used here]_
  - _[Spec tag spec-vX.Y exists]_
- **Blocks:**
  - _[US-NNN — needs this to ship first]_
- **Related (no blocking):**
  - _[Module X — likely to be modified in a future spec update]_

---

## Phase breakdown

This story moves through all four coding phases. Each phase is a separate branch, separate PR.

- [ ] **Phase 5 — Schema & Contracts** → `feat/[module]-phase5-schema-US-XXX`
  - Drizzle table, Zod schemas, service interface with throwing stubs
  - Module CLAUDE.md skeleton created
- [ ] **Phase 6 — Failing Tests** → `feat/[module]-phase6-tests-US-XXX`
  - BEHAVIORS.md (committed first, separate commit)
  - Test files (committed second)
  - All tests failing (NotImplementedError)
  - Four required org isolation tests present
- [ ] **Phase 7 — Implementation** → `feat/[module]-phase7-impl-US-XXX`
  - Service methods implemented, all tests pass
  - Server Actions implemented
  - Components built and wired
- [ ] **Phase 8 — Integration & Polish** → `feat/[module]-phase8-integration-US-XXX`
  - E2E tests passing
  - A11y audit ≥ 95
  - Module CLAUDE.md Exports section updated

---

## Specialist agent invocations

When working this story, invoke the specialists in this exact order. Each command will validate that the previous phase is complete before proceeding.

```
1. /phase5 [module-slug] US-XXX
2. After Phase 5 PR merged → /phase6 [module-slug] US-XXX
3. After Phase 6 PR merged → /phase7 [module-slug] US-XXX
4. After Phase 7 PR merged → /phase8 [module-slug] US-XXX
```

Do not skip phases. The slash commands will refuse to proceed if preconditions aren't met.

---

## Definition of done

- [ ] All four phase PRs merged to main
- [ ] `npm test` passes (unit + integration)
- [ ] `npm run test:e2e` passes (E2E)
- [ ] Four required org isolation tests present and passing
- [ ] No `NotImplementedError` in production code (`grep -r "NotImplementedError" src/` returns nothing)
- [ ] Module CLAUDE.md Exports section reflects final state
- [ ] Manual smoke test on staging: happy path + one permission boundary
- [ ] PR descriptions reference this issue number
- [ ] Issue auto-closed by the state-update workflow when Phase 8 merges

---

## Risk and complexity assessment

*Filled by the orchestrator at planning time. Used to size the sprint correctly.*

| Field | Value |
|---|---|
| **Complexity tier** | _[Small \| Medium \| Large]_ |
| **Estimated PR count** | _[4 — one per phase]_ |
| **Risk areas** | _[e.g. "Forex API failure handling — need to confirm fallback behavior with PM"]_ |
| **Spec ambiguities** | _[List any 🚩 or ❓ items in the relevant SPEC sections that may affect this story]_ |

---

## Notes and open questions

*Added during implementation. The team uses this section for clarifications, decisions, and blockers that emerge mid-story.*

- _[2026-05-12] @dev: Need PM clarification on whether expired contracts are archivable or hard-deletable. Spec section 6.X.11 has this as open question._
- _[2026-05-13] @pm: Hard-deletable for v1. Archival is v2.0._

---

## UI Specification

*Populated by the orchestrator during sprint planning from `docs/wireframes/[module-slug]-ui-spec.md`. The code agent reads this section — not the raw PDF or ui-spec.md directly. Backend-only stories set this to "N/A".*

**Source:** `docs/wireframes/[module-slug]-ui-spec.md` — Screen _[SCREEN-ID]_ (_[Screen name]_)

**Layout:** _[full-page | modal | side panel | etc.]_

**Entry point:** _[What navigation or action brings the user here]_

**Exit points:**
- _[Button/action → destination and side effect]_
- _[Back/cancel → destination]_

**Components for this story:**

| Component | Variant | Notes |
|---|---|---|
| _[e.g. Form card]_ | _[Standard]_ | _[Contains fields below]_ |
| _[e.g. Date picker]_ | _[Calendar popover]_ | _[Min date = today]_ |
| _[e.g. Segmented control]_ | _[3 options]_ | _[Contract Type]_ |
| _[e.g. Primary button]_ | _["Continue"]_ | _[Bottom right, disabled until fields filled]_ |
| _[e.g. Secondary button]_ | _["Save as Draft"]_ | _[Bottom left, always enabled]_ |

**Fields:**

| Field | Component | Label | Validation | Notes |
|---|---|---|---|---|
| _[fieldName]_ | _[component type]_ | _[display label]_ | _[rule]_ | _[pre-fill, conditional, etc.]_ |

**States this story must handle:**

- **Default:** _[Describe the screen's initial state]_
- **Loading:** _[Describe spinner/disabled behavior on submit]_
- **Validation error:** _[Which fields, what messages, where they appear]_
- **Success:** _[Redirect or toast — what happens after save]_
- **Error (network/server):** _[Toast or inline — what the user sees]_

**Out of scope for this story (visible in the wireframe but not implemented here):**
- _[Screen or feature visible in wireframe but deferred — name it explicitly so the code agent doesn't build it]_

---

## Attachments

*Supporting documentation attached by humans during sprint planning or implementation. The wireframe is referenced above via the UI Specification section — not re-linked here unless there is additional context.*

- **QA video** (if this is a bug fix): _[link or attached file]_
- **Related ADR** (if architectural decision required): _[link]_
- **Supporting docs:** _[anything else relevant]_

---

*Generated by the orchestrator agent during sprint planning.*
*Source: `templates/coding-agents/docs/issue-template.md`*
