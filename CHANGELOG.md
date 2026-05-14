# Changelog

## Step 9 — Coding Agent Pipeline (May 2026)

### Added
- `templates/coding-agents/` — full coding agent pipeline
  - `.claude/agents/orchestrator.md` — sprint planner, wireframe-aware, plan-mode
  - `.claude/agents/wireframe-agent.md` — PDF analysis + prototype generation (two modes)
  - `.claude/agents/schema-agent.md` — Phase 5: Drizzle schema, Zod schemas, service stubs
  - `.claude/agents/test-agent.md` — Phase 6: BEHAVIORS.md + failing test suite
  - `.claude/agents/code-agent.md` — Phase 7: implementation until tests pass
  - `.claude/agents/ship-agent.md` — Phase 8: E2E, a11y, CLAUDE.md exports
  - `.claude/commands/plan-sprint.md` — /plan-sprint slash command
  - `.claude/commands/plan-change.md` — /plan-change slash command
  - `.claude/commands/status.md` — /status slash command
  - `.claude/commands/wireframe.md` — /wireframe slash command
  - `.claude/commands/schema.md` — /schema slash command
  - `.claude/commands/test.md`, `code.md`, `ship.md` — phase slash commands
  - `.agent/scripts/preflight-plan-sprint.sh` — 8-check non-interactive preflight
  - `.agent/scripts/preflight-plan-change.sh` — spec-change-specific preflight
  - `.agent/scripts/preflight-phase.sh` — shared preflight for all four phase agents
  - `.github/workflows/update-state.yml` — auto-ticks phase checkboxes on PR merge
  - `.gitea/workflows/update-state.yml` — Gitea Actions variant
  - `docs/project-state.md` — project state template (9-section structured markdown)
  - `docs/issue-template.md` — unified issue body template (12 sections including UI Specification)
  - `docs/ui-spec-template.md` — canonical UI specification format
  - `README.md` — install guide with `install-coding-agents.sh` script

### Added (examples)
- `examples/contract-manager-sprint-1/` — full orchestrator session worked example
  - `SESSION-TRANSCRIPT.md` — complete planning conversation
  - `sprint-1-summary.md`, `issue-body-US-001.md`, `issue-body-US-002.md`
  - `create-sprint-1-issues.sh`, `project-state-after-planning.md`
  - `wireframe-discussion.md` — orchestrator wireframe check example
- `examples/contract-manager-us001/` — full Phase 5–8 implementation worked example
  - `SESSION-TRANSCRIPT.md` — four-phase session with all agent conversations
  - `artifacts/` — Drizzle schema, Zod schemas, service, tests, CLAUDE.md, BEHAVIORS.md

### Changed
- `canon/quick-reference.md` — updated agent command reference table
- `STATUS.md` — reflects Step 9 completion
- `OPEN-ISSUES.md` — updated with remaining items

---

## Step 8 — SPEC.md System + Change Manifest (prior)

### Added
- `canon/spec-template.md` — 7-section SPEC.md structure
- `templates/discovery-agent-codex/scripts/generate_spec.py` — consolidates 5 discovery artifacts into SPEC.md
- `templates/discovery-agent-codex/scripts/generate_change_manifest.py` — diffs spec versions, maps changes to phases
- `canon/phase-handoffs.md` — formal contract between discovery and implementation phases

---

## Step 7 — Security + Permissions Pipeline (prior)

### Added
- `canon/guidelines/rbac.md` — RBAC approach 2 (dynamic roles, static permissions enum)
- `canon/guidelines/caller-context.md` — CallerContext pattern specification
- `templates/discovery-agent-codex/scripts/generate_test_shells.py` — auto-generates test shells with four org isolation tests
- `discovery-agent-codex/guides/permission-extraction-guide.md`
- Security scenarios (SB-1, SB-2, SB-3) mandated in behavioral test spec template

---

## Step 6 — Discovery Pipeline Hardening (prior)

### Added
- `canon/guidelines/agent-token-discipline.md`
- `canon/guidelines/claude-md-structure.md`
- Module definition card Section 6b (permissions)
- Data dictionary guide: Sensitive/PII column, Restricted To column, Security Boundaries

---

## Step 5 — Section 12 + Integrated Workflow (prior)

### Added
- `canon/section-12-integrated-workflow.md` — the eight-phase workflow (Phase 0–8)
- `canon/workflow-quick-reference.md` — one-page agent reference

---

## Steps 1–4 — Canon Foundation (prior)

- Sections 0–11 of the architecture canon
- Org context patterns (org-only, org-with-units, customer-account)
- Section 1b mandatory in all discovery checklists
- Behavioral test spec template with mandatory security scenarios
- Discovery agent Codex pipeline
