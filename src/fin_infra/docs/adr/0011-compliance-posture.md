# ADR 0011: Compliance Posture and PII Boundaries

**Status**: Accepted  
**Date**: 2025-11-06  
**Authors**: fin-infra team

## Context

fin-infra handles sensitive financial data from third-party providers (Plaid, Teller, Alpha Vantage, etc.). Applications using fin-infra must comply with:

- **GLBA** (Gramm-Leach-Bliley Act): Financial PII protection
- **FCRA** (Fair Credit Reporting Act): Credit report handling
- **PCI-DSS**: Payment card data security (when handling cards)
- **Provider Terms of Service**: Plaid, Teller, Alpha Vantage, etc.

This ADR defines:
1. What data fin-infra handles and classifies as PII
2. Compliance boundaries and responsibilities
3. Integration with svc-infra for data lifecycle management
4. Vendor requirements and restrictions

## Decision

### 1. PII Classification

#### Tier 1: High-Sensitivity PII (GLBA/FCRA regulated)
- Account numbers (checking, savings, credit cards)
- Routing numbers
- SSN/Tax ID (full or last 4 digits)
- Credit scores and credit reports
- Authentication tokens (access_token, refresh_token from banking providers)
- Identity information (full name, DOB, address when linked to financial accounts)

#### Tier 2: Moderate-Sensitivity Financial Data
- Transaction history (amounts, dates, merchants, categories)
- Account balances
- Holdings (stocks, crypto)
- Market quotes and portfolio valuations

#### Tier 3: Public/Low-Sensitivity Data
- Market data (stock quotes, crypto prices) - publicly available
- Provider metadata (institution names, product types)
- Aggregated/anonymized analytics

### 2. Compliance Boundaries

**fin-infra Responsibilities**:
- ✅ Provide clear PII markers in code (`# PII: ...` comments)
- ✅ Document vendor ToS requirements (no data resale, attribution)
- ✅ Expose data lifecycle helpers (retention, erasure via svc-infra.data)
- ✅ Support encryption at rest/in transit (HTTPS, TLS for Teller mTLS)
- ✅ Provide compliance tracking helper (`add_compliance_tracking`)
- ✅ Document recommended retention policies

**Application Responsibilities** (using fin-infra):
- ❌ Implementing actual encryption at rest (use svc-infra DB encryption)
- ❌ Running retention jobs (use svc-infra.jobs scheduler)
- ❌ GDPR erasure execution (use svc-infra.data erasure plans)
- ❌ Legal compliance sign-off (consult legal counsel)
- ❌ SOC2/HIPAA certification (application-level certification)

### 3. Vendor ToS Requirements

#### Plaid
- **No data resale**: Cannot sell user financial data to third parties
- **Limited retention**: Delete data when user deletes account or revokes access
- **Attribution**: Must display "Powered by Plaid" or similar
- **Security**: Must use HTTPS, store tokens securely
- **Reference**: https://plaid.com/legal/#end-user-privacy-policy

#### Teller
- **No data resale**: Financial data is user property
- **Minimal retention**: Recommend deleting access tokens after use or on user request
- **mTLS requirement**: Certificate-based auth for production
- **Reference**: https://teller.io/legal

#### Alpha Vantage
- **Attribution**: Must credit Alpha Vantage for market data
- **Rate limits**: Free tier 25 requests/day, respect limits
- **No redistribution**: Cannot resell or redistribute raw data
- **Reference**: https://www.alphavantage.co/terms_of_use/

### 4. Data Lifecycle Integration (svc-infra.data)

fin-infra integrates with svc-infra's data lifecycle management:

**Retention Policies** (use `svc_infra.data.retention`):
```python
from svc_infra.data import RetentionPolicy

# Example: Purge old transactions after 7 years (GLBA requirement)
transaction_retention = RetentionPolicy(
    name="financial_transactions",
    model=Transaction,  # Your SQLAlchemy model
    older_than_days=7 * 365,  # 7 years
    soft_delete_field="deleted_at",
    hard_delete=False,  # Soft delete first
)

# Schedule with svc-infra.jobs
from svc_infra.jobs import easy_jobs
worker, scheduler = easy_jobs(app, retention_policies=[transaction_retention])
```

