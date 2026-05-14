# Discovery Checklist — Internal Operations Tools
*Use this checklist to guide the discovery meeting. Each section should take 10–15 min. Not every question needs a full answer — capture what exists, flag what is unknown.*

---

## 1. Business Context
*Why are we here? What's the trigger for this project?*

- [ ] What problem is this system solving?
- [ ] Who is sponsoring this initiative? (role, not name)
- [ ] Why is this being addressed now — what changed?
- [ ] Has this been attempted before? What happened?
- [ ] What happens if this problem is not solved?

**Notes:**

---

## 1b. Organizational Context
*Who owns the data this system will manage? This question shapes the data model and access rules for everything that follows. It must be answered before any other section.*

Ask the user this open question first:

> *"Who owns the data in this system? Is it one organization using it internally, multiple branches or locations of a single company, or is each customer or external user their own separate account?"*

Listen carefully. The answer rarely uses these exact words — listen for the underlying structure:
- "Just our company" / "It's an internal tool" → **org-only**
- "Multiple offices / branches / regions / stores / locations" → **org-with-units**
- "Each of our customers / clients / vendors will have their own account" → **customer-account**

Follow up with the appropriate questions:

- [ ] If **org-only**: Is the entire team in one tenant, or could there be a future need for multiple internal teams to be separated?
- [ ] If **org-with-units**: How are units organized? (regions → branches → stores, or flat?) Do users belong to one unit, multiple units, or all of them?
- [ ] If **customer-account**: Is each customer account an individual person, or a company with multiple users underneath it? Are customer accounts isolated, or do customers ever interact across accounts?

**Capture the answer as a structured field** in `00-discovery-notes.md`:

```yaml
org_context:
  type: org-only | org-with-units | customer-account
  notes: |
    Brief description of how the user expressed it
  hierarchy: |
    If org-with-units: describe the levels (e.g. region → branch → store)
    If customer-account: describe whether customers are individuals or companies
  user_assignment: |
    How users are assigned to org units (one unit / multiple / all)
```

> 🚩 **Flag:** If the client cannot clearly answer this, do not proceed. Every later section depends on knowing whether data is shared across the whole organization, segmented by sub-unit, or isolated per customer.

**Notes:**

---

## 2. Current Process
*Understand what exists today before proposing anything new.*

- [ ] How is this process handled today? (manual, spreadsheet, existing tool)
- [ ] Walk me through the process step by step — from trigger to completion
- [ ] Where does the current process break down or create friction?
- [ ] What workarounds have people invented?
- [ ] What data is being captured today, and where does it live?

**Notes:**

---

## 3. Actors & Roles
*Who will use this system, and in what capacity?*

- [ ] Who are the users of this system? List all roles
- [ ] For each role: what do they need to *do* in the system?
- [ ] For each role: what do they need to *see* in the system?
- [ ] Are there approvers or reviewers? What triggers an approval?
- [ ] Who administers the system? (user management, configuration)
- [ ] Are there external parties involved? (vendors, clients, partners)

**Roles identified:**
| Role | Actions | Visibility | Notes |
|------|---------|------------|-------|
| | | | |

---

## 4. Core Business Loop
*The single most important process the system must support — everything else is secondary.*

- [ ] If this system only did ONE thing perfectly, what would it be?
- [ ] What is the input that starts this process?
- [ ] What is the output or outcome that ends it?
- [ ] What are the 3–5 steps in between?
- [ ] What decisions are made along the way, and by whom?

**Core loop (sketch):**
```
[Trigger] → [Step 1] → [Step 2] → [Decision?] → [Outcome]
```

---

## 5. Key Processes & Modules
*Secondary flows that the system also needs to support.*

- [ ] Beyond the core loop, what other processes does this system need to handle?
- [ ] Are any of these processes dependent on the core loop?
- [ ] Which processes are highest priority?
- [ ] Which processes are "nice to have" vs essential for launch?

**Module list (rough):**
| Module | Description | Priority | Depends On |
|--------|-------------|----------|------------|
| | | | |

---

## 6. Data & Integrations
*What information does the system need to work, and where does it come from?*

- [ ] What are the main entities / objects in this system? (e.g. orders, employees, requests)
- [ ] For each entity: what are the key data fields?
- [ ] What systems does this need to connect with? (ERP, CRM, HR system, etc.)
- [ ] Is data flowing in, out, or both?
- [ ] Are there reporting or export requirements?
- [ ] Any compliance or data residency requirements?

**Integrations identified:**
| System | Direction | Data exchanged | Notes |
|--------|-----------|----------------|-------|
| | | | |

---

## 7. Success Definition
*How does the client know this worked?*

- [ ] What does success look like in 3 months?
- [ ] Are there measurable goals? (time saved, error rate, volume processed)
- [ ] What would make this project a failure in the client's eyes?
- [ ] Who signs off that the system is working as expected?

**Notes:**

---

## 8. Constraints
*What limits what we can build or how we build it.*

- [ ] Is there a target launch date or deadline?
- [ ] Is there a budget envelope?
- [ ] Are there technology preferences or restrictions? (must use X, cannot use Y)
- [ ] Are there internal IT or security requirements?
- [ ] How many users will use this at launch? Peak load?
- [ ] Is phased delivery acceptable?

**Notes:**

---

## 9. Open Questions & Red Flags
*Capture anything that needs follow-up or raised a concern.*

| # | Question / Issue | Owner | Urgency |
|---|-----------------|-------|---------|
| | | | |

---

## Discovery Summary (fill after the meeting)

**System name (working title):**
**Core problem:**
**Core business loop (1–2 sentences):**
**Number of roles:**
**Number of modules identified:**
**Key integrations:**
**Biggest unknown:**
**Recommended next step:**
