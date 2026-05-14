# Architecture Canon
## Section 12 — The Integrated Workflow
*Version 1.0 | The complete pipeline from client conversation to shipped code.*

---

### What this section covers

The integrated workflow connects the three pillars of our system — discovery, the canon, and the coding agents — into one operating sequence. This document is the authoritative description of how a feature moves from a client's words into production code. Every developer, BA, and AI agent in the system operates inside the workflow defined here.

This replaces the legacy `AGENTIC_WORKFLOW.pdf`. The principles from that document survive; the generic vocabulary is gone, and every phase is now specific to this stack, this canon, and our two-runtime model (Codex for discovery, Claude Code for implementation).

---

### The three pillars and how they connect

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   DISCOVERY     │  │     CANON       │  │     CODING      │
│                 │  │                 │  │                 │
│  Codex agent    │  │  Architectural  │  │  Claude Code    │
│  + BA + client  │  │  law            │  │  agents         │
│                 │  │                 │  │                 │
│  Captures       │  │  Defines code   │  │  Generates code │
│  intent         │  │  structure      │  │  per the canon  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │     loaded into    │     loaded into    │
         └────────────────────┴────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Project git repo │
                    │                   │
                    │  - SPEC.md        │
                    │  - canon synced   │
                    │  - code           │
                    │  - tests          │
                    │  - audit history  │
                    └───────────────────┘
```

The project git repo is the integration layer. Everything that matters lives there: the spec, the synced canon, the code, the tests, the migrations, the deployment history. Discovery happens outside the repo and produces inputs; coding happens inside the repo and consumes those inputs.

---

### The eight phases

Every project moves through these phases in order. No phase begins until the previous phase's gate is signed off.

```
DISCOVERY (Codex)
  ┌─ Phase 0:  Intake
  ├─ Phase 1:  Discovery
  ├─ Phase 2:  Module Definition
  ├─ Phase 3:  Data Dictionary + Acceptance Criteria
  └─ Phase 4:  Behavioral Specs + SPEC Consolidation
                                                          ◄── HANDOFF GATE
                                                              (human review)
CODING (Claude Code)
  ┌─ Phase 5:  Schema & Contracts
  ├─ Phase 6:  Failing Tests
  ├─ Phase 7:  Implementation
  └─ Phase 8:  Integration & Polish
