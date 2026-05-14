# Open Issues

*Known gaps, deferred decisions, and pending work. Reviewed at the start of each major step.*

---

## Active — needs attention before next pilot

### OI-001 — Starter template repo not built
The STARTER-PLAN.md documents every file needed in a bootstrapped project. The actual files (CLAUDE.md, tailwind.config.ts, drizzle.config.ts, lib/auth/ scaffold, etc.) have not been created. A developer installing the coding agents into a brand-new project will need these.

**Priority:** High — blocks first real project pilot
**Location:** `templates/starter/`

---

### OI-002 — Canon sections not yet synced into the coding agent context
The coding agents reference `docs/architecture/section-N-*.md` as on-demand reads. These files are produced by `tools/sync-canon.sh` which copies canon sections into the project repo. The sync tool exists but has not been tested end-to-end with the new coding agent pipeline.

**Priority:** High — agents will fail to load canon sections without this
**Location:** `tools/sync-canon.sh`

---

### OI-003 — Code agent UI Specification reading not validated
The code-agent.md instructs the agent to read the `## UI Specification` section from the issue body and use it to drive component generation. This has not been tested against a real Claude Code session. The issue body format and the agent's reading behavior may need adjustment.

**Priority:** High — core wireframe integration feature
**Validation:** Run `/wireframe contracts` → `/plan-sprint` → `/schema` → `/test` → `/code` on a real project

---

## Deferred — known gaps, not blocking pilot

### OI-004 — `phase-handoffs.md` not updated for wireframes and change manifests
The formal handoff document describes Phase 0–8 contracts. It predates the wireframe integration and the change manifest system. The document should be updated to reflect:
- Wireframe (ui-spec.md) as a Phase 4 gate artifact
- CHANGE-MANIFEST as a trigger for /plan-change rather than /plan-sprint

**Priority:** Medium
**Location:** `canon/phase-handoffs.md`

---

### OI-005 — `acceptance-criteria-guide.md` missing permission column
The AC guide doesn't show how to write ACs that reference permission strings (e.g. `Permission: contracts:create`). The SPEC template and issue template already include this column. The guide should catch up.

**Priority:** Medium
**Location:** `discovery-agent-codex/guides/acceptance-criteria-guide.md`

---

### OI-006 — Section 12 change manifest gate not formally documented
Section 12 (integrated workflow) describes the Phase 4 gate but doesn't yet formally include the CHANGE-MANIFEST as a required artifact when updating the spec. The orchestrator Mode 2 handles this operationally, but the canon section should be updated for completeness.

**Priority:** Low
**Location:** `canon/section-12-integrated-workflow.md`

---

### OI-007 — `behavioral-test-spec-guide.md` not updated for new security scenarios
The guide predates the mandatory SB-1/2/3 security scenarios that were added to the template. The guide should be updated to explain these scenarios and when to add custom security behaviors beyond the three mandatory ones.

**Priority:** Low
**Location:** `discovery-agent-codex/guides/behavioral-test-spec-guide.md`

---

## Deferred indefinitely — out of scope for v1.0

### OI-008 — Brownfield workstream
Adapting the pipeline for existing codebases that don't follow the canon. Requires a separate discovery mode and a different Phase 5 approach (extend existing schemas rather than create from scratch). Not started.

### OI-009 — PHP legacy projects
Explicitly deferred. The canon is Next.js + TypeScript only.

### OI-010 — Production patterns
The following patterns are documented as needed but not yet covered by a canon section:
- Soft deletes
- File uploads (presigned URLs, storage)
- Email (transactional, templates)
- Background jobs (BullMQ introduction criteria)
- Streaming and Suspense boundaries
- Error and loading hierarchy
- Internationalisation (i18n)
- Theming / multi-brand
- Race conditions (optimistic updates, concurrent edits)
- Cross-module write coordination

### OI-011 — State file migration to database
The orchestrator's `docs/project-state.md` is a markdown file. The note in the template says to consider migrating to a real database at ~200 open stories. This migration path is not designed.

### OI-012 — Golden example module
A complete, real-world example module (not contract-manager, which is synthetic) built end-to-end through the agent pipeline and committed as a reference implementation. Planned after the first real pilot project.

### OI-013 — Agent Teams exploration
The Medium article on subagents mentioned Agent Teams (experimental) for cross-session coordination. The current pipeline uses git + issue tracker for coordination. Agent Teams would allow agents to communicate mid-task. Not explored — low priority until the basic pipeline is validated in production.

---

*Last updated: May 2026*
