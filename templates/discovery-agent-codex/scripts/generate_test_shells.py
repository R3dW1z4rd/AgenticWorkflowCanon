#!/usr/bin/env python3
"""
generate_test_shells.py
-----------------------
Reads a project's behavioral test specs and acceptance criteria,
then generates ready-to-run test shell files:

  - [module-slug].service.test.ts   (Vitest — unit + integration layers)
  - [module-slug].spec.ts    (Playwright — e2e layer)

All assertions are written. All implementations are NOT (shells only).
The Agentic Software Factory receives these shells and must make every test pass.

Usage:
    python3 scripts/generate_test_shells.py <project-slug> [module-slug]

Example:
    python3 scripts/generate_test_shells.py contract-manager contract-creation

Output:
    workspace/<project-slug>/exports/[module-slug].service.test.ts
    workspace/<project-slug>/exports/[module-slug].spec.ts
"""

import sys
import re
import argparse
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_file(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def slugify(text):
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-")

def to_camel(text):
    parts = re.split(r"[\s_\-]+", text.strip())
    return parts[0].lower() + "".join(p.title() for p in parts[1:])

def to_pascal(text):
    parts = re.split(r"[\s_\-]+", text.strip())
    return "".join(p.title() for p in parts)

def safe_fn_name(text):
    """Turn a criterion into a valid function/describe name."""
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    words = text.split()[:10]
    return to_camel(" ".join(words))


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_behavioral_specs(spec_md):
    """
    Parse behavioral test spec markdown into structured AC blocks.
    Returns list of:
      { id, criterion, layer, actor, priority, scenarios: [{name, setup, action, expect, notes}] }
    """
    blocks = []

    # Split on AC-level headers: ### [AC-XXX] ...
    ac_pattern = re.compile(
        r"(?:^|\n)#{2,3}\s+\[?(AC-\d+)\]?\s*[—–\-]?\s*(?:The system must\s+)?(.+?)(?=\n#{2,3}\s+(?:\[?AC-|\Z))",
        re.DOTALL
    )

    for m in ac_pattern.finditer(spec_md):
        ac_id   = m.group(1).strip()
        header  = m.group(2).strip().split("\n")[0].strip()
        body    = m.group(0)

        # Extract layer — capture full line to detect multi-layer specs (e.g. "unit + e2e")
        layer_m    = re.search(r"\*\*Layer[:\*]+\s*([^\n]+)", body, re.IGNORECASE)
        layer_raw  = layer_m.group(1).strip().lower() if layer_m else "unit"
        # Primary layer for grouping
        if "unit" in layer_raw:
            layer = "unit"
        elif "integration" in layer_raw:
            layer = "integration"
        elif "e2e" in layer_raw:
            layer = "e2e"
        else:
            layer = "unit"

        # Extract actor
        actor_m = re.search(r"\*\*Actor\*\*:?\s*(.+?)(?=\n|\*\*)", body, re.IGNORECASE)
        actor   = actor_m.group(1).strip() if actor_m else "User"

        # Extract priority
        prio_m  = re.search(r"\*\*Priority\*\*:?\s*(\w+)", body, re.IGNORECASE)
        prio    = prio_m.group(1).strip() if prio_m else "Must"

        # Extract scenarios
        scenarios = []
        scen_pattern = re.compile(
            r"####\s+SCENARIO\s+\d+\s+[—–-]+\s*(.+?)\n"
            r"```\s*\n([\s\S]*?)```",
            re.IGNORECASE
        )
        for sm in scen_pattern.finditer(body):
            scen_name = sm.group(1).strip()
            scen_body = sm.group(2)

            setup_m  = re.search(r"Setup:\s*(.+?)(?=Action:|Expect:|Notes:|$)",
                                  scen_body, re.DOTALL | re.IGNORECASE)
            action_m = re.search(r"Action:\s*(.+?)(?=Expect:|Notes:|$)",
                                  scen_body, re.DOTALL | re.IGNORECASE)
            expect_m = re.search(r"Expect:\s*(.+?)(?=Notes:|$)",
                                  scen_body, re.DOTALL | re.IGNORECASE)
            notes_m  = re.search(r"Notes:\s*(.+?)$",
                                  scen_body, re.DOTALL | re.IGNORECASE)

            scenarios.append({
                "name":   scen_name,
                "setup":  setup_m.group(1).strip()  if setup_m  else "",
                "action": action_m.group(1).strip() if action_m else "",
                "expect": expect_m.group(1).strip() if expect_m else "",
                "notes":  notes_m.group(1).strip()  if notes_m  else "",
            })

        # Fallback: if no backtick blocks found, try plain text scenarios
        if not scenarios:
            plain_scen = re.compile(
                r"####\s+SCENARIO\s+\d+\s+[—–-]+\s*(.+?)(?=####|\Z)", re.DOTALL
            )
            for sm in plain_scen.finditer(body):
                scen_name = sm.group(1).split("\n")[0].strip()
                scen_body = sm.group(1)
                setup_m  = re.search(r"\*\*Setup\*\*:?\s*(.+?)(?=\*\*Action|$)", scen_body, re.DOTALL | re.IGNORECASE)
                action_m = re.search(r"\*\*Action\*\*:?\s*(.+?)(?=\*\*Expect|$)", scen_body, re.DOTALL | re.IGNORECASE)
                expect_m = re.search(r"\*\*Expect\*\*:?\s*(.+?)(?=\*\*Notes|$)", scen_body, re.DOTALL | re.IGNORECASE)
                scenarios.append({
                    "name":   scen_name,
                    "setup":  setup_m.group(1).strip()  if setup_m  else "",
                    "action": action_m.group(1).strip() if action_m else "",
                    "expect": expect_m.group(1).strip() if expect_m else "",
                    "notes":  "",
                })

        if not scenarios:
            scenarios.append({
                "name":   "happy path",
                "setup":  "",
                "action": "",
                "expect": "",
                "notes":  "",
            })

        blocks.append({
            "id":        ac_id,
            "criterion": header,
            "layer":     layer,
            "layer_raw": layer_raw,
            "actor":     actor,
            "priority":  prio,
            "scenarios": scenarios,
        })

    return blocks

def parse_dd_imports(dd_md, module_slug):
    """
    Derive likely import paths from the data dictionary.
    Groups field names by inferred service/validator category.
    """
    validators = set()
    services   = set()
    entities   = set()

    rows = []
    for line in dd_md.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", line.replace(" ", "")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) > 3:
            rows.append(cells)

    for row in rows[1:]:  # skip header
        field = row[0] if row else ""
        dtype = row[3] if len(row) > 3 else ""
        source = row[7] if len(row) > 7 else ""
        validation = row[5] if len(row) > 5 else ""

        if validation or dtype in ("date", "enum", "reference"):
            # Implies a validator
            if "date" in field.lower() or dtype == "date":
                validators.add("validateStartDate")
            elif dtype == "enum":
                validators.add(f"validate{to_pascal(field.replace('_', ' '))}")
            elif validation:
                validators.add(f"validate{to_pascal(field.replace('_', ' '))}")

        if source == "integration":
            services.add(f"fetch{to_pascal(field.replace('_', ' ').replace('rate', 'Rate'))}")

    return validators, services


# ── Unit test generator ───────────────────────────────────────────────────────

def generate_unit_tests(blocks, module_slug, module_title, dd_md):
    """Generate Vitest unit and integration test shells."""

    unit_blocks   = [b for b in blocks if "unit" in b.get("layer_raw", b["layer"]) or "integration" in b.get("layer_raw", b["layer"])]
    validators, services = parse_dd_imports(dd_md, module_slug)

    lines = []
    A = lines.append

    A(f'/**')
    A(f' * {module_title.upper()} — Service Test Shells')
    A(f' * Framework: Vitest')
    A(f' *')
    A(f' * SHELLS ONLY — assertions written, implementations are NOT.')
    A(f' * The coding agent must make every test pass per the canon\'s service patterns.')
    A(f' *')
    A(f' * File location: modules/{module_slug}/{module_slug}.service.test.ts')
    A(f' *')
    A(f' * Coverage:')
    for b in unit_blocks:
        A(f' *   {b["id"]} — {b["criterion"][:70]}')
    A(f' */')
    A('')
    A("import { describe, it, expect, beforeEach } from 'vitest'")
    A(f"import {{ {to_camel(module_slug.replace('-', ' '))}Service }} from './{module_slug}.service'")
    A(f"import {{ {to_camel(module_slug.replace('-', ' '))} }} from '@/db/schema'")
    A(f"import {{ db }} from '@/db'")
    A(f"import {{ makeOrgContext }} from '@/tests/helpers/caller-context'")
    A('')
    A('// ─── Test setup ──────────────────────────────────────────────────────────')
    A('// Each test creates its own org context for isolation.')
    A('// The table is cleared between tests to keep tests independent.')
    A('')
    A(f'beforeEach(async () => {{')
    A(f'  await db.delete({to_camel(module_slug.replace("-", " "))})')
    A(f'}})')
    A('')

    # Group tests by inferred describe block
    describe_groups = {}
    for b in unit_blocks:
        crit_lower = b["criterion"].lower()
        if any(w in crit_lower for w in ("date", "past", "future", "start date")):
            group = "Date Validation"
        elif any(w in crit_lower for w in ("required", "field", "proceed", "step")):
            group = "Required Field Validation"
        elif any(w in crit_lower for w in ("referral", "maximum", "5", "limit", "type")):
            group = "Referral Validation"
        elif any(w in crit_lower for w in ("exchange", "rate", "forex", "api", "loading", "error state")):
            group = "Exchange Rate Service"
        elif any(w in crit_lower for w in ("draft", "creat", "initiat", "save as")):
            group = "Contract Creation Service"
        elif any(w in crit_lower for w in ("audit", "log", "status", "notif", "email")):
            group = "Status & Audit Service"
        elif any(w in crit_lower for w in ("commission", "role", "visible", "permission", "access")):
            group = "Permission Guard"
        elif any(w in crit_lower for w in ("auto-save", "auto save", "60 second", "restore")):
            group = "Auto-Save Service"
        else:
            group = "Core Service"
        describe_groups.setdefault(group, []).append(b)

    for group_name, group_blocks in describe_groups.items():
        A(f"// {'═' * 76}")
        A(f"// {group_name}")
        A(f"// {'═' * 76}")
        A('')
        A(f"describe('{group_name}', () => {{")
        A('')

        needs_timer = any(
            "60" in b["criterion"] or "timer" in b["criterion"].lower() or "auto" in b["criterion"].lower()
            for b in group_blocks
        )
        needs_mock = any(
            any(w in b["criterion"].lower() for w in ("api", "fetch", "email", "notif", "audit"))
            for b in group_blocks
        )

        if needs_timer:
            A("  beforeEach(() => { vi.useFakeTimers() })")
            A("  afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks() })")
            A('')
        elif needs_mock:
            A("  beforeEach(() => { vi.clearAllMocks() })")
            A('')

        for b in group_blocks:
            for scen in b["scenarios"]:
                # Build test description
                scen_name = scen["name"].lower()
                test_desc = f"[{b['id']}] {scen['name']}"

                A(f"  it('{test_desc}', async () => {{")

                # Setup comment
                if scen["setup"]:
                    setup_lines = [l.strip() for l in scen["setup"].splitlines() if l.strip()]
                    for sl in setup_lines[:3]:
                        A(f"    // Setup: {sl[:100]}")

                # Action comment
                if scen["action"]:
                    action_lines = [l.strip() for l in scen["action"].splitlines() if l.strip()]
                    for al in action_lines[:2]:
                        A(f"    // Action: {al[:100]}")

                A('')

                # Generate typed assertions from expect text
                assertions = derive_assertions(b, scen)
                for assertion in assertions:
                    A(f"    {assertion}")

                if scen["notes"]:
                    notes_lines = [l.strip() for l in scen["notes"].splitlines() if l.strip()]
                    A('')
                    for nl in notes_lines[:2]:
                        A(f"    // NOTE: {nl[:100]}")

                A("  })")
                A('')

        A("})")
        A('')
        A('')

    # ── Required org isolation tests (canon mandate) ──────────────────────
    # These four tests are non-negotiable per Section 9 of the canon.
    # They verify the module's data isolation across organizations.
    service_var = to_camel(module_slug.replace('-', ' ')) + 'Service'
    id_param    = to_camel(module_slug.replace('-', ' ')) + 'Id'
    pretty_name = module_title

    A('// ─── Required org isolation tests (canon mandate) ──────────────────────')
    A('// These four tests are non-negotiable per Section 9 of the canon.')
    A('// Do not delete or skip them — they verify cross-org data isolation.')
    A('')
    A(f"describe('{service_var} — org isolation (REQUIRED)', () => {{")
    A('')
    A("  it('cannot fetch a record from another org', async () => {")
    A("    const orgA = makeOrgContext()")
    A("    const orgB = makeOrgContext()")
    A('')
    A(f"    const created = await {service_var}.create({{")
    A("      data: { /* TODO: minimal valid record per schema */ },")
    A("      ctx:  orgA.ctx,")
    A("    })")
    A('')
    A(f"    const found = await {service_var}.getById({{")
    A(f"      {id_param}: created.data!.id,")
    A("      ctx:           orgB.ctx,")
    A("    })")
    A('')
    A("    expect(found).toBeNull()")
    A("  })")
    A('')
    A("  it('cannot update a record from another org', async () => {")
    A("    const orgA = makeOrgContext()")
    A("    const orgB = makeOrgContext()")
    A('')
    A(f"    const created = await {service_var}.create({{")
    A("      data: { /* TODO: minimal valid record */ },")
    A("      ctx:  orgA.ctx,")
    A("    })")
    A('')
    A(f"    const result = await {service_var}.update({{")
    A(f"      {id_param}: created.data!.id,")
    A("      data:           { /* TODO: minimal update */ },")
    A("      ctx:            orgB.ctx,")
    A("    })")
    A('')
    A(f"    expect(result.error).toBe('{pretty_name} not found')")
    A("  })")
    A('')
    A("  it('cannot delete a record from another org', async () => {")
    A("    const orgA = makeOrgContext()")
    A("    const orgB = makeOrgContext()")
    A('')
    A(f"    const created = await {service_var}.create({{")
    A("      data: { /* TODO: minimal valid record */ },")
    A("      ctx:  orgA.ctx,")
    A("    })")
    A('')
    A(f"    const result = await {service_var}.delete({{")
    A(f"      {id_param}: created.data!.id,")
    A("      ctx:           orgB.ctx,")
    A("    })")
    A('')
    A(f"    expect(result.error).toBe('{pretty_name} not found')")
    A("  })")
    A('')
    A("  it('list returns only records from the requesting org', async () => {")
    A("    const orgA = makeOrgContext()")
    A("    const orgB = makeOrgContext()")
    A('')
    A(f"    await {service_var}.create({{ data: {{ /* TODO */ }}, ctx: orgA.ctx }})")
    A(f"    await {service_var}.create({{ data: {{ /* TODO */ }}, ctx: orgA.ctx }})")
    A(f"    await {service_var}.create({{ data: {{ /* TODO */ }}, ctx: orgB.ctx }})")
    A('')
    A(f"    const result = await {service_var}.listByOrg({{ ctx: orgA.ctx }})")
    A('')
    A("    expect(result.data).toHaveLength(2)")
    A("    expect(result.data.every(r => r.orgId === orgA.ctx.orgId)).toBe(true)")
    A("  })")
    A('')
    A("})")
    A('')

    return "\n".join(lines)


def derive_assertions(block, scenario):
    """Derive meaningful Vitest assertions from scenario expect text."""
    assertions = []
    expect_text = scenario["expect"].lower()
    crit_lower  = block["criterion"].lower()
    scen_name   = scenario["name"].lower()

    is_failure = any(w in scen_name for w in ("fail", "error", "invalid", "reject", "missing", "empty", "unavail"))
    is_success = any(w in scen_name for w in ("happy", "success", "valid", "pass", "accept"))

    # Date validation
    if "date" in crit_lower:
        if is_failure:
            assertions += [
                "const result = validateStartDate(pastDate, TODAY)",
                "expect(result.valid).toBe(false)",
                "expect(result.error).toBeDefined()",
            ]
        else:
            assertions += [
                "const result = validateStartDate(TODAY, TODAY)",
                "expect(result.valid).toBe(true)",
                "expect(result.error).toBeUndefined()",
            ]

    # Required fields
    elif "required" in crit_lower and "field" in crit_lower:
        if is_failure:
            assertions += [
                "const errors = validateRequiredFields({ ...VALID_FORM, [field]: '' })",
                "expect(errors[field]).toBeDefined()",
            ]
        else:
            assertions += [
                "const errors = validateRequiredFields(VALID_FORM)",
                "expect(errors).toEqual({})",
            ]

    # API / fetch
    elif any(w in crit_lower for w in ("api", "exchange", "rate", "fetch")):
        if is_failure or any(w in expect_text for w in ("error", "unavail", "fail", "timeout")):
            assertions += [
                "vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(new Error('Network error')))",
                "await expect(fetchExchangeRate()).rejects.toThrow()",
            ]
        elif "loading" in expect_text or "loading" in scen_name:
            assertions += [
                "// Verify loading state is exposed before data resolves",
                "const promise = fetchExchangeRate()",
                "// assert loading state here",
                "const result = await promise",
                "expect(result).toBeDefined()",
            ]
        else:
            assertions += [
                "vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({",
                "  ok: true, json: async () => ({ rate: 1.0823 })",
                "}))",
                "const result = await fetchExchangeRate()",
                "expect(result.exchange_rate).toBe(1.0823)",
                "expect(result.exchange_rate_at).toBeDefined()",
            ]

    # Status / audit
    elif any(w in crit_lower for w in ("status", "audit", "log")):
        assertions += [
            "await changeStatus(contract, newStatus, userId, { auditRepo: mockAuditRepo, notifications: mockNotifications })",
            "expect(mockAuditRepo.create).toHaveBeenCalledOnce()",
            "const entry = mockAuditRepo.create.mock.calls[0][0]",
            "expect(entry.new_status).toBe(newStatus)",
            "expect(entry.user_id).toBe(userId)",
        ]

    # Email / notification
    elif any(w in crit_lower for w in ("email", "notif", "send")):
        if is_failure or "not" in expect_text or "no duplicate" in scen_name:
            assertions += [
                "await changeStatus(contract, sameStatus, userId, deps)",
                "expect(mockNotifications.send).not.toHaveBeenCalled()",
            ]
        else:
            assertions += [
                "await changeStatus(contract, 'pending', userId, deps)",
                "expect(mockNotifications.send).toHaveBeenCalledOnce()",
                "expect(mockNotifications.send).toHaveBeenCalledWith(",
                "  expect.objectContaining({ account_manager_id: contract.account_manager_id })",
                ")",
            ]

    # Draft / create
    elif any(w in crit_lower for w in ("draft", "creat", "initiat")):
        assertions += [
            "const result = await createDraft({ account_manager_id: 'am-001' })",
            "expect(result.status).toBe('draft')",
            "expect(result.contract_id).toMatch(",
            "  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i",
            ")",
        ]

    # Save as draft (no validation)
    elif "save" in crit_lower and "draft" in crit_lower:
        assertions += [
            "// No validation errors should be thrown for draft saves",
            "await expect(saveAsDraft({ account_manager_id: 'am-001' })).resolves.not.toThrow()",
        ]

    # Referral count
    elif any(w in crit_lower for w in ("referral", "maximum", "5", "limit")):
        if is_failure:
            assertions += [
                "const sixReferrals = Array.from({ length: 6 }, (_, i) => ({ referral_type: 'external', external_name: `R${i}` }))",
                "const result = validateReferralList(sixReferrals)",
                "expect(result.valid).toBe(false)",
                "expect(result.error).toContain('5')",
            ]
        else:
            assertions += [
                "const fiveReferrals = Array.from({ length: 5 }, (_, i) => ({ referral_type: 'external', external_name: `R${i}` }))",
                "const result = validateReferralList(fiveReferrals)",
                "expect(result.valid).toBe(true)",
            ]

    # Referral type conditional
    elif "employee" in crit_lower or "external" in crit_lower or "type" in crit_lower and "referral" in crit_lower:
        if "employee" in scen_name or "employee" in expect_text:
            assertions += [
                "const result = validateReferralEntry({ referral_type: 'employee' })",
                "expect(result.valid).toBe(false)",
                "expect(result.errors?.employee_id).toBeDefined()",
            ]
        else:
            assertions += [
                "const result = validateReferralEntry({ referral_type: 'external', external_name: 'Jane' })",
                "expect(result.valid).toBe(true)",
            ]

    # Permission / role / visibility
    elif any(w in crit_lower for w in ("commission", "role", "visible", "permission", "restrict")):
        if "authorized" in expect_text or "account manager" in scen_name.lower() or "finance" in scen_name.lower():
            assertions += [
                "expect(canViewField('commission_rate', 'account_manager')).toBe(true)",
                "expect(canViewField('commission_rate', 'finance')).toBe(true)",
            ]
        else:
            assertions += [
                "expect(canViewField('commission_rate', 'viewer')).toBe(false)",
                "expect(canViewField('commission_rate', 'support')).toBe(false)",
            ]

    # Auto-save
    elif any(w in crit_lower for w in ("auto", "60", "restore", "timer")):
        if "stop" in scen_name or "cancel" in scen_name:
            assertions += [
                "const mockSave = vi.fn()",
                "const { stop } = autoSave('draft-001', {}, mockSave)",
                "stop()",
                "vi.advanceTimersByTime(120_000)",
                "await vi.runAllTimersAsync()",
                "expect(mockSave).not.toHaveBeenCalled()",
            ]
        else:
            assertions += [
                "const mockSave = vi.fn().mockResolvedValue(undefined)",
                "const { stop } = autoSave('draft-001', { field: 'value' }, mockSave)",
                "expect(mockSave).not.toHaveBeenCalled()",
                "vi.advanceTimersByTime(60_000)",
                "await vi.runAllTimersAsync()",
                "expect(mockSave).toHaveBeenCalledOnce()",
                "stop()",
            ]

    else:
        # Generic fallback
        if is_failure:
            assertions += [
                "// TODO: call the relevant function with invalid input",
                "// expect(result.valid).toBe(false)",
                "// expect(result.error).toBeDefined()",
            ]
        else:
            assertions += [
                "// TODO: call the relevant function with valid input",
                "// expect(result.valid).toBe(true)",
            ]

    return assertions


# ── E2E test generator ────────────────────────────────────────────────────────

def generate_e2e_tests(blocks, module_slug, module_title, dd_md):
    """Generate Playwright E2E test shells."""

    e2e_blocks = [b for b in blocks if "e2e" in b.get("layer_raw", b["layer"])]
    if not e2e_blocks:
        return None

    lines = []
    A = lines.append

    A(f'/**')
    A(f' * {module_title.upper()} — E2E Test Shells')
    A(f' * Framework: Playwright')
    A(f' *')
    A(f' * SHELLS ONLY — interactions scripted, implementations are NOT.')
    A(f' * All selectors use data-testid attributes.')
    A(f' * The agent generating UI code must add these attributes.')
    A(f' *')
    A(f' * Coverage:')
    for b in e2e_blocks:
        A(f' *   {b["id"]} — {b["criterion"][:70]}')
    A(f' */')
    A('')
    A("import { test, expect, Page } from '@playwright/test'")
    A('')
    A('// ─── Config ──────────────────────────────────────────────────────────────────')
    A("const BASE_URL = process.env.TEST_BASE_URL ?? 'http://localhost:3000'")
    A('')
    A('const USERS = {')
    A("  default_user:    { email: 'user@test.local',    password: 'Test1234!' },")
    A("  admin:           { email: 'admin@test.local',   password: 'Test1234!' },")
    A("  restricted_user: { email: 'viewer@test.local',  password: 'Test1234!' },")
    A('}')
    A('')

    # Derive selectors from criteria
    all_selectors = derive_selectors(e2e_blocks, module_slug)
    A('const SEL = {')
    for k, v in all_selectors.items():
        A(f"  {k}: '[data-testid=\"{v}\"]',")
    A('}')
    A('')
    A('// ─── Helpers ──────────────────────────────────────────────────────────────────')
    A('async function loginAs(page: Page, role: keyof typeof USERS) {')
    A(f"  await page.goto(`${{BASE_URL}}/login`)")
    A("  await page.fill('[data-testid=\"email-input\"]', USERS[role].email)")
    A("  await page.fill('[data-testid=\"password-input\"]', USERS[role].password)")
    A("  await page.click('[data-testid=\"login-btn\"]')")
    A(f"  await page.waitForURL(`${{BASE_URL}}/dashboard`)")
    A('}')
    A('')

    # Group e2e tests by describe block
    describe_groups = {}
    for b in e2e_blocks:
        crit_lower = b["criterion"].lower()
        if any(w in crit_lower for w in ("initiat", "creat", "new", "start")):
            group = "Initiate / Create"
        elif any(w in crit_lower for w in ("date", "required", "valid", "reject", "field")):
            group = "Form Validation"
        elif any(w in crit_lower for w in ("exchange", "rate", "api", "loading", "unavail")):
            group = "Exchange Rate Display"
        elif any(w in crit_lower for w in ("referral", "maximum", "employee", "external", "type")):
            group = "Referral Management"
        elif any(w in crit_lower for w in ("draft", "save", "restore")):
            group = "Save as Draft"
        elif any(w in crit_lower for w in ("commission", "role", "visible", "restrict", "permission")):
            group = "Role-Based Visibility"
        elif any(w in crit_lower for w in ("notif", "email", "audit", "log")):
            group = "Notifications & Audit"
        else:
            group = "General"
        describe_groups.setdefault(group, []).append(b)

    for group_name, group_blocks in describe_groups.items():
        A(f"// {'═' * 76}")
        A('')
        A(f"test.describe('{group_name}', () => {{")
        A('')
        A("  test.beforeEach(async ({ page }) => {")
        A("    await loginAs(page, 'default_user')")
        A("  })")
        A('')

        for b in group_blocks:
            for scen in b["scenarios"]:
                test_desc = f"[{b['id']}] {scen['name']}"
                A(f"  test('{test_desc}', async ({{ page }}) => {{")

                # Setup comment
                if scen["setup"]:
                    setup_lines = [l.strip() for l in scen["setup"].splitlines() if l.strip()]
                    for sl in setup_lines[:2]:
                        A(f"    // Setup: {sl[:100]}")

                A('')
                # Generate E2E assertions
                e2e_assertions = derive_e2e_assertions(b, scen, all_selectors, module_slug)
                for ea in e2e_assertions:
                    A(f"    {ea}")

                if scen["notes"]:
                    A('')
                    A(f"    // NOTE: {scen['notes'][:120]}")

                A("  })")
                A('')

        A("})")
        A('')
        A('')

    return "\n".join(lines)


def derive_selectors(blocks, module_slug):
    """Derive a set of data-testid selectors from E2E block criteria."""
    sel = {
        "continueBtn":   f"{module_slug}-continue-btn",
        "submitBtn":     f"{module_slug}-submit-btn",
        "saveAsDraftBtn":f"{module_slug}-save-draft-btn",
        "cancelBtn":     f"{module_slug}-cancel-btn",
        "successToast":  "success-toast",
        "errorSummary":  "form-error-summary",
    }
    for b in blocks:
        crit = b["criterion"].lower()
        if any(w in crit for w in ("date", "start date")):
            sel["startDateInput"] = "contract-start-date"
            sel["startDateError"] = "error-contract-start-date"
        if any(w in crit for w in ("account manager", "manager")):
            sel["accountManagerSelect"] = "account-manager-select"
            sel["accountManagerError"]  = "error-account-manager-id"
        if any(w in crit for w in ("type", "contract type")):
            sel["contractTypeSelect"] = "contract-type-select"
        if any(w in crit for w in ("exchange", "rate")):
            sel["exchangeRateDisplay"] = "exchange-rate-display"
            sel["exchangeRateAt"]      = "exchange-rate-at"
            sel["exchangeRateSpinner"] = "exchange-rate-loading"
            sel["exchangeRateError"]   = "exchange-rate-error"
            sel["exchangeRateRetry"]   = "exchange-rate-retry"
        if any(w in crit for w in ("referral",)):
            sel["addReferralBtn"]    = "add-referral-btn"
            sel["referralTypeSelect"]= "referral-type-select"
            sel["employeeSelect"]    = "referral-employee-select"
            sel["externalNameInput"] = "referral-external-name"
            sel["referralListItem"]  = "referral-list-item"
            sel["saveReferralBtn"]   = "save-referral-btn"
            sel["referralError"]     = "referral-list-error"
        if any(w in crit for w in ("commission", "rate", "sensitive")):
            sel["commissionRateField"] = "commission-rate-field"
        if any(w in crit for w in ("new", "initiat", "creat")):
            sel["newBtn"] = f"new-{module_slug}-btn"
        if any(w in crit for w in ("draft", "save")):
            sel["draftSavedIndicator"] = "draft-saved-indicator"
    return sel


def derive_e2e_assertions(block, scenario, selectors, module_slug):
    """Derive Playwright assertions from scenario expect text."""
    assertions = []
    crit_lower  = block["criterion"].lower()
    scen_name   = scenario["name"].lower()
    expect_text = scenario["expect"].lower()
    is_failure  = any(w in scen_name for w in ("fail", "error", "invalid", "reject", "missing", "empty", "unavail", "past"))
    is_success  = any(w in scen_name for w in ("happy", "success", "valid", "pass", "accept"))

    # Navigate to module
    assertions.append(f"await page.goto(`${{BASE_URL}}/{module_slug}/new`)")

    if any(w in crit_lower for w in ("initiat", "creat new", "new contract", "new button")):
        assertions += [
            f"await page.goto(`${{BASE_URL}}/{module_slug}`)",
            f"await expect(page.locator(SEL.newBtn)).toBeVisible()",
            f"await page.click(SEL.newBtn)",
            f"await expect(page).toHaveURL(/{module_slug}\\/new/)",
        ]

    elif any(w in crit_lower for w in ("past", "future", "date")):
        if is_failure:
            assertions += [
                "const yesterday = new Date()",
                "yesterday.setDate(yesterday.getDate() - 1)",
                "const pastDate = yesterday.toISOString().split('T')[0]",
                "await page.fill(SEL.startDateInput, pastDate)",
                "await page.click(SEL.continueBtn)",
                "await expect(page.locator(SEL.startDateError)).toBeVisible()",
                "await expect(page.locator(SEL.startDateError)).toContainText('today or in the future')",
                "await expect(page.locator(SEL.startDateInput)).toHaveValue(pastDate)",
            ]
        else:
            assertions += [
                "const today = new Date().toISOString().split('T')[0]",
                "await page.fill(SEL.startDateInput, today)",
                "await page.click(SEL.continueBtn)",
                "await expect(page.locator(SEL.startDateError)).not.toBeVisible()",
            ]

    elif any(w in crit_lower for w in ("required", "all three", "simultaneously")):
        assertions += [
            "await page.click(SEL.continueBtn)",
            "await expect(page.locator(SEL.startDateError)).toBeVisible()",
            "await expect(page.locator(SEL.accountManagerError)).toBeVisible()",
            "await expect(page).toHaveURL(/\\/new/)",
        ]

    elif any(w in crit_lower for w in ("exchange", "rate", "loading")):
        if "unavail" in crit_lower or "error" in scen_name:
            assertions += [
                "await page.route('**/api/forex/rate**', route => route.abort('failed'))",
                f"await page.goto(`${{BASE_URL}}/{module_slug}/new?step=2`)",
                "await expect(page.locator(SEL.exchangeRateError)).toBeVisible({ timeout: 8000 })",
                "await expect(page.locator(SEL.exchangeRateRetry)).toBeVisible()",
            ]
        elif "loading" in scen_name:
            assertions += [
                "await page.route('**/api/forex/rate**', async route => {",
                "  await new Promise(r => setTimeout(r, 1500))",
                "  await route.fulfill({ status: 200, contentType: 'application/json',",
                "    body: JSON.stringify({ rate: 1.0823 }) })",
                "})",
                f"await page.goto(`${{BASE_URL}}/{module_slug}/new?step=2`)",
                "await expect(page.locator(SEL.exchangeRateSpinner)).toBeVisible()",
                "await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible({ timeout: 5000 })",
            ]
        else:
            assertions += [
                "await page.route('**/api/forex/rate**', route => route.fulfill({",
                "  status: 200, contentType: 'application/json',",
                "  body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })",
                "}))",
                f"await page.goto(`${{BASE_URL}}/{module_slug}/new?step=2`)",
                "await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()",
                "await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')",
            ]

    elif any(w in crit_lower for w in ("referral", "5", "maximum")):
        if is_failure:
            assertions += [
                "for (let i = 0; i < 5; i++) {",
                "  await page.click(SEL.addReferralBtn)",
                "  await page.selectOption(SEL.referralTypeSelect, 'external')",
                "  await page.fill(SEL.externalNameInput, `Referral ${i}`)",
                "  await page.click(SEL.saveReferralBtn)",
                "}",
                "await expect(page.locator(SEL.addReferralBtn)).toBeDisabled()",
            ]
        else:
            assertions += [
                "await page.click(SEL.addReferralBtn)",
                "await page.selectOption(SEL.referralTypeSelect, 'external')",
                "await page.fill(SEL.externalNameInput, 'Test Referral')",
                "await page.click(SEL.saveReferralBtn)",
                "await expect(page.locator(SEL.referralListItem)).toHaveCount(1)",
            ]

    elif any(w in crit_lower for w in ("employee", "external", "type")):
        if "employee" in scen_name:
            assertions += [
                "await page.click(SEL.addReferralBtn)",
                "await page.selectOption(SEL.referralTypeSelect, 'employee')",
                "await expect(page.locator(SEL.employeeSelect)).toBeVisible()",
                "await expect(page.locator(SEL.externalNameInput)).not.toBeVisible()",
            ]
        else:
            assertions += [
                "await page.click(SEL.addReferralBtn)",
                "await page.selectOption(SEL.referralTypeSelect, 'external')",
                "await expect(page.locator(SEL.externalNameInput)).toBeVisible()",
                "await expect(page.locator(SEL.employeeSelect)).not.toBeVisible()",
            ]

    elif any(w in crit_lower for w in ("draft", "save as draft")):
        assertions += [
            "await page.click(SEL.saveAsDraftBtn)",
            "await expect(page.locator(SEL.startDateError)).not.toBeVisible()",
            "await expect(page.locator(SEL.draftSavedIndicator)).toBeVisible()",
        ]

    elif any(w in crit_lower for w in ("commission", "role", "visible", "restrict")):
        if any(w in scen_name for w in ("account manager", "finance", "authorized")):
            assertions += [
                "// Authorized role — field must be visible",
                "await expect(page.locator(SEL.commissionRateField)).toBeVisible()",
            ]
        else:
            assertions += [
                "await loginAs(page, 'restricted_user')",
                f"await page.goto(`${{BASE_URL}}/{module_slug}/test-record`)",
                "// Must not exist in DOM — not just hidden",
                "const count = await page.locator(SEL.commissionRateField).count()",
                "expect(count).toBe(0)",
            ]

    else:
        assertions += [
            f"// TODO: implement E2E steps for: {block['criterion'][:80]}",
            "// await expect(page.locator(SEL.???)).toBeVisible()",
        ]

    return assertions


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate Vitest + Playwright test shells")
    parser.add_argument("project_slug", help="Project slug (subfolder of workspace/)")
    parser.add_argument("module_slug",  nargs="?", default=None,
                        help="Module slug (from 01-module-[slug].md). Omit to use first found.")
    args = parser.parse_args()

    workspace_dir = Path("workspace") / args.project_slug
    export_dir    = workspace_dir / "exports"

    if not workspace_dir.exists():
        print(f"\n❌  Project not found: {workspace_dir}")
        sys.exit(1)

    # Resolve module slug
    if args.module_slug:
        module_slug = args.module_slug
        spec_path   = workspace_dir / "04-behavioral-test-specs.md"
        module_path = workspace_dir / f"01-module-{module_slug}.md"
    else:
        # Use first module found
        candidates = sorted(workspace_dir.glob("01-module-*.md"))
        if not candidates:
            print(f"\n❌  No module files found in {workspace_dir}")
            sys.exit(1)
        module_path = candidates[0]
        module_slug = module_path.stem.replace("01-module-", "")
        spec_path   = workspace_dir / "04-behavioral-test-specs.md"

    # Try behavioral spec first, fall back to acceptance criteria
    spec_text = read_file(spec_path)
    if not spec_text:
        ac_path   = workspace_dir / "03-acceptance-criteria.md"
        spec_text = read_file(ac_path)
        if spec_text:
            print(f"  ⚠   No behavioral test specs found — using acceptance criteria as fallback")
            print(f"      Run the agent's 'generate behavioral test specs' step for richer output\n")

    if not spec_text:
        print(f"\n❌  No test specifications found.")
        print(f"    Run the discovery agent to generate 04-behavioral-test-specs.md first.")
        sys.exit(1)

    dd_text = read_file(workspace_dir / "02-data-dictionary.md")

    module_title = module_slug.replace("-", " ").replace("_", " ").title()
    m = re.search(r"#\s+Module Definition Card\s*[—–-]\s*(.+)", read_file(module_path))
    if m:
        module_title = m.group(1).strip()

    export_dir.mkdir(exist_ok=True)

    print(f"\n🧪  Generating test shells for: {args.project_slug} / {module_slug}\n")

    # Parse specs
    blocks = parse_behavioral_specs(spec_text)
    if not blocks:
        print("  ⚠   Could not parse behavioral spec blocks — check file format")
        sys.exit(1)

    unit_count = sum(1 for b in blocks if "unit" in b.get("layer_raw", b["layer"]) or "integration" in b.get("layer_raw", b["layer"]))
    e2e_count  = sum(1 for b in blocks if "e2e" in b.get("layer_raw", b["layer"]))

    # Generate unit tests
    if unit_count > 0:
        unit_code = generate_unit_tests(blocks, module_slug, module_title, dd_text)
        unit_path = export_dir / f"{module_slug}.service.test.ts"
        unit_path.write_text(unit_code, encoding="utf-8")
        print(f"  ✅  {module_slug}.service.test.ts  →  {unit_path}")

    # Generate E2E tests
    if e2e_count > 0:
        e2e_code = generate_e2e_tests(blocks, module_slug, module_title, dd_text)
        if e2e_code:
            e2e_path = export_dir / f"{module_slug}.spec.ts"
            e2e_path.write_text(e2e_code, encoding="utf-8")
            print(f"  ✅  {module_slug}.spec.ts   →  {e2e_path}")

    print(f"\n  📋  AC blocks parsed:   {len(blocks)}")
    print(f"  🔬  Unit/integration:   {unit_count}")
    print(f"  🌐  E2E:                {e2e_count}")
    print(f"\n  Add these files to your repo.")
    print(f"  Run with Vitest: npx vitest run exports/{module_slug}.service.test.ts")
    print(f"  Run with Playwright: npx playwright test exports/{module_slug}.spec.ts\n")


if __name__ == "__main__":
    main()
