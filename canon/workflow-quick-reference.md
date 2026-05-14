# Workflow Quick Reference
*Two pages. Read this first. Section 12 has the full detail.*

---

## The pipeline at a glance

```
DISCOVERY (OpenAI Codex)              CODING (Claude Code)
─────────────────────────             ────────────────────
Phase 0  Intake                       Phase 5  Schema & Contracts
Phase 1  Discovery                    Phase 6  Failing Tests
Phase 2  Module Definition            Phase 7  Implementation
Phase 3  Data Dictionary + ACs        Phase 8  Integration & Polish
Phase 4  Behavioral Specs + SPEC ───▶ HANDOFF
                                      (BA + designer + dev lead sign off)
```

Eight phases. Two runtimes. One git repo as the integration layer.

---

## What each phase produces

| # | Phase | Output |
|---|---|---|
| 0 | Intake | Project slug, project type, workspace folder |
| 1 | Discovery | `00-discovery-notes.md` with `org_context` block |
| 2 | Module Definition | `01-module-[slug].md` per module |
| 3 | Data Dict + ACs | `02-data-dictionary.md`, `03-acceptance-criteria.md` |
| 4 | Behavioral + SPEC | `04-behavioral-test-specs.md`, **`SPEC.md`** |
| 5 | Schema & Contracts | Drizzle table, Zod schemas, throwing service stubs |
| 6 | Failing Tests | `BEHAVIORS.md` + test files (separate commits) |
| 7 | Implementation | All tests green, no `NotImplementedError` |
| 8 | Integration | E2E, a11y, observability — production-ready |

---

## The gates — quick checklists per phase

Each gate is human sign-off + mechanical check. Both must pass before the next phase begins.

### Phase 1 gate
```
[ ] org_context block filled with one of: org-only / org-with-units / customer-account
[ ] Core business loop fits in one paragraph
[ ] All actors identified with their actions
[ ] Module list reviewed by client
[ ] All 🚩 GAP items resolved or documented as accepted risks
```

### Phase 2 gate
```
[ ] Each module has its own 01-module-[slug].md
[ ] Core flow ≤ 10 steps per module
[ ] 4–8 "The system must…" statements per module with priority
[ ] Out of Scope section non-empty for each module
```

### Phase 3 gate
```
[ ] Every field has BOTH field_name (snake_case) and fieldName (camelCase)
[ ] Every field has Source assigned (user_input / system_generated / integration / derived)
[ ] Sensitive / PII flag filled (Yes / No) for every field
[ ] Every "system must…" outcome is now an AC entry
[ ] Every AC is observable (describes what a tester sees)
[ ] Every AC has priority and links to module + flow step
```

### Phase 4 gate — THE BIG ONE
```
[ ] Every AC has a happy-path scenario
[ ] Every AC has a failure / edge case scenario
[ ] Each module has a security boundary scenario (cross-org or permission)
[ ] SPEC.md generated successfully
[ ] BA sign-off recorded in SPEC.md header
[ ] Designer sign-off recorded in SPEC.md header
[ ] Dev lead sign-off recorded in SPEC.md header
```

After this: SPEC.md → project repo → git tag → runtime switches to Claude Code.

### Phase 5 gate
```
[ ] tsc --noEmit passes
[ ] Migration runs cleanly up and down
[ ] Every service method throws NotImplementedError (no real bodies)
[ ] Every entity in data dictionary appears in db/schema/[module].ts
[ ] Zod schemas exclude id, orgId, createdAt, updatedAt
[ ] Dev lead reviewed types and interfaces
```

### Phase 6 gate
```
[ ] BEHAVIORS.md committed in its own commit (Phase 6a)
[ ] Test files committed in a SEPARATE commit (Phase 6b)
[ ] One test per behavior bullet (1:1 mapping)
[ ] All tests fail when run — output pasted
[ ] Four required org isolation tests present
```

### Phase 7 gate
```
[ ] All tests pass — output pasted
[ ] grep -r "NotImplementedError" src/ returns nothing
[ ] No tests edited (or every edit flagged with justification)
[ ] Every write method calls logger.info AND audit.record({ ..., ctx })
[ ] Every write method receives ctx: CallerContext
[ ] Every query filters by orgId
```

