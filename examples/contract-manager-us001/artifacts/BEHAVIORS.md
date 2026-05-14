# Behaviors — Contracts Module (US-001)
*Committed in Phase 6a, separately from the test code*
*One behavior per line. Test files must have 1:1 correspondence with these bullets.*

---

## Schema behaviors (contracts.schema.test.ts)

- Given valid contract data with a future start date, when createContractSchema parses it, then it succeeds and returns the parsed values
- Given contract data with a start date in the past (e.g. 2020-01-01), when createContractSchema parses it, then it fails with a message containing "past"
- Given contract data missing the required contractType field, when createContractSchema parses it, then it fails
- Given an empty object, when createDraftContractSchema parses it, then it succeeds (all fields are optional for drafts)
- Given an object with a non-uuid accountManagerId, when createDraftContractSchema parses it, then it fails even though the field is optional

---

## Service behaviors (contracts.service.test.ts)

### contractService.create
- Given valid input and a caller in orgA, when create is called, then the returned contract has orgId = orgA.orgId and orgUnitId = orgA.orgUnitId
- Given valid input, when create is called, then the returned contract always has status = 'draft' regardless of what is in the input
- Given input with a past start date, when create is called, then it returns { error } containing "past"

### contractService.createDraft
- Given only an accountManagerId (nothing else), when createDraft is called, then it succeeds and returns a draft contract with null startDate and null contractType

### contractService.getById
- Given a contract that exists in the same org as the caller, when getById is called, then it returns the contract
- Given a contract ID that does not exist, when getById is called, then it returns null

---

## Org isolation behaviors (contracts.service.test.ts — REQUIRED)

- Given a contract created by orgA, when orgB calls getById with that contract's ID, then it receives null (not a 403 — the contract appears to not exist)
- Given a contract created by orgA, when orgB calls update on that contract, then it receives { error: 'Contract not found' }
- Given a contract created by orgA, when orgB calls delete on that contract, then it receives { error: 'Contract not found' }
- Given 2 contracts in orgA and 1 in orgB, when orgA calls listByOrg, then it receives exactly 2 contracts all with orgA's orgId

---

## E2E behaviors (tests/e2e/contracts-create-draft.spec.ts)

- Given an authenticated AM, when they navigate to /contracts, then they see a table with a "New Contract" button
- Given an authenticated AM on /contracts, when they click "New Contract", then they see the create contract form
- Given an AM on the create form who fills start date, AM, and contract type and clicks save, then the draft is persisted and appears in the contracts list
- Given a user without the contracts:create permission who attempts to create a contract, then they receive a 403 Forbidden response
- Given an unauthenticated visitor who navigates to /contracts/new, then they are redirected to /login

---

*Total: 19 behaviors*
*Test file correspondence: each bullet above maps to exactly one `it()` call in the test files*
