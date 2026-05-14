#!/usr/bin/env python3
"""
generate_spec.py — Consolidate discovery artifacts into SPEC.md

Produces a single SPEC.md from the 5 discovery artifacts:
  - 00-discovery-notes.md     (overview, org_context, actors, core loop)
  - 01-module-[slug].md       (one or more module definition cards)
  - 02-data-dictionary.md     (project-wide data dictionary)
  - 03-acceptance-criteria.md (all ACs with priorities)
  - 04-behavioral-test-specs.md (behavioral specs per AC)

Output: workspace/[project-slug]/exports/SPEC.md

Usage:
  python3 generate_spec.py [project-slug]
  python3 generate_spec.py [project-slug] --version v2.0
  python3 generate_spec.py [project-slug] --check  (dry run, validate only)

Versioning:
  - First run produces v1.0
  - Subsequent runs increment minor version (v1.0 → v1.1 → v1.2)
  - Use --version to force a major bump (e.g., v2.0)

This script does NOT enforce sign-offs or fill Section 7 (Cross-Module
Relationships). Those require human / agent judgment at Phase 4 gate review.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────

def workspace_dir(project_slug: str) -> Path:
    return Path("workspace") / project_slug

def exports_dir(project_slug: str) -> Path:
    return workspace_dir(project_slug) / "exports"

def output_path(project_slug: str) -> Path:
    return exports_dir(project_slug) / "SPEC.md"


# ── Source artifact loaders ──────────────────────────────────────────

@dataclass
class DiscoveryNotes:
    """Parsed contents of 00-discovery-notes.md."""
    raw:                   str
    project_name:          str | None = None
    problem:               str | None = None
    users:                 str | None = None
    solution:              str | None = None
    business_model:        str | None = None
    success_criteria:      str | None = None
    org_context_yaml:      str | None = None
    org_context_type:      str | None = None
    actors_table:          str | None = None
    core_loop:             str | None = None
    integrations_external: str | None = None
    integrations_internal: str | None = None


@dataclass
class ModuleCard:
    """Parsed contents of 01-module-[slug].md."""
    slug:             str
    name:             str
    raw:              str
    business_purpose: str = ""
    actors_table:     str = ""
    entry_point:      str = ""
    pre_conditions:   str = ""
    exit_point:       str = ""
    post_conditions:  str = ""
    core_flow:        list[str] | None = None
    states_text:      str = ""
    desired_outcomes: list[dict] | None = None
    out_of_scope:     str = ""
    open_questions:   list[str] | None = None
    priority:         str = "Must"


@dataclass
class DataDictionaryEntry:
    """One row in 02-data-dictionary.md."""
    entity:        str
    field_name:    str  # snake_case
    field_camel:   str  # camelCase
    label:         str
    type:          str
    required:      str
    validation:    str
    default:       str
    source:        str
    integration:   str
    enum_values:   str
    sensitive:     str
    notes:         str
    module_slug:   str | None = None  # which module this belongs to


@dataclass
class AcceptanceCriterion:
    """One row in 03-acceptance-criteria.md."""
    ac_id:       str
    statement:   str
    priority:    str
    module_slug: str
    flow_step:   str
    actor:       str
    permission:  str | None = None  # extracted permission string


@dataclass
class BehavioralSpec:
    """One scenario in 04-behavioral-test-specs.md."""
    behavior_id: str
    ac_id:       str
    layer:       str
    actor:       str
    setup:       str
    action:      str
    expect:      str
    notes:       str = ""
    module_slug: str | None = None


def load_discovery_notes(slug: str) -> DiscoveryNotes:
    path = workspace_dir(slug) / "00-discovery-notes.md"
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")

    raw = path.read_text(encoding="utf-8")
    notes = DiscoveryNotes(raw=raw)

    # Extract org_context YAML block
    org_match = re.search(
        r"```ya?ml\s*\n(\s*org_context:.*?)```",
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if org_match:
        notes.org_context_yaml = org_match.group(1).strip()
        type_match = re.search(r"type:\s*([\w-]+)", notes.org_context_yaml)
        if type_match:
            notes.org_context_type = type_match.group(1).strip()

    # Extract Discovery Summary fields (best-effort regex parsing)
    notes.project_name      = _extract_field(raw, r"\*\*Project name.*?:\*\*\s*(.+)")
    notes.problem           = _extract_field(raw, r"\*\*Core problem.*?:\*\*\s*(.+)")
    notes.users             = _extract_field(raw, r"\*\*(?:Primary user|End-user) personas?.*?:\*\*\s*(.+)")
    notes.solution          = _extract_field(raw, r"\*\*Core (?:business loop|consumer flow).*?:\*\*\s*(.+)")
    notes.business_model    = _extract_field(raw, r"\*\*Business model.*?:\*\*\s*(.+)")
    notes.success_criteria  = _extract_field(raw, r"\*\*Recommended next step.*?:\*\*\s*(.+)")

    return notes


def load_module_cards(slug: str) -> list[ModuleCard]:
    """Load every 01-module-*.md file in the workspace."""
    files = sorted(workspace_dir(slug).glob("01-module-*.md"))
    if not files:
        raise FileNotFoundError(
            f"No module cards found in {workspace_dir(slug)}. "
            f"Expected files matching 01-module-*.md"
        )

    cards = []
    for f in files:
        # slug = filename without "01-module-" prefix and ".md" suffix
        module_slug = f.stem.removeprefix("01-module-")
        raw = f.read_text(encoding="utf-8")
        card = ModuleCard(
            slug = module_slug,
            name = _extract_module_name(raw, module_slug),
            raw  = raw,
        )
        _populate_module_card(card)
        cards.append(card)

    return cards


def load_data_dictionary(slug: str) -> list[DataDictionaryEntry]:
    """Parse the data dictionary table(s) from 02-data-dictionary.md."""
    path = workspace_dir(slug) / "02-data-dictionary.md"
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")

    raw = path.read_text(encoding="utf-8")
    entries: list[DataDictionaryEntry] = []
    current_entity: str | None = None
    current_module: str | None = None

    for line in raw.splitlines():
        # Detect entity headers (e.g. "### Entity: Contract" or "## Contract")
        entity_match = re.match(r"^#{2,4}\s+(?:Entity:\s+)?([\w\s]+?)\s*$", line)
        if entity_match and not line.lstrip().startswith("####"):
            heading = entity_match.group(1).strip()
            if heading.lower() not in ("data dictionary", "naming conventions"):
                current_entity = heading

        # Detect module hint comments (e.g. <!-- module: contract-creation -->)
        module_hint = re.match(r"<!--\s*module:\s*([\w-]+)\s*-->", line)
        if module_hint:
            current_module = module_hint.group(1)

        # Parse table rows — must have at least 8 pipe-separated cells
        if line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 10 and current_entity and not _is_table_header(cells):
                entries.append(DataDictionaryEntry(
                    entity      = current_entity,
                    field_name  = cells[0] if len(cells) > 0 else "",
                    field_camel = cells[1] if len(cells) > 1 else "",
                    label       = cells[2] if len(cells) > 2 else "",
                    type        = cells[3] if len(cells) > 3 else "",
                    required    = cells[4] if len(cells) > 4 else "",
                    validation  = cells[5] if len(cells) > 5 else "",
                    default     = cells[6] if len(cells) > 6 else "",
                    source      = cells[7] if len(cells) > 7 else "",
                    integration = cells[8] if len(cells) > 8 else "",
                    enum_values = cells[9] if len(cells) > 9 else "",
                    sensitive   = cells[10] if len(cells) > 10 else "",
                    notes       = cells[11] if len(cells) > 11 else "",
                    module_slug = current_module,
                ))

    return entries


def load_acceptance_criteria(slug: str) -> list[AcceptanceCriterion]:
    path = workspace_dir(slug) / "03-acceptance-criteria.md"
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")

    raw = path.read_text(encoding="utf-8")
    criteria: list[AcceptanceCriterion] = []
    current_module: str | None = None

    for line in raw.splitlines():
        module_hint = re.match(r"<!--\s*module:\s*([\w-]+)\s*-->", line)
        if module_hint:
            current_module = module_hint.group(1)

        # AC table rows: | AC-001 | Must | The system must... | module | step | actor | permission |
        if line.startswith("|") and "AC-" in line and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and re.match(r"AC-\d+", cells[0]):
                criteria.append(AcceptanceCriterion(
                    ac_id       = cells[0],
                    priority    = cells[1] if len(cells) > 1 else "Must",
                    statement   = cells[2] if len(cells) > 2 else "",
                    module_slug = cells[3] if len(cells) > 3 and cells[3] else (current_module or ""),
                    flow_step   = cells[4] if len(cells) > 4 else "",
                    actor       = cells[5] if len(cells) > 5 else "",
                    permission  = cells[6] if len(cells) > 6 else None,
                ))

    return criteria


def load_behavioral_specs(slug: str) -> list[BehavioralSpec]:
    path = workspace_dir(slug) / "04-behavioral-test-specs.md"
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")

    raw = path.read_text(encoding="utf-8")
    specs: list[BehavioralSpec] = []

    # Split into AC blocks. Match either:
    #   ### [AC-XXX] ...
    #   ## AC-XXX ...
    #   ## AC-XXX — ...
    # The split keeps the AC header in each block.
    behavior_blocks = re.split(
        r"\n#{2,3}\s+\[?AC-\d+\]?[^\n]*",
        raw,
    )
    ac_ids_found = re.findall(r"\n#{2,3}\s+\[?(AC-\d+)\]?", raw)

    behavior_counter = 0
    # behavior_blocks[0] is the preamble before the first AC header
    for ac_id, block in zip(ac_ids_found, behavior_blocks[1:]):
        layer = _extract_field(block, r"\*\*Layer:\*\*\s*(\S+)")    or "unit"
        actor = _extract_field(block, r"\*\*Actor:\*\*\s*([^\n]+)") or ""

        # Find every Setup/Action/Expect block. The Setup, Action, and Expect
        # values can span multiple lines (often do in the contract-manager example).
        scenarios = re.findall(
            r"```\s*\n"
            r"Setup:\s*(.*?)"
            r"\n\s*Action:\s*(.*?)"
            r"\n\s*Expect:\s*(.*?)"
            r"\n```",
            block,
            re.DOTALL,
        )
        for setup, action, expect in scenarios:
            behavior_counter += 1
            specs.append(BehavioralSpec(
                behavior_id = f"B-{behavior_counter:03d}",
                ac_id       = ac_id,
                layer       = layer,
                actor       = actor.strip(),
                setup       = _normalize_multiline(setup),
                action      = _normalize_multiline(action),
                expect      = _normalize_multiline(expect),
            ))

    return specs


# ── Versioning ───────────────────────────────────────────────────────

def determine_version(slug: str, override: str | None) -> tuple[str, list[str]]:
    """Returns (version_string, version_history_lines)."""
    if override:
        return override, []

    existing = output_path(slug)
    if not existing.exists():
        return "v1.0", []

    raw = existing.read_text(encoding="utf-8")
    history_match = re.search(
        r"## Version History\s*\n\s*\|.*?\|.*?\n\s*\|---.*?\|.*?\n((?:\|.*\|.*?\n)+)",
        raw,
        re.DOTALL,
    )
    history_lines = []
    if history_match:
        for line in history_match.group(1).strip().splitlines():
            if line.strip().startswith("|") and "v" in line.lower():
                history_lines.append(line.strip())

    # Find the highest version present
    versions = []
    for line in history_lines:
        m = re.search(r"v(\d+)\.(\d+)", line)
        if m:
            versions.append((int(m.group(1)), int(m.group(2))))

    if not versions:
        return "v1.0", []

    versions.sort()
    latest_major, latest_minor = versions[-1]
    return f"v{latest_major}.{latest_minor + 1}", history_lines


# ── SPEC.md generation ───────────────────────────────────────────────

def generate(slug: str, version: str | None, check_only: bool) -> int:
    if not workspace_dir(slug).exists():
        print(f"❌ Workspace not found: {workspace_dir(slug)}", file=sys.stderr)
        return 1

    # Load all artifacts (fails fast if any are missing)
    try:
        notes      = load_discovery_notes(slug)
        cards      = load_module_cards(slug)
        dictionary = load_data_dictionary(slug)
        criteria   = load_acceptance_criteria(slug)
        behaviors  = load_behavioral_specs(slug)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    # Validation checks
    errors: list[str] = []
    if not notes.org_context_type:
        errors.append("Missing org_context.type in 00-discovery-notes.md (Section 1b)")
    elif notes.org_context_type not in ("org-only", "org-with-units", "customer-account"):
        errors.append(
            f"Invalid org_context.type: '{notes.org_context_type}'. "
            f"Must be one of: org-only, org-with-units, customer-account"
        )

    if not cards:
        errors.append("No module cards found (expected 01-module-*.md files)")

    if not criteria:
        errors.append("No acceptance criteria found in 03-acceptance-criteria.md")

    if errors:
        print("❌ SPEC generation blocked by validation errors:", file=sys.stderr)
        for err in errors:
            print(f"   - {err}", file=sys.stderr)
        return 1

    # Determine version
    spec_version, prior_history = determine_version(slug, version)
    today = date.today().isoformat()

    if check_only:
        print(f"✓ All artifacts valid. Would generate {spec_version}")
        return 0

    # Build the document
    doc = []
    doc.append(_section_1_header(slug, spec_version, today, prior_history))
    doc.append(_section_2_overview(notes))
    doc.append(_section_3_org_context(notes))
    doc.append(_section_4_system_map(notes))
    doc.append(_section_5_module_index(cards))
    doc.append(_section_6_modules(cards, dictionary, criteria, behaviors))
    doc.append(_section_7_cross_module_placeholder(cards))

    output = "\n\n".join(doc)

    exports_dir(slug).mkdir(parents=True, exist_ok=True)

    # Auto-save previous SPEC before overwriting (feeds generate_change_manifest.py)
    existing = output_path(slug)
    if existing.exists() and spec_version != "v1.0":
        previous = workspace_dir(slug) / "SPEC-previous.md"
        previous.write_text(existing.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  → Previous spec saved to {previous}")

    output_path(slug).write_text(output, encoding="utf-8")

    print(f"✓ SPEC.md generated: {output_path(slug)}")
    print(f"  Version: {spec_version}")
    print(f"  Modules: {len(cards)}")
    print(f"  ACs: {len(criteria)}")
    print(f"  Behaviors: {len(behaviors)}")
    print()
    print("Next steps:")
    if spec_version == "v1.0":
        print("  1. Fill the sign-off table in Section 1 (BA, Designer, Dev Lead)")
        print("  2. Review Section 7 — fill cross-module relationships if any exist")
        print("  3. Pass through the Phase 4 gate review")
        print("  4. Copy SPEC.md into the project repo at docs/specs/SPEC.md")
        print(f"  5. Tag the commit: git tag spec-{spec_version}")
    else:
        print(f"  1. Run: python3 scripts/generate_change_manifest.py {slug}")
        print("  2. Complete all [AGENT: ...] sections in the change manifest")
        print("  3. Pass through Phase 4 gate review (BA + Dev Lead sign-off on BOTH files)")
        print("  4. Copy SPEC.md and CHANGE-MANIFEST to the project repo")
        print(f"  5. Tag the commit: git tag spec-{spec_version}")

    return 0


# ── Section builders ─────────────────────────────────────────────────

def _section_1_header(slug: str, version: str, today: str, prior_history: list[str]) -> str:
    history_lines = list(prior_history)
    history_lines.append(
        f"| {version} | {today} | "
        f"{'Initial spec' if version == 'v1.0' else 'Spec update'} | "
        f"discovery workspace |"
    )

    return f"""# SPEC — {slug.replace("-", " ").title()}
