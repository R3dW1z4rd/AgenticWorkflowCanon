# Coding Agents — Setup for a Project Repo

*This folder contains the Claude Code agents that run Phase 5–8 of the integrated workflow.*
*Copy these files into your project repository after the Phase 4 handoff (SPEC.md sign-off).*

---

## What this folder contains

```
coding-agents/
├── .claude/
│   ├── agents/
│   │   ├── orchestrator.md      ← plans sprints, creates issues, reads wireframes
│   │   ├── wireframe-agent.md   ← produces ui-spec.md (analysis or generation mode)
│   │   ├── schema-agent.md      ← (next batch — Schema & Contracts)
│   │   ├── test-agent.md        ← (next batch — Failing Tests)
│   │   ├── code-agent.md        ← (next batch — Implementation)
│   │   └── ship-agent.md        ← (next batch — Integration)
│   └── commands/
│       ├── plan-sprint.md       ← /plan-sprint slash command
│       ├── wireframe.md         ← /wireframe [module] slash command
│       ├── plan-change.md       ← (next batch)
│       ├── status.md            ← (next batch)
│       ├── schema.md            ← (next batch)
│       ├── test.md              ← (next batch)
│       ├── code.md              ← (next batch)
│       └── ship.md              ← (next batch)
├── .agent/
│   └── scripts/
│       └── preflight-plan-sprint.sh  ← non-interactive precondition checks
├── .github/workflows/
│   └── update-state.yml         ← auto-updates project-state.md on PR merge (GitHub)
├── .gitea/workflows/
│   └── update-state.yml         ← Gitea Actions variant
└── docs/
    ├── project-state.md         ← project state template
    ├── issue-template.md        ← reference issue body structure
    └── ui-spec-template.md      ← UI specification template for wireframe agent
```

**Project repo docs/ structure (in the actual project, not this template):**

```
docs/
├── specs/
│   ├── SPEC.md                         ← locked at spec-vX.Y tag
│   └── CHANGE-MANIFEST-vX.Y.md         ← produced by discovery agent on spec update
├── wireframes/
│   ├── contracts-v1.2.pdf              ← client-approved wireframe PDF (committed)
│   ├── contracts-ui-spec.md            ← structured spec produced by /wireframe agent
│   ├── contracts-screenshots/          ← screenshots of built screens (reference material)
│   │   ├── contracts-list.png
│   │   └── contracts-create-step1.png
│   ├── customers-v1.0.pdf
│   └── customers-ui-spec.md
└── architecture/                       ← synced from canon by sync-canon.sh
    └── ...
```

---

## Installation in a project

After Phase 4 handoff (SPEC.md exists in the project repo, tagged as `spec-v1.0`), copy the coding agents into the project.

### One-time setup script

From the project repo root:

```bash
#!/usr/bin/env bash
set -euo pipefail

CANON_REPO="${1:-$HOME/work/architecture-canon}"

if [ ! -d "$CANON_REPO/templates/coding-agents" ]; then
  echo "❌ Canon repo not found at $CANON_REPO"
  echo "   Usage: bash install-coding-agents.sh /path/to/architecture-canon"
  exit 1
fi

# 1. Copy the Claude agent and command files
mkdir -p .claude/agents .claude/commands
cp "$CANON_REPO/templates/coding-agents/.claude/agents/"*.md .claude/agents/
cp "$CANON_REPO/templates/coding-agents/.claude/commands/"*.md .claude/commands/

# 1b. Copy the preflight script(s) used by slash commands
mkdir -p .agent/scripts
cp "$CANON_REPO/templates/coding-agents/.agent/scripts/"*.sh .agent/scripts/
chmod +x .agent/scripts/*.sh

# 2. Copy the state file template (if not already present)
mkdir -p docs
if [ ! -f docs/project-state.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/project-state.md" docs/project-state.md
  echo "📝 Initialized docs/project-state.md — fill in the project info section before /plan-sprint"
else
  echo "📝 docs/project-state.md already exists — keeping the project's version"
fi

# 3. Copy the issue and UI spec templates (reference for the team and for the wireframe agent)
if [ ! -f docs/issue-template.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/issue-template.md" docs/issue-template.md
fi
if [ ! -f docs/ui-spec-template.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/ui-spec-template.md" docs/ui-spec-template.md
fi

# 4. Copy the state-update Actions workflow
# Detect which platform the project uses
if git remote -v | grep -q "github.com"; then
  mkdir -p .github/workflows
  cp "$CANON_REPO/templates/coding-agents/.github/workflows/update-state.yml" .github/workflows/
  echo "⚙️  Installed GitHub Actions workflow"
  echo "   Required: repository's Actions must have 'Read and write' permissions"
  echo "   (Settings → Actions → General → Workflow permissions)"
elif git remote -v | grep -q "gitea\|local"; then
  mkdir -p .gitea/workflows
  cp "$CANON_REPO/templates/coding-agents/.gitea/workflows/update-state.yml" .gitea/workflows/
  echo "⚙️  Installed Gitea Actions workflow"
  echo "   Required secrets/variables:"
  echo "     - secrets.GITEA_TOKEN (repo write scope)"
  echo "     - vars.GITEA_SERVER_URL (e.g. https://gitea.local)"
else
  echo "⚠️  Could not detect GitHub or Gitea remote. Copy the workflow manually."
fi

# 5. Create the docs/wireframes directory (committed PDFs and ui-spec.md files go here)
mkdir -p docs/wireframes
cat > docs/wireframes/.gitkeep << 'EOF'
# docs/wireframes/
#
# Module wireframe PDFs committed here (client-approved designs):
#   [module-slug]-v[X.Y].pdf
#
# UI specification files produced by the /wireframe agent:
#   [module-slug]-ui-spec.md
#
# Screenshots of existing screens (used by the wireframe agent for inference):
#   [module-slug]-screenshots/[screen-name].png
#
# Run /wireframe [module-slug] to produce a ui-spec.md from a PDF or from scratch.
# Run /plan-sprint — the orchestrator reads ui-spec.md files automatically.
EOF

# 6. Create the issue body directory (gitignored — orchestrator writes here)
mkdir -p .work/issue-bodies
cat > .work/.gitignore << 'EOF'
# Issue bodies are committed; build artifacts are not
*.tmp
*.log
EOF

echo ""
echo "✅ Coding agents installed."
echo ""
echo "Next steps:"
echo "  1. Edit docs/project-state.md — fill in project info (name, slug, org context)"
echo "  2. Commit: git add docs/ .claude/ .github/ .gitea/ .work/ && git commit -m 'chore: install coding agents'"
echo "  3. Run /plan-sprint in Claude Code to plan your first sprint"
```

