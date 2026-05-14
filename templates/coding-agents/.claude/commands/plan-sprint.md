---
description: Plan the next sprint. Reads project state, talks through the plan with you, generates the issue creation script.
---

# /plan-sprint

Invokes the orchestrator agent to plan a sprint. Runs preflight checks first, then enters plan-mode conversation.

## Step 1 — Preflight

Run the preflight script:

```bash
bash .agent/scripts/preflight-plan-sprint.sh
```

The script is non-interactive. It writes findings to stdout and exits with one of:

- **Exit 0** (`PREFLIGHT_RESULT=PASS`) — all checks passed, proceed to Step 2
- **Exit 2** (`PREFLIGHT_RESULT=WARNINGS`) — non-blocking issues found, see Step 1a
- **Exit 1** (`PREFLIGHT_RESULT=BLOCKED`) — blocking errors present, see Step 1b

### Step 1a — Handling warnings

If the preflight returns warnings, do NOT proceed automatically. Read the `WARNING:` lines from the script output and surface them to the developer in conversational form:

> "Preflight found some things worth noting before we plan:
>
> 1. _[paraphrase WARNING: line 1]_
> 2. _[paraphrase WARNING: line 2]_
>
> Should I proceed with sprint planning, or would you like to address these first?"

Only proceed once the developer explicitly says to continue. Common warnings include:

- Open issues from a previous sprint (ask about carry-over)
- On a non-default branch (ask if intentional)
- Working directory not clean (ask whether to stash or commit first)
- Issue provider not configured (ask which provider to use)

### Step 1b — Handling blockers

If the preflight returns blockers, do NOT proceed. The script's output includes a `Remediation:` line for each blocker. Surface them to the developer:

> "Preflight found blocking issues. I can't plan until these are resolved:
>
> 1. _[BLOCKER message]_ — _[Remediation steps]_
> 2. _[BLOCKER message]_ — _[Remediation steps]_
>
> Resolve these, then re-run /plan-sprint."

Common blockers:

- `docs/project-state.md` or `docs/specs/SPEC.md` missing → run installer
- Spec tag in project-state.md doesn't exist in git
- `docs/specs/SPEC.md` has drifted from its locked tag → route to discovery's "Update spec"

End the slash command after presenting blockers. The developer fixes the environment, then runs /plan-sprint again.

## Step 2 — Invoke the orchestrator

Once preflight passes (or the developer explicitly proceeds past warnings), invoke the orchestrator agent defined at `.claude/agents/orchestrator.md`.

The orchestrator reads on session start:
- `docs/project-state.md`
- `docs/specs/SPEC.md`
- `docs/architecture/workflow-quick-reference.md`
- `docs/architecture/section-12-integrated-workflow.md`

The orchestrator opens with a summary of project state and invites you into plan-mode conversation. From there:

1. Orchestrator proposes a sprint plan
2. You refine, ask questions, push back
3. When ready, you type the literal phrase `APPROVE PLAN`
4. Orchestrator writes planning artifacts and commits locally (no push)

## Step 3 — Review and run

After the orchestrator commits the plan:

1. Inspect the changes: `git log -1 -p`
2. Read the generated `scripts/create-sprint-N-issues.sh`
3. Read a sample of `.work/issue-bodies/US-XXX.md`
4. If everything looks right: `git push`
5. Run the issue creation script: `bash scripts/create-sprint-N-issues.sh`
6. Issues appear in your tracker
7. Begin work: `/phase5 [module] US-XXX` for the first story

## What this command never does

- Modifies `docs/specs/SPEC.md` (route to discovery agent's "Update spec" mode)
- Writes code, migrations, or anything outside the orchestrator's allowed write surface
- Creates issues directly (the developer runs the script)
- Pushes to remote (the developer reviews then pushes)
- Closes or reopens issues (state updates happen via Actions on PR merge)

## Related commands

- `/plan-change` — plan work after a spec update (CHANGE-MANIFEST present)
- `/status` — read-only progress review
- `/phase5 [module] US-XXX` — start the Phase 5 specialist on a story
- `/phase6`, `/phase7`, `/phase8` — subsequent phase specialists
