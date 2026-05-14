# Discovery Checklist — Customer-Facing Solutions (with Back-Office)
*Use this checklist to guide the discovery meeting. Each section should take 10–15 min. Not every question needs a full answer — capture what exists, flag what is unknown.*

---

## 1. Business Context
*Why are we here? What's the trigger for this project?*

- [ ] What problem is this system solving — and for whom (end user, operator, or both)?
- [ ] Who is sponsoring this initiative? (role, not name)
- [ ] Why is this being addressed now — what changed?
- [ ] Is there a competitor or reference product? What do they like / dislike about it?
- [ ] What is the business model? (how does the client make money from this?)
- [ ] What happens if this is not built?

**Notes:**

---

## 1b. Organizational Context
*Who owns the data this system will manage? This question shapes the data model and access rules for everything that follows. It must be answered before any other section.*

Ask the user this open question first:

> *"Who owns the data in this system? Is it one organization using it internally, multiple branches or locations of a single company, or is each customer or external user their own separate account?"*

For customer-facing products, the answer is almost always **customer-account** — but confirm explicitly. There are exceptions: a customer-facing portal for a single corporate client (org-only), or a B2B platform where each client company has multiple customer-facing branches (org-with-units).

Listen for the underlying structure:
- "Just our company's customers, all under one account" → **org-only** (rare for customer-facing)
- "Customers belong to a company that has multiple offices/branches" → **org-with-units**
- "Each customer (person or company) is their own separate account" → **customer-account**

Follow up with the appropriate questions:

- [ ] If **customer-account** (most common): Is each account an individual person or a company with multiple users? Can multiple users belong to the same customer account? Are accounts ever linked (referrals, family plans, group bookings)?
- [ ] If **org-with-units**: What are the units? (region → branch → store / company → department / etc.) Do customers belong to a specific unit, or can they cross unit boundaries?
- [ ] If **org-only**: Are the customer-facing users employees or external users of the same internal organization?

**Capture the answer as a structured field** in `00-discovery-notes.md`:

```yaml
org_context:
  type: org-only | org-with-units | customer-account
  notes: |
    Brief description of how the user expressed it
  account_shape: |
    individual / company / either (for customer-account)
    description of unit hierarchy (for org-with-units)
  customer_relationships: |
    Are customer accounts isolated, or can they interact?
    Are there multi-user accounts?
```

> 🚩 **Flag:** If the client cannot clearly answer this, do not proceed. The auth model, the data isolation rules, and the back-office operator's view of customer data all depend on this answer.

**Notes:**

---

## 2. End-User Profile
*The customer-facing side lives or dies by understanding the end user.*

- [ ] Who is the end user? Describe them (age, context, technical literacy)
- [ ] Where do they use this? (mobile, desktop, both — and in what context: on-the-go, at a desk)
- [ ] What problem are THEY solving when they use this product?
- [ ] What is their biggest frustration with how they handle this today?
- [ ] How do they find out about / access this product? (onboarding flow)
- [ ] What does a successful session look like from their perspective?

**End-user personas identified:**
| Persona | Context | Key goal | Key frustration |
|---------|---------|----------|-----------------|
| | | | |

---

## 3. Actors & Roles
*Map all users across both the customer-facing and back-office sides.*

- [ ] Who are the end users? (paying customers, guests, registered users)
- [ ] Who operates the back-office? List all internal roles
- [ ] What can each back-office role do? (manage users, approve content, configure settings)
- [ ] Are there different tiers of end users? (free vs paid, standard vs premium)
- [ ] Who administers the system overall?

**Roles identified:**
| Role | Side | Actions | Visibility | Notes |
|------|------|---------|------------|-------|
| | Customer-facing | | | |
| | Back-office | | | |

---

## 4. Core Business Loop
*The single most important interaction the product must support — what it exists to do.*

- [ ] What is the ONE thing the end user comes to do?
- [ ] What does the operator need to do to make that possible?
- [ ] What is the trigger that starts this loop?
- [ ] What is the outcome that completes it?
- [ ] What are the 3–5 steps in between?
- [ ] Where does money, data, or value change hands?

**Core loop (sketch):**
```
[End user trigger] → [Step 1] → [Step 2] → [Operator touchpoint?] → [Outcome]
```

---

## 5. Key Processes & Modules
*Secondary flows — both user-facing features and back-office operations.*

- [ ] Beyond the core loop, what other features does the end user need?
- [ ] What does the back-office need to manage? (content, users, orders, reports)
- [ ] Are there notification or communication flows? (email, push, SMS)
- [ ] Are there transactional flows? (payments, bookings, requests)
- [ ] Which modules are essential for launch vs post-launch?

**Module list (rough):**
| Module | Side | Description | Priority |
|--------|------|-------------|----------|
| | Customer-facing | | |
| | Back-office | | |

---

## 6. Data & Integrations
*What information does the system need, and where does it come from?*

- [ ] What are the main entities in this system? (users, products, orders, listings, etc.)
- [ ] For each entity: what are the key data fields?
- [ ] What third-party services are needed? (payments, auth, maps, notifications, logistics)
- [ ] Are there existing systems the back-office team uses that this must connect with?
- [ ] Are there reporting or analytics requirements?
- [ ] Any compliance requirements? (GDPR, PCI-DSS, industry-specific)

**Integrations identified:**
| System / Service | Purpose | Direction | Notes |
|-----------------|---------|-----------|-------|
| | | | |

---

## 7. Success Definition
*How does the client know this worked?*

- [ ] What does success look like for the end user? (adoption, retention, task completion)
- [ ] What does success look like for the operator? (efficiency, revenue, visibility)
- [ ] Are there measurable goals? (conversion rate, volume, NPS, revenue)
- [ ] What would make this project a failure in the client's eyes?
- [ ] Who signs off that the product is working as expected?

**Notes:**

---

## 8. Constraints
*What limits what we can build or how we build it.*

- [ ] Is there a target launch date or deadline?
- [ ] Is there a budget envelope?
- [ ] Technology preferences or restrictions?
- [ ] Expected volume at launch? Peak traffic?
- [ ] Mobile app required, or responsive web sufficient?
- [ ] Is phased delivery acceptable? What must be in v1?

**Notes:**

---

## 9. Open Questions & Red Flags
*Capture anything that needs follow-up or raised a concern.*

| # | Question / Issue | Owner | Urgency |
|---|-----------------|-------|---------|
| | | | |

---

## Discovery Summary (fill after the meeting)

**Product name (working title):**
**Core problem (end-user perspective):**
**Core problem (operator perspective):**
**Core business loop (1–2 sentences):**
**End-user personas:**
**Back-office roles:**
**Number of modules identified:**
**Key integrations:**
**Biggest unknown:**
**Recommended next step:**