*Project slug: `{slug}` | Version: {version} | Status: Draft (awaiting Phase 4 sign-off)*

## Sign-offs

| Role | Name | Date | Status |
|---|---|---|---|
| Business Analyst | _[fill]_ | _[YYYY-MM-DD]_ | ☐ Pending |
| Designer | _[fill]_ | _[YYYY-MM-DD]_ | ☐ Pending |
| Dev Lead | _[fill]_ | _[YYYY-MM-DD]_ | ☐ Pending |

## Version History

| Version | Date | Summary | Generated from |
|---|---|---|---|
{chr(10).join(history_lines)}"""


def _section_2_overview(notes: DiscoveryNotes) -> str:
    return f"""## Project Overview

**Problem:** {notes.problem or "_[from 00-discovery-notes.md Discovery Summary block]_"}

**Users:** {notes.users or "_[from 00-discovery-notes.md]_"}

**Solution:** {notes.solution or "_[from 00-discovery-notes.md]_"}

**Business model:** {notes.business_model or "_[from 00-discovery-notes.md, if applicable]_"}

**Success criteria:** {notes.success_criteria or "_[from 00-discovery-notes.md]_"}"""


def _section_3_org_context(notes: DiscoveryNotes) -> str:
    yaml_block = notes.org_context_yaml or "org_context:\n  type: _[MISSING]_"
    type_value = notes.org_context_type or "_[MISSING]_"

    implications = {
        "org-only": [
            "Every entity in the data model has an `orgId` column.",
            "Single tenant — no further hierarchy needed.",
            "BetterAuth's organization plugin manages tenancy."
        ],
        "org-with-units": [
            "Every entity has an `orgId` column.",
            "Some entities also have an `orgUnitId` column for branch/region scoping.",
            "User-to-unit assignment determines query scope.",
            "BetterAuth's organization plugin + custom org-unit table per Section 6."
        ],
        "customer-account": [
            "Every entity has an `orgId` column where the org represents a customer account.",
            "Each customer's data is fully isolated; no cross-account queries except admin tools.",
            "BetterAuth's organization plugin treats each customer as a separate organization."
        ],
    }
    impl_lines = implications.get(notes.org_context_type or "", [
        "_[Implications cannot be auto-generated — org_context.type is missing or invalid]_"
    ])

    return f"""## Organizational Context

