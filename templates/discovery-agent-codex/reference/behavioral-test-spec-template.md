# Behavioral Test Specification
## `[Module Name]` — `[System Name]`

> **Purpose:** Expand each Acceptance Criterion into concrete, observable scenarios before any code is written.
> Readable by designers, PMs, and developers. Feeds directly into Vitest unit shells and Playwright E2E shells.
>
> **How to fill this:**
> 1. Copy each "The system must…" row from the Acceptance Criteria Log
> 2. Write at minimum: one happy-path scenario and one failure/edge-case scenario per criterion
> 3. Review with designer (do the wireframes cover every state?) and dev lead (is every scenario testable?)
> 4. Sign off before test shells are generated

---

**Module:** <!-- e.g. Contract Creation -->
**System:** <!-- e.g. CRM -->
**AC Log reference:** <!-- Link to Google Sheet -->
**Definition Card reference:** <!-- Link to Google Doc -->
**Last updated:** <!-- DD/MM/YYYY -->
**Reviewed by:** <!-- Designer name · Dev lead name -->

---

## Scenario Format

```
[AC-XXX] Criterion summary
  Layer:    unit | integration | e2e
  Actor:    Who triggers this
  Setup:    Pre-conditions that must be true
  Action:   What the actor does
  Expect:   What the system does — observable, specific, unambiguous
  Notes:    Edge cases, data dependencies, open questions
```

---

## Scenarios

<!-- Paste and fill one block per AC row. Duplicate the SCENARIO block for multiple scenarios per criterion. -->

---

### [AC-XXX] The system must…

**Layer:** unit / integration / e2e
**Actor:**
**Priority:** Must / Should / Could

#### SCENARIO 1 — Happy path
```
Setup:
Action:
Expect:
```

#### SCENARIO 2 — Failure / edge case
```
Setup:
Action:
Expect:
```

**Notes:**

---

## Security Boundaries — mandatory scenarios per module

*Every module must have AT LEAST these three security boundary scenarios, in addition to the per-AC scenarios above. These scenarios produce the four required org isolation tests in the canon's testing strategy.*

### SB-1 — Cross-org access denied
```
Layer:   integration
Actor:   Authenticated user from Org B
Setup:   A record exists in Org A. User from Org B is authenticated, has all
         module permissions in their own org, knows the Org A record's ID.
Action:  User from Org B requests the record by ID (via getById / GET endpoint).
Expect:  Response is 404 Not Found (NOT 403 Forbidden — we do not leak existence).
         The record content is never disclosed.
```

### SB-2 — Missing permission denied
```
Layer:   integration
Actor:   Authenticated user from Org A WITHOUT the required permission
Setup:   User is in the correct org, has a valid session, but does not hold
         the permission required for the action (e.g. lacks `[module]:create`).
Action:  User attempts the protected action (calls the Server Action / endpoint).
Expect:  Action fails with a 403 Forbidden / { error: 'Forbidden' } response.
         No data is mutated. An audit entry MAY be written for the failed attempt.
```

### SB-3 — Unauthenticated session redirected
```
Layer:   e2e
Actor:   Unauthenticated visitor
Setup:   No active session. Visitor knows the URL of a protected page.
Action:  Visitor navigates directly to the protected URL.
Expect:  Visitor is redirected to /login (or the configured auth entry point).
         No data is fetched, no service methods are called.
```

### Optional but encouraged — sensitive-field gating

*If the module's data dictionary marks any field as Sensitive/PII = Yes, add this scenario per such field.*

```
Layer:   integration
Actor:   Authenticated user WITHOUT the field's required permission
Setup:   User is in the correct org, can access the record, but does not hold
         the permission named in the field's "Restricted To" column.
Action:  User fetches the record (or the form view that would display the field).
Expect:  The record is returned BUT the sensitive field is omitted or masked.
         Inspecting the API response confirms the field is not present.
```

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Designer | | | ☐ Approved |
| Dev Lead | | | ☐ Approved |
| PM | | | ☐ Approved |
