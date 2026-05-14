#!/usr/bin/env bash
# Preflight checks for /plan-change
#
# Different from preflight-plan-sprint.sh because plan-change requires:
#   - A NEW spec tag that differs from the current one in project-state.md
#   - A CHANGE-MANIFEST file for that new spec version
#   - The new SPEC.md to match the new tag (no drift)
#
# Exit codes:
#   0  — PREFLIGHT_RESULT=PASS
#   1  — PREFLIGHT_RESULT=BLOCKED
#   2  — PREFLIGHT_RESULT=WARNINGS

set -uo pipefail

WARNINGS=0
BLOCKERS=0

emit_blocker() {
  echo "BLOCKER: $1"
  [ -n "${2:-}" ] && echo "         Remediation: $2"
  BLOCKERS=$((BLOCKERS + 1))
}

emit_warning() {
  echo "WARNING: $1"
  WARNINGS=$((WARNINGS + 1))
}

emit_ok() {
  echo "OK: $1"
}

# ── 1. Project detection ───────────────────────────────────────────────

if [ ! -f "docs/project-state.md" ] || [ ! -f "docs/specs/SPEC.md" ]; then
  emit_blocker \
    "This doesn't look like an initialized agentic project repo." \
    "Run install-coding-agents.sh from the canon templates."
fi

# ── 2. Read current spec tag from project state ────────────────────────

CURRENT_SPEC_TAG=""
if [ -f "docs/project-state.md" ]; then
  CURRENT_SPEC_TAG=$(grep -i "Current spec tag" docs/project-state.md \
    | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z0-9.-]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
    | head -1)
fi

if [ -z "$CURRENT_SPEC_TAG" ] || [[ "$CURRENT_SPEC_TAG" == *"["* ]]; then
  emit_blocker \
    "current_spec_tag not set in docs/project-state.md." \
    "Add or update: | **Current spec tag** | spec-v1.0 |"
  CURRENT_SPEC_TAG=""
else
  emit_ok "Current spec tag: $CURRENT_SPEC_TAG"
fi

# ── 3. Find the newest spec tag in git ────────────────────────────────

LATEST_SPEC_TAG=$(git tag --list 'spec-*' 2>/dev/null | sort -V | tail -1)

if [ -z "$LATEST_SPEC_TAG" ]; then
  emit_blocker \
    "No spec tags found in git (expected: spec-vX.Y)." \
    "The discovery agent should tag SPEC.md when it produces a new version."
else
  emit_ok "Latest spec tag in git: $LATEST_SPEC_TAG"
fi

# ── 4. Confirm there IS a new tag (plan-change requires a version bump) ─

if [ -n "$CURRENT_SPEC_TAG" ] && [ -n "$LATEST_SPEC_TAG" ]; then
  if [ "$CURRENT_SPEC_TAG" = "$LATEST_SPEC_TAG" ]; then
    emit_blocker \
      "The latest spec tag ($LATEST_SPEC_TAG) is the same as the current tag in project-state.md." \
      "plan-change requires a new spec version. If the spec hasn't changed, use /plan-sprint instead. If the spec was just updated, ensure the discovery agent tagged the new SPEC.md."
  else
    emit_ok "New spec version detected: $CURRENT_SPEC_TAG → $LATEST_SPEC_TAG"
  fi
fi

# ── 5. Confirm SPEC.md matches the new tag (no drift) ─────────────────

if [ -n "$LATEST_SPEC_TAG" ] && git rev-parse "$LATEST_SPEC_TAG" >/dev/null 2>&1; then
  if ! git diff --quiet "$LATEST_SPEC_TAG" -- docs/specs/SPEC.md 2>/dev/null; then
    emit_blocker \
      "docs/specs/SPEC.md has changed since the latest tag ($LATEST_SPEC_TAG)." \
      "Either the tag is stale or SPEC.md was modified after tagging. Re-tag after the final SPEC.md is confirmed."
  else
    emit_ok "SPEC.md matches tag $LATEST_SPEC_TAG"
  fi
fi

# ── 6. CHANGE-MANIFEST exists for the new spec version ────────────────

if [ -n "$LATEST_SPEC_TAG" ]; then
  # Derive version string from tag (spec-v1.1 → v1.1)
  SPEC_VERSION="${LATEST_SPEC_TAG#spec-}"
  MANIFEST_PATH="docs/specs/CHANGE-MANIFEST-${SPEC_VERSION}.md"

  if [ ! -f "$MANIFEST_PATH" ]; then
    emit_blocker \
      "Change manifest not found: $MANIFEST_PATH" \
      "The discovery agent should produce a CHANGE-MANIFEST when updating the spec. Run the discovery agent's 'Update spec' mode first."
  else
    emit_ok "Change manifest found: $MANIFEST_PATH"
  fi
fi

# ── 7. In-progress phase work warning ─────────────────────────────────
# Warn if there are stories currently in-progress — a spec change mid-sprint
# can create conflicts the developer should be aware of.

if [ -f "docs/project-state.md" ]; then
  IN_PROGRESS=$(grep -c "| in-progress |" docs/project-state.md 2>/dev/null | tr -d '\n' || echo 0)
  IN_PROGRESS=${IN_PROGRESS:-0}
  if [ "$IN_PROGRESS" -gt 0 ]; then
    emit_warning \
      "$IN_PROGRESS stories are currently in-progress. A spec change mid-sprint may create conflicts. Consider waiting until in-progress stories complete, or discuss with the orchestrator how to sequence the change."
  fi
fi

# ── 8. Working directory clean ─────────────────────────────────────────

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  emit_warning \
    "Working directory is not clean. Commit or stash changes before planning a spec change."
fi

# ── 9. Issue provider configured ──────────────────────────────────────

if [ -f "docs/project-state.md" ]; then
  PROVIDER=$(grep -i "Issue provider" docs/project-state.md \
    | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
    | head -1)
  case "${PROVIDER:-}" in
    github|gitea|manual) emit_ok "Issue provider: $PROVIDER" ;;
    "") emit_warning "Issue provider not configured in project-state.md." ;;
    *)  emit_warning "Issue provider '$PROVIDER' not recognised. Expected: github, gitea, or manual." ;;
  esac
fi

# ── Summary ────────────────────────────────────────────────────────────

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
