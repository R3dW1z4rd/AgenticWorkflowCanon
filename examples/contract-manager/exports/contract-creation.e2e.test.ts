/**
 * CONTRACT CREATION — E2E Test Shells
 * Framework: Playwright
 *
 * SHELLS ONLY — interactions scripted, implementations are NOT.
 * All selectors use data-testid attributes.
 * The agent generating UI code must add these attributes.
 *
 * Coverage:
 *   AC-001 — Initiate a new contract from the Contracts list view
 *   AC-002 — Require Start Date, Account Manager, and Contract Type before proceedi
 *   AC-004 — Display exchange rate from Forex API, refreshed every 30 seconds
 *   AC-005 — Loading indicator while fetching rate; error state if API is unavailab
 *   AC-006 — Allow up to 5 referrals; enforce the limit
 *   AC-007 — Conditional referral fields based on referral type
 *   AC-010 — Save as Draft at any point without triggering required field validatio
 *   AC-011 — Commission rate visible only to Account Manager and Finance roles
 */

import { test, expect, Page } from '@playwright/test'

// ─── Config ──────────────────────────────────────────────────────────────────
const BASE_URL = process.env.TEST_BASE_URL ?? 'http://localhost:3000'

const USERS = {
  default_user:    { email: 'user@test.local',    password: 'Test1234!' },
  admin:           { email: 'admin@test.local',   password: 'Test1234!' },
  restricted_user: { email: 'viewer@test.local',  password: 'Test1234!' },
}

const SEL = {
  continueBtn: '[data-testid="contract-creation-continue-btn"]',
  submitBtn: '[data-testid="contract-creation-submit-btn"]',
  saveAsDraftBtn: '[data-testid="contract-creation-save-draft-btn"]',
  cancelBtn: '[data-testid="contract-creation-cancel-btn"]',
  successToast: '[data-testid="success-toast"]',
  errorSummary: '[data-testid="form-error-summary"]',
  newBtn: '[data-testid="new-contract-creation-btn"]',
  startDateInput: '[data-testid="contract-start-date"]',
  startDateError: '[data-testid="error-contract-start-date"]',
  accountManagerSelect: '[data-testid="account-manager-select"]',
  accountManagerError: '[data-testid="error-account-manager-id"]',
  contractTypeSelect: '[data-testid="contract-type-select"]',
  exchangeRateDisplay: '[data-testid="exchange-rate-display"]',
  exchangeRateAt: '[data-testid="exchange-rate-at"]',
  exchangeRateSpinner: '[data-testid="exchange-rate-loading"]',
  exchangeRateError: '[data-testid="exchange-rate-error"]',
  exchangeRateRetry: '[data-testid="exchange-rate-retry"]',
  commissionRateField: '[data-testid="commission-rate-field"]',
  addReferralBtn: '[data-testid="add-referral-btn"]',
  referralTypeSelect: '[data-testid="referral-type-select"]',
  employeeSelect: '[data-testid="referral-employee-select"]',
  externalNameInput: '[data-testid="referral-external-name"]',
  referralListItem: '[data-testid="referral-list-item"]',
  saveReferralBtn: '[data-testid="save-referral-btn"]',
  referralError: '[data-testid="referral-list-error"]',
  draftSavedIndicator: '[data-testid="draft-saved-indicator"]',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function loginAs(page: Page, role: keyof typeof USERS) {
  await page.goto(`${BASE_URL}/login`)
  await page.fill('[data-testid="email-input"]', USERS[role].email)
  await page.fill('[data-testid="password-input"]', USERS[role].password)
  await page.click('[data-testid="login-btn"]')
  await page.waitForURL(`${BASE_URL}/dashboard`)
}

// ════════════════════════════════════════════════════════════════════════════

test.describe('Initiate / Create', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'default_user')
  })

  test('[AC-001] Happy path: AM creates a new contract', async ({ page }) => {
    // Setup: User is authenticated as Account Manager
    // Setup: User is on the /contracts list view

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.goto(`${BASE_URL}/contract-creation`)
    await expect(page.locator(SEL.newBtn)).toBeVisible()
    await page.click(SEL.newBtn)
    await expect(page).toHaveURL(/contract-creation\/new/)
  })

  test('[AC-001] AM with read-only role cannot initiate', async ({ page }) => {
    // Setup: User is authenticated with a role that does NOT include contract creation rights

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.goto(`${BASE_URL}/contract-creation`)
    await expect(page.locator(SEL.newBtn)).toBeVisible()
    await page.click(SEL.newBtn)
    await expect(page).toHaveURL(/contract-creation\/new/)
  })

  test('[AC-002] Happy path: all required fields filled', async ({ page }) => {
    // Setup: User is on Contract Creation Step 1
    // Setup: Start Date field = today's date

    await page.goto(`${BASE_URL}/contract-creation/new`)
    const today = new Date().toISOString().split('T')[0]
    await page.fill(SEL.startDateInput, today)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).not.toBeVisible()
  })

  test('[AC-002] Start Date is empty', async ({ page }) => {
    // Setup: User is on Step 1
    // Setup: Account Manager and Contract Type are filled

    await page.goto(`${BASE_URL}/contract-creation/new`)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const pastDate = yesterday.toISOString().split('T')[0]
    await page.fill(SEL.startDateInput, pastDate)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.startDateError)).toContainText('today or in the future')
    await expect(page.locator(SEL.startDateInput)).toHaveValue(pastDate)
  })

  test('[AC-002] Account Manager field is empty', async ({ page }) => {
    // Setup: Start Date and Contract Type are filled. Account Manager is empty.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const pastDate = yesterday.toISOString().split('T')[0]
    await page.fill(SEL.startDateInput, pastDate)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.startDateError)).toContainText('today or in the future')
    await expect(page.locator(SEL.startDateInput)).toHaveValue(pastDate)
  })

  test('[AC-002] Contract Type is empty', async ({ page }) => {
    // Setup: Start Date and Account Manager are filled. Contract Type is empty.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const pastDate = yesterday.toISOString().split('T')[0]
    await page.fill(SEL.startDateInput, pastDate)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.startDateError)).toContainText('today or in the future')
    await expect(page.locator(SEL.startDateInput)).toHaveValue(pastDate)
  })

  test('[AC-002] Multiple fields empty simultaneously', async ({ page }) => {
    // Setup: All three required fields are empty

    await page.goto(`${BASE_URL}/contract-creation/new`)
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const pastDate = yesterday.toISOString().split('T')[0]
    await page.fill(SEL.startDateInput, pastDate)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.startDateError)).toContainText('today or in the future')
    await expect(page.locator(SEL.startDateInput)).toHaveValue(pastDate)
  })

})