**Pattern:** `{type_value}`

### Structured definition

```yaml
{yaml_block}
```

### Implications for the architecture

{chr(10).join(f"- {line}" for line in impl_lines)}"""


def _section_4_system_map(notes: DiscoveryNotes) -> str:
    actors = notes.actors_table or "_[Actors table from 00-discovery-notes.md — fill from discovery]_"
    core_loop = notes.core_loop or "_[Core business loop from 00-discovery-notes.md]_"

    return f"""## System Map

### Actors

{actors}

### Core business loop

{core_loop}

### Integrations

_[External and internal integrations identified in discovery. Fill from 00-discovery-notes.md and 02-data-dictionary.md.]_"""


def _section_5_module_index(cards: list[ModuleCard]) -> str:
    lines = [
        "## Module Index",
        "",
        "| # | Module | Slug | Priority | Status |",
        "|---|---|---|---|---|",
    ]
    for i, card in enumerate(cards, start=1):
        lines.append(
            f"| 6.{i} | {card.name} | `{card.slug}` | {card.priority} | 🟢 Specified |"
        )

    lines.extend([
        "",
        "**Status legend:** 🟢 Specified · 🟡 Partial · 🔴 Blocked",
        "**Priority legend:** Must (required for v1.0 launch) · Should (important, not blocking) · Could (nice to have, may defer)",
    ])
    return "\n".join(lines)


def _section_6_modules(
    cards:      list[ModuleCard],
    dictionary: list[DataDictionaryEntry],
    criteria:   list[AcceptanceCriterion],
    behaviors:  list[BehavioralSpec],
) -> str:
    sections = ["## Modules"]
    for i, card in enumerate(cards, start=1):
        sections.append(_module_section(i, card, dictionary, criteria, behaviors))
    return "\n\n".join(sections)


def _module_section(
    index:       int,
    card:        ModuleCard,
    dictionary:  list[DataDictionaryEntry],
    criteria:    list[AcceptanceCriterion],
    behaviors:   list[BehavioralSpec],
) -> str:
    # Filter to this module's records
    mod_acs        = [ac for ac in criteria  if ac.module_slug == card.slug]
    mod_behaviors  = [b  for b  in behaviors if b.ac_id in {ac.ac_id for ac in mod_acs}]
    mod_dict       = [e  for e  in dictionary if e.module_slug == card.slug]

    ac_range = ""
    if mod_acs:
        ac_ids   = sorted(set(ac.ac_id for ac in mod_acs))
        ac_range = f" | AC range: {ac_ids[0]} to {ac_ids[-1]}"

    parts = [
        f"### 6.{index} {card.name}",
        f"*Module slug: `{card.slug}` | Priority: {card.priority}{ac_range}*",
        "",
        f"#### 6.{index}.1 Business purpose",
        card.business_purpose or "_[from module card]_",
        "",
        f"#### 6.{index}.2 Actors",
        card.actors_table or "_[actors table from module card]_",
        "",
        f"#### 6.{index}.3 Entry & exit points",
        f"- **Entry:** {card.entry_point or '_[from module card]_'}",
        f"- **Pre-conditions:** {card.pre_conditions or '_[from module card]_'}",
        f"- **Exit:** {card.exit_point or '_[from module card]_'}",
        f"- **Post-conditions:** {card.post_conditions or '_[from module card]_'}",
        "",
        f"#### 6.{index}.4 Core flow",
    ]
    if card.core_flow:
        parts.extend(f"{i}. {step}" for i, step in enumerate(card.core_flow, start=1))
    else:
        parts.append("_[from module card]_")

    parts.extend([
        "",
        f"#### 6.{index}.5 States & transitions",
        card.states_text or "_[from module card]_",
        "",
        f"#### 6.{index}.6 Data dictionary (this module)",
    ])
    parts.append(_data_dict_table(mod_dict) if mod_dict else "_[Filter from 02-data-dictionary.md by entity / module association]_")

    parts.extend(["", f"#### 6.{index}.7 Acceptance criteria"])
    parts.append(_ac_table(mod_acs) if mod_acs else "_[no ACs for this module]_")

    parts.extend(["", f"#### 6.{index}.8 Behavioral specs"])
    if mod_behaviors:
        for b in mod_behaviors:
            parts.append(_behavior_block(b))
    else:
        parts.append("_[no behaviors for this module]_")

    parts.extend([
        "",
        f"#### 6.{index}.9 Permissions required",
        _permissions_table(mod_acs),
        "",
        f"#### 6.{index}.10 Out of scope",
        card.out_of_scope or "_[from module card]_",
        "",
        f"#### 6.{index}.11 Open questions",
    ])
    if card.open_questions:
        for q in card.open_questions:
            parts.append(f"- {q}")
    else:
        parts.append("_[none — or fill from module card]_")

    return "\n".join(parts)


def _section_7_cross_module_placeholder(cards: list[ModuleCard]) -> str:
    if len(cards) < 2:
        return """## Cross-Module Relationships

