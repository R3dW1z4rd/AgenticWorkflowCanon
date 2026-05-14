#!/usr/bin/env bash
# Preflight checks for phase slash commands (/schema, /test, /code, /ship)
#
# Usage:
#   bash .agent/scripts/preflight-phase.sh schema contracts US-001
#   bash .agent/scripts/preflight-phase.sh test contracts US-001
#   bash .agent/scripts/preflight-phase.sh code contracts US-001
#   bash .agent/scripts/preflight-phase.sh ship contracts US-001
#
# Exit codes:
#   0  — PREFLIGHT_RESULT=PASS
#   1  — PREFLIGHT_RESULT=BLOCKED  (must fix before proceeding)
#   2  — PREFLIGHT_RESULT=WARNINGS (agent asks developer before proceeding)
#
# Each line of output is prefixed: BLOCKER: / WARNING: / OK:
# Last line is always: PREFLIGHT_RESULT=PASS|WARNINGS|BLOCKED

set -uo pipefail

# ── Arguments ─────────────────────────────────────────────────────────

PHASE_NAME="${1:-}"
MODULE_SLUG="${2:-}"
STORY_ID="${3:-}"

if [ -z "$PHASE_NAME" ] || [ -z "$MODULE_SLUG" ] || [ -z "$STORY_ID" ]; then
  echo "BLOCKER: Missing arguments."
  echo "         Usage: bash .agent/scripts/preflight-phase.sh [schema|test|code|ship] [module-slug] [US-XXX]"
  echo "PREFLIGHT_RESULT=BLOCKED"
  exit 1
fi

# Map phase name to number (for branch detection and state file)
case "$PHASE_NAME" in
  schema|5) PHASE_NUM=5; PHASE_NAME=schema ;;
  test|6)   PHASE_NUM=6; PHASE_NAME=test   ;;
  code|7)   PHASE_NUM=7; PHASE_NAME=code   ;;
  ship|8)   PHASE_NUM=8; PHASE_NAME=ship   ;;
  *)
    echo "BLOCKER: Unknown phase '$PHASE_NAME'. Expected: schema, test, code, or ship."
    echo "PREFLIGHT_RESULT=BLOCKED"
    exit 1
    ;;
esac

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

# ── 2. Story ID format ─────────────────────────────────────────────────

if ! echo "$STORY_ID" | grep -qE '^US-[0-9]+$'; then
  emit_blocker \
    "Story ID '$STORY_ID' is not in the expected format." \
    "Use the format US-001, US-042, etc."
fi

# ── 3. Check that the previous phase is complete (dependency gate) ─────
#
# Phase ordering: schema(5) → test(6) → code(7) → ship(8)
# Each phase requires the previous one to be complete (merged to main).
# We detect this by checking the phase checkboxes in project-state.md.
#
# project-state.md sprint table row format:
#   | US-001 | title | module | status | ✓ ☐ ☐ ☐ | notes |
#   Indexes: phase 5=pos0, 6=pos1, 7=pos2, 8=pos3

