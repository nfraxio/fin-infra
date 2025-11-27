# ADR-0008: Financial Security, Secrets & PII Boundaries

**Status**: Accepted  
**Date**: 2025-11-05  
**Context**: Production readiness punch list Section 8  
**Related**: ADR-0003 (Banking), ADR-0004 (Market Data), ADR-0005 (Crypto), ADR-0006 (Brokerage), ADR-0007 (Normalization)

---

## Context

Financial applications handle highly sensitive personally identifiable information (PII) and must comply with regulations like PCI-DSS, SOC 2, and GDPR. Provider API tokens (Plaid, Alpaca, etc.) must be encrypted at rest and in transit.

### Key Requirements

1. **Financial PII Detection & Masking**: Automatically detect and mask sensitive data in logs
   - SSN (Social Security Numbers): `123-45-6789`
   - Bank account numbers: `1234567890`
   - Routing numbers (ABA): `021000021`
   - Credit card numbers (PAN): `4111 1111 1111 1111`
   - CVV codes: `123`
   - Driver's license numbers
   - Tax IDs (EIN): `12-3456789`

2. **Provider Token Encryption**: Secure storage for API credentials
   - Plaid access tokens (banking)
   - Alpaca API keys (brokerage)
   - Alpha Vantage keys (market data)
   - CoinGecko API keys (crypto)
   - exchangerate-api.io keys (currency conversion)

3. **Compliance**: Meet regulatory requirements
   - **PCI-DSS**: Credit card data protection
   - **SOC 2 Type II**: Security controls
   - **GDPR**: EU data privacy
   - **GLBA**: Financial privacy (US)
   - **CCPA**: California consumer privacy

4. **Audit Trail**: Log access to sensitive data
   - Who accessed what PII
   - When was it accessed
   - What operations were performed
   - Immutable audit logs

### Critical Considerations

- **Logging Safety**: Never log SSN, full card numbers, or account numbers
- **Encryption at Rest**: Provider tokens in database must be encrypted
- **Encryption in Transit**: HTTPS for all provider API calls
- **Key Management**: Secure storage for encryption keys (env vars, KMS)
- **Zero-Knowledge**: Minimize PII exposure in application code

---

## svc-infra Reuse Assessment

### Research Findings

**Searched for**:
- PII masking: `grep -r "pii|mask|redact" svc-infra/src/` → No results
- Token encryption: `grep -r "encrypt|decrypt" svc-infra/src/` → No results
- Security headers: `svc-infra/src/svc_infra/security/headers.py` → Generic security headers (CSP, HSTS, etc.)
- Password hashing: `svc-infra/src/svc_infra/security/passwords.py` → Argon2 password hashing
- JWT tokens: `svc-infra/src/svc_infra/security/jwt_rotation.py` → JWT rotation patterns
- Audit logs: `svc-infra/src/svc_infra/security/audit.py` → Generic audit trails

**Classification**: **Type B** (Financial-specific PII + Generic Security)

**Justification**:
- svc-infra provides: Generic auth, password hashing, JWT, audit trails, security headers
- fin-infra needs: Financial PII detection (SSN, account numbers, card numbers), provider token encryption
- Financial PII patterns are domain-specific (regex for SSN, routing numbers, etc.)
- Provider token encryption is financial-specific (Plaid, Alpaca, Alpha Vantage)

**Reuse Plan**:
- ✅ Use `svc_infra.api.fastapi.auth` for authentication/authorization
- ✅ Use `svc_infra.security.passwords` for password hashing (not needed for providers)
- ✅ Use `svc_infra.security.audit` for audit trails (extend with PII access logs)
- ✅ Use `svc_infra.logging.setup_logging` as base (extend with PII filters)
- ✅ Use `svc_infra.db` for token storage (add encryption layer)
- ✅ Use `svc_infra.http` for HTTPS provider calls (already secure)
- ❌ Financial PII detection: NOT in svc-infra (implement in fin-infra)
- ❌ Provider token encryption: NOT in svc-infra (implement in fin-infra)

