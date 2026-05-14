#!/usr/bin/env bash
#
# sync-canon.sh
# Copies the canon files into a project's docs/architecture/ folder.
#
# USAGE:
#   bash /path/to/architecture-canon/tools/sync-canon.sh [target-project-dir]
#
# If no target dir is provided, syncs into the current working directory.
#
# WHAT IT DOES:
#   - Copies canon/* into <target>/docs/architecture/
#   - Removes any canon files that no longer exist in the source
#   - Adds a .canon-version file recording which canon version was synced
#   - Does NOT touch any other files in the project
#
# WHAT IT DOES NOT DO:
#   - Does not modify the canon repo (read-only operation against source)
#   - Does not run as part of every build — it's an explicit, deliberate update
#

set -euo pipefail

# ── Resolve paths ────────────────────────────────────────────────────

# Source: this script lives in <canon-repo>/tools/, so canon/ is one level up
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CANON_SOURCE_DIR="$( cd "${SCRIPT_DIR}/../canon" && pwd )"

# Target: argument or current working directory
TARGET_DIR="${1:-$(pwd)}"
if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Target directory does not exist: $TARGET_DIR"
  exit 1
fi

TARGET_CANON_DIR="${TARGET_DIR}/docs/architecture"

# ── Sanity check ─────────────────────────────────────────────────────

if [ ! -f "${CANON_SOURCE_DIR}/quick-reference.md" ]; then
  echo "❌ Canon source not found at ${CANON_SOURCE_DIR}"
  echo "   Are you running this from inside the architecture-canon repo?"
  exit 1
fi

# ── Confirm with the user ────────────────────────────────────────────

echo "📚 Architecture Canon sync"
echo "   Source: ${CANON_SOURCE_DIR}"
echo "   Target: ${TARGET_CANON_DIR}"
echo ""

if [ -d "$TARGET_CANON_DIR" ]; then
  echo "⚠  Target already exists. Existing canon files will be overwritten."
  echo "   Files in the project that aren't in the source will be removed."
  echo ""
  read -p "   Proceed? [y/N] " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   Cancelled."
    exit 0
  fi
fi

# ── Sync ─────────────────────────────────────────────────────────────

mkdir -p "$TARGET_CANON_DIR"

# Use rsync if available — handles deletes and is fast
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.canon-version' \
    "${CANON_SOURCE_DIR}/" "${TARGET_CANON_DIR}/"
else
  # Fallback: clear and copy
  rm -rf "${TARGET_CANON_DIR}"/*
  cp -r "${CANON_SOURCE_DIR}/." "${TARGET_CANON_DIR}/"
fi

# ── Stamp the version ────────────────────────────────────────────────

# If we're inside a git repo, use the canon's commit SHA. Otherwise, timestamp.
if git -C "${SCRIPT_DIR}" rev-parse --git-dir >/dev/null 2>&1; then
  CANON_VERSION="$(git -C "${SCRIPT_DIR}" rev-parse --short HEAD)"
  CANON_REF="$(git -C "${SCRIPT_DIR}" describe --tags --always 2>/dev/null || echo "${CANON_VERSION}")"
else
  CANON_VERSION="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  CANON_REF="$CANON_VERSION (no git history)"
fi

cat > "${TARGET_CANON_DIR}/.canon-version" <<EOF
# Canon sync record — DO NOT EDIT MANUALLY
# Re-run sync-canon.sh to update.

canon_version: ${CANON_VERSION}
canon_ref:     ${CANON_REF}
synced_at:     $(date -u +%Y-%m-%dT%H:%M:%SZ)
synced_by:     ${USER:-unknown}
EOF

# ── Add to .gitignore in target if not already ──────────────────────

# We track the synced canon in git (so all developers see it) but ignore
# the .canon-version file changes that happen on every sync — those just
# spam diffs without conveying useful changes.

if [ -f "${TARGET_DIR}/.gitignore" ]; then
  if ! grep -q "docs/architecture/.canon-version" "${TARGET_DIR}/.gitignore"; then
    echo "" >> "${TARGET_DIR}/.gitignore"
    echo "# Canon sync version stamp — managed by sync-canon.sh" >> "${TARGET_DIR}/.gitignore"
    echo "docs/architecture/.canon-version" >> "${TARGET_DIR}/.gitignore"
  fi
fi

echo ""
echo "✅ Canon synced successfully."
echo "   ${CANON_REF}"
echo ""
echo "   Read first: ${TARGET_CANON_DIR}/quick-reference.md"