Save this as `install-coding-agents.sh` in the project root, then:

```bash
bash install-coding-agents.sh ~/work/architecture-canon
```

### Manual setup

If you prefer to copy files individually rather than run a script, the install script is the spec — read it and run each step by hand.

---

## Required secrets and permissions

### GitHub

| Setting | Where | Value |
|---|---|---|
| Workflow permissions | Repo Settings → Actions → General | "Read and write permissions" |
| `GITHUB_TOKEN` | Auto-provided by Actions | (no manual setup) |

The default `GITHUB_TOKEN` has issue read/write and contents read/write scope when "Read and write permissions" is enabled. No personal access token needed.

### Gitea

| Setting | Where | Value |
|---|---|---|
| Actions enabled | Repo Settings → Units → Actions | ✓ Enabled |
| `GITEA_TOKEN` secret | Repo Settings → Actions → Secrets | A token with `repo` scope |
| `GITEA_SERVER_URL` variable | Repo Settings → Actions → Variables | e.g. `https://gitea.local` |

You generate the `GITEA_TOKEN` from your user settings (Settings → Applications → Generate token) and add it as a repo secret.

---

## Verifying the install

After installation, run these checks in the project repo:

```bash
# 1. Agent files exist
ls .claude/agents/orchestrator.md              # should exist
ls .claude/agents/wireframe-agent.md           # should exist
ls .claude/commands/plan-sprint.md             # should exist
ls .claude/commands/wireframe.md               # should exist
ls .agent/scripts/preflight-plan-sprint.sh    # should exist and be executable

# 2. State file exists and has the right shape
grep -q "## Project info" docs/project-state.md && echo "✓ state file OK"

# 3. Wireframes directory exists
ls docs/wireframes/ && echo "✓ wireframes dir OK"

# 3. CI workflow installed (one of these should be true)
ls .github/workflows/update-state.yml 2>/dev/null && echo "✓ GitHub Actions installed"
ls .gitea/workflows/update-state.yml 2>/dev/null && echo "✓ Gitea Actions installed"

# 4. Spec is tagged
git tag --list 'spec-*' | head -1   # should show spec-v1.0 (or your version)

# 5. Claude Code can see the commands
# Open Claude Code in the project and type /
# You should see /plan-sprint in the autocomplete list
```

If all five pass, you're ready to run `/plan-sprint`.

---

## Workflow overview

```
                    ┌──────────────────────────────────┐
                    │   Phase 4 handoff complete        │
                    │   - SPEC.md in docs/specs/        │
                    │   - spec-v1.0 tag created         │
                    └──────────────────────────────────┘
                                    │
                                    ▼
                    bash install-coding-agents.sh
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │   /plan-sprint                    │
                    │   - orchestrator conversation     │
                    │   - generates issue script        │
                    │   - updates project-state.md      │
                    └──────────────────────────────────┘
                                    │
                                    ▼
                    bash scripts/create-sprint-1-issues.sh
                                    │
                                    ▼  (issues now exist in Gitea/GitHub)
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │   /phase5 [module] US-XXX         │
                    │   - schema & contracts            │
                    │   - PR opened → dev reviews →     │
                    │     dev merges → Actions updates  │
                    │     state automatically           │
                    └──────────────────────────────────┘
                                    │
                                    ▼  (repeat for phases 6, 7, 8)
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │   /phase8 merged → issue closed   │
                    │   automatically                   │
                    └──────────────────────────────────┘
                                    │
                                    ▼  (repeat for next story)
                                    │
                                    ▼
                    /plan-sprint    (next sprint)
                                    or
                    /plan-change    (after spec update)
                                    or
                    /status         (review progress)
```

---

## Status of this template

Currently shipped:
- ✅ Orchestrator agent (`orchestrator.md`)
- ✅ `/plan-sprint` command
- ✅ Project state template
- ✅ Issue template
- ✅ GitHub Actions workflow
- ✅ Gitea Actions workflow

Coming next:
- 🚧 Phase 5 specialist (Schema & Contracts)
- 🚧 Phase 6 specialist (Failing Tests)
- 🚧 Phase 7 specialist (Implementation)
- 🚧 Phase 8 specialist (Integration)
- 🚧 `/plan-change` command (for spec updates)
- 🚧 `/status` command (read-only state review)
- 🚧 `/phase5`, `/phase6`, `/phase7`, `/phase8` slash commands