### svc-infra Integration Points

```python
# Extend svc-infra logging with PII filters
from svc_infra.logging import setup_logging
from fin_infra.security.pii_filter import FinancialPIIFilter

setup_logging(level="INFO")
logging.getLogger().addFilter(FinancialPIIFilter())

# Use svc-infra audit with PII access tracking
from svc_infra.security.audit import log_audit_event
from fin_infra.security.audit import log_pii_access

await log_pii_access(
    user_id=user.id,
    pii_type="ssn",
    action="read",
    resource="banking_account"
)

# Use svc-infra DB with encryption
from svc_infra.db import get_db
from fin_infra.security.encryption import encrypt_token, decrypt_token

encrypted = encrypt_token(plaid_access_token, user_id)
db.execute("INSERT INTO provider_tokens VALUES (..., encrypted)")
```

---

## Decision

### Architecture Overview

Implement **two-layer security architecture**:

1. **PII Masking Layer**: Logging filter that detects and masks financial PII
2. **Token Encryption Layer**: Encrypt provider API tokens at rest

Both extend svc-infra's existing security primitives without duplicating functionality.

### Financial PII Masking

**Capabilities**:
```python
class FinancialPIIFilter(logging.Filter):
    """Logging filter that masks financial PII."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask PII in log message before emission."""
        # SSN: 123-45-6789 → ***-**-6789
        # Account: 1234567890 → ******7890
        # Routing: 021000021 → ******021
        # Card: 4111 1111 1111 1111 → **** **** **** 1111
        # CVV: 123 → ***
        record.msg = self._mask_pii(record.msg)
        return True
```

**PII Patterns Detected** (regex-based):

| PII Type | Pattern | Masked Format | Example |
|----------|---------|---------------|---------|
| **SSN** | `\d{3}-\d{2}-\d{4}` | `***-**-XXXX` | `***-**-6789` |
| **SSN (no dash)** | `\d{9}` (context) | `*****XXXX` | `*****6789` |
| **Account Number** | `\d{8,17}` | `******XXXX` | `******7890` |
| **Routing Number** | `\d{9}` (ABA format) | `******XXX` | `******021` |
| **Credit Card** | Luhn algorithm | `**** **** **** XXXX` | `**** **** **** 1111` |
| **CVV** | `\d{3,4}` (context) | `***` or `****` | `***` |
| **Driver's License** | State-specific patterns | `**XXXXXXX` | `**G123456` |
| **Tax ID (EIN)** | `\d{2}-\d{7}` | `**-****XXX` | `**-****789` |

**Implementation**:
```python
import re
import logging

class FinancialPIIFilter(logging.Filter):
    """Mask financial PII in log messages."""
    
    # Regex patterns
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    SSN_NO_DASH = re.compile(r'\b\d{9}\b')
    ACCOUNT_PATTERN = re.compile(r'\b\d{8,17}\b')
    ROUTING_PATTERN = re.compile(r'\b\d{9}\b')  # Overlap with SSN
    CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    CVV_PATTERN = re.compile(r'\b\d{3,4}\b')
    EIN_PATTERN = re.compile(r'\b\d{2}-\d{7}\b')
    
    def _mask_ssn(self, text: str) -> str:
        """Mask SSN: 123-45-6789 → ***-**-6789"""
        return self.SSN_PATTERN.sub(
            lambda m: f"***-**-{m.group()[-4:]}",
            text
        )
    
    def _mask_account(self, text: str) -> str:
        """Mask account: 1234567890 → ******7890"""
        return self.ACCOUNT_PATTERN.sub(
            lambda m: f"{'*' * (len(m.group()) - 4)}{m.group()[-4:]}",
            text
        )
    
    def _mask_card(self, text: str) -> str:
        """Mask card: 4111 1111 1111 1111 → **** **** **** 1111"""
        def mask_match(m):
            digits = m.group().replace(' ', '').replace('-', '')
            if self._is_valid_card(digits):
                return f"**** **** **** {digits[-4:]}"
            return m.group()  # Not a valid card
        return self.CARD_PATTERN.sub(mask_match, text)
    
    def _is_valid_card(self, number: str) -> bool:
        """Luhn algorithm to validate card numbers."""
        digits = [int(d) for d in number]
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask all PII in log record."""
        if isinstance(record.msg, str):
            record.msg = self._mask_ssn(record.msg)
            record.msg = self._mask_account(record.msg)
            record.msg = self._mask_card(record.msg)
            # Add more masking as needed
        return True
```

