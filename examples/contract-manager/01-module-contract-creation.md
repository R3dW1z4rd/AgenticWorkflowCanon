# Module Definition Card — Contract Creation
**System:** CRM
**Version:** v0.1 — Draft

## 1. Business Purpose
Allows Account Managers to create and manage contracts with clients. Without this module, contracts are tracked in spreadsheets, creating version conflicts and audit risk.

## 2. Actors & Roles
| Role | Actions | What they see |
|------|---------|---------------|
| Account Manager | Create, edit, submit contracts | All fields except commission rate is restricted to AM + Finance |
| Finance | Review commission rates | Commission rate field visible |
| System | Auto-generate IDs, timestamps, audit log | — |

## 3. Entry & Exit Points
**Entry point:** User clicks "New Contract" from the Contracts list view
**Pre-conditions:** User must be authenticated with Account Manager role
**Exit point:** Contract status changes to Active and notifications are sent
**Post-conditions:** Contract is stored, audit log entry created, AM notified

## 4. Core Flow
| Step | Description |
|------|-------------|
| 1 | Account Manager clicks New Contract → system creates draft record |
| 2 | AM fills Step 1: Start Date, Account Manager, Contract Type |
| 3 | AM fills Step 2: exchange rate displayed from Forex API |
| 4 | AM adds referrals (0–5) with type and details |
| 5 | AM submits → system validates and changes status to Pending |
| 6 | System sends notification to AM, creates audit log entry |

## 5. States & Edge Cases
**States:** Draft → Pending Approval → Active → Expired / Cancelled

## 6. Desired Outcomes
| # | The system must… | Priority |
|---|-----------------|----------|
| 1 | Allow AM to create a new contract from the list view | Must |
| 2 | Reject a past Start Date with an inline error | Must |
| 3 | Display Forex exchange rate and refresh every 30 seconds | Must |
| 4 | Enforce maximum of 5 referrals per contract | Must |
| 5 | Restrict commission rate visibility to AM and Finance | Must |

## 7. Out of Scope
Contract renewal, payment processing, and document signing are not in scope for v1.

## 8. Open Questions & Flags
| # | Question | Owner |
|---|---------|-------|
| 🚩 | Is contract type a fixed catalog or user-defined? | PM |