None — this version has only one module."""

    return """## Cross-Module Relationships

_[Fill this section during Phase 4 gate review. The discovery agent + dev lead identify:]_

### Data relationships

_[Entity foreign keys and ownership across modules]_

| Entity in module | References | Relationship | Notes |
|---|---|---|---|
| _[Entity (6.X)]_ | _[Other entity (6.Y)]_ | _[1-1, 1-N, N-N]_ | _[notes]_ |

### Cross-module operations

_[Operations that write to multiple modules atomically. These belong in `lib/services/`.]_

| Operation | Modules touched | Suggested location |
|---|---|---|
| _[operation name]_ | _[6.X + 6.Y]_ | `lib/services/[name].service.ts` |

### Cross-module queries

_[Read-only queries joining across modules. These belong in `lib/joins/`.]_

| Query | Modules joined | Suggested file |
|---|---|---|
| _[query name]_ | _[6.X + 6.Y]_ | `lib/joins/[name].ts` |

### Shared validation

_[Validation logic used by 2+ modules. These belong in `lib/schemas/`.]_

| Validation | Used by | Suggested location |
|---|---|---|
| _[validation name]_ | _[modules]_ | `lib/schemas/[name].ts` |

> If no cross-module relationships exist, replace this section with: **None — modules are fully independent in this version.**"""


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_field(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _extract_module_name(raw: str, default_slug: str) -> str:
    # Look for the first H1 or H2 heading
    h_match = re.search(r"^#{1,2}\s+(.+?)\s*$", raw, re.MULTILINE)
    if h_match:
        name = h_match.group(1).strip()
        # Strip "Module:" prefix or similar
        name = re.sub(r"^(?:Module|MODULE DEFINITION CARD)[:\s-]+", "", name, flags=re.IGNORECASE)
        if name:
            return name
    return default_slug.replace("-", " ").title()


def _populate_module_card(card: ModuleCard) -> None:
    """Best-effort extraction of module card fields from markdown."""
    raw = card.raw

    # Business purpose — text after "Business Purpose" or "1 Business Purpose"
    card.business_purpose = _extract_section(raw, r"Business Purpose|1\s+Business Purpose").strip()

    # Entry / exit points
    card.entry_point     = _extract_table_cell(raw, "Entry point")    or _extract_after_label(raw, "Entry point")
    card.pre_conditions  = _extract_table_cell(raw, "Pre-conditions") or _extract_after_label(raw, "Pre-conditions")
    card.exit_point      = _extract_table_cell(raw, "Exit point")     or _extract_after_label(raw, "Exit point")
    card.post_conditions = _extract_table_cell(raw, "Post-conditions") or _extract_after_label(raw, "Post-conditions")

    # Core flow — numbered list under "Core Flow"
    flow_section = _extract_section(raw, r"Core Flow|4\s+Core Flow")
    if flow_section:
        steps = re.findall(r"^\s*\d+\s*[.|]\s+(.+?)$", flow_section, re.MULTILINE)
        if steps:
            card.core_flow = [s.strip() for s in steps]

    # States & edge cases
    card.states_text = _extract_section(raw, r"States?\s*&\s*Edge Cases|5\s+States").strip()

    # Out of scope
    card.out_of_scope = _extract_section(raw, r"Out of Scope|7\s+Out of Scope").strip()

    # Open questions
    qa_section = _extract_section(raw, r"Open Questions(?:.*?)Flags|8\s+Open Questions")
    if qa_section:
        card.open_questions = [
            line.strip("|").strip()
            for line in qa_section.splitlines()
            if line.strip().startswith("|") and "🚩" in line or "❓" in line
        ]


def _extract_section(text: str, header_pattern: str) -> str:
    """Extract content between a header matching the pattern and the next header."""
    pattern = rf"#{{2,4}}\s*\*?\*?\s*{header_pattern}\s*\*?\*?\s*\n(.*?)(?=\n#{{2,4}}\s|\Z)"
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_table_cell(text: str, label: str) -> str:
    """Extract a value from a 2-column table where first column matches label."""
    pattern = rf"\|\s*\*?\*?{re.escape(label)}\*?\*?\s*\|\s*(.+?)\s*\|"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_after_label(text: str, label: str) -> str:
    """Extract a value following a bold label (e.g. **Entry point:** value)."""
    pattern = rf"\*\*{re.escape(label)}\*\*:?\s*(.+?)(?:\n|$)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _is_table_header(cells: list[str]) -> bool:
    headers_keywords = {"field", "name", "label", "type", "required"}
    first = (cells[0] if cells else "").lower()
    return any(kw in first for kw in headers_keywords) and "_" not in (cells[0] if cells else "")


def _normalize_multiline(text: str) -> str:
    """Collapse multi-line setup/action/expect content into a single readable line."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " · ".join(lines)


