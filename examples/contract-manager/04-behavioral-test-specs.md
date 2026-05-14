# Behavioral Test Specification
## `Contract Creation` — `CRM`

> This document expands each Acceptance Criterion for the Contract Creation module into
> concrete, observable scenarios. It is the bridge between the Acceptance Criteria Log
> and the Vitest / Playwright test shells. Any scenario not covered by a wireframe state
> or a test case is a gap that must be resolved before development begins.

**Module:** Contract Creation
**System:** CRM
**AC Log reference:** module-workbook.xlsx → ✅ Acceptance Criteria
**Definition Card reference:** module-definition-card.docx
**Last updated:** 2025-04-26
**Reviewed by:** [Designer name] · [Dev lead name]

---

## AC-001 — Initiate a new contract from the Contracts list view

**Layer:** e2e
**Actor:** Account Manager
**Priority:** Must

#### SCENARIO 1 — Happy path: AM creates a new contract
```
Setup:   User is authenticated as Account Manager
         User is on the /contracts list view
         At least 0 contracts may exist (empty state is valid)
Action:  User clicks the primary "New Contract" button
Expect:  - User is navigated to /contracts/new (or a modal opens — per wireframe)
         - A new contract record is created in status: "draft"
         - The contract_id is auto-generated (UUID v4) and never shown to the user
         - The form is empty / pre-filled with system defaults only
```

#### SCENARIO 2 — AM with read-only role cannot initiate
```
Setup:   User is authenticated with a role that does NOT include contract creation rights
Action:  User visits the /contracts list view
Expect:  - "New Contract" button is either hidden or visibly disabled
         - No navigation to /contracts/new occurs
         - No draft record is created
```

**Notes:** Confirm with designer whether creation is a full page or a modal flow.

---

## AC-002 — Require Start Date, Account Manager, and Contract Type before proceeding past Step 1

**Layer:** unit (validator) + e2e (form behaviour)
**Actor:** Account Manager
**Priority:** Must

#### SCENARIO 1 — Happy path: all required fields filled
```
Setup:   User is on Contract Creation Step 1
         Start Date field = today's date
         Account Manager field = a valid, active AM (current user or another)
         Contract Type field = a valid enum value
Action:  User clicks "Continue" / "Next"
Expect:  - No validation errors are shown
         - User advances to Step 2
         - No data is persisted yet (or saved as draft — confirm with designer)
```

#### SCENARIO 2 — Start Date is empty
```
Setup:   User is on Step 1
         Account Manager and Contract Type are filled
         Start Date is empty
Action:  User clicks "Continue"
Expect:  - Form does not advance
         - Inline error appears directly below the Start Date field
         - Error text: "Start date is required"
         - All other fields retain their values
```

#### SCENARIO 3 — Account Manager field is empty
```
Setup:   Start Date and Contract Type are filled. Account Manager is empty.
Action:  User clicks "Continue"
Expect:  - Form does not advance
         - Inline error below Account Manager: "Account manager is required"
```

#### SCENARIO 4 — Contract Type is empty
```
Setup:   Start Date and Account Manager are filled. Contract Type is empty.
Action:  User clicks "Continue"
Expect:  - Form does not advance
         - Inline error below Contract Type: "Contract type is required"
```

#### SCENARIO 5 — Multiple fields empty simultaneously
```
Setup:   All three required fields are empty
Action:  User clicks "Continue"
Expect:  - Form does not advance
         - All three inline errors appear simultaneously (not one at a time)
         - Focus moves to the first errored field
```

**Notes:** Validation must run client-side on submit attempt. Do not validate on blur
for this step — it creates friction during first-time form fill.

---

## AC-003 — Reject a Start Date set in the past

**Layer:** unit (date validator)
**Actor:** Account Manager
**Priority:** Must

#### SCENARIO 1 — User enters yesterday's date
```
Setup:   User is on Step 1
Action:  User enters a date 1 day before today in the Start Date field
         User clicks "Continue"
Expect:  - Form does not advance
         - Inline error below Start Date: "Start date must be today or in the future"
         - The invalid date value remains visible in the field (do not clear it)
```