### Provider Token Encryption

**Capabilities**:
```python
from cryptography.fernet import Fernet

class ProviderTokenEncryption:
    """Encrypt/decrypt provider API tokens."""
    
    def __init__(self, key: bytes):
        """Initialize with encryption key from env/KMS."""
        self._fernet = Fernet(key)
    
    def encrypt(self, token: str, context: dict) -> str:
        """Encrypt token with context (user_id, provider)."""
        # Add context to prevent token reuse across users
        data = json.dumps({"token": token, "context": context})
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted: str, context: dict) -> str:
        """Decrypt token and verify context."""
        decoded = base64.urlsafe_b64decode(encrypted.encode())
        data = json.loads(self._fernet.decrypt(decoded).decode())
        
        # Verify context matches
        if data["context"] != context:
            raise ValueError("Context mismatch")
        
        return data["token"]
```

**Key Management**:
- **Development**: `PROVIDER_TOKEN_ENCRYPTION_KEY` environment variable
- **Production**: AWS KMS, Google Cloud KMS, Azure Key Vault
- **Key Rotation**: Support multiple active keys (key ID in encrypted data)

**Database Schema**:
```sql
CREATE TABLE provider_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'plaid', 'alpaca', 'alphavantage'
    encrypted_token TEXT NOT NULL,  -- Fernet-encrypted token
    key_id VARCHAR(50),             -- For key rotation
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(user_id, provider)
);

-- Audit log for token access
CREATE TABLE provider_token_access_log (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'read', 'write', 'delete'
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Easy Builder Pattern

**One-liner setup**:
```python
from fastapi import FastAPI
from fin_infra.security import add_financial_security

app = FastAPI()

# Configure financial security (PII masking + token encryption)
add_financial_security(
    app,
    encryption_key="your-key-here",  # From env: PROVIDER_TOKEN_ENCRYPTION_KEY
    enable_pii_filter=True,          # Add PII filter to loggers
    enable_audit_log=True,           # Log PII access
)
```

**Configuration via environment**:
```bash
# Required
PROVIDER_TOKEN_ENCRYPTION_KEY=<base64-encoded-32-byte-key>

# Optional
FINANCIAL_PII_FILTER_ENABLED=true
FINANCIAL_AUDIT_LOG_ENABLED=true
FINANCIAL_PII_RETENTION_DAYS=90  # Auto-delete old PII access logs
```

---

## Consequences

### Positive

1. **Compliance-Ready**: Meets PCI-DSS, SOC 2, GDPR requirements
2. **Zero PII Leaks**: Automatic masking prevents SSN/account numbers in logs
3. **Secure Token Storage**: Provider tokens encrypted at rest
4. **Audit Trail**: Track all PII access for compliance
5. **Reuses svc-infra**: Extends existing security, doesn't duplicate
6. **Easy Setup**: One-line `add_financial_security()` configuration
7. **Key Rotation**: Support multiple encryption keys
8. **Provider-Agnostic**: Works with all financial providers

### Negative

1. **Performance Overhead**: Regex matching on every log message
2. **False Positives**: May mask non-PII numbers (e.g., order IDs)
3. **Key Management**: Requires secure key storage (KMS in production)
4. **Storage Overhead**: Encrypted tokens larger than plaintext
5. **Complexity**: Adds encryption/decryption layer to token operations
6. **Key Loss**: Encrypted tokens unrecoverable if key lost

### Neutral

1. **Regex Tuning**: May need adjustment for edge cases
2. **Audit Log Size**: PII access logs grow over time (need retention policy)
3. **Migration**: Existing plaintext tokens need re-encryption
4. **Testing**: Need comprehensive test coverage for all PII patterns

---

## Implementation Notes

### Module Structure

```
src/fin_infra/
  security/
    __init__.py           # add_financial_security() builder
    pii_filter.py         # FinancialPIIFilter logging filter
    pii_patterns.py       # Regex patterns for PII detection
    encryption.py         # ProviderTokenEncryption class
    token_store.py        # Database operations for tokens
    audit.py              # PII access audit logging
    models.py             # Pydantic models