if [ -f "docs/project-state.md" ] && echo "$STORY_ID" | grep -qE '^US-[0-9]+$'; then
  STORY_ROW=$(grep "| ${STORY_ID} |" docs/project-state.md | head -1)

  if [ -z "$STORY_ROW" ]; then
    emit_blocker \
      "$STORY_ID not found in docs/project-state.md." \
      "Run /plan-sprint to add it to the sprint, or check the story ID."
  else
    # Extract the phase checkboxes (4 characters: ✓ or ☐)
    PHASE_CELLS=$(echo "$STORY_ROW" | python3 -c "
import sys, re
row = sys.stdin.read()
boxes = re.findall(r'[✓☐]', row)
print(''.join(boxes[:4]) if len(boxes) >= 4 else '')
" 2>/dev/null)

    if [ -z "$PHASE_CELLS" ]; then
      emit_warning \
        "Could not parse phase checkboxes for $STORY_ID in project-state.md."
    else
      # Check that all prior phases are complete
      PREV_PHASE=$((PHASE_NUM - 1))
      if [ "$PHASE_NUM" -gt 5 ]; then
        PREV_IDX=$((PHASE_NUM - 6))   # phase 6→idx0, 7→idx1, 8→idx2
        PREV_CHAR=$(echo "$PHASE_CELLS" | cut -c$((PREV_IDX + 1)))
        if [ "$PREV_CHAR" != "✓" ]; then
          emit_blocker \
            "Phase $PREV_PHASE is not yet complete for $STORY_ID." \
            "Merge the Phase $PREV_PHASE PR first, then re-run /$PHASE_NAME $MODULE_SLUG $STORY_ID."
        else
          emit_ok "Phase $PREV_PHASE complete for $STORY_ID"
        fi
      fi

      # Check this phase isn't already done
      CURR_IDX=$((PHASE_NUM - 5))
      CURR_CHAR=$(echo "$PHASE_CELLS" | cut -c${CURR_IDX})
      if [ "$CURR_CHAR" = "✓" ]; then
        emit_warning \
          "Phase $PHASE_NUM already marked complete for $STORY_ID in project-state.md. Running again?"
      fi
    fi
  fi
fi

# ── 4. No open PR already exists for this phase/story ─────────────────
#
# Branch naming convention: feat/[module]-phase[N]-[anything]-US-XXX
# Check whether such a branch exists remotely (would indicate work in flight).

BRANCH_PATTERN="feat/${MODULE_SLUG}-phase${PHASE_NUM}-"
EXISTING_BRANCH=$(git branch -a 2>/dev/null | grep -m1 "$BRANCH_PATTERN" | tr -d ' *' || echo "")

if [ -n "$EXISTING_BRANCH" ]; then
  emit_warning \
    "A branch matching '$BRANCH_PATTERN' already exists: $EXISTING_BRANCH. Is Phase $PHASE_NUM already in progress?"
fi

# ── 5. Working directory clean ─────────────────────────────────────────

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  emit_warning \
    "Working directory is not clean. Commit or stash uncommitted changes before starting Phase $PHASE_NUM."
fi

# ── 6. On or near the default branch ──────────────────────────────────

DEFAULT_BRANCH=$(grep -i "Default branch" docs/project-state.md 2>/dev/null \
  | sed -E 's/.*\|[[:space:]]*\*?_?\[?([a-z]+)\]?_?\*?[[:space:]]*\|.*/\1/' \
  | head -1)
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
  # Warn unless already on a phase branch for this story (resuming work)
  if ! echo "$CURRENT_BRANCH" | grep -q "$STORY_ID"; then
    emit_warning \
      "On branch '$CURRENT_BRANCH', not '$DEFAULT_BRANCH'. Phase work should start from the default branch."
  fi
fi

# ── 7. Module slug exists in SPEC.md ──────────────────────────────────

if [ -f "docs/specs/SPEC.md" ]; then
  if ! grep -qi "slug.*${MODULE_SLUG}\|${MODULE_SLUG}.*slug\|\`${MODULE_SLUG}\`" docs/specs/SPEC.md 2>/dev/null; then
    emit_warning \
      "Module slug '$MODULE_SLUG' not clearly found in docs/specs/SPEC.md. Verify the slug matches the SPEC."
  else
    emit_ok "Module '$MODULE_SLUG' found in SPEC.md"
  fi
fi

# ── 8. ui-spec.md present for UI-bearing stories (warning only) ────────
#
# Non-UI phases (schema for backend-only stories) don't need this.
# For code (phase 7), missing ui-spec is a real concern.

if [ "$PHASE_NUM" -ge 7 ]; then
  UI_SPEC="docs/wireframes/${MODULE_SLUG}-ui-spec.md"
  if [ ! -f "$UI_SPEC" ]; then
    emit_warning \
      "No ui-spec.md found at $UI_SPEC. If this story has UI work, run '/wireframe $MODULE_SLUG' first. If backend-only, ignore this warning."
  else
    emit_ok "ui-spec.md found for $MODULE_SLUG"
  fi
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
