#!/usr/bin/env bash
# Sprint 1 issue creation — generated 2026-05-12
# Target version: v1.0.0 | Spec version: spec-v1.0 | Provider: github
# Project: contract-manager
#
# Review this script before running.
# To create all issues at once:
#   bash scripts/create-sprint-1-issues.sh
#
# To create one issue (for testing):
#   copy that gh command and run it.

set -euo pipefail

# ── Preconditions ──────────────────────────────────────────────────────
gh auth status || { echo "Error: gh CLI not authenticated. Run: gh auth login"; exit 1; }

# Verify the issue body files exist
for story in US-001 US-002; do
  if [ ! -f ".work/issue-bodies/${story}.md" ]; then
    echo "Error: .work/issue-bodies/${story}.md not found"
    echo "  Did the planning commit get checked out?"
    exit 1
  fi
done

# ── Create issues ──────────────────────────────────────────────────────
echo "Creating sprint 1 issues on GitHub..."

gh issue create \
  --title "US-001: AM can create a draft contract with required step-1 fields" \
  --label "user-story,sprint-1,module-contracts,phase-5,phase-6,phase-7,phase-8" \
  --body-file .work/issue-bodies/US-001.md \
  --assignee "@me"

gh issue create \
  --title "US-002: System logs contract creation in audit trail" \
  --label "user-story,sprint-1,module-contracts,phase-5,phase-6,phase-7,phase-8" \
  --body-file .work/issue-bodies/US-002.md \
  --assignee "@me"

echo ""
echo "Done. Created 2 issues for sprint 1."
echo ""
echo "Next steps:"
echo "  1. Begin US-001 with: /phase5 contracts US-001"
echo "  2. US-002 must wait — its preflight will block until US-001 is fully done"
