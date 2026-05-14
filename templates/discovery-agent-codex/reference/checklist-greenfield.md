# Discovery Checklist — New Process / Greenfield
*For projects where the client is envisioning something that doesn't fully exist yet — no prior system, no defined process, or a process that exists informally and needs to be designed properly before it can be built.*

*Your role in this discovery is part consultant, part architect. The goal is not just to capture requirements but to help the client think clearly about what they are building, for whom, and how it will actually operate.*

---

> **How to use this checklist**
> Many clients at this stage have a strong vision for the *product* but have not thought through the *operations* behind it. Use the questions in each section to surface gaps, challenge assumptions, and help them arrive at a clearer picture. Flag anything that feels undefined — that is the work.

---

## 1. The Vision & the Problem
*Start here. Understand what the client believes they are building and why.*

- [ ] Describe the product or solution you want to build — as if explaining it to a friend
- [ ] What problem does this solve, and for whom?
- [ ] What made you decide this is the right solution to that problem?
- [ ] Who else is solving this problem today? What do you think you'll do differently?
- [ ] How long have you been thinking about this? What has stopped it from existing already?
- [ ] What does success look like 12 months after launch?

> 🚩 **Flag:** If the client cannot clearly articulate the problem separate from the solution, slow down here. A system built around a fuzzy problem will drift.

**Notes:**

---

## 1b. Organizational Context
*Who owns the data this system will manage? This question shapes the data model and access rules for everything that follows. It must be answered before any other section.*

For greenfield projects, this question is especially important — clients often have not thought about it yet. The answer determines whether the system has a single tenant, multiple sub-organizations, or per-customer accounts.

Ask the user this open question first:

> *"Who owns the data in this system? Is it one organization using it internally, multiple branches or locations of a single company, or is each customer or external user their own separate account?"*

If the client hesitates, give examples grounded in their domain:
- *"For example — if your business is a chain of clinics, do all clinics share data, or is each clinic separate?"*
- *"If you're building a marketplace, are sellers individual accounts, or do they belong to a parent company?"*

Listen for the underlying structure:
- "Just our internal team / company" → **org-only**
- "Multiple offices / branches / locations / clinics / outlets" → **org-with-units**
- "Each customer or vendor or seller is their own account" → **customer-account**

Greenfield projects often combine patterns — e.g. a marketplace where sellers are customer-accounts AND there's an internal admin org-only side. Capture this honestly:

- [ ] Is there a back-office side (your operations team) AND a customer-facing side (their accounts)? If so, both org contexts apply — internal team is **org-only**, customers are **customer-account**.
- [ ] Will the system need to support different tiers, regions, or franchise locations in the future, even if not at launch?
- [ ] Are there any cross-account interactions (customers transacting with each other, marketplaces, referrals)?

**Capture the answer as a structured field** in `00-discovery-notes.md`:

```yaml
org_context:
  internal_side:
    type: org-only | org-with-units | not-applicable
    notes: |
      How the operating team is organized
  customer_side:
    type: customer-account | org-with-units | not-applicable
    notes: |
      How external users / customers are organized
  cross_account_interactions: |
    Whether and how accounts interact (marketplaces, referrals, etc.)
```

> 🚩 **Flag:** If the client cannot answer this, slow down. Greenfield projects without a clear answer here typically get rebuilt within their first year. The data isolation model is a fundamental architectural decision and changing it later is expensive.

**Notes:**

---

## 2. The Business Model
*Most clients think about the product. Few have thought through how it sustains itself.*

- [ ] How does this generate revenue — or value — for your business?
- [ ] Who pays, and for what exactly?
- [ ] Is this a one-time transaction, a subscription, a marketplace fee, or something else?
- [ ] What does a customer relationship look like over time? (acquisition → use → retention)
- [ ] Are there multiple revenue streams or tiers?
- [ ] What is the minimum viable version that could generate its first revenue or value?

> 🚩 **Flag:** If the business model is unclear, the back-office and admin requirements will be impossible to define. Resolve this before designing the operational layer.

**Notes:**

---

## 3. End-User Profile
*Who are you building this for? Be specific — a broad audience is usually a sign of unclear thinking.*

