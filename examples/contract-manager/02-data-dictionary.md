# Data Dictionary — Contract Manager

## Entity: contract

| field_name | fieldName | Display Label | Type | Required | Validation Rules | Default | Source | Integration / Module Ref | Enum Values | Used In | PII | Notes |
|------------|-----------|---------------|------|----------|-----------------|---------|--------|--------------------------|-------------|---------|-----|-------|
| contract_id | contractId | Contract ID | string | Yes | Auto-generated UUID | UUID v4 | system_generated | | | All views | No | Primary key |
| contract_start_date | contractStartDate | Start Date | date | Yes | Must not be in the past | Today | user_input | | | Create Form · Detail | No | |
| account_manager_id | accountManagerId | Account Manager | reference | Yes | Must be active AM user | | user_input | Users Module | | Create Form · List | No | FK → users |
| referral_type | referralType | Referral Type | enum | No | | none | user_input | | none · employee · external | Create Form | No | |
| exchange_rate | exchangeRate | Exchange Rate | decimal | Yes | 4 decimal places | | integration | Forex API (every 30s) | | Create Form · Detail | No | |
| status | status | Status | enum | Yes | | draft | system_generated | | draft · pending · active · expired · cancelled | All views | No | |
| commission_rate | commissionRate | Commission Rate | decimal | No | 0–100% | 0 | user_input | | | Create Form · Detail | Yes | Sensitive — AM and Finance only |