def _data_dict_table(entries: list[DataDictionaryEntry]) -> str:
    if not entries:
        return "_[no entries]_"

    # Group by entity
    by_entity: dict[str, list[DataDictionaryEntry]] = {}
    for e in entries:
        by_entity.setdefault(e.entity, []).append(e)

    parts = []
    for entity, fields in by_entity.items():
        parts.append(f"##### Entity: {entity}\n")
        parts.append("| field_name | fieldName | Type | Required | Source | Sensitive | Validation |")
        parts.append("|---|---|---|---|---|---|---|")
        for f in fields:
            parts.append(
                f"| `{f.field_name}` | `{f.field_camel}` | {f.type} | {f.required} | "
                f"{f.source} | {f.sensitive} | {f.validation} |"
            )
        parts.append("")
    return "\n".join(parts)


def _ac_table(criteria: list[AcceptanceCriterion]) -> str:
    if not criteria:
        return "_[no ACs]_"
    lines = [
        "| AC ID | Priority | The system must… | Permission | Actor |",
        "|---|---|---|---|---|",
    ]
    for ac in criteria:
        perm = ac.permission or "(none)"
        lines.append(f"| {ac.ac_id} | {ac.priority} | {ac.statement} | {perm} | {ac.actor} |")
    return "\n".join(lines)