```

### PII Detection Patterns

```python
# security/pii_patterns.py
import re

# Social Security Number (SSN)
SSN_PATTERN = re.compile(
    r'\b\d{3}-\d{2}-\d{4}\b',  # With dashes
    re.IGNORECASE
)

SSN_NO_DASH = re.compile(
    r'\b\d{9}\b',  # Without dashes (needs context)
    re.IGNORECASE
)

# Bank Account Number (8-17 digits)
ACCOUNT_PATTERN = re.compile(
    r'\b\d{8,17}\b',
    re.IGNORECASE
)

# ABA Routing Number (9 digits)
ROUTING_PATTERN = re.compile(
    r'\b\d{9}\b',
    re.IGNORECASE
)

# Credit Card (with Luhn validation)
CARD_PATTERN = re.compile(
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    re.IGNORECASE
)

# CVV (3-4 digits, context-dependent)
CVV_PATTERN = re.compile(
    r'\b\d{3,4}\b',
    re.IGNORECASE
)

# Tax ID / EIN
EIN_PATTERN = re.compile(
    r'\b\d{2}-\d{7}\b',
    re.IGNORECASE
)
```

### Encryption Key Generation

```python
from cryptography.fernet import Fernet

# Generate new encryption key (one-time, store securely)
key = Fernet.generate_key()
print(f"PROVIDER_TOKEN_ENCRYPTION_KEY={key.decode()}")
```

### Token Storage Example

```python
from fin_infra.security import ProviderTokenEncryption
from sqlalchemy import select

encryption = ProviderTokenEncryption(key=os.getenv("PROVIDER_TOKEN_ENCRYPTION_KEY"))

# Store encrypted token
async def store_provider_token(
    db: AsyncSession,
    user_id: str,
    provider: str,
    token: str
):
    context = {"user_id": user_id, "provider": provider}
    encrypted = encryption.encrypt(token, context)
    
    stmt = """
        INSERT INTO provider_tokens (user_id, provider, encrypted_token)
        VALUES (:user_id, :provider, :encrypted_token)
        ON CONFLICT (user_id, provider) DO UPDATE
        SET encrypted_token = :encrypted_token
    """
    await db.execute(stmt, {
        "user_id": user_id,
        "provider": provider,
        "encrypted_token": encrypted
    })
    await db.commit()

# Retrieve decrypted token
async def get_provider_token(
    db: AsyncSession,
    user_id: str,
    provider: str
) -> str:
    result = await db.execute(
        select(ProviderToken.encrypted_token)
        .where(ProviderToken.user_id == user_id)
        .where(ProviderToken.provider == provider)
    )
    row = result.one_or_none()
    if not row:
        raise ValueError("Token not found")
    
    context = {"user_id": user_id, "provider": provider}
    return encryption.decrypt(row.encrypted_token, context)
```

---

## Example Integrations

### 1. Complete Security Setup

```python
from fastapi import FastAPI
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.logging import setup_logging
from fin_infra.security import add_financial_security

# Create app
app = easy_service_app(name="FinanceAPI")

# Setup base logging (svc-infra)
setup_logging(level="INFO")

