#!/usr/bin/env bash
# install-starter.sh
#
# Bootstraps a new agentic project from the architecture canon starter template.
# Run this ONCE when starting a new project, from the empty project repo root.
#
# Usage:
#   bash /path/to/architecture-canon/templates/starter/install-starter.sh \
#     --canon /path/to/architecture-canon \
#     --name "Contract Manager" \
#     --slug contract-manager \
#     --org-context org-with-units
#
# After running:
#   1. Review and commit the scaffolded files
#   2. Run `npm install`
#   3. Copy .env.example to .env.local and fill in values
#   4. Run install-coding-agents.sh (from templates/coding-agents/)
#   5. Fill in docs/project-state.md with project info
#   6. Run /plan-sprint

set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────

CANON_REPO=""
PROJECT_NAME=""
PROJECT_SLUG=""
ORG_CONTEXT=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --canon)       CANON_REPO="$2";    shift 2 ;;
    --name)        PROJECT_NAME="$2";  shift 2 ;;
    --slug)        PROJECT_SLUG="$2";  shift 2 ;;
    --org-context) ORG_CONTEXT="$2";   shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Validation ────────────────────────────────────────────────────────────────

if [ -z "$CANON_REPO" ] || [ -z "$PROJECT_NAME" ] || [ -z "$PROJECT_SLUG" ] || [ -z "$ORG_CONTEXT" ]; then
  echo "Usage: bash install-starter.sh \\"
  echo "  --canon /path/to/architecture-canon \\"
  echo "  --name 'My Project' \\"
  echo "  --slug my-project \\"
  echo "  --org-context [org-only|org-with-units|customer-account]"
  exit 1
fi

case "$ORG_CONTEXT" in
  org-only|org-with-units|customer-account) ;;
  *)
    echo "❌ --org-context must be: org-only, org-with-units, or customer-account"
    exit 1
    ;;
esac

STARTER="$CANON_REPO/templates/starter"

if [ ! -d "$STARTER" ]; then
  echo "❌ Starter template not found at $STARTER"
  exit 1
fi

if [ ! -f "package.json" ] && [ -n "$(ls -A . 2>/dev/null)" ]; then
  echo "⚠️  The current directory is not empty and has no package.json."
  echo "   Run this script from an empty directory or a fresh Next.js project root."
  read -p "Continue anyway? [y/N] " confirm
  [ "$confirm" = "y" ] || exit 1
fi

echo "🚀 Bootstrapping $PROJECT_NAME ($PROJECT_SLUG)"
echo "   Org context: $ORG_CONTEXT"
echo ""

# ── 1. Copy starter lib files ─────────────────────────────────────────────────

echo "📁 Copying lib/ files..."
mkdir -p lib/auth
cp "$STARTER/lib/auth/caller-context.ts" lib/auth/
cp "$STARTER/lib/auth/index.ts"          lib/auth/
cp "$STARTER/lib/auth/permissions.ts"    lib/auth/
cp "$STARTER/lib/audit.ts"               lib/
cp "$STARTER/lib/logger.ts"              lib/
cp "$STARTER/lib/types.ts"               lib/

# ── 2. Copy db scaffold ───────────────────────────────────────────────────────

echo "📁 Copying db/ scaffold..."
mkdir -p db/schema db/migrations
cp "$STARTER/db/index.ts"          db/
cp "$STARTER/db/schema/index.ts"   db/schema/
touch db/migrations/.gitkeep

# ── 3. Copy test helpers ──────────────────────────────────────────────────────

echo "📁 Copying tests/ helpers..."
mkdir -p tests/helpers tests/e2e
cp "$STARTER/tests/helpers/caller-context.ts" tests/helpers/
cp "$STARTER/tests/helpers/dates.ts"          tests/helpers/
cp "$STARTER/tests/setup.ts"                  tests/

# ── 4. Copy config files (if not already present) ─────────────────────────────

echo "📁 Copying config files..."

if [ ! -f "drizzle.config.ts" ]; then
  cp "$STARTER/drizzle.config.ts" .
else
  echo "   drizzle.config.ts already exists — keeping yours"
fi

if [ ! -f "vitest.config.ts" ]; then
  cp "$STARTER/vitest.config.ts" .
