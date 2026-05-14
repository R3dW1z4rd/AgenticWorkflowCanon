# Phase Handoff Specification
*The formal contract between phases. Defines exactly what each phase consumes and what each phase produces. Use this when designing or invoking agents.*

---

## What this document is for

Section 12 describes the workflow conceptually. The SPEC.md template defines one specific artifact in detail. This document defines **the contract at every phase boundary** — what files exist when a phase ends, what structure they must have, and what the next phase's agent can rely on.

Think of this as the *interface specification* between agents. When designing a Phase 5 agent (Schema & Contracts), this document tells you:
- What inputs you can assume exist and are validated
- What outputs you must produce and in what format
- What the next phase (Phase 6 — Tests) will read from your output

The contracts here are enforceable. If a phase produces output that doesn't match its contract, the next phase's agent fails fast with a clear error rather than silently doing the wrong thing.

---

## Quick map

```
Phase 0  ──▶  Phase 1     Workspace setup → discovery
Phase 1  ──▶  Phase 2     Discovery notes → module cards
Phase 2  ──▶  Phase 3     Module cards → data dictionary + ACs
Phase 3  ──▶  Phase 4     ACs → behavioral specs + SPEC.md
Phase 4  ──▶  Phase 5     SPEC.md → schema + contracts ◄── CRITICAL HANDOFF
Phase 5  ──▶  Phase 6     Schema → failing tests
Phase 6  ──▶  Phase 7     Failing tests → implementation
Phase 7  ──▶  Phase 8     Implementation → integration & polish
```

The Phase 4 → Phase 5 boundary is the most critical because it crosses runtimes (Codex → Claude Code) and crosses environments (discovery workspace → project repo). It receives the most attention in this document.

---

## Phase 0 ──▶ Phase 1

**Producer:** Discovery agent during intake conversation
**Consumer:** Discovery agent during discovery
**Where:** Discovery workspace (Codex)

### Files produced

```
workspace/[project-slug]/
└── 00-discovery-notes.md   (initial — only the header and project-type fields)
```

### Required structure of `00-discovery-notes.md` at this boundary

```markdown
# Discovery Notes — [Project Name]

## Project Type
[internal-ops | customer-facing | greenfield]

## Project Slug
[kebab-case-slug]

## Initial Brief
[1–3 paragraphs from intake conversation]
```

### Invariants

- `project_slug` is lowercase, kebab-case, no spaces
- `project_type` is one of three exact values
- The slug matches the workspace folder name

### Verification

```bash
# The slug matches its folder
[ -d "workspace/$slug" ] && grep -q "## Project Slug" workspace/$slug/00-discovery-notes.md

# The project type is one of three values
grep -E "^(internal-ops|customer-facing|greenfield)$" workspace/$slug/00-discovery-notes.md
```

### Failure handling

If any invariant fails, the discovery agent is instructed to ask the user to clarify before proceeding to Phase 1's full discovery.

---

## Phase 1 ──▶ Phase 2

**Producer:** Discovery agent (after running through the chosen checklist)
**Consumer:** Discovery agent (now writing module cards)
**Where:** Discovery workspace (Codex)

### Files produced

```
workspace/[project-slug]/
└── 00-discovery-notes.md   (now fully filled with all sections)
```

### Required content

`00-discovery-notes.md` must contain, at minimum:

1. **Project Type and Slug** (carried from Phase 0)
2. **Section 1 — Business Context** filled
3. **Section 1b — Organizational Context** with a YAML block:
   ```yaml
   org_context:
     type: org-only | org-with-units | customer-account
     notes: |
       [non-empty]
     ...
   ```
4. **Section 3 — Actors & Roles** with at least one actor
5. **Section 4 — Core Business Loop** described (text or sketch)
6. **Module list** — at least one module identified with a slug
7. **Discovery Summary block** at the end

### Invariants

- `org_context.type` is exactly one of: `org-only`, `org-with-units`, `customer-account`
- At least one actor is identified
- At least one module is identified, each with a kebab-case slug
- Every 🚩 GAP marker either has an "Owner" assigned or is documented as an accepted risk
- Discovery Summary block is filled (not blank)