#### SCENARIO 2 — User enters today's date
```
Setup:   User is on Step 1
Action:  User enters today's date in the Start Date field (all other fields valid)
         User clicks "Continue"
Expect:  - No error shown for Start Date
         - Form advances to Step 2
```

#### SCENARIO 3 — User enters a future date
```
Setup:   User is on Step 1
Action:  User enters a date 30 days in the future (all other fields valid)
         User clicks "Continue"
Expect:  - No error shown for Start Date
         - Form advances to Step 2
```

#### SCENARIO 4 — Boundary: midnight edge case
```
Setup:   System clock is at 23:59 on day D
         User enters date D+1 (tomorrow)
Action:  User submits
Expect:  - Date D+1 is accepted (it is in the future)
Notes:   Date comparison must use the user's local date, not UTC
```

**Notes:** The validator function `validateStartDate(date: string): ValidationResult`
is a pure function — it receives a date string and today's reference date and returns
`{ valid: boolean, error?: string }`. Unit-testable without any UI.

---

## AC-004 — Display exchange rate from Forex API, refreshed every 30 seconds

**Layer:** unit (service) + integration (API mapping) + e2e (UI refresh)
**Actor:** System (automatic)
**Priority:** Must

#### SCENARIO 1 — Happy path: rate fetched on form load
```
Setup:   User navigates to Contract Creation Step 2 (or whichever step shows the rate)
         Forex API is available and returns a valid rate
Action:  Page loads
Expect:  - Exchange rate is displayed within 3 seconds of page load
         - exchange_rate_at timestamp is shown alongside the rate
         - The rate field is not editable by the user
```

#### SCENARIO 2 — Rate auto-refreshes after 30 seconds
```
Setup:   Form is open, initial rate is displayed (e.g. 1.0823)
         Forex API returns a different rate on second call (e.g. 1.0891)
Action:  30 seconds elapse without user interaction
Expect:  - Rate value updates to 1.0891 without page reload
         - exchange_rate_at timestamp updates to current time
         - No user-visible disruption (no flash, no spinner on refresh — only on initial load)
```

#### SCENARIO 3 — Rate refresh does not reset other form fields
```
Setup:   User has partially filled the form. 30 seconds elapse.
Action:  Rate auto-refreshes
Expect:  - All user-entered field values are preserved
         - Only exchange_rate and exchange_rate_at values change
```

**Notes:** The refresh is driven by a client-side interval (setInterval / useEffect cleanup).
Test the service layer (`fetchExchangeRate()`) independently of the UI timer logic.
The 30-second interval should be cleared on component unmount.

---

## AC-005 — Loading indicator while fetching rate; error state if API is unavailable

**Layer:** unit (service error handling) + e2e (UI states)
**Actor:** System
**Priority:** Must

#### SCENARIO 1 — Loading state on initial fetch
```
Setup:   Forex API has a simulated 1.5 second response delay
Action:  User loads the form step that displays the exchange rate
Expect:  - A loading indicator (spinner or skeleton) appears in the exchange rate field
         - The rate field shows "--" or similar placeholder (not 0, not empty string)
         - Loading indicator disappears and rate appears once API responds
```

#### SCENARIO 2 — API timeout
```
Setup:   Forex API is configured to not respond (timeout after 5 seconds)
Action:  User loads the form step
Expect:  - Loading indicator appears initially
         - After 5 seconds, an error state appears in the rate field area
         - Error message: "Exchange rate unavailable. Please try again."
         - A "Retry" action is available
         - The rest of the form remains usable (user can still fill other fields)
```

#### SCENARIO 3 — API returns malformed data
```
Setup:   Forex API returns a 200 response but with invalid/missing rate field
Action:  System processes the response
Expect:  - Error is caught and logged (not thrown to the UI as an unhandled error)
         - UI shows the same "unavailable" error state as Scenario 2
         - exchange_rate field is NOT updated with invalid data
```

