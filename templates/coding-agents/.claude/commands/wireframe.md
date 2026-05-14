---
description: Produce a UI specification for a module. Reads a wireframe PDF (analysis mode) or generates a prototype from SPEC.md and existing project screens (generation mode). Run before /plan-sprint when a module lacks a ui-spec.md.
---

# /wireframe [module-slug]

Invokes the wireframe agent to produce `docs/wireframes/[module-slug]-ui-spec.md`.

## Usage

```
/wireframe contracts
/wireframe customers
/wireframe referrals
```

The agent auto-detects which mode to run:
- **Analysis mode**: a PDF exists at `docs/wireframes/[module-slug]-*.pdf`
- **Generation mode**: no PDF found — prototype is generated from SPEC.md

## When to run this

**Before `/plan-sprint`** when a module doesn't yet have a `ui-spec.md`. The orchestrator checks for this file during sprint planning and uses it to map screens to stories. If it's missing, the orchestrator will prompt you to run `/wireframe` before proceeding.

**Before implementation begins** for any story that has UI work. The code agent reads the UI Specification section in the issue body, which the orchestrator extracted from the ui-spec.md.

**For prototypes and pitches** — before a full discovery pass is complete. Provide a rough brief and the agent generates a prototype for client review.

## What it produces

One file: `docs/wireframes/[module-slug]-ui-spec.md`

This file contains:
- A screen inventory (every screen in the module)
- Per-screen detail (layout, components, fields, states, permissions, accessibility)
- A story-to-screen mapping table (left blank for the orchestrator to fill)
- Design system notes

## What it does NOT do

- Modify SPEC.md
- Write implementation code (.ts, .tsx, migrations)
- Push to remote (developer reviews and pushes)
- Feed back to Figma or Miro — the ui-spec.md is the terminal design artifact

## After completion

1. Review the committed `docs/wireframes/[module-slug]-ui-spec.md`
2. `git push`
3. Run `/plan-sprint` — the orchestrator will read the spec when planning stories for this module

## Related commands

- `/plan-sprint` — reads the ui-spec.md to map screens to stories
- `/schema [module] US-XXX` — uses the issue body's UI Specification section
- `/code [module] US-XXX` — builds components matching the UI spec
