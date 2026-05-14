#!/usr/bin/env bash
# Preflight checks for /plan-sprint
#
# Exit codes:
#   0  — all checks passed, safe to proceed
#   1  — blocking error, cannot proceed (state file missing, spec drift, etc)
#   2  — warnings present, agent should ask developer before proceeding
#
# Output:
#   Lines prefixed BLOCKER:   — blocking errors with remediation
#   Lines prefixed WARNING:   — non-blocking warnings the agent surfaces to the dev
#   Lines prefixed OK:        — successful checks (informational)
#   Final line PREFLIGHT_RESULT=PASS | WARNINGS | BLOCKED
#
# This script runs non-interactively. The agent reads stdout/stderr and
# stages a natural-language summary for the developer.

set -uo pipefail   # no -e: we want to collect all problems, not stop at the first

WARNINGS=0
BLOCKERS=0

emit_blocker() {
  echo "BLOCKER: $1"
  if [ -n "${2:-}" ]; then
    echo "         Remediation: $2"
  fi
  BLOCKERS=$((BLOCKERS + 1))
}

emit_warning() {
  echo "WARNING: $1"
  WARNINGS=$((WARNINGS + 1))
}

emit_ok() {
  echo "OK: $1"
}

# ── 1. Project detection ──────────────────────────────────────────────
# Look for the workflow markers, not a generic indicator like package.json.
if [ ! -f "docs/project-state.md" ] || [ ! -f "docs/specs/SPEC.md" ]; then
  emit_blocker \
    "This doesn't look like an initialized agentic project repo." \
    "Run install-coding-agents.sh from the canon templates and ensure both docs/project-state.md and docs/specs/SPEC.md exist."
fi

# ── 2. Read the spec tag from project state ───────────────────────────
SPEC_TAG=""
if [ -f "docs/project-state.md" ]; then
  # Match the "| **Current spec tag** | _[spec-vX.Y]_ |" row, stripping italics/underscores
  SPEC_TAG=$(grep -i "Current spec tag" docs/project-state.md \
    | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z0-9.-]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
    | head -1)

  if [ -z "$SPEC_TAG" ] || [[ "$SPEC_TAG" == *"["* ]]; then
    emit_blocker \
      "Current spec tag missing from docs/project-state.md (Project info section)." \
      "Add a row: | **Current spec tag** | spec-v1.0 |"
    SPEC_TAG=""
  fi
fi

# ── 3. Validate spec tag exists in git ────────────────────────────────
if [ -n "$SPEC_TAG" ]; then
  if ! git rev-parse "$SPEC_TAG" >/dev/null 2>&1; then
    emit_blocker \
      "Spec tag '$SPEC_TAG' from project-state.md does not exist in this git repo." \
      "Either correct the tag in project-state.md, or run: git tag $SPEC_TAG && git push --tags"
  else
    emit_ok "Spec tag $SPEC_TAG exists"
  fi
fi

# ── 4. Validate SPEC.md matches the tagged version ────────────────────
if [ -n "$SPEC_TAG" ] && git rev-parse "$SPEC_TAG" >/dev/null 2>&1; then
  if ! git diff --quiet "$SPEC_TAG" -- docs/specs/SPEC.md 2>/dev/null; then
    emit_blocker \
      "docs/specs/SPEC.md has changed since it was tagged as $SPEC_TAG." \
      "The spec is meant to be locked at the tag. Either revert SPEC.md to match the tag, OR run the discovery agent's 'Update spec' mode to produce a new version and tag."
  else
    emit_ok "SPEC.md matches its locked tag"
  fi
fi

# ── 5. Issue provider configuration ───────────────────────────────────
if [ -f "docs/project-state.md" ]; then
  PROVIDER=$(grep -i "Issue provider" docs/project-state.md \
    | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
    | head -1)

  case "$PROVIDER" in
    github|gitea|manual)
      emit_ok "Issue provider: $PROVIDER"
      ;;
    "")
      emit_warning "Issue provider not configured in project-state.md. Orchestrator will ask."
      ;;
    *)
      emit_warning "Issue provider value '$PROVIDER' is not recognized. Expected: github, gitea, or manual."
      ;;
  esac
fi

# ── 6. Carry-over: open issues from a prior sprint ────────────────────
if [ -f "docs/project-state.md" ]; then
  # `grep -c` can return multi-line output via shell substitution; tr -d '\n'
  # collapses to a single value and || true keeps -uo from biting on no-match.
  OPEN_COUNT=$(grep -c "| open |" docs/project-state.md 2>/dev/null | tr -d '\n' || echo 0)
  PROGRESS_COUNT=$(grep -c "| in-progress |" docs/project-state.md 2>/dev/null | tr -d '\n' || echo 0)
  REVIEW_COUNT=$(grep -c "| in-review |" docs/project-state.md 2>/dev/null | tr -d '\n' || echo 0)
  OPEN_COUNT=${OPEN_COUNT:-0}
  PROGRESS_COUNT=${PROGRESS_COUNT:-0}
  REVIEW_COUNT=${REVIEW_COUNT:-0}
  TOTAL_OPEN=$((OPEN_COUNT + PROGRESS_COUNT + REVIEW_COUNT))

  if [ "$TOTAL_OPEN" -gt 0 ]; then
    emit_warning "$TOTAL_OPEN open/in-progress/in-review story rows in project-state.md. Carry-over to new sprint is allowed, but the orchestrator should ask about each one."
  fi
fi

# ── 7. Current branch ─────────────────────────────────────────────────
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
DEFAULT_BRANCH=""
if [ -f "docs/project-state.md" ]; then
  DEFAULT_BRANCH=$(grep -i "Default branch" docs/project-state.md \
    | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
    | head -1)
fi
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}

if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  emit_warning "On branch '$CURRENT_BRANCH', not '$DEFAULT_BRANCH'. Sprint planning normally happens on the default branch."
fi

# ── 8. Working directory cleanliness (untracked files included) ───────
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  emit_warning "Working directory is not clean (uncommitted or untracked files present). The orchestrator commits its planning artifacts — stage existing work first."
fi

# ── Summary ───────────────────────────────────────────────────────────
echo ""
if [ "$BLOCKERS" -gt 0 ]; then
  echo "PREFLIGHT_RESULT=BLOCKED"
  echo "BLOCKER_COUNT=$BLOCKERS"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  echo "PREFLIGHT_RESULT=WARNINGS"
  echo "WARNING_COUNT=$WARNINGS"
  exit 2
else
  echo "PREFLIGHT_RESULT=PASS"
  exit 0
fi