### Verification

The discovery agent reads its own output and confirms:

```
[ ] org_context YAML block parses cleanly
[ ] org_context.type is one of three values
[ ] Actors list is non-empty
[ ] Module list is non-empty
[ ] Every 🚩 has an Owner field filled
[ ] Discovery Summary block has content
```

### Failure handling

The Phase 1 gate (per Section 12) is the human review point. The agent does not proceed to Phase 2 until the BA confirms.

---

## Phase 2 ──▶ Phase 3

**Producer:** Discovery agent (after writing module cards)
**Consumer:** Discovery agent (now building data dictionary and ACs)
**Where:** Discovery workspace (Codex)

### Files produced

```
workspace/[project-slug]/
├── 00-discovery-notes.md
└── 01-module-[slug].md       ← one per module identified in Phase 1
```

### Required structure of each `01-module-[slug].md`

```markdown
# Module Definition Card — [Module Name]

## 1. Business Purpose
[paragraph]

## 2. Actors & Roles
| Role | Actions in this module | What they see |
|---|---|---|
| ...

## 3. Entry & Exit Points
| Entry point | ... |
| Pre-conditions | ... |
| Exit point | ... |
| Post-conditions | ... |

## 4. Core Flow
1. [step]
2. [step]
... (max 10 steps)

## 5. States & Edge Cases
[States list and edge cases table]

## 6. Desired Outcomes — AC Seeds
| The system must… | Priority |
|---|---|
| [outcome] | Must / Should / Could |
... (4–8 outcomes)

## 7. Out of Scope
[explicit statement]

## 8. Open Questions & Flags
[table — may be empty]
```

### Invariants

- One file per module identified in Phase 1's module list
- Filename matches `01-module-[module-slug].md` exactly (the slug is the connection)
- Each card has all 8 sections (some may be marked "_[none]_" but the heading must exist)
- Core Flow has 1–10 numbered steps
- Desired Outcomes section has 4–8 entries with priorities
- Out of Scope section is non-empty (even if it just says "no exclusions identified")

### Verification

```bash
# Every module from the Phase 1 list has a card
for slug in $(extract_module_slugs 00-discovery-notes.md); do
  [ -f "01-module-$slug.md" ] || echo "MISSING: $slug"
done

# Every card has all 8 sections
grep -c "^## [0-9]\." 01-module-*.md   # should output 8 per file
```

### Failure handling

The Phase 2 gate is human review. Modules that need additional discovery are flagged as 🟡 Partial in the Module Index.

---

## Phase 3 ──▶ Phase 4

**Producer:** Discovery agent (after writing data dictionary and ACs)
**Consumer:** Discovery agent (now writing behavioral specs and generating SPEC.md)
**Where:** Discovery workspace (Codex)

### Files produced

```
workspace/[project-slug]/
├── 00-discovery-notes.md
├── 01-module-[slug].md (one per module)
├── 02-data-dictionary.md
└── 03-acceptance-criteria.md
```

### Required structure of `02-data-dictionary.md`

The file contains a section per entity, each with a structured table:

```markdown
# Data Dictionary — [Project Name]

## Entity: [EntityName]
<!-- module: [module-slug] -->

| field_name | fieldName | Label | Type | Required | Validation | Default | Source | Integration | Enum values | Sensitive | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `field_a` | `fieldA` | "Field A" | string | Yes | min 1 | (none) | user_input | (none) | (none) | No | (none) |
...
```

The `<!-- module: [slug] -->` HTML comment is the link from each entity to its module. Multiple entities can belong to the same module.

### Invariants for the data dictionary

- Every entity has both `field_name` (snake_case) AND `fieldName` (camelCase) for every field
- Every field has a `Source` value: one of `user_input`, `system_generated`, `integration`, `derived`
- Every field has a `Sensitive` value: `Yes` or `No` (PII flag)
- Every entity has a `<!-- module: [slug] -->` comment linking it to a module slug from Phase 1

### Required structure of `03-acceptance-criteria.md`