def _behavior_block(b: BehavioralSpec) -> str:
    return f"""##### {b.behavior_id} [{b.ac_id}]
- **Layer:** {b.layer}
- **Actor:** {b.actor}
- **Setup:** {b.setup}
- **Action:** {b.action}
- **Expect:** {b.expect}"""


def _permissions_table(criteria: list[AcceptanceCriterion]) -> str:
    perms: dict[str, list[str]] = {}
    for ac in criteria:
        if ac.permission and ac.permission != "(none)":
            perms.setdefault(ac.permission, []).append(ac.ac_id)

    if not perms:
        return "_[no permissions extracted from ACs — review during Phase 4]_"

    lines = [
        "| Permission string | Required by | Default roles |",
        "|---|---|---|",
    ]
    for perm, acs in perms.items():
        lines.append(f"| `{perm}` | {', '.join(acs)} | _[fill at Phase 4 review]_ |")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consolidate discovery artifacts into SPEC.md",
    )
    parser.add_argument("project_slug", help="Project slug (workspace folder name)")
    parser.add_argument("--version", help="Override version (e.g. v2.0)")
    parser.add_argument("--check", action="store_true",
                        help="Validate artifacts without generating output")
    args = parser.parse_args()

    return generate(args.project_slug, args.version, args.check)


if __name__ == "__main__":
    sys.exit(main())
