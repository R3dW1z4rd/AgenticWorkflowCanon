#!/usr/bin/env python3
"""
generate_miro_prompt.py
-----------------------
Reads a project's workspace files and generates a structured Miro AI prototype prompt.

The prompt is engineered to produce connected, flow-complete prototypes — not just
isolated screens. It explicitly enumerates every screen, every transition, every
data field per screen, and every conditional state.

Usage:
    python3 scripts/generate_miro_prompt.py <project-slug> <module-slug> [options]

Options:
    --device    mobile | desktop | both      (default: desktop)
    --style     enterprise | consumer | neutral (default: neutral)
    --density   compact | comfortable | spacious (default: comfortable)
    --lang      en | es | (any)              (default: en)

Example:
    python3 scripts/generate_miro_prompt.py contract-manager contract-creation --device desktop

Output:
    workspace/<project-slug>/exports/miro-prompt-<module-slug>.md
"""

import sys
import os
import re
import argparse
from pathlib import Path

# ── Markdown helpers ──────────────────────────────────────────────────────────

def read_file(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def extract_section(md, heading):
    pattern = rf"##\s+\d*\.?\s*{re.escape(heading)}.*?\n([\s\S]*?)(?=\n##|\Z)"
    m = re.search(pattern, md, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def parse_md_table(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line.replace(" ", "")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if any(c for c in cells):
            rows.append(cells)
    return rows[1:] if rows else []

def safe(lst, idx, default=""):
    try:
        v = lst[idx].strip()
        return v if v not in ("-", "—", "") else default
    except IndexError:
        return default

def clean(text):
    """Strip markdown formatting for clean prompt output."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*",     r"\1", text)
    text = re.sub(r"`(.*?)`",       r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_flow_steps(module_md):
    """Extract core flow steps as list of {step, description}."""
    flow_text = extract_section(module_md, "Core Flow")
    rows = parse_md_table(flow_text)
    steps = []
    for row in rows:
        step = safe(row, 0)
        desc = safe(row, 1) or safe(row, 2, "")   # some tables have 3 cols
        if step and desc:
            steps.append({"step": step, "description": clean(desc)})
    # Fallback: numbered lines if no table
    if not steps:
        for line in flow_text.splitlines():
            line = line.strip()
            m = re.match(r"^(\d+)[\.:\)]\s+(.+)", line)
            if m:
                steps.append({"step": m.group(1), "description": clean(m.group(2))})
    return steps

def parse_actors(module_md):
    """Extract actor/role names."""
    actors_text = extract_section(module_md, "Actors")
    rows = parse_md_table(actors_text)
    actors = []
    for row in rows:
        role = safe(row, 0)
        if role and role.lower() not in ("role", "actor", "—"):
            actors.append(role)
    return actors or ["User"]

def parse_states(module_md):
    """Extract entity states."""
    states_text = extract_section(module_md, "States")
    m = re.search(r"\*\*[Mm]odule states\*\*:?\s*(.+)", states_text)
    if m:
        raw = m.group(1)
        return [s.strip() for s in re.split(r"→|·|,|\|", raw) if s.strip()]
    return []

def parse_entry_exit(module_md):
    """Extract entry point and exit point."""
    text = extract_section(module_md, "Entry")
    entry = re.search(r"\*\*Entry point\*\*:?\s*(.+)", text)
    exit_ = re.search(r"\*\*Exit point\*\*:?\s*(.+)", text)
    pre   = re.search(r"\*\*Pre-conditions?\*\*:?\s*(.+)", text)
    return {
        "entry": clean(entry.group(1)) if entry else "",
        "exit":  clean(exit_.group(1)) if exit_  else "",
        "pre":   clean(pre.group(1))   if pre    else "",
    }

def parse_dd_for_module(dd_md, module_name):
    """
    Extract fields from data dictionary, grouped by screen.
    Header-aware: detects column positions from the header row.
    Returns: {screen_name: [{field_name, display_label, type, required, validation, source, enum_vals, pii}]}
    Also returns: all_fields list and integration_fields list
    """
    # Find header row first
    col_idx = {}
    all_rows = []
    for line in dd_md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line.replace(" ", "")):
            continue
        cells = [c.strip().lower() for c in line.strip("|").split("|")]
        if not all_rows:  # first valid row = header
            for i, cell in enumerate(cells):
                if "field_name" in cell or ("field" in cell and "name" in cell and "display" not in cell):
                    col_idx.setdefault("field_name", i)
                elif "fieldname" in cell or "camel" in cell:
                    col_idx.setdefault("camel", i)
                elif "display" in cell and "label" in cell:
                    col_idx.setdefault("display", i)
                elif cell in ("type", "data type"):
                    col_idx.setdefault("type", i)
                elif "required" in cell:
                    col_idx.setdefault("required", i)
                elif "validation" in cell:
                    col_idx.setdefault("validation", i)
                elif "default" in cell:
                    col_idx.setdefault("default", i)
                elif "source" in cell and "integration" not in cell:
                    col_idx.setdefault("source", i)
                elif "integration" in cell or "module ref" in cell:
                    col_idx.setdefault("ref", i)
                elif "enum" in cell:
                    col_idx.setdefault("enum_vals", i)
                elif "used in" in cell or "screens" in cell:
                    col_idx.setdefault("used_in", i)
                elif "pii" in cell or "sensitive" in cell:
                    col_idx.setdefault("pii", i)
                elif "note" in cell:
                    col_idx.setdefault("notes", i)
                elif "entity" in cell:
                    col_idx.setdefault("entity", i)
        all_rows.append([c.strip() for c in line.strip("|").split("|")])

    # Fallback column indices if header detection incomplete
    defaults = {
        "field_name": 0, "camel": 1, "display": 2, "type": 3,
        "required": 4, "validation": 5, "default": 6, "source": 7,
        "ref": 8, "enum_vals": 9, "used_in": 10, "pii": 11, "notes": 12
    }
    # If entity column detected, shift everything by 1
    if "entity" in col_idx and col_idx["entity"] == 0:
        defaults = {k: v+1 for k, v in defaults.items()}
        defaults["entity"] = 0
    for k, v in defaults.items():
        col_idx.setdefault(k, v)

    rows = all_rows[1:] if all_rows else []  # skip header
    screens = {}
    all_fields = []
    integration_fields = []
    derived_fields = []

    for row in rows:
        field_snake = safe(row, col_idx["field_name"]) or safe(row, col_idx.get("camel", 1))
        display     = safe(row, col_idx["display"])
        dtype       = safe(row, col_idx["type"])
        required    = safe(row, col_idx["required"])
        validation  = safe(row, col_idx["validation"])
        source      = safe(row, col_idx["source"])
        ref         = safe(row, col_idx["ref"])
        enum_vals   = safe(row, col_idx["enum_vals"])
        used_in     = safe(row, col_idx["used_in"])
        pii         = safe(row, col_idx["pii"])
        notes       = safe(row, col_idx["notes"])

        if not field_snake or field_snake.lower() in ("field_name", "entity"):
            continue

        field_info = {
            "field_name": field_snake,
            "display":    display or field_snake.replace("_", " ").title(),
            "type":       dtype,
            "required":   required,
            "validation": validation,
            "source":     source,
            "ref":        ref,
            "enum_vals":  enum_vals,
            "pii":        pii,
            "notes":      notes,
        }
        all_fields.append(field_info)

        if source == "integration":
            integration_fields.append(field_info)
        if source == "derived":
            derived_fields.append(field_info)

        # Map to screens from "Used In" column
        if used_in:
            for screen in re.split(r"·|,|/", used_in):
                screen = screen.strip()
                if screen and screen not in ("—", ""):
                    screens.setdefault(screen, []).append(field_info)

    return screens, all_fields, integration_fields, derived_fields

def parse_ac_states(ac_md):
    """
    Extract acceptance criteria that imply specific screen states.
    Returns list of {id, criterion, implies_screen_state}
    """
    rows = parse_md_table(ac_md)
    states = []
    state_keywords = [
        "error", "loading", "empty", "disabled", "hidden", "visible",
        "unavailable", "invalid", "pending", "success", "confirmation",
        "notification", "redirect", "restrict", "role"
    ]
    for row in rows:
        ac_id    = safe(row, 0)
        crit     = safe(row, 4)
        if not crit:
            continue
        crit_lower = crit.lower()
        for kw in state_keywords:
            if kw in crit_lower:
                states.append({
                    "id": ac_id,
                    "criterion": clean(crit),
                    "keyword": kw
                })
                break
    return states

def parse_oos(module_md):
    """Extract out of scope items."""
    oos_text = extract_section(module_md, "Out of Scope")
    items = []
    for line in oos_text.splitlines():
        line = line.strip().lstrip("-·*•").strip()
        if line and len(line) > 5:
            items.append(clean(line))
    return items


# ── Screen inventory derivation ───────────────────────────────────────────────

def normalize_screen_name(name):
    """Normalize a screen name for comparison."""
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    replacements = {
        "create form": "Create / New",
        "new form":    "Create / New",
        "create":      "Create / New",
        "new":         "Create / New",
        "list view":   "List View",
        "list":        "List View",
        "all views":   "List View",
        "detail view": "Detail View",
        "detail":      "Detail View",
        "edit form":   "Edit",
        "edit":        "Edit",
        "review":      "Review & Confirm",
        "confirm":     "Review & Confirm",
        "success":     "Success / Confirmation",
        "error state": "Error State",
        "error":       "Error State",
        "empty state": "Empty State",
    }
    for old, new in replacements.items():
        if n == old or n.endswith(f" {old}") or n.startswith(f"{old} "):
            return new
    return name.title()


def derive_screens(steps, entry_exit, states_list, dd_screens, ac_states):
    """
    Derive the complete screen inventory from all available sources.
    Deduplicates screens with similar names, merging their fields.
    Returns ordered list of screen objects.
    """
    raw_screens = []
    seen_normalized = {}

    def add_screen(name, source, step_ref=None, notes="", fields=None):
        norm = normalize_screen_name(name)
        canonical = norm  # use normalized as canonical name
        if canonical in seen_normalized:
            # Merge fields into existing screen
            existing = seen_normalized[canonical]
            if fields:
                existing_field_names = {f["field_name"] for f in existing.get("fields", [])}
                for f in (fields or []):
                    if f["field_name"] not in existing_field_names:
                        existing.setdefault("fields", []).append(f)
            if notes and not existing.get("notes"):
                existing["notes"] = notes
        else:
            entry = {
                "name":     canonical,
                "source":   source,
                "step_ref": step_ref,
                "notes":    notes,
                "fields":   list(fields or []),
            }
            seen_normalized[canonical] = entry
            raw_screens.append(entry)

    # 1. Entry point → first screen (only if distinct from first flow step)
    if entry_exit.get("entry") and steps:
        first_step_name = infer_screen_name(steps[0]["description"], steps[0]["step"])
        if "list" in entry_exit["entry"].lower() or "trigger" in entry_exit["entry"].lower():
            add_screen("List View", "entry", "—", entry_exit["entry"])

    # 2. One screen per flow step
    for s in steps:
        screen_name = infer_screen_name(s["description"], s["step"])
        # Try to get matching DD fields
        fields = dd_screens.get(screen_name, []) or dd_screens.get(
            normalize_screen_name(screen_name), [])
        add_screen(screen_name, "flow", s["step"], s["description"], fields)

    # 3. Screens from data dictionary — merge fields into existing or add new
    for dd_screen_name, fields in dd_screens.items():
        norm = normalize_screen_name(dd_screen_name)
        if norm in seen_normalized:
            # Merge fields
            existing = seen_normalized[norm]
            existing_field_names = {f["field_name"] for f in existing.get("fields", [])}
            for f in fields:
                if f["field_name"] not in existing_field_names:
                    existing.setdefault("fields", []).append(f)
        else:
            add_screen(dd_screen_name, "data_dictionary", fields=fields)

    # 4. State screens from acceptance criteria
    error_states   = [a for a in ac_states if a["keyword"] in ("error", "invalid", "unavailable")]
    success_states = [a for a in ac_states if a["keyword"] in ("success", "confirmation")]
    empty_states   = [a for a in ac_states if a["keyword"] == "empty"]

    if error_states:
        add_screen("Error State", "acceptance_criteria", "—",
                   "Required by: " + "; ".join(a["id"] for a in error_states[:3]))
    if success_states:
        add_screen("Success / Confirmation", "acceptance_criteria", "—",
                   "Required by: " + "; ".join(a["id"] for a in success_states[:3]))
    if empty_states:
        add_screen("Empty State", "acceptance_criteria", "—",
                   "Required by: " + "; ".join(a["id"] for a in empty_states[:3]))

    return raw_screens

def infer_screen_name(description, step_num):
    """Map a flow step description to a screen name."""
    desc_lower = description.lower()
    patterns = [
        (r"list|overview|dashboard|home",     "List View"),
        (r"creat|new|add|start|initiat",      "Create / New"),
        (r"edit|updat|modif",                  "Edit Form"),
        (r"detail|view|show|open|see",         "Detail View"),
        (r"review|approv|confirm|submit",      "Review & Confirm"),
        (r"notif|email|alert|message",         "Notification"),
        (r"success|complet|done|finish",       "Success / Confirmation"),
        (r"error|fail|invalid|reject",         "Error State"),
        (r"search|filter|find",               "Search / Filter"),
        (r"upload|attach|import",             "Upload"),
        (r"login|sign.in|auth",               "Login"),
        (r"onboard|welcome|setup",            "Onboarding"),
        (r"setting|config|prefer",            "Settings"),
        (r"report|export|download",           "Report / Export"),
        (r"assign|delegate",                  "Assignment"),
        (r"payment|checkout|billing",         "Payment"),
        (r"step|form|fill|enter",             f"Form — Step {step_num}"),
    ]
    for pattern, name in patterns:
        if re.search(pattern, desc_lower):
            return name
    return f"Screen {step_num}"


# ── Transition map derivation ─────────────────────────────────────────────────

def derive_transitions(screens, steps, ac_states):
    """
    Derive transitions between screens.
    Returns list of {from, action, to, condition}
    """
    transitions = []

    # Sequential flow transitions
    for i in range(len(screens) - 1):
        s_from = screens[i]
        s_to   = screens[i + 1]
        # Get the action from the step description
        action = ""
        if s_from.get("step_ref") and s_from["step_ref"] != "—":
            step_desc = s_from.get("notes", "")
            action = extract_action_verb(step_desc)
        transitions.append({
            "from":      s_from["name"],
            "action":    action or "Continue →",
            "to":        s_to["name"],
            "condition": "",
        })

    # Error path transitions (back or to error screen)
    error_screens = [s for s in screens if "error" in s["name"].lower()]
    if error_screens:
        # Find screens that have validation (imply error paths)
        for s in screens:
            has_validation = any(
                f.get("validation") or f.get("required") == "Yes"
                for f in s.get("fields", [])
            )
            if has_validation:
                transitions.append({
                    "from":      s["name"],
                    "action":    "Submit (validation fails)",
                    "to":        error_screens[0]["name"],
                    "condition": "CONDITION: required fields empty or invalid",
                })
                transitions.append({
                    "from":      s["name"],
                    "action":    "Submit (validation passes)",
                    "to":        screens[min(screens.index(s) + 1, len(screens)-1)]["name"],
                    "condition": "CONDITION: all required fields valid",
                })

    # Cancel / back transitions
    for s in screens:
        if s["source"] == "flow" and s["name"] not in ("List View", "Entry / Trigger"):
            transitions.append({
                "from":      s["name"],
                "action":    "Cancel / Back",
                "to":        screens[0]["name"],
                "condition": "No data saved",
            })

    return transitions


def extract_action_verb(description):
    """Extract a short action label from a step description."""
    verbs = [
        r"click[s]?\s+(.+?)(?:\s+button|\s+→|$)",
        r"submit[s]?\s+(.+?)(?:\s+→|$)",
        r"select[s]?\s+(.+?)(?:\s+→|$)",
        r"fill[s]?\s+(.+?)(?:\s+→|$)",
        r"complet[e]?[s]?\s+(.+?)(?:\s+→|$)",
        r"save[s]?\s+(.+?)(?:\s+→|$)",
        r"confirm[s]?\s+(.+?)(?:\s+→|$)",
    ]
    desc_lower = description.lower()
    for pattern in verbs:
        m = re.search(pattern, desc_lower)
        if m:
            verb = m.group(0).split("→")[0].strip()
            return verb[:50] + ("…" if len(verb) > 50 else "")
    # Fallback: first N words
    words = description.split()
    return " ".join(words[:6]) + ("…" if len(words) > 6 else "")


# ── Interaction rules derivation ──────────────────────────────────────────────

def derive_interaction_rules(all_fields, ac_states, module_md):
    """Derive UI interaction rules from fields and acceptance criteria."""
    rules = []

    # Conditional required fields
    for f in all_fields:
        if f["required"] == "Conditional":
            cond = f.get("notes") or f.get("validation") or "under specific conditions"
            rules.append(f'"{f["display"]}" is required only when {cond}')

        if f["type"] == "enum" and f.get("enum_vals"):
            vals = f["enum_vals"].replace("·", ",")
            rules.append(f'"{f["display"]}" must be one of: {vals}')

        if f.get("validation"):
            rules.append(f'"{f["display"]}": {f["validation"]}')

        if f.get("pii") == "Yes":
            rules.append(f'"{f["display"]}" is sensitive — restrict visibility to authorized roles only')

    # Rules from acceptance criteria keywords
    for a in ac_states:
        kw   = a["keyword"]
        crit = a["criterion"]
        if kw == "disabled":
            rules.append(f'[{a["id"]}] Disabled state required: {crit[:100]}')
        elif kw == "hidden":
            rules.append(f'[{a["id"]}] Hidden/conditional element: {crit[:100]}')
        elif kw == "role":
            rules.append(f'[{a["id"]}] Role-based visibility: {crit[:100]}')

    return rules[:20]  # cap at 20 to keep prompt focused


# ── Prompt assembler ──────────────────────────────────────────────────────────

def assemble_prompt(
    module_title, system_name, actors, entry_exit,
    screens, transitions, all_fields, integration_fields,
    interaction_rules, oos_items, states_list, ac_screen_states,
    device, style_tone, density, module_md
):
    purpose_text = extract_section(module_md, "Business Purpose")
    purpose_clean = clean(purpose_text.split("\n")[0]) if purpose_text else ""

    lines = []
    A = lines.append  # shorthand

    A("# MIRO AI PROTOTYPE PROMPT")
    A(f"## Module: {module_title}")
    if system_name:
        A(f"## System: {system_name}")
    A("")
    A("---")
    A("")

    # ── CONTEXT ──────────────────────────────────────────────────────────────
    A("## CONTEXT")
    A("")
    if purpose_clean:
        A(f"{purpose_clean}")
        A("")
    A(f"**Primary actors:** {', '.join(actors)}")
    if entry_exit.get("entry"):
        A(f"**Triggered by:** {entry_exit['entry']}")
    if entry_exit.get("pre"):
        A(f"**Pre-conditions:** {entry_exit['pre']}")
    if entry_exit.get("exit"):
        A(f"**Completes when:** {entry_exit['exit']}")
    if states_list:
        A(f"**Entity states:** {' → '.join(states_list)}")
    A("")
    A(f"**Target device:** {device}")
    A(f"**Visual style:** {style_tone}")
    A(f"**Layout density:** {density}")
    A("")
    A("---")
    A("")

    # ── SCREEN INVENTORY ─────────────────────────────────────────────────────
    A("## SCREEN INVENTORY")
    A("")
    A("Generate **exactly** these screens, with these exact names. Do not add extra screens.")
    A("Do not merge screens. Every screen listed must appear as a separate frame in the prototype.")
    A("")
    for i, s in enumerate(screens, 1):
        note = f" — {s['notes']}" if s.get("notes") else ""
        A(f"{i}. **{s['name']}**{note}")
    A("")
    A("---")
    A("")

    # ── FLOW MAP ─────────────────────────────────────────────────────────────
    A("## FLOW MAP")
    A("")
    A("Connect the screens using these **exact transitions**. Every arrow listed must exist in the prototype.")
    A("Do not add connections that are not listed here.")
    A("")
    for t in transitions:
        cond = f"  ← {t['condition']}" if t.get("condition") else ""
        A(f"**[{t['from']}]** --[{t['action']}]--> **[{t['to']}]**{cond}")
    A("")
    A("---")
    A("")

    # ── SCREEN DETAILS ────────────────────────────────────────────────────────
    A("## SCREEN DETAILS")
    A("")
    A("For each screen, build exactly the layout described. No additional sections or panels.")
    A("")

    for s in screens:
        A(f"### {s['name']}")
        if s.get("notes"):
            A(f"_{s['notes']}_")
        A("")

        # Fields
        fields = s.get("fields", [])
        if fields:
            A("**Fields / elements to show:**")
            for f in fields:
                req_marker = " *(required)*" if f.get("required") == "Yes" else \
                             " *(conditional)*" if f.get("required") == "Conditional" else ""
                type_note  = f" `[{f['type']}]`" if f.get("type") else ""
                enum_note  = f" — options: {f['enum_vals']}" if f.get("type") == "enum" and f.get("enum_vals") else ""
                source_note= f" ⚠ read-only (from {f['ref'] or f['source']})" \
                             if f.get("source") in ("integration", "system_generated", "derived") else ""
                A(f"- {f['display']}{type_note}{req_marker}{enum_note}{source_note}")
            A("")

        # Integration fields on this screen
        screen_integrations = [f for f in fields if f.get("source") == "integration"]
        if screen_integrations:
            A("**Integration displays (read-only, auto-updating):**")
            for f in screen_integrations:
                A(f"- {f['display']} — fetched from {f.get('ref', 'external source')} · Show loading state while fetching · Show error state if unavailable")
            A("")

        # Infer layout hint
        name_lower = s["name"].lower()
        if any(w in name_lower for w in ("list", "overview", "dashboard")):
            A("**Layout:** Table or card list with column headers. Include search/filter bar at top. Empty state if no records.")
        elif any(w in name_lower for w in ("form", "create", "edit", "step")):
            A("**Layout:** Single-column form. Group related fields. Show required field indicators. Primary action button at bottom.")
            if len(screens) > screens.index(s) + 1:
                A(f"**Progress indicator:** Show step progress if this is part of a multi-step flow.")
        elif any(w in name_lower for w in ("detail", "view", "show")):
            A("**Layout:** Two-column detail view. Labels on left, values on right. Action buttons in header.")
        elif any(w in name_lower for w in ("confirm", "review", "success")):
            A("**Layout:** Centered confirmation card. Summary of submitted data. Clear primary CTA.")
        elif "error" in name_lower:
            A("**Layout:** Inline error messages below affected fields. Do not replace the form — show errors in context.")
        elif "empty" in name_lower:
            A("**Layout:** Centered illustration + headline + CTA to create first record.")
        A("")

    A("---")
    A("")

    # ── INTERACTION RULES ─────────────────────────────────────────────────────
    if interaction_rules:
        A("## INTERACTION RULES")
        A("")
        A("Apply these rules to the relevant screens:")
        A("")
        for rule in interaction_rules:
            A(f"- {rule}")
        A("")
        A("---")
        A("")

    # ── INTEGRATION & LOADING STATES ──────────────────────────────────────────
    if integration_fields:
        A("## INTEGRATION & LOADING STATES")
        A("")
        A("For every field sourced from an external API, show three states:")
        A("")
        for f in integration_fields:
            A(f"**{f['display']}** (from: {f.get('ref', 'API')})")
            A(f"- Loading state: skeleton/spinner in the field area")
            A(f"- Loaded state: value displayed as read-only with timestamp if relevant")
            A(f"- Error state: inline error message + retry action. Rest of form remains usable.")
            A("")
        A("---")
        A("")

    # ── ROLE-BASED VISIBILITY ─────────────────────────────────────────────────
    role_criteria = [a for a in ac_screen_states if a["keyword"] == "role"]
    if role_criteria:
        A("## ROLE-BASED VISIBILITY")
        A("")
        A("Show these variations in the prototype (use annotations or separate frames):")
        A("")
        for a in role_criteria:
            A(f"- [{a['id']}] {a['criterion']}")
        A("")
        A("---")
        A("")

    # ── OUT OF SCOPE ──────────────────────────────────────────────────────────
    if oos_items:
        A("## DO NOT INCLUDE")
        A("")
        A("The following are explicitly out of scope. Do not add screens or flows for these:")
        A("")
        for item in oos_items:
            A(f"- {item}")
        A("")
        A("---")
        A("")

    # ── QUALITY CHECKLIST ────────────────────────────────────────────────────
    A("## PROTOTYPE QUALITY CHECKLIST")
    A("")
    A("Before finishing, verify:")
    A("")
    A(f"- [ ] Exactly {len(screens)} screens exist — one for each item in the Screen Inventory")
    A(f"- [ ] Every transition in the Flow Map has a visible connector with a label")
    A("- [ ] Every screen with a form shows field labels, input types, and required indicators")
    A("- [ ] Every integration field has a loading state visible")
    A("- [ ] Error states are shown in context (inline), not as separate replacement screens")
    A("- [ ] Empty states are included for list views")
    A("- [ ] Role-restricted fields are annotated")
    A("- [ ] No screens were added beyond the inventory list")
    A("")
    A("---")
    A("")
    A(f"_Generated from workspace artifacts. Module: {module_title}. ")
    A(f"Source files: 01-module-*.md + 02-data-dictionary.md + 03-acceptance-criteria.md_")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Miro prototype prompt")
    parser.add_argument("project_slug", help="Project slug (subfolder of workspace/)")
    parser.add_argument("module_slug",  help="Module slug (from 01-module-[slug].md)")
    parser.add_argument("--device",  default="desktop",   choices=["mobile", "desktop", "both"])
    parser.add_argument("--style",   default="neutral",   choices=["enterprise", "consumer", "neutral"])
    parser.add_argument("--density", default="comfortable", choices=["compact", "comfortable", "spacious"])
    args = parser.parse_args()

    workspace_dir = Path("workspace") / args.project_slug
    export_dir    = workspace_dir / "exports"

    if not workspace_dir.exists():
        print(f"\n❌  Project not found: {workspace_dir}")
        sys.exit(1)

    # Find module file
    module_path = workspace_dir / f"01-module-{args.module_slug}.md"
    if not module_path.exists():
        # Try to find any module file
        candidates = list(workspace_dir.glob("01-module-*.md"))
        if len(candidates) == 1:
            module_path = candidates[0]
            args.module_slug = module_path.stem.replace("01-module-", "")
        else:
            print(f"\n❌  Module file not found: {module_path}")
            if candidates:
                print("    Available modules:")
                for c in candidates:
                    print(f"      - {c.stem.replace('01-module-', '')}")
            sys.exit(1)

    export_dir.mkdir(exist_ok=True)

    print(f"\n🎨  Generating Miro prompt for: {args.project_slug} / {args.module_slug}")
    print(f"    Device: {args.device} | Style: {args.style} | Density: {args.density}\n")

    # Read source files
    module_md = read_file(module_path)
    dd_md     = read_file(workspace_dir / "02-data-dictionary.md")
    ac_md     = read_file(workspace_dir / "03-acceptance-criteria.md")

    # Extract meta
    system_name = ""
    m = re.search(r"\*\*System\*\*:?\s*(.+)", module_md)
    if m: system_name = m.group(1).strip()
    module_title = args.module_slug.replace("-", " ").replace("_", " ").title()
    m2 = re.search(r"#\s+Module Definition Card\s*[—–-]\s*(.+)", module_md)
    if m2: module_title = m2.group(1).strip()

    # Parse everything
    steps              = parse_flow_steps(module_md)
    actors             = parse_actors(module_md)
    states_list        = parse_states(module_md)
    entry_exit         = parse_entry_exit(module_md)
    dd_screens, all_fields, integration_fields, derived_fields = parse_dd_for_module(dd_md, module_title)
    ac_screen_states   = parse_ac_states(ac_md)
    oos_items          = parse_oos(module_md)

    # Derive screens and transitions
    screens     = derive_screens(steps, entry_exit, states_list, dd_screens, ac_screen_states)
    transitions = derive_transitions(screens, steps, ac_screen_states)
    rules       = derive_interaction_rules(all_fields, ac_screen_states, module_md)

    # Assemble prompt
    prompt = assemble_prompt(
        module_title, system_name, actors, entry_exit,
        screens, transitions, all_fields, integration_fields,
        rules, oos_items, states_list, ac_screen_states,
        device=args.device,
        style_tone=args.style,
        density=args.density,
        module_md=module_md,
    )

    # Write output
    out_path = export_dir / f"miro-prompt-{args.module_slug}.md"
    Path(out_path).write_text(prompt, encoding="utf-8")

    print(f"  ✅  miro-prompt-{args.module_slug}.md  →  {out_path}")
    print(f"\n  📋  Screen inventory: {len(screens)} screens")
    print(f"  🔗  Transitions:      {len(transitions)} connections")
    print(f"  📊  Fields mapped:    {len(all_fields)} fields")
    print(f"  ⚡  Integration fields: {len(integration_fields)}")
    print(f"\n  Open the .md file, copy the full contents, and paste into Miro AI.\n")

if __name__ == "__main__":
    main()