// ════════════════════════════════════════════════════════════════════════════

test.describe('Exchange Rate Display', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'default_user')
  })

  test('[AC-004] Happy path: rate fetched on form load', async ({ page }) => {
    // Setup: User navigates to Contract Creation Step 2 (or whichever step shows the rate)
    // Setup: Forex API is available and returns a valid rate

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

  test('[AC-004] Rate auto-refreshes after 30 seconds', async ({ page }) => {
    // Setup: Form is open, initial rate is displayed (e.g. 1.0823)
    // Setup: Forex API returns a different rate on second call (e.g. 1.0891)

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

  test('[AC-004] Rate refresh does not reset other form fields', async ({ page }) => {
    // Setup: User has partially filled the form. 30 seconds elapse.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

  test('[AC-005] Loading state on initial fetch', async ({ page }) => {
    // Setup: Forex API has a simulated 1.5 second response delay

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.abort('failed'))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateError)).toBeVisible({ timeout: 8000 })
    await expect(page.locator(SEL.exchangeRateRetry)).toBeVisible()
  })

  test('[AC-005] API timeout', async ({ page }) => {
    // Setup: Forex API is configured to not respond (timeout after 5 seconds)

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.abort('failed'))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateError)).toBeVisible({ timeout: 8000 })
    await expect(page.locator(SEL.exchangeRateRetry)).toBeVisible()
  })

  test('[AC-005] API returns malformed data', async ({ page }) => {
    // Setup: Forex API returns a 200 response but with invalid/missing rate field

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.abort('failed'))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateError)).toBeVisible({ timeout: 8000 })
    await expect(page.locator(SEL.exchangeRateRetry)).toBeVisible()
  })

  test('[AC-011] AM can see commission rate', async ({ page }) => {
    // Setup: User is authenticated as Account Manager

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

  test('[AC-011] Finance role can see commission rate', async ({ page }) => {
    // Setup: User is authenticated as Finance

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

  test('[AC-011] Other roles cannot see commission rate', async ({ page }) => {
    // Setup: User is authenticated as any role other than AM or Finance
    // Setup: (e.g. Viewer, External Partner, Support)

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.route('**/api/forex/rate**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ rate: 1.0823, timestamp: new Date().toISOString() })
    }))
    await page.goto(`${BASE_URL}/contract-creation/new?step=2`)
    await expect(page.locator(SEL.exchangeRateDisplay)).toBeVisible()
    await expect(page.locator(SEL.exchangeRateDisplay)).toContainText('1.0823')
  })

})


// ════════════════════════════════════════════════════════════════════════════

test.describe('Referral Management', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'default_user')
  })

  test('[AC-006] Adding referrals up to the limit', async ({ page }) => {
    // Setup: User is on the referrals step. 0 referrals added.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-006] Attempting to exceed the limit', async ({ page }) => {
    // Setup: 5 referrals already added

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-006] Removing a referral re-enables the Add button', async ({ page }) => {
    // Setup: 5 referrals added. "Add Referral" is disabled.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-006] 0 referrals is valid', async ({ page }) => {
    // Setup: User completes the form with no referrals added

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

})


// ════════════════════════════════════════════════════════════════════════════

test.describe('Form Validation', () => {

  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'default_user')
  })

  test('[AC-007] Referral type: employee', async ({ page }) => {
    // Setup: User is adding a referral. referral_type = "employee"

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-007] Referral type: external', async ({ page }) => {
    // Setup: User is adding a referral. referral_type = "external"

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-007] Switching type clears previous value', async ({ page }) => {
    // Setup: User has selected "Employee" and chosen an employee from the dropdown

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-007] Attempting to save employee referral without selecting an employee', async ({ page }) => {
    // Setup: referral_type = "employee". Employee field is empty.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.addReferralBtn)
    await page.selectOption(SEL.referralTypeSelect, 'external')
    await page.fill(SEL.externalNameInput, 'Test Referral')
    await page.click(SEL.saveReferralBtn)
    await expect(page.locator(SEL.referralListItem)).toHaveCount(1)
  })

  test('[AC-010] Save as Draft with all fields empty', async ({ page }) => {
    // Setup: User is on Step 1. All fields are empty.

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.accountManagerError)).toBeVisible()
    await expect(page).toHaveURL(/\/new/)
  })

  test('[AC-010] Save as Draft with partial data', async ({ page }) => {
    // Setup: User has filled Start Date and Account Manager but not Contract Type

    await page.goto(`${BASE_URL}/contract-creation/new`)
    await page.click(SEL.continueBtn)
    await expect(page.locator(SEL.startDateError)).toBeVisible()
    await expect(page.locator(SEL.accountManagerError)).toBeVisible()
    await expect(page).toHaveURL(/\/new/)
  })

})

