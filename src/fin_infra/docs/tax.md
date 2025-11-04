# Tax Data Integration

fin-infra provides interfaces for accessing tax documents, tax data, and tax calculations for fintech applications.

## Supported Providers

- **IRS e-File**: Direct IRS integration (coming soon)
- **TaxBit**: Crypto tax calculations
- **TurboTax**: Tax document import (coming soon)
- **H&R Block**: Tax document import (coming soon)

## Quick Setup

```python
from fin_infra.tax import easy_tax

# Auto-configured from environment variables
tax = easy_tax()
```

## Core Operations

### 1. Get Tax Documents
```python
from datetime import date

documents = await tax.get_tax_documents(
    user_id="user_123",
    tax_year=2024
)

for doc in documents:
    print(f"{doc.form_type}: {doc.name}")
    print(f"  Issuer: {doc.issuer}")
    print(f"  Download: {doc.download_url}")
```

### 2. Calculate Tax Liability
```python
liability = await tax.calculate_tax_liability(
    user_id="user_123",
    income=150000,
    deductions=25000,
    filing_status="single"
)

print(f"Taxable Income: ${liability.taxable_income}")
print(f"Total Tax: ${liability.total_tax}")
print(f"Effective Rate: {liability.effective_rate}%")
```

### 3. Crypto Tax Calculations
```python
crypto_taxes = await tax.calculate_crypto_taxes(
    user_id="user_123",
    transactions=crypto_transactions,
    tax_year=2024
)

print(f"Capital Gains: ${crypto_taxes.capital_gains}")
print(f"Short-term Gains: ${crypto_taxes.short_term_gains}")
print(f"Long-term Gains: ${crypto_taxes.long_term_gains}")
```

### 4. Tax Form Generation
```python
# Generate 1099-INT for interest income
form_1099 = await tax.generate_1099_int(
    user_id="user_123",
    interest_income=1250.00,
    tax_year=2024
)

# Download PDF
pdf_bytes = await tax.download_form(form_1099.form_id)
```

## Data Models

### TaxDocument
```python
from fin_infra.models.tax import TaxDocument

class TaxDocument:
    document_id: str
    user_id: str
    form_type: str  # W2, 1099-INT, 1099-DIV, 1099-B, etc.
    tax_year: int
    issuer: str
    download_url: str | None
    status: str  # pending, available, downloaded
    created_at: datetime
```

### TaxLiability
```python
class TaxLiability:
    taxable_income: Decimal
    total_tax: Decimal
    federal_tax: Decimal
    state_tax: Decimal
    effective_rate: Decimal
    marginal_rate: Decimal
```

## Compliance

### IRS Requirements
- Store tax documents for 7 years minimum
- Encrypt sensitive tax data
- Provide audit trail for all tax calculations
- Follow IRS e-File security standards

### Data Security
```python
from fin_infra.security import encrypt_tax_data

# Encrypt before storing
encrypted_data = encrypt_tax_data(
    ssn="123-45-6789",
    key=settings.encryption_key
)
```

## Best Practices

1. **Data Retention**: Store tax documents for legal minimum period
2. **Encryption**: Encrypt all tax-related PII
3. **Audit Trail**: Log all tax calculations and document access
4. **Compliance**: Stay updated with IRS regulations
5. **Professional Review**: Recommend CPA review for complex situations

## Testing

```python
import pytest
from fin_infra.tax import easy_tax

@pytest.mark.asyncio
async def test_calculate_tax():
    tax = easy_tax()
    
    liability = await tax.calculate_tax_liability(
        user_id="test_user",
        income=100000,
        deductions=12000,
        filing_status="single"
    )
    
    assert liability.total_tax > 0
```

## Next Steps

- [Banking Integration](banking.md)
- [Brokerage Integration](brokerage.md)
- [Credit Scores](credit.md)
