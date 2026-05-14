# Discovery & Documentation Agent — Codex Edition
> A project-agnostic Codex agent that guides you through the full discovery and
> documentation pipeline — from first client conversation to development-ready artifacts,
> formatted exports, and Miro prototype prompts.

## Quickstart

```bash
unzip discovery-agent-codex.zip
cd discovery-agent-codex
codex
```

Codex reads `AGENTS.md` automatically. No configuration needed.

## What to say

| You want to… | Say… |
|-------------|------|
| Start a new project | "Start a new project" + paste any existing notes |
| Resume a session | "Resume discovery for [project name]" |
| Define a module | "Let's define the [module name] module" |
| Export formatted files | "Export the formatted files for [project]" |
| Generate a Miro prompt | "Generate the Miro prompt for [module]" |

## Full Pipeline

```
Discovery (guided Q&A)     → 00-discovery-notes.md
Module Definition          → 01-module-[name].md
Data Dictionary            → 02-data-dictionary.md
Acceptance Criteria        → 03-acceptance-criteria.md
Behavioral Test Specs      → 04-behavioral-test-specs.md
Export                     → exports/module-workbook.xlsx
                             exports/module-card-[name].docx
Miro Prompt                → exports/miro-prompt-[module].md
                             ↓ paste into Miro AI → prototype
```

## Exports

### Formatted files
Say: *"Export the formatted files for [project]"*

Produces in `workspace/[project]/exports/`:
- **module-workbook.xlsx** — Data Dictionary (color-coded, dropdowns, snake_case + camelCase) + Acceptance Criteria + How to Use
- **module-card-[name].docx** — Module Definition Card with branded layout and tables

### Miro prompt
Say: *"Generate the Miro prompt for [module]"*

The agent asks device / style / density, then produces `exports/miro-prompt-[module].md`.
Copy the full file contents → paste into **Miro AI → Generate prototype**.

The prompt gives Miro:
- Exact named screen inventory
- Full labelled transition map
- Fields per screen from the Data Dictionary
- Loading/error states for every integration field
- Interaction rules and role-based visibility
- Quality checklist for you to verify the output

## Folder Structure

```
discovery-agent-codex/
├── AGENTS.md                          ← Codex reads this automatically
├── README.md
├── prompts/
│   └── discovery-system-prompt.md
├── reference/
│   ├── checklist-internal-ops.md
│   ├── checklist-customer-facing.md
│   ├── checklist-greenfield.md
│   ├── module-definition-card.md
│   ├── data-dictionary-guide.md
│   ├── acceptance-criteria-guide.md
│   └── behavioral-test-spec-guide.md
├── scripts/
│   ├── generate_artifacts.py          ← xlsx + docx export
│   ├── generate_module_card.js        ← called automatically
│   └── generate_miro_prompt.py        ← Miro AI prompt
└── workspace/
    └── [project-slug]/
        ├── 00-discovery-notes.md
        ├── 01-module-[name].md
        ├── 02-data-dictionary.md
        ├── 03-acceptance-criteria.md
        ├── 04-behavioral-test-specs.md
        └── exports/
```

## Dependencies

Checked and installed automatically on first export:
- `pip install openpyxl python-docx`
- Node.js + `docx` npm package (for .docx generation)

## Connects to

- **Miro AI** — paste the prompt file directly
- **Figma** — module cards describe every screen state
- **Agentic Software Factory** — data dictionary + behavioral specs ground code generation
- **Gitea** — AC IDs become issue numbers
- **Vitest / Playwright** — behavioral specs become test shells

v1.2 — Codex edition
