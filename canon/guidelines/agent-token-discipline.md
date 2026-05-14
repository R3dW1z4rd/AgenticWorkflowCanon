# Agent Token Discipline
*This section is included verbatim in every coding agent's CLAUDE.md.*
*It defines how the agent manages context, reads files, and uses tools efficiently.*

---

## How to use this document

Copy the "Rules" section below into the coding agent's CLAUDE.md — not the full document,
just the Rules section. This document explains the reasoning; the rules stand alone.

---

## The Rules (copy into agent CLAUDE.md)

```markdown
## Context and token discipline

### Load order — read in this sequence at the start of every session
1. SPEC.md at the locked spec tag (docs/specs/SPEC.md) — read this first, always
2. The module section in SPEC.md that matches the current task
3. The module CLAUDE.md for context (modules/[slug]/CLAUDE.md)
4. The canon section relevant to the current phase only
5. Actual code files — only after the proposal is approved

### Proposal before file reading
Do not read .service.ts, .schema.ts, or any implementation file
before the proposal is approved by the developer.
Propose based on SPEC.md + module CLAUDE.md + canon rules.
Load code files only when generating or debugging concrete code.

### File reading discipline
- Read a specific function or section, not an entire file, when only part is needed
- Use the module CLAUDE.md Exports section to understand a module's interface
  without reading its source files
- Read source files when: writing or debugging code that calls them directly

### Tool output — reduce before inserting into context
Tests:      show only failing tests and their error messages
TypeScript: show only errors, not passing checks
Git diff:   show only the files changed in the current phase
Migration:  show only the generated SQL, not the full drizzle output
Lint:       show only errors, not warnings

### Session structure — one module, all phases
This agent is responsible for one module through all four coding phases (5–8).
Do not end the session between phases. Use /compact at each phase gate.

Compaction triggers (use /compact [focus] at each of these):
- After Phase 5 PR is merged: compact with focus "schema and contracts decisions"
- After Phase 6 PR is merged: compact with focus "behavior coverage and isolation tests"
- After service layer tests green in Phase 7: compact with focus "service implementation complete"
- After Phase 8 PR is merged: compact with focus "module complete"

What to preserve through compaction:
- Non-obvious design decisions and why they were made
- Permission strings and their rationale
- Any spec ambiguities resolved during the session
- Open questions not yet answered

What to let go through compaction:
- The full conversation history of each proposal round
- Raw tool output (tests, builds, diffs)
- Rejected alternatives

### Phase gate behavior
At each phase gate, the agent must:
1. Confirm what was produced and committed
2. Provide the PR URL for review
3. Compact with the appropriate focus
4. Wait for the developer to confirm merge before proceeding
5. Never start the next phase without explicit developer confirmation

### What this agent never does
- Reads a whole file when it only needs one function or type
- Inserts raw test output, full lint output, or full migration output into its response
- Starts Phase N+1 without developer confirmation that Phase N is merged
- Modifies test files during Phase 7 without flagging and justifying each edit
- Generates code before the proposal is accepted
```

---

## Why these rules (explanation for agent designers)

### Load order

SPEC.md is the stable prefix. It was written before any code and does not change during
a phase. Loading it first creates a cache-stable context anchor — every turn in the session
reuses the same prefix rather than regenerating it. Variable content (code reads, tool
output, conversation) goes after this stable prefix.

### Proposal before file reading

The proposal conversation is where most direction changes happen. If a proposal needs
three rounds of refinement, that costs 600–900 tokens in conversation. If the agent
reads four source files before proposing and the proposal is rejected, those reads cost
6,000–8,000 tokens with no value. Separating proposal from code reading makes the
expensive reads happen only once, after direction is confirmed.

### File reading discipline

A 200-line service file is approximately 1,500–2,000 tokens. A module CLAUDE.md that
summarizes the same module's exports is 200–300 tokens. For cross-module context
(understanding what `branchService` returns so the contracts agent can call it),
the CLAUDE.md is sufficient 90% of the time. Read the source only when writing code
that directly calls into it.

### Tool output reduction

A full Vitest run output for a 20-test file is 2,000–4,000 tokens. The failing tests
alone are 200–400 tokens. This is an 80–90% reduction with zero information loss for
the agent's next action (fix the failing tests). Apply this reduction to every tool
that produces multi-line output.

### One module, all phases

Context accumulated during Phase 5 (why the schema is designed a certain way) is
directly useful in Phase 7 (implementing the service that uses that schema). A separate
Phase 7 agent re-derives this from committed code — more tokens, less nuance. Keeping
one session per module lets accumulated understanding compound across phases.

Compaction prevents the session from ballooning. After each gate, compress the
completed phase to 200–400 tokens of decisions and continue. The session carries
four compacted summaries (one per phase) plus the current working context — far
cheaper than four separate sessions that each re-establish from scratch.

### Phase gate behavior

The gate is not ceremonial. It is where the developer reviews the PR and confirms
the work is correct before the next phase begins. The agent compacts at this point
because the raw Phase N conversation is no longer needed — only the decisions matter.

---

## Token budget reference

Starting context for a typical module session:

| Source | Approximate tokens |
|---|---|
| Project CLAUDE.md (root) | 500–700 |
| Module CLAUDE.md | 300–500 |
| SPEC.md (full project) | 3,000–8,000 |
| Relevant canon section | 500–1,000 |
| **Total at session start** | **~5,000–10,000** |

After each compacted gate:

| Accumulated item | Approximate tokens |
|---|---|
| Phase 5 compacted summary | 200–350 |
| Phase 6 compacted summary | 250–400 |
| Phase 7 partial compact (service layer) | 300–450 |
| **Total accumulated summaries by Phase 8** | **~750–1,200** |

The session ends with roughly the same starting overhead it began with, because
compaction keeps the accumulated history flat.

---

*Part of the Architecture Canon.*
*Source: canon/guidelines/agent-token-discipline.md*
*Included in: every coding agent's CLAUDE.md (Rules section only)*