```markdown
# Acceptance Criteria — [Project Name]

| AC ID | Priority | The system must… | Module | Flow step | Actor | Permission |
|---|---|---|---|---|---|---|
| AC-001 | Must | [observable statement] | contract-creation | 1 | Account Manager | contracts:create |
| AC-002 | Must | [observable statement] | contract-creation | 2 | (system) | (none) |
...
```

### Invariants for the AC log

- AC IDs are unique and sequential (`AC-001`, `AC-002`, ...)
- Every AC has a `Priority` of `Must`, `Should`, or `Could`
- Every AC's `Module` value matches a module slug from Phase 1
- Every AC has either a permission string (e.g. `contracts:create`) or `(none)`
- Every "The system must…" statement is observable (describes what a tester can see, not implementation)

### Verification

The discovery agent runs:

```bash
# Validate AC log structure
python3 scripts/validate_artifacts.py [project-slug] --check-ac-log

# Validate data dictionary structure
python3 scripts/validate_artifacts.py [project-slug] --check-data-dict

# Confirm every module has at least one entity and at least one AC
python3 scripts/validate_artifacts.py [project-slug] --check-coverage
```

(The `validate_artifacts.py` script is a future addition. Until it exists, validation is the discovery agent's responsibility per its system prompt.)

### Failure handling

If any AC is unobservable ("The system must be performant"), the agent flags it and asks the user to rewrite it. ACs without a clear module assignment are blocking — the agent does not proceed.

---

## Phase 4 ──▶ Phase 5  ◄── CRITICAL HANDOFF

**Producer:** Discovery agent (Codex), final output is `generate_spec.py` consolidating all artifacts
**Consumer:** Schema & Contracts agent (Claude Code)
**Where:** Discovery workspace ──▶ Project repo
**Runtime:** Codex ──▶ Claude Code

This is the most important boundary in the entire workflow. Everything produced before this point is reviewed once and frozen at the gate; everything after consumes the frozen artifact.

### Files produced

```
workspace/[project-slug]/                           ← stays in discovery archive
├── 00-discovery-notes.md
├── 01-module-[slug].md
├── 02-data-dictionary.md
├── 03-acceptance-criteria.md
├── 04-behavioral-test-specs.md
└── exports/
    └── SPEC.md   ◄── the consolidated artifact

[copied at handoff to:]

[project-repo]/docs/specs/SPEC.md                   ← canonical version, tagged
```

### Required structure of SPEC.md

Defined in full in `spec-template.md`. The seven required sections, in order:

1. Header & Sign-offs (with all three sign-offs filled)
2. Project Overview
3. Organizational Context (with `org_context` YAML block)
4. System Map
5. Module Index (table of contents)
6. Modules (one detailed section per module, numbered 6.1, 6.2, ...)
7. Cross-Module Relationships (or explicit "None")

### Invariants — non-negotiable

These are checked at the Phase 4 gate. Failure of any one invariant blocks the handoff.

```
[ ] SPEC.md exists at workspace/[slug]/exports/SPEC.md
[ ] Section 1 sign-off table has all three names filled (BA, Designer, Dev Lead)
[ ] Section 1 sign-off table has all three statuses set to ✅ Approved
[ ] Section 3's org_context.type is exactly one of: org-only, org-with-units, customer-account
[ ] Section 5's module index lists every 01-module-*.md file from the workspace
[ ] Section 6 has one numbered subsection per module in the index
[ ] Each module subsection (6.X) has all 11 sub-sections (6.X.1 through 6.X.11)
[ ] Each module's "Permissions required" sub-section is filled (or explicitly states "no permissions")
[ ] Section 7 is either filled with relationships OR explicitly states "None — modules are fully independent"
[ ] Version Number in header is set (v1.0 for initial, v1.x for updates)
```

### The handoff procedure

This is a deliberate, manual sequence. It is not automated.

1. **Generate SPEC.md** in the discovery workspace:
   ```bash
   python3 scripts/generate_spec.py [project-slug]
   ```

2. **Phase 4 gate review.** BA, Designer, and Dev Lead read SPEC.md and apply the gate checklist (above). They fill the sign-off table at the top of the document.

3. **Copy SPEC.md to the project repo:**
   ```bash
   mkdir -p [project-repo]/docs/specs
   cp workspace/[slug]/exports/SPEC.md [project-repo]/docs/specs/SPEC.md
   ```

4. **Commit and tag:**
   ```bash
   cd [project-repo]
   git add docs/specs/SPEC.md
   git commit -m "spec: add v1.0 (Phase 4 sign-off complete)"
   git tag spec-v1.0
   git push origin main --tags
   ```

5. **Switch runtime.** Discovery agent (Codex) work is done for this version. Subsequent phases run in Claude Code, against the project repo, referencing `spec-v1.0`.

### What Phase 5 can rely on

When the Schema & Contracts agent starts, it can assume:

- `docs/specs/SPEC.md` exists in the project repo
- The current `git describe --tags` (or a `git tag --list spec-*`) returns a valid spec tag
- `org_context.type` in Section 3 is one of three valid values
- Every module section in Section 6 has a complete data dictionary block (6.X.6) and AC table (6.X.7)
- Every "The system must…" outcome corresponds to an AC in the AC table

The agent does NOT need to validate the spec — that was done at the Phase 4 gate. It can read and trust.

### What Phase 5 must produce

```
[project-repo]/
├── db/
│   ├── schema/
│   │   ├── [module].ts            ← one Drizzle table per entity in the module's data dictionary
│   │   └── index.ts               ← updated with the new export
│   └── migrations/
│       └── XXXX_init_[module].sql ← generated migration
└── modules/
    └── [module]/
        ├── [module].schema.ts     ← Zod create / update / list / id schemas
        ├── [module].service.ts    ← service object with method signatures and throwing stubs
        └── [module].actions.ts    ← Server Action signatures with throwing stubs
```

(Plus `components/` folder with placeholder structure — components are filled in Phase 7.)

### Phase 5 invariants (what Phase 6 will rely on)

```
[ ] tsc --noEmit passes
[ ] db/migrations/XXXX_*.sql runs cleanly up and down
[ ] Every Drizzle table has an orgId column (type: uuid, not null)
[ ] Every Zod schema EXCLUDES id, orgId, createdAt, updatedAt (canon rule)
[ ] Every service method body throws NotImplementedError
[ ] No service method has real implementation logic
[ ] All file paths follow the canon's module structure (Section 3)
```

### Failure handling

If the SPEC.md fails any invariant at the Phase 4 gate, the handoff does not proceed. The discovery agent is invoked in "fix" mode to address specific issues. The cycle repeats until all invariants pass.

If Phase 5 produces output that fails its invariants, Phase 6 (Tests) cannot proceed. The Schema & Contracts agent is re-invoked.

---

## Phase 5 ──▶ Phase 6

**Producer:** Schema & Contracts agent (Claude Code)
**Consumer:** Test agent (Claude Code)
**Where:** Project repo

### Files produced (consumed by Phase 6)

```
[project-repo]/
├── docs/specs/SPEC.md             ← unchanged, locked at spec-vX.Y tag
├── db/schema/[module].ts          ← Drizzle table
├── db/migrations/XXXX_*.sql       ← migration
└── modules/[module]/
    ├── [module].schema.ts         ← Zod schemas
    ├── [module].service.ts        ← throwing service stubs
    └── [module].actions.ts        ← throwing action stubs
```

### Invariants

(See Phase 5 output invariants above. The Test agent verifies these before proceeding.)

### What Phase 6 reads

- `SPEC.md` Section 6.X.7 (the AC table for the module)
- `SPEC.md` Section 6.X.8 (the behavioral specs for the module)
- `modules/[module]/[module].service.ts` — to know which methods exist and what they throw
- `modules/[module]/[module].schema.ts` — to know what types to import in tests
- Canon Section 9 (loaded into agent context)

### What Phase 6 must produce

Two commits, separately, in this exact order:

**Commit 1 (Phase 6a):**
```
modules/[module]/
└── BEHAVIORS.md   ← English Given/When/Then bullets, one per behavior in SPEC.md
```

**Commit 2 (Phase 6b):**
```
modules/[module]/
├── [module].schema.test.ts    ← Vitest tests for Zod schemas
└── [module].service.test.ts   ← Vitest tests for service methods (including 4 isolation tests)
tests/e2e/
└── [module].spec.ts           ← Playwright tests for happy path + permission boundary
```

### Phase 6 invariants (what Phase 7 will rely on)

```
[ ] BEHAVIORS.md committed in its own commit (Phase 6a)
[ ] Test files committed in a SEPARATE subsequent commit (Phase 6b)
[ ] One test per BEHAVIORS.md bullet (1:1 mapping verifiable by line count)
[ ] All tests fail when `npm test` is run (output pasted in PR)
[ ] Service test file contains the four required org isolation tests:
    - cannot fetch a record from another org
    - cannot update a record from another org
    - cannot delete a record from another org
    - list returns only own org records
[ ] No implementation code added in either commit
```

### Verification (mechanical checks)

```bash
# Two-commit rule
git log --oneline -2 modules/[module]/ | head -2
# Should show Phase 6b first (HEAD), Phase 6a second

# All tests fail
npm test 2>&1 | grep -c "FAIL"   # Greater than zero

# 1:1 mapping
behavior_count=$(grep -c "^- Given" modules/[module]/BEHAVIORS.md)
test_count=$(grep -c "^  it(" modules/[module]/*.test.ts tests/e2e/[module].spec.ts)
[ "$behavior_count" -eq "$test_count" ] || echo "1:1 mapping violated"

# Four required isolation tests present
grep -c "cannot.*from another org\|list returns only own org records" \
  modules/[module]/[module].service.test.ts
# Should be 4
```

### Failure handling

If the two-commit rule is violated (tests + implementation in the same commit), the PR is rejected at review. The agent must split commits and re-push.

---

## Phase 6 ──▶ Phase 7

**Producer:** Test agent (Claude Code)
**Consumer:** Implementation agent (Claude Code)
**Where:** Project repo

### Files produced

(See Phase 6 output above.)

### What Phase 7 reads

- All Phase 5 + Phase 6 outputs
- `SPEC.md` (full module section — the spec is the truth, tests are the gate)
- Canon Sections 6, 7, 8 (loaded into agent context)
- Quick reference (always loaded)

### What Phase 7 must produce

Filled implementations of:

```
modules/[module]/
├── [module].service.ts        ← every method body written, no NotImplementedError
├── [module].actions.ts        ← every action body written
└── components/
    ├── [Module]List.tsx       ← real implementation
    ├── Create[Module]Form.tsx
    └── ... (other components per SPEC's UI requirements)
app/(dashboard)/[module]/
└── page.tsx                   ← page wired to real services
```

### Phase 7 invariants (what Phase 8 will rely on)

```
[ ] All tests from Phase 6 now pass: npm test  (output pasted)
[ ] grep -r "NotImplementedError" src/ returns nothing in production code
[ ] No tests were modified (or every test edit is flagged in PR with justification)
[ ] Every service write method receives ctx: CallerContext (not loose strings)
[ ] Every service write method calls logger.info AND audit.record({ ..., ctx })
[ ] Every database query filters by orgId
[ ] Page components fetch data via service, not via direct DB queries
[ ] Components are typed against schema types (not any)
```

### The "do not edit tests" rule

This rule has its own enforcement mechanism:

```bash
# Pre-merge check — list test files modified in this branch
git diff main..HEAD --name-only | grep -E "(test\.ts|spec\.ts)$"
# For each result, the PR description must contain a justification block
```

If tests were modified without justification, the PR is rejected.

### Verification

```bash
npm test                                              # All pass
grep -r "NotImplementedError" src/                    # Returns nothing
npm run lint                                          # Passes
npx tsc --noEmit                                      # Passes
```

### Failure handling

If tests don't pass after Phase 7, the agent is re-invoked with the failing test output as input. The agent does NOT modify tests — it modifies implementation until the tests pass.

If grep finds `NotImplementedError`, Phase 7 is incomplete. The agent must finish implementations.

---

## Phase 7 ──▶ Phase 8

**Producer:** Implementation agent (Claude Code)
**Consumer:** Integration agent (Claude Code)
**Where:** Project repo

### Files produced

(See Phase 7 output above.)

### What Phase 8 reads

- All previous outputs
- `SPEC.md` Section 6.X.5 (states & transitions — the state matrix to walk through)
- Canon Sections 9 and 10 (loaded into agent context)
- Quick reference

### What Phase 8 must produce

```
tests/e2e/
└── [module].spec.ts           ← extended with happy path + sad paths
                                  (Phase 6 had stubs; Phase 8 makes them real)
modules/[module]/
└── README.md                  ← module-level runbook
docs/
└── runbook-[module].md        ← (optional) cross-module operational notes
```

Plus:
- Logging confirmed flowing to log destination
- Audit records confirmed appearing in `audit_log` table
- Loading and error states verified for every state in SPEC.md's state matrix
- a11y audit completed (axe-core, keyboard navigation)

### Phase 8 invariants (final production-readiness)

```
[ ] E2E happy path passes against staging
[ ] At least one E2E permission boundary test passes (member vs admin)
[ ] Lighthouse a11y ≥ 95 on new screens
[ ] Manual walkthrough of every state in SPEC's state matrix completed
[ ] No console.log / console.error left from debugging
[ ] Logger calls verified producing entries in production log destination
[ ] Audit records verified appearing in audit_log table
[ ] QA sign-off recorded (in PR description or linked issue)
```

### Verification

```bash
npm run test:e2e                                      # All E2E pass
npm run lighthouse -- --url http://staging/[module]   # a11y >= 95
grep -r "console.log\|console.error" src/             # Returns nothing
```

### Failure handling

If any invariant fails, Phase 8 is re-run. Phase 8 is the only phase that can iterate without re-running prior phases — fixing a logging gap or accessibility issue does not require returning to Phase 7.

---

## Spec update workflow — handoff variations

When the discovery agent runs in "Update spec" mode (existing project, new requirement), the handoffs work the same way but with these differences:

### Phase 4 ──▶ Phase 5 (spec update version)

- The producer reads the existing `SPEC.md` from the project repo at `docs/specs/SPEC.md`
- The producer increments the version (v1.0 → v1.1, or v1.x → v2.0 if major)
- The handoff procedure adds two steps:
  ```bash
  # The new tag includes the version
  git tag spec-v1.1
  ```
- Phase 5+ now runs **only for the modules affected by the spec update** — modules not affected are not touched
- The implementation cycle for the new version uses `git checkout spec-v1.1` to reference the locked spec

### What Phase 5 must check in spec update mode

```
[ ] git rev-parse spec-v1.1   ← tag exists
[ ] docs/specs/SPEC.md at HEAD matches the spec at the tag (no drift)
[ ] Modules affected by the update are explicitly listed in SPEC.md's Version History entry
```

The Version History entry must specify which modules changed:

```markdown
| v1.1 | 2026-08-15 | Add commission rate adjustment | Modules: contract-creation, reporting-dashboard |
```

This is the contract that tells Phase 5 which modules to re-run.

---

## How agents use this document

When designing a new agent for a phase:

1. Read the relevant section above to understand the exact contract
2. Build the agent's prompt to assume the input invariants are met (don't re-validate what's already been gated)
3. Build the agent to produce output that matches the output invariants exactly
4. Include the verification commands in the agent's "self-check" before declaring success

When invoking an agent for a phase:

1. Confirm the previous phase's gate was passed (not just claimed)
2. Provide the agent with the input files specified in this document
3. Provide the agent with the relevant canon sections (per Section 12)
4. After the agent finishes, run the output verification before proceeding

---

*Companion documents:*
*- `section-12-integrated-workflow.md` — the conceptual workflow*
*- `spec-template.md` — the SPEC.md structure in detail*
*- `workflow-quick-reference.md` — the daily reference card*
