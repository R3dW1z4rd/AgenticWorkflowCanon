# Acceptance Criteria — Contract Manager

## Module: Contract Creation

| ID | Module | Flow Step | Actor | The system must… | Priority | Status | Gitea Issue | Linked Fields | Notes |
|----|--------|-----------|-------|-----------------|----------|--------|-------------|---------------|-------|
| AC-001 | Contract Creation | Step 1 | Account Manager | allow an Account Manager to initiate a new contract from the list view | Must | Approved | #141 | contract_id, status | |
| AC-002 | Contract Creation | Step 1 | Account Manager | require Start Date, Account Manager, and Contract Type before proceeding past Step 1 | Must | In Dev | #142 | contract_start_date, account_manager_id | |
| AC-003 | Contract Creation | Step 1 | Account Manager | reject a Start Date set in the past and display a clear inline error | Must | Approved | #143 | contract_start_date | |
| AC-004 | Contract Creation | Step 2 | System | display the current exchange rate from the Forex API and refresh every 30 seconds | Must | Draft | | exchange_rate, exchange_rate_at | |
| AC-005 | Contract Creation | Step 2 | System | show a loading indicator while fetching the rate and an error state if the API is unavailable | Must | Draft | | exchange_rate | |
| AC-006 | Contract Creation | Step 3 | Account Manager | allow adding up to 5 referrals and enforce the limit with an inline message | Must | Reviewed | #145 | referral_ids | |
| AC-007 | Contract Creation | Step 3 | Account Manager | require an Employee selection when referral type is employee, and a name when type is external | Must | Reviewed | #146 | referral_type, employee_id, external_name | |
| AC-008 | Contract Creation | Step 4 | System | create an audit log entry whenever a contract status changes | Must | Draft | | contract_id, status | |
| AC-009 | Contract Creation | Step 4 | System | send an email to the assigned AM when a contract moves to Pending Approval | Must | Draft | | account_manager_id, status | |
| AC-010 | Contract Creation | — | Account Manager | allow saving a contract as Draft without triggering required field validation | Should | Draft | | status | |
| AC-011 | Contract Creation | — | System | display commission rate only to Account Manager and Finance roles | Must | Draft | | commission_rate | |
| AC-012 | Contract Creation | — | System | auto-save the form every 60 seconds and restore unsaved data on re-open | Could | Draft | | contract_id | |
