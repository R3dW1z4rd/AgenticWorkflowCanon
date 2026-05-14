#!/usr/bin/env python3
"""
generate_artifacts.py
---------------------
Reads the markdown workspace files for a project and generates:
  - module-workbook.xlsx  (Data Dictionary + Acceptance Criteria, fully formatted)
  - module-definition-card.docx  (for each 01-module-*.md found)

Usage:
    python scripts/generate_artifacts.py <project-slug>

Example:
    python scripts/generate_artifacts.py client-portal

Output files are written to:
    workspace/<project-slug>/exports/
"""

import sys
import os
import re
import glob
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
def check_deps():
    missing = []
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")
    try:
        import docx
    except ImportError:
        missing.append("python-docx")
    if missing:
        print(f"\n❌  Missing dependencies: {', '.join(missing)}")
        print(f"    Run: pip install {' '.join(missing)}")
        sys.exit(1)

check_deps()

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
import docx
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── Colors ────────────────────────────────────────────────────────────────────
BRAND_BLUE   = "1F4E79"
MID_BLUE     = "2E75B6"
LIGHT_BLUE   = "D6E4F0"
LIGHTEST_BLUE= "EBF3FB"
DARK_GREY    = "404040"
MID_GREY     = "737373"
LIGHT_GREY   = "F2F2F2"
WHITE        = "FFFFFF"
YELLOW_FLAG  = "FFF2CC"

TYPE_COLORS = {
    "enum":      "FFF2CC",
    "reference": "E2EFDA",
    "json":      "EDEDED",
}
SOURCE_COLORS = {
    "system_generated": "F2F2F2",
    "integration":      "FFF2CC",
    "derived":          "E2EFDA",
}
PRIORITY_COLORS = {"Must": "FCE4D6", "Should": "FFF2CC", "Could": "E2EFDA"}
STATUS_COLORS   = {
    "Draft":    "F2F2F2", "Reviewed": "D6E4F0",
    "Approved": "E2EFDA", "In Dev":   "FFF2CC", "Done": "C6EFCE",
}


# ── Style helpers ─────────────────────────────────────────────────────────────
def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def fnt(bold=False, size=10, color="000000", italic=False, name="Arial"):
    return Font(name=name, bold=bold, size=size, color=color, italic=italic)

def align(h="left", wrap=True):
    return Alignment(horizontal=h, vertical="center", wrap_text=wrap)

def thin():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

def med_border():
    s = Side(style="medium", color=MID_BLUE)
    return Border(left=s, right=s, top=s, bottom=s)

def hdr(cell, text, center=True):
    cell.value = text
    cell.font  = fnt(bold=True, size=10, color=WHITE)
    cell.fill  = fill(MID_BLUE)
    cell.alignment = align("center" if center else "left")
    cell.border = med_border()

def hint(cell, text):
    cell.value = text
    cell.font  = fnt(size=9, color=MID_GREY, italic=True)
    cell.fill  = fill(LIGHTEST_BLUE)
    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    cell.border = thin()

def data(cell, text="", bg=WHITE, bold=False, center=False, mono=False):
    cell.value = text
    cell.font  = Font(name="Courier New" if mono else "Arial",
                      size=9 if mono else 10, bold=bold, color=DARK_GREY)
    cell.fill  = fill(bg)
    cell.alignment = align("center" if center else "left")
    cell.border = thin()