```

Each phase has three things defined: its **inputs** (what it consumes), its **outputs** (what it produces), and its **gate** (the criteria that must be met before the next phase begins).

---

### Phase 0 — Intake

**Run by:** Discovery agent (Codex), with the BA and client
**Duration:** 15–30 minutes

**Purpose.** Capture the bare minimum to start the discovery process. This is not the discovery itself — it's the on-ramp.

**Inputs.**
- Client conversation, brief, or any pre-existing material (notes, transcripts, ChatGPT exports)
- BA's understanding of what the client is asking for

**Outputs.**
- Project slug (kebab-case, e.g. `contract-manager`) — used as the workspace folder name and eventually the project repo name
- Project type identified (`internal-ops` / `customer-facing` / `greenfield`)
- Workspace folder created at `workspace/[project-slug]/`
- Initial `00-discovery-notes.md` written with whatever is known from intake

**Gate — quick checklist:**

```
[ ] Project slug agreed with the client
[ ] Project type selected (one of three)
[ ] Workspace folder created and initial notes written
[ ] Right discovery checklist identified (greenfield / internal-ops / customer-facing)
```

If any of these is unclear, do not proceed to Phase 1.

---

### Phase 1 — Discovery

**Run by:** Discovery agent (Codex), with the BA and client
**Duration:** 1–3 sessions of 1–2 hours each (depending on project complexity)

**Purpose.** Capture the project's vision, organizational context, actors, core business loop, and module list. This phase produces the foundational understanding everything downstream depends on.

**Inputs.**
- Phase 0 outputs
- The appropriate checklist (`reference/checklist-*.md` based on project type)

**Outputs.**
- `00-discovery-notes.md` — fully filled with all sections completed, including:
  - Business context
  - **`org_context:` YAML block** (mandatory — defines `org-only` / `org-with-units` / `customer-account` pattern)
  - Actors and roles
  - Core business loop
  - Module list (high-priority modules identified)
  - Open questions and gaps (🚩 GAP, ❓ OPEN, ✅ CONFIRMED markers throughout)
  - Discovery summary block

**Gate — quick checklist:**

```
[ ] org_context block is filled with a clear pattern selected
[ ] Core business loop fits in a single readable paragraph or sketch
[ ] All actors identified with their actions
[ ] Module list reviewed and approved by the client
[ ] All 🚩 GAP items either resolved or documented as accepted risks
[ ] Discovery summary block filled at the end of the notes
```

The most common failure mode is leaving the `org_context` ambiguous because "we'll figure that out later." Do not proceed without a clear answer.

---

### Phase 2 — Module Definition

**Run by:** Discovery agent (Codex), with the BA
**Duration:** 30–60 minutes per module

**Purpose.** For each module identified in discovery, produce a complete module definition card that the design and development teams can act on directly.

**Inputs.**
- Phase 1 outputs (especially the module list and core loop)
- `reference/module-definition-card.md` (the template structure)

**Outputs.**
- One file per module: `01-module-[module-slug].md`
- Each file contains:
  - Business purpose and motivation
  - Actors involved
  - Entry point, pre-conditions, exit point, post-conditions
  - Core flow (numbered steps, max 10)
  - States and edge cases
  - Desired outcomes ("The system must…" — 4–8 statements)
  - Out of scope (explicit)
  - Open questions for this module

**Gate — quick checklist:**

```
[ ] Each module has its own 01-module-[slug].md file
[ ] Core flow has 10 steps or fewer (longer = consider splitting the module)
[ ] Each module has 4–8 "The system must…" statements with priority assigned
[ ] Out of Scope section is non-empty
[ ] All edge cases identified for each step in the core flow
[ ] States and transitions documented
```

---

### Phase 3 — Data Dictionary + Acceptance Criteria

**Run by:** Discovery agent (Codex), with the BA (and dev lead consulted as needed)
**Duration:** 1–2 hours total

**Purpose.** Convert the module definitions into structured data definitions and observable acceptance criteria.

**Inputs.**
- Phase 2 outputs (all module cards)
- `reference/data-dictionary-guide.md`
- `reference/acceptance-criteria-guide.md`

**Outputs.**
- `02-data-dictionary.md` — project-wide. Every entity, every field, with:
  - Entity name
  - `field_name` (snake_case, for DB)
  - `fieldName` (camelCase, for JS/API)
  - Display label
  - Type, required flag, validation rules, default
  - Source (user_input / system_generated / integration / derived)
  - Enum values (if applicable)
  - Sensitive / PII flag
  - Notes
- `03-acceptance-criteria.md` — all ACs across all modules, each with:
  - AC ID (sequential, e.g. AC-001)
  - "The system must [observable outcome]" wording
  - Priority (Must / Should / Could)
  - Module reference, flow step reference, actor, field references

**Gate — quick checklist:**

```
[ ] Every field in the data dictionary has BOTH field_name and fieldName
[ ] Every field has a Source assigned (user_input / system_generated / integration / derived)
[ ] Sensitive / PII flag is filled (Yes / No) for every field
[ ] Every "The system must…" outcome from the module cards is now an AC entry
[ ] Every AC is observable (describes what a tester sees, not implementation)
[ ] Every AC has a priority assigned
[ ] Every AC links to a module and a flow step
```

---

### Phase 4 — Behavioral Specs + SPEC Consolidation

**Run by:** Discovery agent (Codex), then `generate_spec.py`
**Duration:** 1–2 hours

**Purpose.** Expand each AC into observable test scenarios, then consolidate the five discovery artifacts into a single SPEC.md that coding agents can consume directly.

**Inputs.**
- Phase 3 outputs (data dictionary + ACs)
- `reference/behavioral-test-spec-template.md`
- `reference/behavioral-test-spec-guide.md`

**Outputs.**
- `04-behavioral-test-specs.md` — for each AC:
  - Layer (unit / integration / e2e)
  - Actor
  - At least one happy-path scenario (Setup / Action / Expect)
  - At least one failure or edge-case scenario
  - Security boundary scenarios (cross-org access denied, missing permission denied) where applicable
- `SPEC.md` — generated by `scripts/generate_spec.py` from the five discovery artifacts. Single project-level document with:
  - Project header (slug, version, date, sign-offs)
  - System overview (org_context, actors, core loop, integration map)
  - Module index (table of contents)
  - One section per module (flow, data, ACs, behaviors)
  - Cross-module relationships section (data and operations that cross module boundaries)

**Gate — quick checklist:**

```
[ ] Every AC has at least one happy-path scenario
[ ] Every AC has at least one failure / edge case scenario
[ ] Each module has at least one security boundary scenario (cross-org, permission)
[ ] SPEC.md generated successfully with no script errors
[ ] SPEC.md table of contents lists every module
[ ] Cross-module relationships section is filled (or explicitly states "none")
[ ] BA sign-off recorded in SPEC.md header
[ ] Designer sign-off recorded in SPEC.md header
[ ] Dev lead sign-off recorded in SPEC.md header
```

**This is the most important gate in the entire pipeline.** Everything before it is reversible — discovery can be redone, modules can be redefined, ACs can be rewritten. Everything after it commits to code that is expensive to change. The Phase 4 gate is the last moment changes are cheap.

If any of the three sign-offs is missing, do not proceed.

---

### ═══ The Handoff ═══

After Phase 4 is signed off:

1. The `SPEC.md` is **copied** from the discovery workspace into the project repo at `docs/specs/SPEC.md`
2. The project repo creates a **git tag** at the commit where `SPEC.md` is added: `spec-v1.0` (or appropriate version)
3. The discovery workspace remains as the **source notes archive** — never touched again unless a spec update happens
4. **Runtime switches** from OpenAI Codex to Claude Code
5. The project enters Phase 5

The handoff is physical, deliberate, and visible in git history. The tag becomes the immutable target for the implementation cycle — coding agents reference the tag, never the branch HEAD. This prevents the spec from moving under active implementation work.

---

### Phase 5 — Schema & Contracts

**Run by:** Schema & Contracts agent (Claude Code)
**Duration:** 30 minutes – 2 hours per module

**Purpose.** Convert the SPEC's data dictionary and module definitions into Drizzle tables, Zod schemas, and service interfaces. No method bodies are written in this phase — only structure and types.

**Inputs.**
- `SPEC.md` (locked at `spec-v1.0` tag)
- `docs/architecture/quick-reference.md`
- Canon Sections 3, 5, 7 (loaded into agent context)

**Outputs (per module):**
- `db/schema/[module].ts` — Drizzle table definition
- `db/migrations/XXXX_*.sql` — generated migration
- `modules/[module]/[module].schema.ts` — Zod schemas (create, update, list, ID)
- `modules/[module]/[module].service.ts` — service object with method signatures, JSDoc, throwing stubs (`throw new NotImplementedError(...)`)
- `modules/[module]/[module].actions.ts` — Server Action signatures, throwing stubs

**The agent uses the scaffolder.** Phase 5 starts by running `npm run scaffold:module [name]`, then customizes the generated files to match the data dictionary. The scaffolder enforces canon compliance by construction.

**Gate — quick checklist:**

```
[ ] tsc --noEmit passes
[ ] Migration runs cleanly up and down on a scratch database
[ ] No service method has a real body (every method throws NotImplementedError)
[ ] Every entity in SPEC's data dictionary appears in db/schema/[module].ts
[ ] Every Zod schema excludes id, orgId, createdAt, updatedAt (canon rule)
[ ] db/schema/index.ts is updated with the new exports
[ ] Sidebar nav link added (if scaffolder didn't auto-update)
[ ] Dev lead reviewed the type and interface design
```

---

### Phase 6 — Failing Tests

**Run by:** Test agent (Claude Code)
**Duration:** 1–2 hours per module

**Purpose.** Convert the behavioral specs into failing test files, committed before any implementation begins.

This phase has two sub-phases that **must be in separate commits**:

**Phase 6a — English behavior list.** The agent reads the SPEC's behavioral specs and produces `BEHAVIORS.md` per module — one bullet per behavior in Given/When/Then form. This is the human-reviewable map of what the tests will assert. No code yet.

**Phase 6b — Failing test code.** The agent converts each bullet into one test in the appropriate test file. All tests must currently fail (services throw `NotImplementedError`, components don't exist yet). Test runner output is pasted to confirm failures.

**Inputs.**
- SPEC.md (specifically the behavioral specs sections)
- Phase 5 outputs (service interfaces with throwing stubs)
- Canon Section 9 (loaded into agent context)
- Quick reference (always loaded)

**Outputs.**
- `modules/[module]/BEHAVIORS.md` (Phase 6a — committed first, separately)
- `modules/[module]/[module].schema.test.ts` (Phase 6b)
- `modules/[module]/[module].service.test.ts` — including the four required org isolation tests (Phase 6b)
- `tests/e2e/[module].spec.ts` (Phase 6b)

**Gate — quick checklist:**

```
[ ] BEHAVIORS.md committed in its own commit (Phase 6a)
[ ] Every state in SPEC's state matrix has a behavior bullet
[ ] Every error / throw in service JSDoc has a behavior bullet
[ ] Every validation rule has a behavior bullet
[ ] Test files committed in a separate commit (Phase 6b)
[ ] One test per behavior bullet (1:1 mapping)
[ ] All tests fail when run (npm test output pasted)
[ ] The four required org isolation tests are present in the service test file
[ ] Dev lead confirms behavior coverage matches SPEC
```

The two-commit rule is non-negotiable. It prevents an implementation agent in Phase 7 from silently rewriting tests to make buggy code pass — git history shows the failing-then-passing transition unambiguously.

---

### Phase 7 — Implementation

**Run by:** Implementation agent (Claude Code)
**Duration:** 2–8 hours per module

**Purpose.** Make all failing tests pass by implementing services first, then UI wiring. The agent works incrementally — service method by service method, component by component — committing each as it goes green.

**Inputs.**
- Phase 5 + Phase 6 outputs
- SPEC.md
- Canon Sections 6, 7, 8 (loaded into agent context)
- Quick reference (always loaded)

**Outputs.**
- Filled service methods (no more `NotImplementedError`)
- Filled Server Actions
- Implemented components
- Wired pages
- All Phase 6 tests passing

**The agent's order of work within Phase 7:**

```
1. Repository / query layer (if needed)
2. Service methods — until all service tests pass
3. Server Actions — until all action-related tests pass
4. Component logic — until component tests pass
5. Component wiring — replace mocks with real service calls
```

**The "do not edit tests" rule.** The agent must not modify tests in this phase except for trivial import fixes. Any test edit must be flagged with explicit justification in the PR. This rule blocks the most insidious failure mode of agentic TDD: tests being silently rewritten to match buggy implementations.

**Gate — quick checklist:**

```
[ ] All tests passing (npm test output pasted)
[ ] grep -r "NotImplementedError" src/ returns nothing in production code
[ ] No test files were edited (or every edit is flagged with justification in PR)
[ ] Every service write method calls logger.info and audit.record
[ ] Every service write method receives ctx: CallerContext (not loose strings)
[ ] Every query filters by orgId
[ ] PR review against the canon's service checklist passes
```

---

### Phase 8 — Integration & Polish

**Run by:** Integration agent (Claude Code), with QA review
**Duration:** 2–6 hours per module

**Purpose.** Everything that unit tests don't cover — real backend integration, accessibility, observability, error states, loading states, and manual QA against the SPEC's state matrix.

**Inputs.**
- Phase 7 outputs (working module)
- SPEC.md (specifically the state matrix and any external integration specs)
- Canon Sections 9, 10 (loaded into agent context)

**Outputs.**
- Playwright E2E test for happy path + critical sad paths
- Accessibility audit (axe-core, keyboard navigation, screen reader labels)
- Loading and error states verified
- Logging and metrics confirmed in service methods
- Updated module README / runbook

**Gate — quick checklist:**

```
[ ] E2E happy path passes against staging
[ ] At least one E2E permission boundary test passes (member vs admin role)
[ ] Lighthouse accessibility score ≥ 95 on new screens
[ ] Manual walkthrough of every state in SPEC's state matrix completed on a real device
[ ] No console.log or console.error left from debugging
[ ] Logger calls verified in production log destination
[ ] Audit records verified appearing in audit_log table
[ ] QA sign-off recorded
```

After Phase 8 passes, the module is production-ready. The PR can be merged to main.

---

### Spec versioning and ongoing projects

The SPEC.md is a living document. Each version is tagged in git and locks the implementation cycle for that version.

**Versioning rules:**

| Change type | Version bump | Trigger |
|---|---|---|
| Initial delivery | v1.0 | First sign-off |
| Adding a field, AC, or small behavior change | v1.1, v1.2 | Client request, scope clarification |
| Adding a new module | v1.x or v2.0 | Depends on impact (dev lead decides) |
| Removing or fundamentally restructuring a module | v2.0 | Major scope change |

**The update workflow:**

When a client requests a change (during UAT or otherwise):

1. Discovery agent enters **"Update spec" mode**
2. Developer copies the current `docs/specs/SPEC.md` from the project repo into the discovery workspace as `SPEC-previous.md` (the diff baseline)
3. Agent conducts targeted discovery focused only on what's changing
4. Agent updates the relevant source artifacts and regenerates `SPEC.md`
5. Agent runs `generate_change_manifest.py` to produce `CHANGE-MANIFEST-v1.1.md`
6. Agent completes all `[AGENT: ...]` sections in the manifest: specific file paths per phase, what does not change, plain-English summary
7. **Both** `SPEC.md` and `CHANGE-MANIFEST-v1.1.md` go through the Phase 4 gate (BA + Dev Lead sign-off)
8. Both files are copied into the project repo and a new git tag is created

The change manifest is the key artifact that prevents unnecessary rework. It explicitly states:
- Which sections changed in the spec
- Which phases need to re-run and how much of each
- Which files to modify, add, or delete
- What does NOT change (the agent leaves these files alone entirely)

**Coding phases always target a tag, never HEAD.** When a developer or agent starts an implementation cycle, they explicitly check out (or reference) the spec tag. This means:

- Multiple spec versions can be in flight at the same time without interference
- The implementation cycle for v1.0 is never affected by a v1.1 update happening in parallel
- Git history shows exactly which spec version drove which code changes

---

### What lives where — the file map

```
DISCOVERY WORKSPACE (Codex environment)
  workspace/[project-slug]/
    ├── 00-discovery-notes.md         ← Phase 1 output
    ├── 01-module-[name].md           ← Phase 2 output (one per module)
    ├── 02-data-dictionary.md         ← Phase 3 output
    ├── 03-acceptance-criteria.md     ← Phase 3 output
    ├── 04-behavioral-test-specs.md   ← Phase 4 output
    └── exports/
        ├── SPEC.md                   ← Generated, copied into project repo at handoff
        ├── module-card-[name].docx   ← Stakeholder-facing
        ├── module-workbook.xlsx      ← Stakeholder-facing
        └── miro-prompt-[name].md     ← For wireframe generation

PROJECT REPO (Claude Code environment, after handoff)
  my-project/
    ├── docs/
    │   ├── architecture/             ← Synced canon (read-only locally)
    │   └── specs/
    │       └── SPEC.md               ← Tagged at each version (spec-v1.0, etc.)
    ├── modules/                      ← Phase 5+ output
    │   └── [module]/
    │       ├── [module].schema.ts
    │       ├── [module].service.ts
    │       ├── [module].actions.ts
    │       ├── BEHAVIORS.md          ← Phase 6a output
    │       ├── [module].schema.test.ts
    │       ├── [module].service.test.ts
    │       └── components/
    ├── db/                           ← Phase 5+ output
    ├── tests/e2e/                    ← Phase 8 output
    └── ...
```

---

### How agents load context

Each agent in the workflow receives a specific subset of the canon, plus the spec, plus the always-on quick reference. This keeps context windows focused and prevents irrelevant rules from confusing the agent.

| Agent | Phase | Canon sections loaded | Spec input |
|---|---|---|---|
| Discovery agent | 0–4 | None (uses checklists + reference docs) | Produces SPEC.md |
| Schema & Contracts agent | 5 | 3, 5, 7 | SPEC.md |
| Test agent | 6 | 9 | SPEC.md (focus: behavioral specs) |
| Implementation agent | 7 | 6, 7, 8 | SPEC.md (focus: ACs + behaviors) |
| Integration agent | 8 | 9, 10 | SPEC.md (focus: state matrix) |

**Quick reference is always loaded** — it's small enough and contains the non-negotiable rules every agent must respect.

**Canon sections are loaded from the project's `docs/architecture/` folder** — the synced copy. This means a canon update only propagates to a project when `sync-canon.sh` is explicitly run. Deliberate, not automatic.

---

### The cardinal rules of the workflow

These rules are enforced by tooling, gates, and review. They are non-negotiable.

1. **Phases run in order. No skipping.** Even small features go through every phase — they're just shorter.

2. **No coding before SPEC.md is signed off.** The handoff gate is the strongest gate in the system.

3. **Two-commit rule for tests and implementation.** Tests committed alone, in their own commit. Then implementation in subsequent commits.

4. **Coding phases target a spec tag.** Never `main`, never HEAD. Implementation references the tag at which the spec was signed off.

5. **The canon is loaded from the project's `docs/architecture/`** — the synced copy. Agents never read directly from the canon repo.

6. **`org_context` is mandatory in every project.** It's the foundational decision that shapes data, auth, and tests.

7. **The four required org isolation tests are non-negotiable per module.** Without them, the module is not complete.

8. **Spec updates are versioned and tagged.** Each update goes through Phase 4's review gate. No silent updates.

---

### When the workflow is too heavy

The full eight-phase workflow is calibrated for net-new modules with non-trivial UI and business logic. For some changes it's overkill:

| Change | Adjusted workflow |
|---|---|
| Renaming a UI string | Skip discovery. Edit, test, ship. |
| Bug fix with a known reproduction | Skip discovery. Write the failing test, fix, ship. |
| Internal refactor with no behavior change | Skip discovery. Characterization tests + refactor + verify. |
| Adding a single field to an existing module | Spec update mode (light) → scaffolder field addition → test → ship |
| Major new module | Full workflow — all eight phases |

The principle: **the workflow tracks the size of the change, not the project**. A bug fix in a year-old project follows the same lightweight path as a bug fix in a new one.

---

### How to use this document

- **Developers:** When you start a new piece of work, identify which phase you're entering. The phase defines what's expected of you, what gate you must pass, and what canon sections you need open. If you don't know what phase you're in, the workflow has been bypassed somewhere — pause and figure out where.

- **BAs and consultants:** You operate in Phases 0–4. Your work product is the spec. The Phase 4 gate is your final review checkpoint — past that, your work is locked and the coding team takes over. If a client asks for changes after Phase 4 has been signed off, that's a spec update (a new version), not a continuation of the current cycle.

- **Tech leads:** You sign the gates. Specifically: Phase 4 (SPEC review), Phase 5 (schema review), Phase 6 (test coverage review), Phase 7 (PR code review), Phase 8 (production readiness). Each gate has a quick checklist above. Use it.

- **Agents:** You operate in one phase at a time. You receive the inputs for that phase, you produce the outputs for that phase, and you end your work at the gate. You do not skip ahead. If a gate's mechanical check fails (tests not passing, types not compiling), do not declare success — paste the failure output and stop. Humans decide whether to continue.

---

*Previous: Section 11 — Evolution Rules*
*This is the final section of the Architecture Canon for the greenfield workflow.*
*See also: `workflow-quick-reference.md` for a two-page summary of this section.*
*Brownfield workflow (legacy projects without prior discovery) is a separate workstream.*