**Erasure Plans** (use `svc_infra.data.erasure`):
```python
from svc_infra.data import ErasurePlan, ErasureStep

# Example: GDPR erasure for user financial data
async def erase_banking_tokens(session, user_id):
    # Delete provider access tokens
    stmt = delete(BankingToken).where(BankingToken.user_id == user_id)
    result = await session.execute(stmt)
    return result.rowcount

erasure_plan = ErasurePlan(
    steps=[
        ErasureStep("banking_tokens", erase_banking_tokens),
        ErasureStep("transactions", erase_user_transactions),
        ErasureStep("accounts", erase_user_accounts),
    ]
)

# Execute erasure
from svc_infra.data import run_erasure
affected = await run_erasure(session, user_id="user123", plan=erasure_plan)
```

### 5. Recommended Retention Periods

| Data Type | Minimum | Recommended | Justification |
|-----------|---------|-------------|---------------|
| Banking tokens | Until revoked | 90 days inactive | Minimize breach exposure |
| Transactions | 7 years | 7 years | GLBA, tax records |
| Credit reports | Until user deletes | 2 years | FCRA compliance |
| Market data | N/A (public) | Cache: 15 min | Real-time pricing |
| Identity data | Until user deletes | Match account lifecycle | GLBA |

### 6. PII Marking Convention

Code handling PII must include comments:

```python
# PII: account_number (GLBA Tier 1)
def store_account(account_number: str):
    # Encrypt before storage
    pass

# PII: ssn_last4 (FCRA Tier 1)
def verify_identity(ssn_last4: str):
    pass

# PII: transactions (GLBA Tier 2)
def get_transaction_history(user_id: str):
    pass
```

### 7. Compliance Tracking Events

Use `add_compliance_tracking(app)` to log compliance events:

```python
from fin_infra.compliance import add_compliance_tracking

app = FastAPI()
add_compliance_tracking(app)

# Events logged automatically:
# - "banking.token_created": When access token issued
# - "banking.token_revoked": When user revokes access
# - "banking.data_accessed": When financial data fetched
# - "credit.report_accessed": When credit report retrieved
# - "erasure.requested": When user requests data deletion
# - "erasure.completed": When erasure plan finishes
```

## Consequences

### Positive
✅ Clear PII boundaries for audits and compliance reviews  
✅ Reuses svc-infra data lifecycle (retention, erasure) - no duplication  
✅ Vendor ToS requirements documented for legal review  
✅ Compliance tracking provides audit trail  
✅ Recommended retention periods guide production setup  

### Negative
⚠️ Applications still responsible for legal compliance sign-off  
⚠️ Retention policies require manual configuration (not auto-applied)  
⚠️ PII comments are convention, not enforced by tooling  
⚠️ Vendor ToS may change (requires periodic review)  

### Neutral
➖ Compliance is a shared responsibility (fin-infra + svc-infra + application)  
➖ Not a substitute for legal counsel or SOC2/HIPAA certification  
➖ fin-infra provides building blocks, not turnkey compliance  

## Alternatives Considered

**1. No PII marking**  
Rejected: Makes audits difficult, no visibility into sensitive data flow.

**2. Automatic encryption at rest**  
Rejected: svc-infra already provides DB encryption; would duplicate infrastructure.

**3. Built-in retention jobs**  
Rejected: svc-infra.jobs already provides scheduler; fin-infra defines policies only.

**4. Vendor ToS auto-enforcement**  
Rejected: ToS are legal contracts; automated enforcement is impossible (e.g., "no resale" requires business process controls).

## References

- GLBA: https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act
- FCRA: https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act
- PCI-DSS: https://www.pcisecuritystandards.org/
- svc-infra data lifecycle: `svc_infra.data` module
- Plaid Legal: https://plaid.com/legal/
- Teller Legal: https://teller.io/legal

## Implementation Status

- [x] ADR documented
- [ ] PII comments added to banking providers
- [ ] Compliance tracking helper (`add_compliance_tracking`) implemented
- [ ] docs/compliance.md created
- [ ] Retention policy examples in docs
- [ ] Erasure plan examples in docs
