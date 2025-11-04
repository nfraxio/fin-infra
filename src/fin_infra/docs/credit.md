# Credit Score Integration

fin-infra provides interfaces for fetching user credit scores, credit reports, and credit history from major credit bureaus and alternative data providers.

## Supported Providers

- **Experian**: Credit scores and full reports
- **Equifax**: Coming soon
- **TransUnion**: Coming soon
- **Stripe Identity**: Identity verification
- **Plaid Identity**: Identity verification via banking

## Quick Setup

```python
from fin_infra.credit import easy_credit

# Auto-configured from environment variables
credit = easy_credit()
```

## Core Operations

### 1. Get Credit Score
```python
from fin_infra.models.credit import CreditScore

score = await credit.get_credit_score(
    user_id="user_123",
    ssn="123-45-6789",  # Encrypted in transit
    date_of_birth="1990-01-01"
)

print(f"FICO Score: {score.fico_score}")
print(f"VantageScore: {score.vantage_score}")
print(f"Credit Grade: {score.credit_grade}")  # Excellent, Good, Fair, Poor
print(f"Last Updated: {score.updated_at}")
```

### 2. Get Full Credit Report
```python
report = await credit.get_credit_report(user_id="user_123")

print(f"Personal Info: {report.personal_info}")
print(f"Credit Score: {report.credit_score.fico_score}")
print(f"Total Accounts: {len(report.accounts)}")
print(f"Total Inquiries: {len(report.inquiries)}")
print(f"Public Records: {len(report.public_records)}")

# Credit accounts
for account in report.accounts:
    print(f"{account.creditor_name}: ${account.balance}")
    print(f"  Status: {account.status}")
    print(f"  Payment History: {account.payment_history}")

# Hard inquiries
for inquiry in report.inquiries:
    print(f"{inquiry.date}: {inquiry.creditor_name}")
```

### 3. Credit Monitoring
```python
# Subscribe to credit monitoring
subscription = await credit.subscribe_monitoring(
    user_id="user_123",
    alert_preferences={
        "score_change": True,
        "new_account": True,
        "hard_inquiry": True,
        "balance_change": True
    }
)

# Handle webhook alerts
@app.post("/webhooks/credit")
async def credit_webhook(request: Request):
    alert = await credit.parse_webhook(request)
    
    if alert.type == "score_change":
        print(f"Score changed: {alert.old_score} → {alert.new_score}")
    elif alert.type == "new_account":
        print(f"New account opened: {alert.account.creditor_name}")
    
    return {"status": "received"}
```

### 4. Identity Verification
```python
from fin_infra.credit import verify_identity

# Verify user identity before accessing credit data
verification = await verify_identity(
    user_id="user_123",
    full_name="John Doe",
    ssn="123-45-6789",
    date_of_birth="1990-01-01",
    address={
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94102"
    }
)

if verification.verified:
    # Proceed with credit check
    score = await credit.get_credit_score(...)
else:
    print(f"Verification failed: {verification.failure_reason}")
```

## Data Models

### CreditScore
```python
from fin_infra.models.credit import CreditScore, CreditGrade

class CreditScore:
    user_id: str
    fico_score: int | None  # 300-850
    vantage_score: int | None  # 300-850
    credit_grade: CreditGrade  # EXCELLENT, GOOD, FAIR, POOR, VERY_POOR
    score_factors: list[str]  # Factors affecting score
    updated_at: datetime
```

### CreditReport
```python
from fin_infra.models.credit import CreditReport

class CreditReport:
    user_id: str
    personal_info: PersonalInfo
    credit_score: CreditScore
    accounts: list[CreditAccount]
    inquiries: list[CreditInquiry]
    public_records: list[PublicRecord]
    collections: list[Collection]
    report_date: date
```

### CreditAccount
```python
class CreditAccount:
    account_id: str
    creditor_name: str
    account_type: str  # revolving, installment, mortgage
    balance: Decimal
    credit_limit: Decimal | None
    payment_status: str  # current, late, charged_off
    months_reviewed: int
    payment_history: list[PaymentHistory]
    opened_date: date
    closed_date: date | None
```

## Compliance & Security

### PCI DSS Compliance
```python
# Never log or store SSN unencrypted
from fin_infra.security import encrypt_pii, decrypt_pii

# Encrypt before storing
encrypted_ssn = encrypt_pii(ssn, key=settings.encryption_key)

# Decrypt when needed
ssn = decrypt_pii(encrypted_ssn, key=settings.encryption_key)
```

### FCRA Compliance
```python
# Fair Credit Reporting Act requirements
from fin_infra.credit.compliance import log_credit_pull

# Log every credit pull with permissible purpose
await log_credit_pull(
    user_id="user_123",
    purpose="credit_application",  # FCRA permissible purpose
    application_id="app_456",
    pulled_by="loan_officer_789"
)
```

### User Consent
```python
# Always get explicit user consent before pulling credit
from fin_infra.credit.consent import verify_consent

consent = await verify_consent(user_id="user_123")

if not consent.has_valid_consent:
    raise ValueError("User consent required for credit check")

if consent.is_expired:
    # Request new consent
    await request_consent(user_id="user_123")
```

## Error Handling

```python
from fin_infra.credit.exceptions import (
    CreditProviderError,
    IdentityVerificationError,
    InsufficientCreditHistoryError,
    ConsentRequiredError
)

try:
    score = await credit.get_credit_score(user_id="user_123")
except IdentityVerificationError:
    print("Identity verification failed")
except InsufficientCreditHistoryError:
    print("User has insufficient credit history")
except ConsentRequiredError:
    print("User consent required")
except CreditProviderError as e:
    print(f"Provider error: {e.message}")
```

## Best Practices

1. **User Consent**: Always obtain explicit user consent before pulling credit
2. **Data Minimization**: Only request data you actually need
3. **Encryption**: Encrypt PII at rest and in transit
4. **Audit Logging**: Log all credit pulls with purpose and timestamp
5. **Access Control**: Restrict credit data access to authorized personnel
6. **Data Retention**: Follow FCRA guidelines for data retention and disposal
7. **Adverse Action**: Provide adverse action notices when required
8. **Dispute Handling**: Implement process for users to dispute credit data

## Testing

```python
import pytest
from fin_infra.credit import easy_credit

@pytest.mark.asyncio
async def test_get_credit_score():
    credit = easy_credit()
    
    # Use test/sandbox credentials
    score = await credit.get_credit_score(
        user_id="test_user",
        ssn="666-00-0000",  # Test SSN
        date_of_birth="1990-01-01"
    )
    
    assert score.fico_score is not None
    assert 300 <= score.fico_score <= 850
```

## Next Steps

- [Banking Integration](banking.md)
- [Identity Verification](identity.md)
- [Tax Data Integration](tax.md)