### Phase 8 gate
```
[ ] E2E happy path passes against staging
[ ] At least one permission boundary E2E test passes
[ ] Lighthouse a11y ≥ 95
[ ] Manual walkthrough of every state in SPEC's state matrix completed
[ ] No console.log / console.error left behind
[ ] QA sign-off recorded
```

---

## The cardinal rules

1. **No phase skipping.** Small changes go through every phase, just shorter.
2. **No coding before SPEC.md is signed off.** Phase 4 is the strongest gate.
3. **Tests and implementation in separate commits.** Phase 6a, 6b, then 7 — three distinct commits minimum.
4. **Coding phases reference a git tag, not HEAD.** `spec-v1.0`, not `main`.
5. **Canon is read from `docs/architecture/`** in the project, never directly from the canon repo.
6. **`org_context` is mandatory.** Every project, every time.
7. **Four required org isolation tests per module.** Non-negotiable.
8. **Spec updates are versioned and tagged.** v1.1, v1.2, v2.0 — each goes through Phase 4 review.

---

## What lives where

```
DISCOVERY (Codex)                    PROJECT REPO (Claude Code)
─────────────────                    ──────────────────────────
workspace/[slug]/                    docs/
  ├ 00-discovery-notes.md              ├ architecture/   ← synced canon
  ├ 01-module-X.md                     └ specs/SPEC.md   ← copied at handoff
  ├ 02-data-dictionary.md
  ├ 03-acceptance-criteria.md        modules/[name]/
  ├ 04-behavioral-test-specs.md        ├ X.schema.ts
  └ exports/                           ├ X.service.ts
      ├ SPEC.md  ────────────────▶    ├ X.actions.ts
      ├ module-card.docx                ├ BEHAVIORS.md
      ├ module-workbook.xlsx            ├ X.schema.test.ts
      └ miro-prompt-X.md                ├ X.service.test.ts
                                        └ components/
```

---

## Spec versioning

| Trigger | Version bump | Workflow |
|---|---|---|
| Initial delivery | v1.0 | Full pipeline (Phases 0–8) |
| Add field / small AC change | v1.1 | Spec update mode → Phase 4 gate → Phase 5+ for affected modules |
| Add a new module | v1.x or v2.0 | Spec update mode → Phase 4 → Phases 5–8 for the new module |
| Major restructure | v2.0 | Spec update mode → Phase 4 → cycle for all affected modules |

**Coding phases always target a spec tag**, never HEAD. This prevents the spec from moving under active implementation.

---

## When the workflow is too heavy

| Change | Workflow |
|---|---|
| Rename a UI string | Skip discovery. Edit, test, ship. |
| Bug fix with known reproduction | Failing test → fix → ship |
| Internal refactor, no behavior change | Characterization tests → refactor → verify |
| Add a single field | Spec update (light) → scaffolder → test → ship |
| Major new module | Full pipeline (all eight phases) |

The workflow tracks the size of the change, not the project's age.

---

## Three operating modes for the discovery agent

```
NEW PROJECT          → Full discovery (Phases 0–4) from blank
RESUME DISCOVERY     → Continue an unfinished discovery
UPDATE SPEC          → Read current SPEC.md, do targeted discovery for changes,
                       produce a new version, increment, re-run Phase 4 gate
```

Update spec mode is what handles ongoing greenfield projects. The `00-discovery-notes.md` is the working file; `SPEC.md` is the deliverable. Updates re-run Phase 4 (gate review), then Phases 5–8 for the affected modules only.

---

## Who reads what

| Role | Reads |
|---|---|
| BA running discovery | Discovery checklists + this card |
| Designer | Module cards + SPEC.md |
| Dev lead | SPEC.md + relevant canon sections + this card |
| Developer (in a module) | Quick reference + relevant canon section + module's SPEC section |
| Schema & Contracts agent | Quick reference + Sections 3, 5, 7 + SPEC.md |
| Test agent | Quick reference + Section 9 + SPEC.md (behavioral specs focus) |
| Implementation agent | Quick reference + Sections 6, 7, 8 + SPEC.md |
| Integration agent | Quick reference + Sections 9, 10 + SPEC.md (state matrix focus) |

---

*Full detail: `canon/section-12-integrated-workflow.md`*