**Notes:** The contract must not be submittable while exchange_rate is in an error state.
Confirm this constraint with the dev lead — it may require a form-level disabled state.

---

## AC-006 — Allow up to 5 referrals; enforce the limit

**Layer:** unit (referral list validator) + e2e
**Actor:** Account Manager
**Priority:** Must

#### SCENARIO 1 — Adding referrals up to the limit
```
Setup:   User is on the referrals step. 0 referrals added.
Action:  User adds referrals one by one until 5 are present
Expect:  - Each referral is added and displayed in a list
         - After the 5th is added, the "Add Referral" button becomes disabled
         - No error message is shown (the disabled state is sufficient feedback)
```

#### SCENARIO 2 — Attempting to exceed the limit
```
Setup:   5 referrals already added
Action:  User attempts to click "Add Referral" (if not disabled) or submits a 6th
Expect:  - 6th referral is rejected
         - Inline message: "Maximum of 5 referrals allowed per contract"
         - The existing 5 referrals are unaffected
```

#### SCENARIO 3 — Removing a referral re-enables the Add button
```
Setup:   5 referrals added. "Add Referral" is disabled.
Action:  User removes one referral
Expect:  - "Add Referral" button becomes enabled again
         - referral_ids array length is now 4
```

#### SCENARIO 4 — 0 referrals is valid
```
Setup:   User completes the form with no referrals added
Action:  User submits the contract
Expect:  - Contract is created successfully
         - referral_ids is stored as an empty array []
         - No validation error about missing referrals
```

---

## AC-007 — Conditional referral fields based on referral type

**Layer:** unit (conditional field logic) + e2e (form behaviour)
**Actor:** Account Manager
**Priority:** Must

#### SCENARIO 1 — Referral type: employee
```
Setup:   User is adding a referral. referral_type = "employee"
Action:  User selects "Employee" from the referral type dropdown
Expect:  - Employee selection field appears (searchable dropdown of active employees)
         - External name text field is hidden
         - Employee field is marked required
         - Commission rate field appears (visible to AM role)
```

#### SCENARIO 2 — Referral type: external
```
Setup:   User is adding a referral. referral_type = "external"
Action:  User selects "External" from the referral type dropdown
Expect:  - External name text field appears (free text, max 100 chars)
         - Employee selection field is hidden
         - External name field is marked required
```

#### SCENARIO 3 — Switching type clears previous value
```
Setup:   User has selected "Employee" and chosen an employee from the dropdown
Action:  User changes referral_type to "External"
Expect:  - employee_id is cleared / reset to null
         - External name field appears empty
         - No stale data from the previous type is submitted
```

#### SCENARIO 4 — Attempting to save employee referral without selecting an employee
```
Setup:   referral_type = "employee". Employee field is empty.
Action:  User attempts to add/save the referral
Expect:  - Inline error below employee field: "Please select an employee"
         - Referral is not added to the list
```

---

## AC-008 — Audit log entry on every contract status change

**Layer:** unit (audit service) + integration (DB write)
**Actor:** System
**Priority:** Must

#### SCENARIO 1 — Status changes from draft to pending
```
Setup:   Contract exists with status: "draft"
         Triggering user is an authenticated Account Manager
Action:  System processes a status change to "pending"
Expect:  - Audit log entry is created with:
             - contract_id (correct)
             - previous_status: "draft"
             - new_status: "pending"
             - user_id of the triggering user
             - timestamp: within 1 second of the action
             - action_type: "status_change"
         - The contract record is updated
         - Both writes succeed or both fail (atomically)
```

#### SCENARIO 2 — Audit log entry is immutable after creation
```
Setup:   An audit log entry exists
Action:  Any user or system process attempts to update or delete it
Expect:  - The operation is rejected (403 or equivalent)
         - The original entry is unchanged
```

**Notes:** The audit service must be tested independently of the contract service.
Inject a mock audit repository in unit tests. Integration test verifies the DB record.

---

## AC-009 — Email notification to AM when contract moves to Pending Approval

**Layer:** unit (notification service) + integration (email dispatch)
**Actor:** System
**Priority:** Must