# Add financial security (fin-infra)
add_financial_security(
    app,
    encryption_key=os.getenv("PROVIDER_TOKEN_ENCRYPTION_KEY"),
    enable_pii_filter=True,
    enable_audit_log=True,
)

# Now all logs are PII-safe, tokens are encrypted
```

### 2. Secure Provider Token Usage

```python
from fin_infra.banking import easy_banking
from fin_infra.security import get_provider_token, store_provider_token

@app.post("/banking/link")
async def link_bank_account(
    public_token: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Exchange Plaid public token for access token and store securely."""
    banking = easy_banking(provider="plaid")
    
    # Exchange public token (from Plaid Link)
    exchange_result = await banking.exchange_public_token(public_token)
    access_token = exchange_result["access_token"]
    
    # Store encrypted in database
    await store_provider_token(db, user_id, "plaid", access_token)
    
    return {"status": "linked"}

@app.get("/banking/accounts")
async def get_accounts(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get banking accounts using encrypted token."""
    # Retrieve and decrypt token
    access_token = await get_provider_token(db, user_id, "plaid")
    
    banking = easy_banking(provider="plaid")
    accounts = await banking.get_accounts(access_token)
    
    return accounts
```

### 3. PII-Safe Logging

```python
import logging

logger = logging.getLogger(__name__)

# Before: Logs expose PII
logger.info(f"Processing SSN: 123-45-6789")
# Output: Processing SSN: 123-45-6789  ❌ PII LEAKED

# After: PII automatically masked
logger.info(f"Processing SSN: 123-45-6789")
# Output: Processing SSN: ***-**-6789  ✅ PII MASKED

# Account numbers masked
logger.info(f"Account: 1234567890")
# Output: Account: ******7890

# Card numbers masked
logger.info(f"Card: 4111 1111 1111 1111")
# Output: Card: **** **** **** 1111
```

### 4. Audit PII Access

```python
from fin_infra.security.audit import log_pii_access

async def view_user_ssn(user_id: str, requesting_user_id: str):
    """View SSN with audit logging."""
    # Log access attempt
    await log_pii_access(
        user_id=requesting_user_id,
        pii_type="ssn",
        action="read",
        resource=f"user:{user_id}",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Retrieve SSN (from encrypted storage)
    ssn = await get_user_ssn(user_id)
    
    return {"ssn": ssn}
```

---

## Future Enhancements

1. **Additional PII Types**: Passport numbers, ITIN, biometric data
2. **Geographic Patterns**: International phone numbers, postal codes
3. **Field-Level Encryption**: Encrypt specific DB columns (not just tokens)
4. **Tokenization**: Replace sensitive data with random tokens
5. **Data Loss Prevention (DLP)**: Block API responses with PII
6. **Key Rotation**: Automated key rotation schedule
7. **Hardware Security Modules (HSM)**: Integration for key storage
8. **Anonymization**: Hash PII for analytics (k-anonymity)
9. **Right to Deletion**: GDPR-compliant PII deletion
10. **PII Discovery**: Scan database for unencrypted PII

---

## Related Documentation

- [svc-infra Security](../../../../svc-infra/src/svc_infra/security/)
- [svc-infra Audit Logging](../../../../svc-infra/src/svc_infra/security/audit.py)
- [svc-infra Logging](../../../../svc-infra/src/svc_infra/logging/)
- [Banking Provider Guide](../banking.md)
- [Brokerage Provider Guide](../brokerage.md)
- [PCI-DSS Requirements](https://www.pcisecuritystandards.org/)
- [GDPR Compliance](https://gdpr.eu/)

---

## References

- **PCI-DSS v4.0**: https://www.pcisecuritystandards.org/
- **GDPR**: https://gdpr.eu/
- **GLBA**: https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act
- **SOC 2**: https://www.aicpa.org/soc2
- **Python cryptography**: https://cryptography.io/
- **Fernet (symmetric encryption)**: https://cryptography.io/en/latest/fernet/
