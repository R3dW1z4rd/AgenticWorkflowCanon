#!/usr/bin/env python3
"""
generate_change_manifest.py — Produce a change manifest from a SPEC.md diff.

Compares SPEC-previous.md with the newly generated SPEC.md and produces a
structured change manifest listing what changed and which coding phases are
affected. The discovery agent then annotates the manifest with specific
file-level impacts before it goes to the Phase 4 gate review.

Usage:
  python3 generate_change_manifest.py [project-slug]
  python3 generate_change_manifest.py [project-slug] --old path/to/SPEC-previous.md

Reads:
  workspace/[slug]/SPEC-previous.md    ← the old spec (saved before update)
  workspace/[slug]/exports/SPEC.md     ← the new spec (just generated)

Outputs:
  workspace/[slug]/exports/CHANGE-MANIFEST-vX.Y.md

The manifest is in two parts:
  Part A (script-generated): which sections changed, which phases are affected
  Part B (agent-completed): specific files to modify per phase, what does not change

Agents: after running this script, review the output and complete every
        section marked [AGENT: complete this].
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


# ── Path helpers ─────────────────────────────────────────────────────

def workspace_dir(slug: str) -> Path:
    return Path("workspace") / slug

def exports_dir(slug: str) -> Path:
    return workspace_dir(slug) / "exports"

def previous_spec_path(slug: str) -> Path:
    return workspace_dir(slug) / "SPEC-previous.md"

def current_spec_path(slug: str) -> Path:
    return exports_dir(slug) / "SPEC.md"


# ── Section-to-phase mapping ─────────────────────────────────────────
#
# Each entry: (regex pattern matching section heading, phases affected, explanation)
# Phases: '5'=Schema, '6'=Tests, '7'=Implementation, '8'=Integration

SECTION_PHASE_RULES: list[tuple[str, list[str], str]] = [
    # Org context — the most fundamental change possible
    (
        r'##\s+3[\.\s].*[Oo]rganizational',
        ['5', '6', '7', '8'],
        'CRITICAL: org_context change ripples through the entire module. '
        'Every phase needs review. Verify data model, isolation tests, and auth model.',
    ),
    # System map — actors, integrations
    (
        r'##\s+4[\.\s].*[Ss]ystem [Mm]ap',
        ['5', '7', '8'],
        'New actor or integration may require schema changes, new service methods, '
        'and new E2E flows.',
    ),
    # Core flow — the numbered steps
    (
        r'####\s+6\.\d+\.4.*[Cc]ore [Ff]low',
        ['6', '7', '8'],
        'Flow change affects test coverage, service logic, and E2E scenarios.',
    ),
    # States and transitions
    (
        r'####\s+6\.\d+\.5.*[Ss]tates',
        ['5', '6', '7', '8'],
        'State changes may require schema enum update, new migration, updated tests, '
        'and updated service transition logic.',
    ),
    # Data dictionary — field-level changes
    (
        r'####\s+6\.\d+\.6.*[Dd]ata [Dd]ictionary',
        ['5', '6', '7', '8'],
        'Data model change requires: migration, Zod schema update, service update, '
        'component update, and test update.',
    ),
    # Acceptance criteria
    (
        r'####\s+6\.\d+\.7.*[Aa]cceptance',
        ['6', '7', '8'],
        'AC changes affect test code, service implementation, and E2E scenarios.',
    ),
    # Behavioral specs
    (
        r'####\s+6\.\d+\.8.*[Bb]ehavioral',
        ['6', '7'],
        'Behavior changes affect test code and service implementation.',
    ),
    # Permissions
    (
        r'####\s+6\.\d+\.9.*[Pp]ermissions',
        ['5', '6', '7', '8'],
        'Permission changes affect: lib/auth/permissions.ts, service action guards, '
        'SB-2 security test scenarios, and E2E permission boundary tests.',
    ),
    # Out of scope — usually just documentation
    (
        r'####\s+6\.\d+\.10.*[Oo]ut of [Ss]cope',
        [],
        'Scope clarification only. Verify no code was relying on the removed scope.',
    ),
    # Cross-module relationships
    (
        r'##\s+7[\.\s].*[Cc]ross',
        ['5', '7'],
        'Cross-module change may affect lib/joins/ or lib/services/ coordinating services.',
    ),
]

PHASE_NAMES = {
    '5': 'Schema & Contracts',
    '6': 'Failing Tests',
    '7': 'Implementation',
    '8': 'Integration & Polish',
}


# ── Spec parsing ─────────────────────────────────────────────────────

@dataclass
class SpecSection:
    heading:   str
    content:   str
    level:     int     # 1=#, 2=##, 3=###, 4=####
    module_ref: str | None = None   # e.g. "6.1" if inside a module section


def parse_spec(text: str) -> dict[str, SpecSection]:
    """
    Split a SPEC.md into sections keyed by their heading.
    Returns {heading: SpecSection}.
    """
    sections: dict[str, SpecSection] = {}
    # Split on any heading line
    parts = re.split(r'\n(#{1,4}\s+[^\n]+)', text)
    # parts[0] = preamble before first heading
    # parts[1,3,5,...] = headings
    # parts[2,4,6,...] = content

    for i in range(1, len(parts) - 1, 2):
        heading_line = parts[i].strip()
        content      = parts[i + 1] if (i + 1) < len(parts) else ""
        level        = len(re.match(r'^(#+)', heading_line).group(1))
        heading_text = re.sub(r'^#+\s*', '', heading_line)

        # Detect module reference (e.g. "6.1 Contract Creation")
        module_ref = None
        m = re.match(r'^6\.(\d+)', heading_text)
        if m:
            module_ref = f"6.{m.group(1)}"

        sections[heading_text] = SpecSection(
            heading    = heading_text,
            content    = content.strip(),
            level      = level,
            module_ref = module_ref,
        )

    return sections


def extract_version(text: str) -> str:
    """Extract version string (e.g. 'v1.0') from a SPEC.md header."""
    m = re.search(r'Version:\s*(v[\d.]+)', text)
    return m.group(1) if m else "v?.?"


def extract_project_name(text: str) -> str:
    """Extract project name from the first H1 heading."""
    m = re.search(r'^#\s+SPEC\s+[—–-]\s+(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else "Unknown Project"


# ── Diff logic ───────────────────────────────────────────────────────

@dataclass
class SectionChange:
    heading:       str
    change_type:   str   # 'modified' | 'added' | 'removed'
    phases:        list[str]
    explanations:  list[str]
    is_new_module: bool = False


def detect_changes(
    old_sections: dict[str, SpecSection],
    new_sections: dict[str, SpecSection],
) -> list[SectionChange]:
    """
    Compare two parsed specs section by section.
    Returns a list of changed sections with their phase impact.
    """
    changes: list[SectionChange] = []
    all_headings = set(old_sections) | set(new_sections)

    for heading in all_headings:
        old = old_sections.get(heading)
        new = new_sections.get(heading)

        if old is None and new is not None:
            change_type = 'added'
        elif old is not None and new is None:
            change_type = 'removed'
        elif old.content.strip() != new.content.strip():
            change_type = 'modified'
        else:
            continue  # unchanged

        # Detect new module addition (new top-level module section)
        is_new_module = (
            change_type == 'added'
            and new is not None
            and new.level == 3
            and re.match(r'^6\.\d+\s', heading)
        )

        # Apply phase mapping rules
        phases: list[str] = []
        explanations: list[str] = []

        if is_new_module:
            phases       = ['5', '6', '7', '8']
            explanations = ['New module requires full pipeline (Phases 5–8).']
        else:
            for pattern, rule_phases, explanation in SECTION_PHASE_RULES:
                if re.search(pattern, heading, re.IGNORECASE):
                    for p in rule_phases:
                        if p not in phases:
                            phases.append(p)
                    if explanation not in explanations:
                        explanations.append(explanation)

        # If no rule matched, flag for agent review
        if not phases and change_type != 'removed':
            phases       = ['?']
            explanations = ['No phase rule matched — agent should assess impact.']

        changes.append(SectionChange(
            heading       = heading,
            change_type   = change_type,
            phases        = sorted(set(phases)),
            explanations  = explanations,
            is_new_module = is_new_module,
        ))

    return changes


# ── Manifest generation ───────────────────────────────────────────────

def generate_manifest(
    slug:       str,
    old_text:   str,
    new_text:   str,
    today:      str,
) -> str:
    old_version     = extract_version(old_text)
    new_version     = extract_version(new_text)
    project_name    = extract_project_name(new_text)

    old_sections    = parse_spec(old_text)
    new_sections    = parse_spec(new_text)
    changes         = detect_changes(old_sections, new_sections)

    # Collect all affected phases across all changes
    all_phases: set[str] = set()
    for c in changes:
        for p in c.phases:
            if p != '?':
                all_phases.add(p)

    # Group changes by type
    modified = [c for c in changes if c.change_type == 'modified']
    added    = [c for c in changes if c.change_type == 'added']
    removed  = [c for c in changes if c.change_type == 'removed']

    has_new_module   = any(c.is_new_module for c in changes)
    has_full_rerun   = all_phases == {'5', '6', '7', '8'}
    has_unknown      = any('?' in c.phases for c in changes)

    lines: list[str] = []
    A = lines.append

    # ── Header ─────────────────────────────────────────────────────
    A(f"# Change Manifest — {old_version} → {new_version}")
    A(f"*Project: {project_name} | Generated: {today} | Status: Draft — agent annotation required*")
    A("")
    A("## Sign-offs")
    A("")
    A("| Role | Name | Date | Status |")
    A("|---|---|---|---|")
    A("| Business Analyst | _[fill]_ | _[YYYY-MM-DD]_ | ☐ Pending |")
    A("| Dev Lead | _[fill]_ | _[YYYY-MM-DD]_ | ☐ Pending |")
    A("")
    A("> **Both sign-offs are required before the coding agent begins any change implementation.**")
    A("")

    # ── Summary ────────────────────────────────────────────────────
    A("## Summary")
    A("")

    if has_full_rerun:
        A("⚠️ **This change affects all four coding phases.** Review carefully before proceeding.")
    elif has_new_module:
        A("A new module has been added. It requires a full pipeline run (Phases 5–8) alongside any partial re-runs for existing modules.")
    else:
        phases_affected = sorted(all_phases)
        phase_names = [f"Phase {p} ({PHASE_NAMES[p]})" for p in phases_affected if p in PHASE_NAMES]
        A(f"This change affects: {', '.join(phase_names) if phase_names else 'unknown — see below'}.")

    if has_unknown:
        A("")
        A("⚠️ Some sections had no automatic phase mapping — see **Agent review required** below.")

    A("")
    A("*[AGENT: Add a 2–3 sentence plain-English summary of what the client requested and why.]*")
    A("")

    # ── Changed sections ───────────────────────────────────────────
    A("## Spec sections changed")
    A("")

    if modified:
        A("### Modified")
        for c in modified:
            phase_str = ', '.join(f"Phase {p}" for p in c.phases) or "none"
            A(f"- **{c.heading}** → affects {phase_str}")
    if added:
        A("")
        A("### Added")
        for c in added:
            label = " *(new module — full pipeline)*" if c.is_new_module else ""
            A(f"- **{c.heading}**{label}")
    if removed:
        A("")
        A("### Removed")
        for c in removed:
            A(f"- **{c.heading}** ⚠️ verify no code depends on this")
    if not changes:
        A("*No structural section changes detected. Check that the spec was actually updated.*")

    A("")

    # ── Impact by phase ────────────────────────────────────────────
    A("## Impact by phase")
    A("")
    A("*Part A (script-generated) identifies which phases are affected and why.*")
    A("*Part B ([AGENT: ...] markers) must be completed before gate review.*")
    A("")

    for phase_id, phase_name in PHASE_NAMES.items():
        phase_changes = [c for c in changes if phase_id in c.phases]

        if not phase_changes:
            A(f"### Phase {phase_id} — {phase_name}")
            A("**Status: NOT AFFECTED** — no changes required in this phase.")
            A("")
            continue

        is_full = all_phases == {'5', '6', '7', '8'}
        status  = "FULL RE-RUN" if is_full else "PARTIAL RE-RUN"

        A(f"### Phase {phase_id} — {phase_name}")
        A(f"**Status: {status}**")
        A("")
        A("**Driven by:**")
        seen_explanations: set[str] = set()
        for c in phase_changes:
            for exp in c.explanations:
                if exp not in seen_explanations:
                    A(f"- {c.heading}: {exp}")
                    seen_explanations.add(exp)
        A("")
        A("**Files to modify:**")
        A("*[AGENT: list specific files below — use MODIFY / NEW / DELETE prefix]*")
        A("")
        A("```")
        A("MODIFY:  [file path] — [what changes]")
        A("MODIFY:  [file path] — [what changes]")
        A("NEW:     [file path] — [what it contains]")
        A("```")
        A("")

    # ── Unknown impact ─────────────────────────────────────────────
    unknown_changes = [c for c in changes if '?' in c.phases]
    if unknown_changes:
        A("### Phase ? — Agent review required")
        A("")
        A("These sections changed but no automatic phase rule matched.")
        A("The agent must assess the impact before completing the manifest.")
        A("")
        for c in unknown_changes:
            A(f"- **{c.heading}** ({c.change_type})")
        A("")

    # ── What does NOT change ───────────────────────────────────────
    A("## What does NOT change")
    A("")
    A("*Explicitly stating what is unaffected is as important as what is affected.*")
    A("*An agent that knows what to leave alone is faster and safer.*")
    A("")
    A("*[AGENT: Complete this section. For each major feature of the module, state whether it is affected or not.]*")
    A("")
    A("| Feature / component | Status | Notes |")
    A("|---|---|---|")
    A("| Org isolation and orgId scoping | ☐ Unchanged ☐ Affected | |")
    A("| Permission model | ☐ Unchanged ☐ Affected | |")
    A("| Forex API integration | ☐ Unchanged ☐ Affected | |")
    A("| Cross-module relationships | ☐ Unchanged ☐ Affected | |")
    A("| Audit trail and logging | ☐ Unchanged ☐ Affected | |")
    A("| E2E permission boundary tests | ☐ Unchanged ☐ Affected | |")
    A("| Org isolation tests (4 required) | ☐ Unchanged ☐ Affected | |")
    A("| *[add rows for module-specific features]* | | |")
    A("")

    # ── Coding agent instructions ──────────────────────────────────
    A("## Instructions for the coding agent")
    A("")
    A("1. Read this manifest **before** reading any code files.")
    A("2. Load the change manifest alongside SPEC.md at session start.")
    A("3. For each phase listed as NOT AFFECTED: do not touch those files.")
    A("4. For each phase listed as PARTIAL RE-RUN: modify only the listed files.")
    A("5. For FULL RE-RUN phases: treat as a fresh phase but preserve what the manifest marks as unchanged.")
    A("6. Branch name: `feat/[module-slug]-change-[new-version]-[short-description]`")
    A("7. Commit message prefix: `change([module-slug]): [spec-version] — [description]`")
    A("")
    A("*The change manifest is the primary context for this session.*")
    A("*SPEC.md is the reference. The manifest tells you where to look in the spec.*")
    A("")

    # ── Unchanged modules ──────────────────────────────────────────
    # Detect module sections from old spec that don't appear in changes
    old_modules = {
        h: s for h, s in old_sections.items()
        if s.level == 3 and re.match(r'^6\.\d+\s', h)
    }
    changed_module_headings = {c.heading for c in changes}
    unchanged_modules = [h for h in old_modules if h not in changed_module_headings]

    if unchanged_modules:
        A("## Unchanged modules")
        A("")
        A("These modules have no spec changes and require no code changes:")
        A("")
        for h in unchanged_modules:
            A(f"- {h}")
        A("")

    # ── Footer ─────────────────────────────────────────────────────
    A("---")
    A(f"*Generated by `generate_change_manifest.py` from diff of {old_version} → {new_version}*")
    A("*This draft must be completed by the discovery agent before Phase 4 gate review.*")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a change manifest from a SPEC.md diff",
    )
    parser.add_argument("project_slug",  help="Project slug (workspace folder name)")
    parser.add_argument(
        "--old",
        default=None,
        help="Path to the previous SPEC.md (default: workspace/[slug]/SPEC-previous.md)",
    )
    args = parser.parse_args()

    slug     = args.project_slug
    old_path = Path(args.old) if args.old else previous_spec_path(slug)
    new_path = current_spec_path(slug)

    # Validate inputs
    if not old_path.exists():
        print(f"❌ Previous spec not found: {old_path}", file=sys.stderr)
        print(
            f"   Before updating the spec, save the current version:\n"
            f"   cp docs/specs/SPEC.md {old_path}",
            file=sys.stderr,
        )
        return 1

    if not new_path.exists():
        print(
            f"❌ New spec not found: {new_path}\n"
            f"   Run generate_spec.py first: python3 scripts/generate_spec.py {slug}",
            file=sys.stderr,
        )
        return 1

    old_text = old_path.read_text(encoding="utf-8")
    new_text = new_path.read_text(encoding="utf-8")

    if old_text.strip() == new_text.strip():
        print("⚠️  No changes detected between old and new SPEC.md.")
        print("   Is the spec actually updated?")
        return 0

    old_version = extract_version(old_text)
    new_version = extract_version(new_text)
    today       = date.today().isoformat()

    manifest = generate_manifest(slug, old_text, new_text, today)

    # Write output
    out_path = exports_dir(slug) / f"CHANGE-MANIFEST-{new_version}.md"
    exports_dir(slug).mkdir(parents=True, exist_ok=True)
    out_path.write_text(manifest, encoding="utf-8")

    print(f"✓ Change manifest generated: {out_path}")
    print(f"  Comparing: {old_version} → {new_version}")

    # Count stats
    old_sections = parse_spec(old_text)
    new_sections = parse_spec(new_text)
    changes      = detect_changes(old_sections, new_sections)
    modified     = sum(1 for c in changes if c.change_type == 'modified')
    added        = sum(1 for c in changes if c.change_type == 'added')
    removed      = sum(1 for c in changes if c.change_type == 'removed')
    unknown      = sum(1 for c in changes if '?' in c.phases)

    print(f"  Sections: {modified} modified, {added} added, {removed} removed")
    if unknown:
        print(f"  ⚠️  {unknown} section(s) need agent review for phase mapping")

    all_phases = sorted({p for c in changes for p in c.phases if p != '?'})
    if all_phases:
        phase_str = ', '.join(f"Phase {p}" for p in all_phases)
        print(f"  Affected phases: {phase_str}")

    print()
    print("Next steps:")
    print(f"  1. Review and complete all [AGENT: ...] sections in the manifest")
    print(f"  2. Fill in specific file paths for each affected phase")
    print(f"  3. Complete the 'What does NOT change' table")
    print(f"  4. Pass through Phase 4 gate review (BA + Dev Lead sign-off)")
    print(f"  5. Copy both SPEC.md and CHANGE-MANIFEST to the project repo")
    print(f"  6. Tag: git tag spec-{new_version}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