#### SCENARIO 1 — Notification sent on pending status
```
Setup:   Contract has account_manager_id pointing to AM with a valid email
Action:  Contract status changes to "pending"
Expect:  - Email is dispatched to the AM's registered email address
         - Email is sent within 60 seconds
         - Email subject references the contract (e.g. includes contract ID or name)
         - If email dispatch fails, the status change is NOT rolled back —
           log the failure and retry asynchronously
```

#### SCENARIO 2 — No duplicate notification on repeated status writes
```
Setup:   Contract already in "pending" status
Action:  A system process writes "pending" to status again (idempotent write)
Expect:  - No additional email is sent
         - Notification is only triggered on actual status transitions
```

---

## AC-010 — Save as Draft at any point without triggering required field validation

**Layer:** unit (draft save logic) + e2e
**Actor:** Account Manager
**Priority:** Should

#### SCENARIO 1 — Save as Draft with all fields empty
```
Setup:   User is on Step 1. All fields are empty.
Action:  User clicks "Save as Draft"
Expect:  - No validation errors appear
         - Contract is saved with status: "draft"
         - User receives confirmation (toast, message, or navigation)
         - Saved data: only system-generated fields (contract_id, status, timestamps)
```

#### SCENARIO 2 — Save as Draft with partial data
```
Setup:   User has filled Start Date and Account Manager but not Contract Type
Action:  User clicks "Save as Draft"
Expect:  - No validation errors
         - Contract is saved with the partial data that was entered
         - On re-opening the draft, the filled fields are restored
```

---

## AC-011 — Commission rate visible only to Account Manager and Finance roles

**Layer:** unit (permission guard) + e2e (per-role UI)
**Actor:** System (access control)
**Priority:** Must

#### SCENARIO 1 — AM can see commission rate
```
Setup:   User is authenticated as Account Manager
Action:  User opens Contract Creation or Contract Detail
Expect:  - commission_rate field is visible and editable (on creation)
```

#### SCENARIO 2 — Finance role can see commission rate
```
Setup:   User is authenticated as Finance
Action:  User opens Contract Detail view
Expect:  - commission_rate field is visible (read-only or editable — confirm with designer)
```

#### SCENARIO 3 — Other roles cannot see commission rate
```
Setup:   User is authenticated as any role other than AM or Finance
         (e.g. Viewer, External Partner, Support)
Action:  User opens Contract Detail view
Expect:  - commission_rate field is not rendered in the DOM
         - The field is not accessible via direct API call (backend guard also required)
         - No placeholder or "hidden" label is shown
```

**Notes:** This must be enforced on BOTH the frontend (field not rendered) and the backend
(field excluded from API response). A frontend-only guard is not sufficient.

---

## AC-012 — Auto-save every 60 seconds; restore unsaved data on re-open

**Layer:** unit (auto-save service) + e2e
**Actor:** System
**Priority:** Could

#### SCENARIO 1 — Auto-save triggers after 60 seconds of inactivity
```
Setup:   User has partially filled the form. No manual save has occurred.
Action:  60 seconds elapse
Expect:  - Form data is saved silently (no disruptive UI change)
         - A subtle "Saved" indicator appears briefly (confirm with designer)
         - The draft record in the DB is updated with current field values
```

#### SCENARIO 2 — Data is restored after accidental tab close
```
Setup:   User has partially filled the form. Auto-save has run at least once.
Action:  User closes the browser tab without saving manually
         User re-opens the contract draft
Expect:  - All field values present at the time of the last auto-save are restored
         - User sees the form in the state it was left (not a blank form)
```

#### SCENARIO 3 — Auto-save interval is cleared on intentional navigation away
```
Setup:   Auto-save is running (interval active)
Action:  User manually submits the contract OR navigates away intentionally
Expect:  - The auto-save interval is cleared
         - No further background saves occur after the user has left the form
```

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Designer | | | ☐ Approved |
| Dev Lead | | | ☐ Approved |
| PM | | | ☐ Approved |