else
  echo "   vitest.config.ts already exists — keeping yours"
fi

if [ ! -f ".env.example" ]; then
  cp "$STARTER/.env.example" .
  sed -i "s/\[project-slug\]/$PROJECT_SLUG/g" .env.example
else
  echo "   .env.example already exists — keeping yours"
fi

# ── 5. Copy and customize CLAUDE.md ───────────────────────────────────────────

echo "📄 Setting up root CLAUDE.md..."

if [ -f "CLAUDE.md" ]; then
  echo "   CLAUDE.md already exists — backing up to CLAUDE.md.bak"
  cp CLAUDE.md CLAUDE.md.bak
fi

cp "$STARTER/CLAUDE.md" CLAUDE.md
# Replace placeholders
sed -i "s/\[Project Name\]/$PROJECT_NAME/g" CLAUDE.md
sed -i "s/\[org-only | org-with-units | customer-account\]/$ORG_CONTEXT/" CLAUDE.md

# ── 6. Create module scaffold directory ───────────────────────────────────────

mkdir -p modules
cat > modules/.gitkeep << 'EOF'
# modules/
# One directory per module. Created by the schema agent during Phase 5.
# Each module contains: *.schema.ts, *.service.ts, *.actions.ts,
# *.service.test.ts, BEHAVIORS.md, CLAUDE.md, components/
EOF

# ── 7. Merge package.json scripts ────────────────────────────────────────────

if [ -f "package.json" ]; then
  echo "📦 package.json exists — merging scripts section..."
  python3 << PYEOF
import json, sys

with open('package.json') as f:
    existing = json.load(f)

starter_scripts = {
    "test":            "vitest run",
    "test:watch":      "vitest",
    "test:e2e":        "playwright test",
    "db:generate":     "drizzle-kit generate",
    "db:migrate":      "drizzle-kit migrate",
    "db:migrate:down": "drizzle-kit migrate --rollback",
    "db:studio":       "drizzle-kit studio",
}

existing.setdefault('scripts', {})
for k, v in starter_scripts.items():
    if k not in existing['scripts']:
        existing['scripts'][k] = v
        print(f"  Added script: {k}")
    else:
        print(f"  Kept existing script: {k}")

with open('package.json', 'w') as f:
    json.dump(existing, f, indent=2)
    f.write('\n')
PYEOF
else
  echo "📦 No package.json found — copying starter package.json..."
  cp "$STARTER/package.json" .
  sed -i "s/\[project-slug\]/$PROJECT_SLUG/g" package.json
fi

# ── 8. Sync canon sections ────────────────────────────────────────────────────

echo "📚 Syncing architecture canon sections..."
if [ -f "$CANON_REPO/tools/sync-canon.sh" ]; then
  bash "$CANON_REPO/tools/sync-canon.sh" "$CANON_REPO"
  echo "   Canon synced to docs/architecture/"
else
  echo "   ⚠️  sync-canon.sh not found — copy canon sections manually to docs/architecture/"
fi

# ── 9. Install coding agents ─────────────────────────────────────────────────

echo ""
echo "📦 Installing coding agents..."
if [ -f "$CANON_REPO/templates/coding-agents/README.md" ]; then
  bash "$CANON_REPO/templates/coding-agents/install-coding-agents.sh" "$CANON_REPO"
else
  echo "   ⚠️  install-coding-agents.sh not found — install agents manually"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "✅ $PROJECT_NAME bootstrapped."
echo ""
echo "Next steps:"
echo "  1. Run:  npm install"
echo "  2. Copy: cp .env.example .env.local"
echo "  3. Fill in .env.local (DATABASE_URL, BETTER_AUTH_SECRET, etc.)"
echo "  4. Fill in docs/project-state.md (issue provider, spec tag, etc.)"
echo "  5. Set up your BetterAuth instance at lib/auth/auth.ts"
echo "     (see lib/auth/caller-context.ts for the session extension needed)"
echo "  6. Create the test database and run: npm run db:migrate"
echo "  7. In Claude Code: /plan-sprint"
echo ""
echo "Files created:"
find lib/ db/ tests/ modules/ -name "*.ts" 2>/dev/null | sort | sed 's/^/  /'