# ── Markdown parser ───────────────────────────────────────────────────────────
def parse_md_table(text):
    """Extract rows from a markdown table, skipping header and separator lines."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line.replace(" ", "")):
            continue                           # separator row
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows[1:] if rows else []            # skip header row

def read_file(path):
    if not Path(path).exists():
        return ""
    return Path(path).read_text(encoding="utf-8")

def safe(lst, idx, default=""):
    try:
        v = lst[idx].strip()
        return v if v not in ("-", "—", "") else default
    except IndexError:
        return default


# ══════════════════════════════════════════════════════════════════════════════
# XLSX GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def build_workbook(project_slug, workspace_dir, export_dir):
    wb = Workbook()

    dd_path = workspace_dir / "02-data-dictionary.md"
    ac_path = workspace_dir / "03-acceptance-criteria.md"

    dd_text = read_file(dd_path)
    ac_text = read_file(ac_path)

    # ── Sheet 1: Data Dictionary ──────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "📋 Data Dictionary"

    # Title
    ws1.merge_cells("A1:N1")
    c = ws1["A1"]
    c.value = "DATA DICTIONARY"
    c.font  = Font(name="Arial", bold=True, size=16, color=WHITE)
    c.fill  = fill(BRAND_BLUE)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[1].height = 36

    # Meta row
    meta = [("Module:", project_slug.replace("-", " ").title()),
            ("System:", ""),
            ("Version:", "v1.0 — Draft"),
            ("Last Updated:", "")]
    for col, (lbl, val) in enumerate(meta, 1):
        cl = ws1.cell(row=2, column=col*2-1, value=lbl)
        cv = ws1.cell(row=2, column=col*2,   value=val)
        cl.font = fnt(bold=True, size=10, color=BRAND_BLUE); cl.fill = fill(LIGHT_BLUE)
        cv.font = fnt(size=10, color=DARK_GREY);             cv.fill = fill(LIGHTEST_BLUE)
        for c2 in (cl, cv):
            c2.alignment = align(); c2.border = thin()
    ws1.row_dimensions[2].height = 22
    ws1.row_dimensions[3].height = 8

    # Column headers
    DD_COLS = [
        ("Entity",                16),
        ("field_name\n(snake_case)", 20),
        ("fieldName\n(camelCase)",   20),
        ("Display Label",         22),
        ("Type",                  13),
        ("Required",              11),
        ("Validation Rules",      28),
        ("Default",               16),
        ("Source",                16),
        ("Integration /\nModule Ref", 22),
        ("Enum Values",           22),
        ("Used In\n(Screens)",    22),
        ("PII?",                  10),
        ("Notes",                 28),
    ]
    DD_HINTS = [
        "Object name\ne.g. contract",
        "DB/class name\nsnake_case",
        "JS/API name\ncamelCase",
        "UI label shown to user",
        "string·integer·decimal\nboolean·date·datetime\nenum·reference·file·json",
        "Yes / No / Conditional",
        "e.g. Must not be past\nMax 255 chars",
        "e.g. null · Today · false",
        "user_input\nsystem_generated\nintegration · derived",
        "API name & refresh rate\nor source module.field",
        "For enum fields:\nlist all allowed values",
        "Which screens use this\ne.g. Create · Detail",
        "Yes / No",
        "Business rules, notes,\ncross-module deps",
    ]

    ws1.row_dimensions[4].height = 44
    ws1.row_dimensions[5].height = 52
    for i, ((col_name, col_w), hint_txt) in enumerate(zip(DD_COLS, DD_HINTS), 1):
        hdr(ws1.cell(row=4, column=i), col_name)
        hint(ws1.cell(row=5, column=i), hint_txt)
        ws1.column_dimensions[get_column_letter(i)].width = col_w

    # Data rows from markdown
    dd_rows = parse_md_table(dd_text)
    for r_idx, row in enumerate(dd_rows, 6):
        ws1.row_dimensions[r_idx].height = 28
        bg = WHITE if r_idx % 2 == 0 else LIGHTEST_BLUE

        entity      = safe(row, 0)
        field_snake = safe(row, 1)
        field_camel = safe(row, 2)
        display     = safe(row, 3)
        dtype       = safe(row, 4)
        required    = safe(row, 5)
        validation  = safe(row, 6)
        default     = safe(row, 7)
        source      = safe(row, 8)
        ref         = safe(row, 9)
        enum_vals   = safe(row, 10)
        screens     = safe(row, 11)
        pii         = safe(row, 12)
        notes       = safe(row, 13)

        # Entity (A)
        c = ws1.cell(row=r_idx, column=1, value=entity)
        c.font = fnt(bold=True, size=10, color=BRAND_BLUE)
        c.fill = fill(LIGHT_BLUE); c.alignment = align(); c.border = thin()

        # snake_case (B)
        c = ws1.cell(row=r_idx, column=2, value=field_snake)
        c.font = Font(name="Courier New", size=9, color="333333")
        c.fill = fill(LIGHT_GREY); c.alignment = align(); c.border = thin()

        # camelCase (C)
        c = ws1.cell(row=r_idx, column=3, value=field_camel)
        c.font = Font(name="Courier New", size=9, color="333333")
        c.fill = fill(LIGHT_GREY); c.alignment = align(); c.border = thin()

        # Display label (D)
        data(ws1.cell(row=r_idx, column=4), display, bg)

        # Type (E)
        c = ws1.cell(row=r_idx, column=5, value=dtype)
        c.font = fnt(bold=True, size=9, color=DARK_GREY)
        c.fill = fill(TYPE_COLORS.get(dtype, WHITE))
        c.alignment = align("center"); c.border = thin()

        # Required (F)
        req_bg = "E2EFDA" if required == "Yes" else ("FFF2CC" if required == "Conditional" else LIGHT_GREY)
        c = ws1.cell(row=r_idx, column=6, value=required)
        c.font = fnt(bold=True, size=9); c.fill = fill(req_bg)
        c.alignment = align("center"); c.border = thin()

        # Validation, Default (G, H)
        data(ws1.cell(row=r_idx, column=7), validation, bg)
        data(ws1.cell(row=r_idx, column=8), default, bg)

        # Source (I)
        c = ws1.cell(row=r_idx, column=9, value=source)
        c.font = fnt(bold=True, size=9)
        c.fill = fill(SOURCE_COLORS.get(source, WHITE))
        c.alignment = align("center"); c.border = thin()

        # Ref, Enum, Screens (J, K, L)
        data(ws1.cell(row=r_idx, column=10), ref, bg)
        data(ws1.cell(row=r_idx, column=11), enum_vals, bg)
        data(ws1.cell(row=r_idx, column=12), screens, bg)

        # PII (M)
        c = ws1.cell(row=r_idx, column=13, value=pii)
        c.font = fnt(bold=True, size=9, color="C00000" if pii == "Yes" else DARK_GREY)
        c.fill = fill("FCE4D6" if pii == "Yes" else bg)
        c.alignment = align("center"); c.border = thin()

        # Notes (N)
        data(ws1.cell(row=r_idx, column=14), notes, bg)

    # Data validations
    for dv_range, formula in [
        ("E6:E500", '"string,integer,decimal,boolean,date,datetime,enum,reference,file,json"'),
        ("F6:F500", '"Yes,No,Conditional"'),
        ("I6:I500", '"user_input,system_generated,integration,derived"'),
        ("M6:M500", '"Yes,No"'),
    ]:
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        ws1.add_data_validation(dv)
        dv.sqref = dv_range

    ws1.freeze_panes = "A6"

    # ── Sheet 2: Acceptance Criteria ──────────────────────────────────────────
    ws2 = wb.create_sheet("✅ Acceptance Criteria")

    # Title
    ws2.merge_cells("A1:L1")
    c = ws2["A1"]
    c.value = "ACCEPTANCE CRITERIA LOG"
    c.font  = Font(name="Arial", bold=True, size=16, color=WHITE)
    c.fill  = fill(BRAND_BLUE)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[1].height = 36

    # Meta
    for col, (lbl, val) in enumerate([("Module:", project_slug.replace("-", " ").title()),
                                       ("System:", ""), ("Version:", "v1.0"), ("Last Updated:", "")], 1):
        cl = ws2.cell(row=2, column=col*2-1, value=lbl)
        cv = ws2.cell(row=2, column=col*2,   value=val)
        cl.font = fnt(bold=True, size=10, color=BRAND_BLUE); cl.fill = fill(LIGHT_BLUE)
        cv.font = fnt(size=10, color=DARK_GREY);             cv.fill = fill(LIGHTEST_BLUE)
        for c2 in (cl, cv): c2.alignment = align(); c2.border = thin()
    ws2.row_dimensions[2].height = 22
    ws2.row_dimensions[3].height = 8

    # Guidance
    ws2.merge_cells("A4:L4")
    gc = ws2["A4"]
    gc.value = ('Format: "The system must…"  |  Priority: Must = required for launch · Should = important · Could = nice to have  |  '
                'Status: Draft → Reviewed → Approved → In Dev → Done  |  Link each criterion to a Gitea issue once ticketed')
    gc.font = fnt(size=9, color=DARK_GREY, italic=True)
    gc.fill = fill(YELLOW_FLAG)
    gc.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    gc.border = thin()
    ws2.row_dimensions[4].height = 36

    # Headers
    AC_COLS = [
        ("ID",                  7),
        ("Module",              18),
        ("Flow Step",           10),
        ("Actor",               16),
        ("The system must…",    55),
        ("Priority",            12),
        ("Status",              14),
        ("Gitea Issue #",       14),
        ("Linked Fields",       22),
        ("Test Notes",          30),
        ("Designer Sign-off",   16),
        ("Dev Sign-off",        14),
    ]
    AC_HINTS = [
        "AC-001",
        "Module name",
        "Step # from Core Flow",
        "Who triggers this",
        "Observable outcome — what the system does, not how",
        "Must / Should / Could",
        "Draft / Reviewed /\nApproved / In Dev / Done",
        "e.g. #142",
        "field_name(s) from\nData Dictionary",
        "Specific scenario or\ndata setup needed",
        "Name + date",
        "Name + date",
    ]

    ws2.row_dimensions[5].height = 40
    ws2.row_dimensions[6].height = 46
    for i, ((col_name, col_w), hint_txt) in enumerate(zip(AC_COLS, AC_HINTS), 1):
        hdr(ws2.cell(row=5, column=i), col_name)
        hint(ws2.cell(row=6, column=i), hint_txt)
        ws2.column_dimensions[get_column_letter(i)].width = col_w

    # Data rows
    ac_rows = parse_md_table(ac_text)
    for r_idx, row in enumerate(ac_rows, 7):
        ws2.row_dimensions[r_idx].height = 40
        bg = WHITE if r_idx % 2 == 0 else LIGHTEST_BLUE

        ac_id    = safe(row, 0)
        module   = safe(row, 1)
        step     = safe(row, 2)
        actor    = safe(row, 3)
        crit     = safe(row, 4)
        priority = safe(row, 5)
        status   = safe(row, 6)
        gitea    = safe(row, 7)
        fields   = safe(row, 8)
        notes    = safe(row, 9)
        dso      = safe(row, 10)
        devso    = safe(row, 11)

        # ID
        c = ws2.cell(row=r_idx, column=1, value=ac_id)
        c.font = fnt(bold=True, size=9, color=BRAND_BLUE)
        c.fill = fill(LIGHT_BLUE); c.alignment = align("center"); c.border = thin()

        data(ws2.cell(row=r_idx, column=2), module, bg)

        c = ws2.cell(row=r_idx, column=3, value=step)
        c.font = fnt(bold=True, size=10); c.fill = fill(bg)
        c.alignment = align("center"); c.border = thin()

        data(ws2.cell(row=r_idx, column=4), actor, bg)

        c = ws2.cell(row=r_idx, column=5)
        # Normalise criterion text
        if crit and not crit.lower().startswith("the system must"):
            c.value = "The system must " + crit
        else:
            c.value = crit
        c.font = Font(name="Arial", size=10, color="000000")
        c.fill = fill(bg)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border = thin()

        # Priority
        c = ws2.cell(row=r_idx, column=6, value=priority)
        c.font = fnt(bold=True, size=9); c.fill = fill(PRIORITY_COLORS.get(priority, WHITE))
        c.alignment = align("center"); c.border = thin()

        # Status
        c = ws2.cell(row=r_idx, column=7, value=status or "Draft")
        c.font = fnt(bold=True, size=9); c.fill = fill(STATUS_COLORS.get(status, LIGHT_GREY))
        c.alignment = align("center"); c.border = thin()

        # Gitea
        c = ws2.cell(row=r_idx, column=8, value=gitea)
        c.font = fnt(bold=True, size=9); c.fill = fill(LIGHT_BLUE if gitea else LIGHT_GREY)
        c.alignment = align("center"); c.border = thin()

        # Fields (monospace)
        c = ws2.cell(row=r_idx, column=9, value=fields)
        c.font = Font(name="Courier New", size=8, color="555555")
        c.fill = fill(bg); c.alignment = align(); c.border = thin()

        data(ws2.cell(row=r_idx, column=10), notes, bg)

        # Sign-offs
        for col_n, val in [(11, dso), (12, devso)]:
            c = ws2.cell(row=r_idx, column=col_n, value=val or "pending")
            c.font = fnt(size=9, color="006100" if val else MID_GREY, italic=not val)
            c.fill = fill("C6EFCE" if val else bg)
            c.alignment = align("center"); c.border = thin()

    # Validations
    for dv_range, formula in [
        ("F7:F500", '"Must,Should,Could"'),
        ("G7:G500", '"Draft,Reviewed,Approved,In Dev,Done"'),
    ]:
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        ws2.add_data_validation(dv)
        dv.sqref = dv_range

    ws2.freeze_panes = "A7"

    # ── Sheet 3: How to Use ───────────────────────────────────────────────────
    ws3 = wb.create_sheet("📖 How to Use")
    ws3.column_dimensions["A"].width = 26
    ws3.column_dimensions["B"].width = 68

    ws3.merge_cells("A1:B1")
    c = ws3["A1"]
    c.value = "HOW TO USE THIS WORKBOOK"
    c.font  = Font(name="Arial", bold=True, size=14, color=WHITE)
    c.fill  = fill(BRAND_BLUE)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws3.row_dimensions[1].height = 30

    how_to = [
        ("WORKFLOW", ""),
        ("Step 1", "Complete the discovery and module definition first (discovery agent)."),
        ("Step 2", "In the Data Dictionary tab: start from front-end fields (what does the user fill in?), then expand to backend entities."),
        ("Step 3", "Both field_name (snake_case) and fieldName (camelCase) are required for every field — no exceptions."),
        ("Step 4", "In Acceptance Criteria: transfer every 'The system must…' from the module card. One row per criterion."),
        ("Step 5", "Once Approved, create a Gitea issue and log the number in column H."),
        ("", ""),
        ("NAMING RULES", ""),
        ("snake_case", "DB columns and internal class properties: contract_start_date, account_manager_id"),
        ("camelCase", "JavaScript and API fields: contractStartDate, accountManagerId"),
        ("Foreign keys", "Always end in _id: user_id, referral_id, account_manager_id"),
        ("Booleans", "Prefix with is_ or has_: is_active, has_referral"),
        ("Timestamps", "Suffix with _at: created_at, updated_at, approved_at"),
        ("", ""),
        ("COLOR GUIDE — DATA DICTIONARY", ""),
        ("Type: enum (yellow)", "Fixed set of allowed values — list them in Enum Values column"),
        ("Type: reference (green)", "Foreign key — document the source module"),
        ("Source: integration (yellow)", "From external API — document name and refresh behavior"),
        ("Source: derived (green)", "Computed from another field or module"),
        ("PII: Yes (red)", "Personally identifiable — requires access controls"),
        ("Required: Conditional (yellow)", "Required only under specific conditions — document in Validation Rules"),
        ("", ""),
        ("COLOR GUIDE — ACCEPTANCE CRITERIA", ""),
        ("Priority: Must (red-orange)", "Required for launch — feature does not ship without this"),
        ("Priority: Should (yellow)", "Important and expected — a workaround exists"),
        ("Priority: Could (green)", "Nice to have — candidate for a later sprint"),
        ("Status: Done (bright green)", "Implemented and verified"),
    ]

    for i, (section, detail) in enumerate(how_to, 2):
        ws3.row_dimensions[i].height = 20 if detail else 8
        c1 = ws3.cell(row=i, column=1, value=section)
        c2 = ws3.cell(row=i, column=2, value=detail)
        if not detail and section:
            c1.font = fnt(bold=True, size=10, color=WHITE); c1.fill = fill(MID_BLUE)
            c2.fill = fill(MID_BLUE)
        elif section and detail:
            c1.font = fnt(bold=True, size=9, color=BRAND_BLUE); c1.fill = fill(LIGHT_BLUE)
            c2.font = fnt(size=9, color=DARK_GREY);             c2.fill = fill("FAFAFA")
        for cx in (c1, c2):
            cx.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            cx.border = thin()

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = export_dir / "module-workbook.xlsx"
    wb.save(str(out_path))
    print(f"  ✅  module-workbook.xlsx  →  {out_path}")
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# DOCX GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def rgb(hex_str):
    return RGBColor(int(hex_str[0:2],16), int(hex_str[2:4],16), int(hex_str[4:6],16))

def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14 if level == 1 else 11)
    run.font.color.rgb = rgb(BRAND_BLUE if level == 1 else MID_BLUE)
    run.font.name = "Arial"
    return p

def add_field_row(table, label, hint_text):
    row = table.add_row()
    lc  = row.cells[0]
    vc  = row.cells[1]
    set_cell_bg(lc, LIGHT_GREY)
    p = lc.paragraphs[0]
    run = p.add_run(label)
    run.bold = True; run.font.size = Pt(10); run.font.name = "Arial"
    vp = vc.paragraphs[0]
    run2 = vp.add_run(hint_text)
    run2.italic = True; run2.font.size = Pt(9)
    run2.font.color.rgb = rgb(MID_GREY); run2.font.name = "Arial"

def build_module_card_js(module_path, export_dir):
    """Delegate docx generation to generate_module_card.js (uses docx npm package)."""
    import subprocess
    slug     = Path(module_path).stem.replace("01-module-", "")
    out_path = export_dir / f"module-card-{slug}.docx"
    js_script = Path(__file__).parent / "generate_module_card.js"

    result = subprocess.run(
        ["node", str(js_script), str(module_path), str(out_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ❌  Error generating module card: {result.stderr}")
    else:
        if result.stdout:
            print(result.stdout.strip())
    return out_path

def build_module_card(module_path, export_dir):
    text    = read_file(module_path)
    slug    = Path(module_path).stem.replace("01-module-", "")
    title   = slug.replace("-", " ").title()

    # Try to extract sections from the markdown
    def extract_section(md, heading):
        pattern = rf"##\s+\d*\.*\s*{re.escape(heading)}.*?\n(.*?)(?=\n##|\Z)"
        m = re.search(pattern, md, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    purpose   = extract_section(text, "Business Purpose")
    actors    = extract_section(text, "Actors")
    entry_exit= extract_section(text, "Entry")
    core_flow = extract_section(text, "Core Flow")
    states    = extract_section(text, "States")
    outcomes  = extract_section(text, "Desired Outcomes")
    oos       = extract_section(text, "Out of Scope")
    questions = extract_section(text, "Open Questions")

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # Title block
    p = doc.add_paragraph()
    run = p.add_run("MODULE DEFINITION CARD")
    run.bold = True; run.font.size = Pt(22)
    run.font.color.rgb = rgb(BRAND_BLUE); run.font.name = "Arial"

    p2 = doc.add_paragraph()
    run2 = p2.add_run(title)
    run2.font.size = Pt(14); run2.italic = True
    run2.font.color.rgb = rgb(MID_BLUE); run2.font.name = "Arial"
    doc.add_paragraph()

    # Meta table
    meta_tbl = doc.add_table(rows=3, cols=4)
    meta_tbl.style = "Table Grid"
    meta_items = [
        ("Module Name", title),    ("System", ""),
        ("Version",     "v0.1 — Draft"), ("Last Updated", ""),
        ("Author",      ""),       ("Reviewed By", ""),
    ]
    for i, (lbl, val) in enumerate(meta_items):
        row_idx, col_idx = divmod(i, 2)
        lc = meta_tbl.cell(row_idx, col_idx*2)
        vc = meta_tbl.cell(row_idx, col_idx*2+1)
        set_cell_bg(lc, LIGHT_BLUE)
        lc.paragraphs[0].add_run(lbl).bold = True
        lc.paragraphs[0].runs[0].font.name = "Arial"
        lc.paragraphs[0].runs[0].font.size = Pt(10)
        vc.paragraphs[0].add_run(val)
        vc.paragraphs[0].runs[0].font.name = "Arial"
        vc.paragraphs[0].runs[0].font.size = Pt(10)
    doc.add_paragraph()

    # ── Sections ──────────────────────────────────────────────────────────────
    sections_data = [
        ("1  Business Purpose",         purpose   or "[Describe why this module exists — link to a business problem, not a feature]"),
        ("2  Actors & Roles",           actors    or "[List roles: what they do, what they see]"),
        ("3  Entry & Exit Points",      entry_exit or "[Entry point / Pre-conditions / Exit point / Post-conditions]"),
        ("4  Core Flow",                core_flow or "[Numbered steps: Actor → Action → System response]"),
        ("5  States & Edge Cases",      states    or "[Module states + edge case table]"),
        ("6  Desired Outcomes",         outcomes  or "[The system must… statements (4–8)]"),
        ("7  Out of Scope",             oos       or "[What this module explicitly does NOT handle]"),
        ("8  Open Questions & Flags",   questions or "[Unresolved questions with owners and due dates]"),
    ]

    for heading, content in sections_data:
        # Section header with blue background
        p_hdr = doc.add_paragraph()
        p_hdr.paragraph_format.space_before = Pt(10)
        p_hdr.paragraph_format.space_after  = Pt(4)
        run_hdr = p_hdr.add_run(f"  {heading}")
        run_hdr.bold = True; run_hdr.font.size = Pt(11)
        run_hdr.font.color.rgb = rgb(WHITE); run_hdr.font.name = "Arial"
        # Background shading on paragraph
        pPr = p_hdr._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  BRAND_BLUE)
        pPr.append(shd)

        # Content
        p_content = doc.add_paragraph()
        run_c = p_content.add_run(content)
        run_c.font.size = Pt(10); run_c.font.name = "Arial"
        doc.add_paragraph()

    # Footer note
    p_footer = doc.add_paragraph()
    run_f = p_footer.add_run(
        "Data Dictionary and Acceptance Criteria are maintained in the companion module-workbook.xlsx  ·  "
        "This card is the source of truth for scope and flow."
    )
    run_f.italic = True; run_f.font.size = Pt(9)
    run_f.font.color.rgb = rgb(MID_GREY); run_f.font.name = "Arial"
    pPr2 = p_footer._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top  = OxmlElement("w:top")
    top.set(qn("w:val"),   "single")
    top.set(qn("w:sz"),    "4")
    top.set(qn("w:color"), MID_BLUE)
    pBdr.append(top)
    pPr2.append(pBdr)

    out_path = export_dir / f"module-card-{slug}.docx"
    doc.save(str(out_path))
    print(f"  ✅  module-card-{slug}.docx  →  {out_path}")
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project_slug  = sys.argv[1].strip("/").strip()
    workspace_dir = Path("workspace") / project_slug
    export_dir    = workspace_dir / "exports"

    if not workspace_dir.exists():
        print(f"\n❌  Project not found: {workspace_dir}")
        print(f"    Available projects:")
        for p in Path("workspace").iterdir():
            if p.is_dir() and not p.name.startswith("."):
                print(f"      - {p.name}")
        sys.exit(1)

    export_dir.mkdir(exist_ok=True)
    print(f"\n🔨  Generating artifacts for: {project_slug}")
    print(f"    Output: {export_dir}\n")

    # Generate workbook
    if (workspace_dir / "02-data-dictionary.md").exists() or \
       (workspace_dir / "03-acceptance-criteria.md").exists():
        build_workbook(project_slug, workspace_dir, export_dir)
    else:
        print("  ⚠️   No data dictionary or acceptance criteria found — skipping workbook")

    # Generate module card(s) — uses Node.js via generate_module_card.js
    module_files = sorted(glob.glob(str(workspace_dir / "01-module-*.md")))
    if module_files:
        for mf in module_files:
            build_module_card_js(mf, export_dir)
    else:
        print("  ⚠️   No module definition files found — skipping module cards")

    print(f"\n✅  Done. Open the exports/ folder to find your files.\n")

if __name__ == "__main__":
    main()
