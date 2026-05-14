#!/usr/bin/env bash
# install-coding-agents.sh
#
# Copies the coding agents from the architecture canon into a project repo.
# Run from the project repo root, passing the canon path as the first argument.
#
# Usage:
#   bash /path/to/architecture-canon/templates/coding-agents/install-coding-agents.sh \
#     /path/to/architecture-canon
#
# Example:
#   bash ~/work/architecture-canon/templates/coding-agents/install-coding-agents.sh \
#     ~/work/architecture-canon

set -euo pipefail

CANON_REPO="${1:-$HOME/work/architecture-canon}"

if [ ! -d "$CANON_REPO/templates/coding-agents" ]; then
  echo "❌ Canon repo not found at $CANON_REPO"
  echo "   Usage: bash install-coding-agents.sh /path/to/architecture-canon"
  exit 1
fi

echo "📦 Installing coding agents from $CANON_REPO"
echo ""

# 1. Copy the Claude agent and command files
mkdir -p .claude/agents .claude/commands
cp "$CANON_REPO/templates/coding-agents/.claude/agents/"*.md .claude/agents/
cp "$CANON_REPO/templates/coding-agents/.claude/commands/"*.md .claude/commands/
echo "✓ Agents and commands installed"

# 1b. Copy the preflight scripts used by slash commands
mkdir -p .agent/scripts
cp "$CANON_REPO/templates/coding-agents/.agent/scripts/"*.sh .agent/scripts/
chmod +x .agent/scripts/*.sh
echo "✓ Preflight scripts installed"

# 2. Copy the state file template (if not already present)
mkdir -p docs
if [ ! -f docs/project-state.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/project-state.md" docs/project-state.md
  echo "📝 Initialized docs/project-state.md — fill in Project info before /plan-sprint"
else
  echo "📝 docs/project-state.md already exists — keeping your version"
fi

# 3. Copy the issue and UI spec templates
if [ ! -f docs/issue-template.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/issue-template.md" docs/issue-template.md
fi
if [ ! -f docs/ui-spec-template.md ]; then
  cp "$CANON_REPO/templates/coding-agents/docs/ui-spec-template.md" docs/ui-spec-template.md
fi
echo "✓ Issue and UI spec templates installed"

# 4. Copy the state-update Actions workflow
# Detect platform from git remote
if git remote -v 2>/dev/null | grep -q "github.com"; then
  mkdir -p .github/workflows
  cp "$CANON_REPO/templates/coding-agents/.github/workflows/update-state.yml" .github/workflows/
  echo "⚙️  GitHub Actions workflow installed"
  echo "   Required: Settings → Actions → General → 'Read and write permissions'"
elif git remote -v 2>/dev/null | grep -qE "gitea|\.local"; then
  mkdir -p .gitea/workflows
  cp "$CANON_REPO/templates/coding-agents/.gitea/workflows/update-state.yml" .gitea/workflows/
  echo "⚙️  Gitea Actions workflow installed"
  echo "   Required secrets: GITEA_TOKEN"
  echo "   Required variables: GITEA_SERVER_URL"
else
  echo "⚠️  Remote not detected as GitHub or Gitea."
  echo "   Copy the workflow manually from:"
  echo "   $CANON_REPO/templates/coding-agents/.github/workflows/update-state.yml"
fi

# 5. Create the docs/wireframes directory
mkdir -p docs/wireframes
if [ ! -f docs/wireframes/.gitkeep ]; then
  cat > docs/wireframes/.gitkeep << 'EOF'
# docs/wireframes/
# PDFs:     [module-slug]-v[X.Y].pdf
# UI specs: [module-slug]-ui-spec.md
# Screenshots: [module-slug]-screenshots/
EOF
fi
echo "✓ docs/wireframes/ created"

# 6. Create the .work directory (where the orchestrator writes issue bodies)
mkdir -p .work/issue-bodies .work/sprint-plans
if [ ! -f .work/.gitignore ]; then
  cat > .work/.gitignore << 'EOF'
*.tmp
*.log
EOF
fi
echo "✓ .work/ directory created"

echo ""
echo "✅ Coding agents installed."
echo ""
echo "Next steps:"
echo "  1. Fill in docs/project-state.md (project name, slug, org context, issue provider)"
echo "  2. git add docs/ .claude/ .agent/ .github/ .gitea/ .work/"
echo "  3. git commit -m 'chore: install coding agents'"
echo "  4. Open project in Claude Code and run /plan-sprint"
