# Architecture Canon
*The single source of truth for how we build software.*

This repository is the canonical reference for everyone — developers, BAs, and AI agents — who builds, maintains, or evolves software in our consultancy. It contains the architectural law (the canon), the templates that bootstrap new projects, the discovery agents that capture client requirements, and the tools that turn specifications into code.

---

## What lives here

```
architecture-canon/
├── canon/                      ← The architectural law. Read this first.
│   ├── quick-reference.md      ← Two-page summary. Start here every day.
│   ├── section-00-overview.md  ← How the layers fit together
│   ├── section-01-philosophy.md
│   ├── ... (sections 02-11)
│   └── guidelines/
│       ├── rbac.md             ← Permission system implementation
│       └── caller-context.md   ← Agent authorization pattern
│
├── templates/                  ← What you copy when starting something new
│   ├── starter/                ← New project template (Next.js + canon-compliant)
│   │   ├── STARTER-PLAN.md     ← Full file manifest for bootstrapping a project
│   │   └── scaffold-module.ts  ← CLI for adding modules to a running project
│   ├── discovery-agent-codex/  ← Codex deployment of the discovery agent
│   └── discovery-agent-cc/     ← Claude Code deployment (used for coding agents)
│
├── examples/                   ← Reference outputs from real workflows
│   └── contract-manager/       ← Complete worked example of a discovery → spec flow
│
├── tools/                      ← Scripts that operate across all projects
│   └── sync-canon.sh           ← Pulls the canon into a project's docs/architecture/
│
├── OPEN-ISSUES.md              ← Visible debt — gaps and deferred decisions
└── CHANGELOG.md                ← What changed in the canon, when, and why
```

---

## Who uses this and how

### For developers

The canon is the law. Read `canon/quick-reference.md` on day one. Keep it open. The deeper sections in `canon/section-XX-*.md` are for when you need to understand a specific layer or pattern in depth.

When you start a new project, you do not start from a blank Next.js install. You bootstrap from `templates/starter/` and the canon comes with it — synced into your project's `docs/architecture/` folder. See **Bootstrapping a new project** below.

When you add a feature to an existing project, you run `npm run scaffold:module <name>` and the scaffolder generates a canon-compliant module skeleton.

### For BAs and consultants running discovery

The discovery agent in `templates/discovery-agent-codex/` is what you deploy to run a discovery session with a client. It walks through the right checklist (greenfield / internal-ops / customer-facing), produces a module card, builds a data dictionary, derives acceptance criteria, and generates the test shells that feed the coding pipeline.

You don't need to read the canon to run discovery. The discovery agent has been built to capture exactly what the canon needs — but expresses it in client-friendly language.

### For AI agents

The canon defines the invariants every agent must respect — module structure, the `CallerContext` pattern, the four required org isolation tests, the schema-first ordering. Every agent in the system is given the relevant section as context before it generates code or makes architectural decisions.

The discovery agent already lives in `templates/discovery-agent-codex/`. The coding agents (Schema & Contracts, Implementation, Integration, etc.) will be added to `templates/discovery-agent-cc/` as they are built.

---

## Bootstrapping a new project

```bash
# 1. Clone the starter template into a new project
git clone https://github.com/your-org/architecture-canon.git
cp -r architecture-canon/templates/starter/ ../my-new-project/
cd ../my-new-project/

# 2. Sync the canon into the project's docs folder
bash ../architecture-canon/tools/sync-canon.sh

# 3. Follow the bootstrap commands in templates/starter/STARTER-PLAN.md
#    (npx create-next-app, install deps, copy custom files, etc.)
```

After step 2, `my-new-project/docs/architecture/` contains a read-only copy of the canon. Developers and AI agents working in the project read from this local copy. Updates to the canon are pulled in by re-running the sync script.

---

## Bootstrapping a discovery agent

The discovery agent runs as a separate workspace, typically in OpenAI Codex (for token economics — see *Why two deployment formats* below).

```bash
# 1. Copy the codex discovery agent into a new working directory
cp -r architecture-canon/templates/discovery-agent-codex/ ~/discovery-projects/client-name/

# 2. Set up the agent in Codex
# 3. Begin discovery — the agent reads its own AGENTS.md and prompts/discovery-system-prompt.md
```

The agent produces a `workspace/<project-slug>/` folder containing the discovery artifacts. When discovery is complete, those artifacts feed the coding pipeline (Phase 1+ of the integrated workflow — see `canon/section-12-integrated-workflow.md` once it's added).

---

## Why two deployment formats

| Variant | Runtime | Used for |
|---|---|---|
| `discovery-agent-codex/` | OpenAI Codex | Discovery sessions — Codex tokens are cheaper for the long conversational discovery flow |
| `discovery-agent-cc/` | Claude Code | The coding agents (Schema & Contracts, Implementation, etc.) — Claude is preferred for code generation quality |

The two formats share most files (`reference/`, `prompts/`, `scripts/`). They differ only in the entry-point file (`AGENTS.md` for Codex, `CLAUDE.md` for Claude Code) and platform-specific commands.

---

## How the canon evolves

Changes to the canon are deliberate and versioned.

1. A change is proposed (a new pattern, a fix, a clarification)
2. The change is written into the relevant section
3. An entry is added to `CHANGELOG.md` with the date, section, and rationale
4. Projects pull in the change by re-running `tools/sync-canon.sh`

Active issues and deferred decisions live in `OPEN-ISSUES.md`. This is the visible backlog — gaps we know about but have not yet addressed.

---

## Reading order

| You are... | Start with |
|---|---|
| A new developer on day one | `canon/quick-reference.md` |
| A BA preparing for discovery | `templates/discovery-agent-codex/README.md` |
| A senior reviewing the architecture | `canon/section-00-overview.md` then `canon/section-01-philosophy.md` |
| A tech lead resolving a design question | The relevant `canon/section-XX-*.md` |
| An AI agent receiving a task | The section relevant to the task — passed as context, not read by the agent itself |

---

## Status

- ✅ Canon v2 (Sections 0–11, plus guidelines) — current
- ✅ Discovery pipeline (codex + cc variants) — current
- ✅ Project starter template — current
- ✅ Module scaffold script — current
- 🚧 Section 12 — Integrated Workflow — in progress
- 🚧 Coding agent roster (Schema & Contracts, Implementation, etc.) — designed, not yet built
- 🗓️ Brownfield workflow + agent — backlog (post-greenfield validation)
- 🗓️ PHP-stack legacy projects integration — backlog (separate workstream)

See `CHANGELOG.md` for details.

---

## License & contribution

This is internal tooling. The canon is the team's collective design decision. Changes to the canon must be discussed and approved — not unilateral. Open an issue or PR with a clear rationale before changing patterns.
