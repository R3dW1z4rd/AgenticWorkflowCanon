# Worked Example — Contract Manager Sprint 1

*A full end-to-end demonstration of the orchestrator running its first sprint on a new project. Use this to understand what working with the orchestrator looks like in practice — what the developer types, what the agent says back, and what artifacts get produced.*

## What's in this folder

| File | What it shows |
|---|---|
| `SESSION-TRANSCRIPT.md` | The full conversation between developer and orchestrator. Read this first. |
| `sprint-1-summary.md` | Short PM-readable summary the orchestrator commits to `.work/sprint-plans/` |
| `issue-body-US-001.md` | Full Gitea/GitHub issue body for the first story |
| `issue-body-US-002.md` | Full Gitea/GitHub issue body for the second story (depends on US-001) |
| `create-sprint-1-issues.sh` | The shell script the orchestrator generates for the developer to run |
| `project-state-after-planning.md` | The diff the orchestrator applies to `docs/project-state.md` |

## What this example covers

- The orchestrator's session start (preflight + load + opening summary)
- Plan-mode discussion (proposal, refinement, dependency analysis, exclusions)
- The APPROVE PLAN gate
- Artifact generation (state update, issue bodies, script, summary)
- The handoff to the developer (review, push, run script)

## What this example deliberately doesn't cover

- The Phase 5–8 specialist work (still being designed)
- Spec change planning (use `/plan-change`, not `/plan-sprint`)
- Sprint retrospectives (orchestrator is forward-looking)
- Mid-sprint status checks (use `/status` for those)

These will get their own worked examples as the corresponding agents are built.

## Source project

The discovery artifacts that this sprint is being built from live at:

```
examples/contract-manager/
├── 00-discovery-notes.md
├── 01-module-contract-creation.md
├── 02-data-dictionary.md
├── 03-acceptance-criteria.md
└── 04-behavioral-test-specs.md
```

In a real project these would have been consolidated into SPEC.md via `generate_spec.py` and tagged at `spec-v1.0`. Here, the worked example assumes that handoff has already happened.

## How to use this example

**As a developer learning the workflow:**
Read `SESSION-TRANSCRIPT.md` start to finish. It's the closest thing to a video walkthrough — you see what the agent says, what you say back, and what gets committed. Then skim the artifacts so you know what to expect in your own project.

**As an orchestrator-reviewer:**
Read the transcript looking for these behaviors that the agent must exhibit:
- Asks about sprint goal before proposing scope
- Walks through each AC and assigns it to "in sprint 1" or "deferred"
- Surfaces dependencies (US-002 depends on US-001)
- Lists explicit exclusions with rationale
- Refuses to write files before `APPROVE PLAN`
- Commits without pushing
- Names the next slash command to invoke

If a real session diverges from these behaviors, the orchestrator definition needs revision.

**As a project lead estimating effort:**
The sprint summary at `sprint-1-summary.md` is the level of detail you'd present to a PM or client. It's deliberately short — risk areas are surfaced, exclusions are explicit, dependencies are named. Use it as the format your team starts producing for every sprint.

---

*This example will be referenced from the orchestrator's documentation and from the canon's Section 12 (integrated workflow) once the Phase 5–8 specialists are also designed.*
