# Module Definition Card — Reference Guide
> Agent reference file. Use this as the template structure when writing module cards to workspace/.

## File naming
`workspace/[project-slug]/01-module-[module-slug].md`
One file per module. Example: `01-module-contract-creation.md`

## Status header (add at top when complete)
```
## Status: Complete ✅  |  Last updated: YYYY-MM-DD  |  Reviewed by: [name]
```

---

## Template Structure

```markdown
# Module Definition Card — [Module Name]
**System:** [Parent system name]
**Version:** v0.1 — Draft
**Last Updated:** YYYY-MM-DD
**Author:** [Who filled this]
**Reviewed By:** [Designer / Dev lead]

---

## 1. Business Purpose
### Why does this module exist?
[2–3 sentences. Link to a real operational need, not a feature description.]

### Business motivation
[What happens if this module does not exist or fails?]

---

## 2. Actors & Roles
| Role | Actions in this module | What they see | Notes |
|------|----------------------|---------------|-------|
| | | | |

---

## 3. Entry & Exit Points
**Entry point:** [What triggers this module?]
**Pre-conditions:** [What must be true before this module can start?]
**Exit point:** [What signals successful completion?]
**Post-conditions:** [What state does the system reach after completion?]

---

## 4. Core Flow
| Step | Description — Actor | Action | System Response |
|------|---------------------|--------|-----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## 5. States & Edge Cases
**Module states:** [e.g. Draft → Pending → Active → Expired]
**State transitions:** [Who triggers each? Under what conditions?]

### Edge Cases
| Scenario | Expected Behavior | Flag |
|----------|------------------|------|
| | | |

---

## 6. Desired Outcomes
| # | The system must… | Priority | AC ID |
|---|-----------------|----------|-------|
| 1 | | Must / Should / Could | AC-XXX |

---

## 6b. Permissions
*Each row maps a natural-language access rule to a structured permission. The permission strings here are read by the canon's RBAC system.*

| # | Natural-language rule | Permission string | Default roles |
|---|-----------------------|-------------------|---------------|
| 1 | e.g. "Only AMs can create contracts" | `contracts:create` | Account Manager, Admin |
| 2 | e.g. "Commission rate visible to AM and Finance" | `contracts:viewCommission` | Account Manager, Finance |

**How to fill this:**
1. Read every "The system must…" outcome above
2. Read every Restricted To value in the data dictionary for this module's entities
3. For each unique access rule, derive a permission string using the format `[module]:[action]`
4. List the default roles that should hold this permission at project launch

See the Permission Extraction Guideline (`reference/permission-extraction-guide.md`) for the full convention.

---

## 7. Out of Scope
[Explicit list of what this module does NOT handle.]

---

## 8. Open Questions & Flags
| # | Question / Gap | Owner | Must resolve before |
|---|---------------|-------|---------------------|
| 🚩 | | | |
```

---

## Writing Guidelines

**Business Purpose:** 2–3 sentences max. Must answer "why does this exist?" not "what does it do?".
Always link to a business problem, not a feature.

**Core Flow:** Max 10 steps. If you need more, the module should be split.
Each step format: `[Actor] [verb] [object] → [System response]`
Example: `Account Manager submits the form → System validates required fields and creates a draft record`

**States:** Every entity in the module should have a defined lifecycle.
If there are no states, the module probably doesn't have workflow — confirm this.

**Desired Outcomes:** These become AC-XXX entries in the Acceptance Criteria file.
Write them as observable outcomes: "The system must [verb] [observable result]"
Aim for 4–8 per module. If you have fewer than 4, the module is probably underdefined.

**Out of Scope:** This is as important as the in-scope content.
Ask: "What would someone reasonably expect this module to do that it actually does NOT do?"