- [ ] Describe your ideal user in detail — who are they, what do they do, what is their context?
- [ ] What job are they trying to get done when they use this product?
- [ ] What do they do today instead? (even if it's manual, informal, or with a different tool)
- [ ] What frustrates them most about the way they handle it today?
- [ ] How will they find out about this product?
- [ ] What would make them come back — or stop coming back?
- [ ] Have you spoken to any of these users directly? What did they tell you?

> 🚩 **Flag:** If the client has not spoken to any real users, their assumptions about user behavior are untested. Note this explicitly — it is a project risk.

**End-user personas identified:**
| Persona | Context | Job to be done | Current alternative | Key frustration |
|---------|---------|---------------|---------------------|-----------------|
| | | | | |

---

## 4. The Consumer Experience (Front-End Vision)
*What does the client imagine the user experiencing? This is often where they have the clearest ideas — and where scope creep starts.*

- [ ] Walk me through the product as you imagine a user would experience it, from first contact to completion
- [ ] What is the first thing a new user sees or does?
- [ ] What is the core action — the one thing the product exists to let them do?
- [ ] How does the user know they succeeded?
- [ ] Are there different paths for different user types?
- [ ] What happens when something goes wrong? (error, cancellation, rejection)
- [ ] What notifications or communications does the user receive, and when?
- [ ] Is this primarily a mobile experience, desktop, or both?

**Consumer flow (sketch):**
```
[First contact / Onboarding] → [Core action] → [Outcome / Confirmation] → [Return / Retention]
```

**Notes:**

---

## 5. The Operational Process (Back-End Vision)
*This is usually the most underdeveloped area. The client knows what the user sees — but who runs this, and how?*

- [ ] When a user does [core action], what has to happen on your side to fulfill it?
- [ ] Who on your team handles what? Walk me through the operational steps
- [ ] Are any steps manual today, or will they remain manual after launch?
- [ ] How do you handle exceptions — cases that don't follow the standard flow?
- [ ] How do you communicate with users when intervention is needed?
- [ ] How do you measure whether operations are running well?
- [ ] What would break first if you had 10x the current volume?

> 🚩 **Flag:** If the client hasn't thought through the operational side, they are effectively designing a product with no back-end process. This needs to be resolved before the back-office can be designed.

**Operational steps (sketch):**
```
[User action] → [Who receives it] → [What they do] → [How they respond / fulfill]
```

**Notes:**

---

## 6. Actors, Roles & Organizational Readiness
*Who will actually operate this system — and do they exist yet?*

- [ ] Who will manage the day-to-day operations of this product?
- [ ] Do these people already exist in your organization, or will they need to be hired?
- [ ] What tools do they use today to manage similar work?
- [ ] Who has authority to approve, reject, configure, or override?
- [ ] Who is responsible for the system as a whole? (the "owner")
- [ ] Will there be different permission levels? Who can see what?

> 🚩 **Flag:** If the operational team doesn't exist yet, factor in onboarding time and training requirements as part of the project scope.

**Roles identified:**
| Role | Side | Exists today? | Actions | Visibility |
|------|------|--------------|---------|------------|
| | Customer-facing | | | |
| | Back-office / Ops | | | |

---

## 7. Key Processes to Design
*Unlike existing-process projects, here we are defining what needs to exist — not documenting what does.*

For each process below, ask: *does this need to exist, and if so, who owns it?*

- [ ] User onboarding & verification
- [ ] Core transaction / fulfillment process
- [ ] Exception handling & escalation
- [ ] User support & communication
- [ ] Quality control or review process
- [ ] Reporting & performance monitoring
- [ ] Billing & payments (if applicable)
- [ ] Content or catalog management (if applicable)
- [ ] User lifecycle (suspension, deactivation, re-engagement)

**Processes to design:**
| Process | Owner (role) | Manual or automated | Priority | Notes |
|---------|-------------|---------------------|----------|-------|
| | | | | |

---

## 8. Data & Integrations
*What information does the system need, and where does it come from?*

- [ ] What are the main entities in this system? (users, products, orders, requests, etc.)
- [ ] For each entity: what are the key data fields?
- [ ] What third-party services will be needed? (payments, identity verification, maps, notifications)
- [ ] Are there existing internal systems this must connect to?
- [ ] What does the client need to *see* to run this business? (dashboards, reports, alerts)
- [ ] Any compliance, legal, or data requirements? (GDPR, industry regulations, contracts)

**Integrations identified:**
| System / Service | Purpose | Notes |
|-----------------|---------|-------|
| | | |

---

## 9. Assumptions & Risks
*New process projects run on assumptions. Surface them before they become problems.*

- [ ] What is the client most confident about — and what is that confidence based on?
- [ ] What is the client most uncertain about?
- [ ] What assumptions about user behavior is the product design dependent on?
- [ ] What assumptions about operational capacity are baked into the plan?
- [ ] What external dependencies could block this? (regulations, suppliers, partners)
- [ ] What is the riskiest part of this project?

**Assumption log:**
| Assumption | Impact if wrong | Validated? | How to validate |
|-----------|----------------|------------|-----------------|
| | | | |

---

## 10. Constraints
*What limits what we can build or how we build it.*

- [ ] Is there a target launch date or milestone?
- [ ] Is there a budget envelope?
- [ ] Technology preferences or restrictions?
- [ ] Is there a minimum viable version that must ship first?
- [ ] Are there partnerships or dependencies that affect the timeline?
- [ ] How much of the operational process needs to be in place before launch?

**Notes:**

---

## 11. Open Questions & Next Steps
*Capture anything unresolved — especially anything that must be answered before design can begin.*

| # | Question / Gap | Owner | Must resolve before |
|---|---------------|-------|---------------------|
| | | | |

---

## Discovery Summary (fill after the meeting)

**Product name (working title):**
**Core problem (1 sentence):**
**Primary user persona:**
**Business model (1 sentence):**
**Core consumer flow (1–2 sentences):**
**Core operational process (1–2 sentences):**
**Processes that need to be designed from scratch:**
**Key integrations:**
**Biggest assumption being made:**
**Most critical open question:**
**Recommended next step:**
**Consulting gaps to address before next session:**
