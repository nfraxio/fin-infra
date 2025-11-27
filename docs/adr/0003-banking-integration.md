# ADR 0003: Banking Integration Architecture

**Status**: Accepted  
**Date**: 2025-01-04  
**Owner**: fin-infra  
**Tags**: banking, providers, security, PII

## Context

fin-infra needs to provide account aggregation from banking providers (Teller, Plaid, MX) to enable fintech applications like Mint, YNAB, Personal Capital, and Credit Karma. This requires:

1. Provider abstraction for multiple banking APIs
2. Secure OAuth-style token flows
3. PII handling (account numbers, routing numbers, SSN)
4. Caching strategy for account/transaction data
5. Easy setup with sensible defaults

## svc-infra Reuse Assessment

**What was checked**:
- `svc-infra/src/svc_infra/billing/` - Usage tracking, subscriptions, invoicing (NOT bank aggregation)
- `svc-infra/src/svc_infra/apf_payments/` - Payment processing (Stripe/Adyen), NOT bank account linking
- `svc-infra/src/svc_infra/cache/` - Cache infrastructure (REUSE for account/transaction caching)
- `svc-infra/src/svc_infra/db/` - Database utilities (REUSE for token storage)
- `svc-infra/src/svc_infra/logging/` - Structured logging (REUSE for provider call logging)
- `svc-infra/src/svc_infra/http/` - HTTP client with retry (REUSE for provider API calls)
- `svc-infra/src/svc_infra/security/` - Security primitives (REUSE for token encryption)

**Why svc-infra's solution wasn't suitable**:
- svc-infra.billing is for internal subscription billing, not external bank account aggregation
- svc-infra.apf_payments is for payment processing (charges/refunds), not account data fetching
- Banking providers (Teller/Plaid/MX) are financial domain-specific and not generic backend infrastructure

**Which svc-infra modules are being reused**:
- `svc_infra.cache` - Cache account balances/transactions (60s TTL to reduce API calls)
- `svc_infra.db` - Store encrypted access tokens
- `svc_infra.logging` - Log provider calls with PII masking
- `svc_infra.http` - HTTP client with retry for provider APIs
- `svc_infra.security` - Token encryption at rest

## Provider Comparison

| Feature | Teller | Plaid | MX |
|---------|--------|-------|-----|
| **Pricing** | Free (100 conn/mo) | Free sandbox, $0.10-0.30/user prod | Enterprise only |
| **Auth Flow** | Direct access token | Link UI → token exchange | Connect widget |
| **Coverage** | US (5k+ institutions) | US/CA/EU (18k+ institutions) | US/CA (16k+ institutions) |
| **Sandbox** | Full free sandbox | Full free sandbox | With account |
| **SDK** | REST API (no SDK) | plaid-python (official) | mx-platform-python |
| **Rate Limits** | 100 req/min | Generous (varies by endpoint) | Custom |
| **Best For** | Dev, demos, MVPs | Production fintech apps | Enterprise |

**Decision: Teller as default**
- True free tier (no credit card required)
- Simpler auth flow (no UI embedding)
- Perfect for development and demos
- Plaid and MX as alternates for production

## Design Decisions

### 1. Provider Abstraction

Use existing `BankingProvider` ABC from `fin_infra/providers/base.py`:

```python
class BankingProvider(ABC):
    @abstractmethod
    def create_link_token(self, user_id: str) -> str:
        """Create a link/connect token for user to authenticate."""
        pass

    @abstractmethod
    def exchange_public_token(self, public_token: str) -> dict:
        """Exchange public token for access token."""
        pass

    @abstractmethod
    def accounts(self, access_token: str) -> list[dict]:
        """Fetch accounts for an access token."""
        pass
```

**Additional methods to add**:
```python
    @abstractmethod
    def transactions(
        self, access_token: str, *, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict]:
        """Fetch transactions for an access token."""
        pass

    @abstractmethod
    def balances(self, access_token: str, account_id: str | None = None) -> dict:
        """Fetch current balances."""
        pass

    @abstractmethod
    def identity(self, access_token: str) -> dict:
        """Fetch identity/account holder information."""
        pass
```

### 2. Auth Flow

**Teller Flow** (simpler):
```
1. User → App: "Connect bank"
2. App → Teller: POST /link (gets link_token)
3. User → Teller UI: Authenticate with bank
4. Teller → App: Callback with access_token
5. App: Store encrypted access_token in DB
```

**Plaid Flow** (standard):
```
1. User → App: "Connect bank"
2. App → Plaid: POST /link/token/create (gets link_token)
3. User → Plaid Link UI: Authenticate with bank
4. Plaid Link → App: Returns public_token
5. App → Plaid: POST /item/public_token/exchange (gets access_token)
6. App: Store encrypted access_token in DB
```

### 3. Token Storage

Use svc-infra DB with encryption:

```python
# In application code
from svc_infra.db import get_session
from svc_infra.security import encrypt, decrypt

# Store token
encrypted_token = encrypt(access_token)
session.add(BankConnection(user_id=user_id, encrypted_token=encrypted_token))

# Retrieve token
connection = session.query(BankConnection).filter_by(user_id=user_id).first()
access_token = decrypt(connection.encrypted_token)
```

### 4. PII Boundaries

**PII in banking data**:
- Account numbers (mask all but last 4 digits)
- Routing numbers (mask completely)
- SSN/Tax ID (never log)
- Account holder names (log only hashed user_id)

**Masking strategy**:
```python
# In logging
from svc_infra.logging import setup_logging, mask_pii

setup_logging()  # Enables PII masking

# Account number: 1234567890 → ****7890
# Routing number: 021000021 → *********
```

### 5. Caching Strategy

Use svc-infra cache for account data:

```python
from svc_infra.cache import cache_read, cache_write, init_cache

init_cache(url="redis://localhost", prefix="fin_infra", version="v1")

# Cache accounts (60s TTL)
@cache_read(ttl=60, prefix="banking:accounts")
async def get_accounts(access_token: str) -> list[dict]:
    return await banking.accounts(access_token)

# Cache transactions (5 min TTL)
@cache_read(ttl=300, prefix="banking:transactions")
async def get_transactions(access_token: str, start_date: str, end_date: str) -> list[dict]:
    return await banking.transactions(access_token, start_date=start_date, end_date=end_date)
```

**Cache invalidation**:
- On new transaction webhook: `cache.delete(f"banking:transactions:{access_token}")`
- On balance change: `cache.delete(f"banking:accounts:{access_token}")`

### 6. Easy Setup Pattern

Provide `easy_banking()` one-liner:

```python
def easy_banking(provider: str = "teller", **config) -> BankingProvider:
    """Create configured banking provider with env auto-detection.
    
    Args:
        provider: "teller" (default), "plaid", or "mx"
        **config: Override env vars (api_key, client_id, secret, environment)
    
    Returns:
        Configured BankingProvider instance
    
    Env vars (auto-detected):
        Teller: TELLER_API_KEY, TELLER_ENVIRONMENT (sandbox/production)
        Plaid: PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENVIRONMENT (sandbox/development/production)
        MX: MX_CLIENT_ID, MX_API_KEY, MX_ENVIRONMENT
    
    Examples:
        # Zero config (uses env vars)
        banking = easy_banking()
        
        # Explicit provider
        banking = easy_banking(provider="plaid")
        
        # Override config
        banking = easy_banking(provider="teller", api_key="test_key", environment="sandbox")
    """
    return resolve("banking", provider, **config)
```

FastAPI integration helper:

```python
def add_banking(
    app: FastAPI, 
    *, 
    provider: str | None = None, 
    prefix: str = "/banking",
    cache_ttl: int = 60
) -> BankingProvider:
    """Wire banking provider to FastAPI app with routes and caching.
    
    Adds routes:
        POST {prefix}/link - Create link token
        POST {prefix}/exchange - Exchange public token
        GET {prefix}/accounts - List accounts
        GET {prefix}/transactions - List transactions
        GET {prefix}/balances - Get balances
        GET {prefix}/identity - Get identity info
    
    Uses svc-infra:
        - cache: Account/transaction caching
        - logging: Provider call logging with PII masking
        - db: Token storage (encrypted)
    
    Example:
        from svc_infra.api.fastapi.ease import easy_service_app
        from fin_infra.banking import add_banking
        
        app = easy_service_app(name="FinanceAPI")
        banking = add_banking(app, provider="teller")
    """
    # Implementation in next phase
    pass
```

### 7. Data Models

Use existing `Account` and `Transaction` models from `fin_infra.models`:

```python
from fin_infra.models import Account, Transaction

# Account model already exists:
# - id, name, type, mask, currency, institution
# - balance_available, balance_current

# Transaction model already exists:
# - id, account_id, amount, currency, date, description
# - category, pending, merchant_name
```

## Security Considerations

1. **Token Encryption**: All access tokens encrypted at rest using svc-infra security
2. **PII Masking**: Account numbers, routing numbers masked in logs (svc-infra logging)
3. **Token Expiration**: Monitor token expiration, provide refresh flow
4. **Rate Limiting**: Use provider rate limits, cache aggressively
5. **Audit Trail**: Log all provider calls (without PII) for debugging

## Testing Strategy

1. **Unit Tests**: Mock HTTP responses for each provider
2. **Integration Tests**: Use provider sandbox environments
3. **Acceptance Tests**: Real provider calls (Teller/Plaid sandbox)
4. **PII Tests**: Verify no sensitive data in logs
5. **Cache Tests**: Verify TTL and invalidation logic

## Migration Path

**From existing `clients/plaid.py` to providers**:
```python
# Old (clients-based)
from fin_infra.clients.plaid import PlaidClient
plaid = PlaidClient(client_id="...", secret="...")

# New (providers-based with easy setup)
from fin_infra.banking import easy_banking
banking = easy_banking(provider="plaid")  # Auto-detects env vars
```

## Consequences

**Positive**:
- Clear separation: fin-infra (bank data) vs svc-infra (billing/payments)
- Easy setup with sensible defaults (free tier by default)
- Secure token handling with encryption
- PII masking built-in
- Multi-provider support with consistent interface
- Aggressive caching reduces API costs

**Negative**:
- Requires provider API keys for production use
- Rate limits vary by provider
- Token refresh logic adds complexity
- US-only coverage for Teller (default)

**Neutral**:
- Applications must install both fin-infra (bank data) and svc-infra (backend)
- Provider selection based on use case (dev/prod, geography)

## References

- [Teller API Docs](https://teller.io/docs)
- [Plaid API Docs](https://plaid.com/docs)
- [MX API Docs](https://docs.mx.com)
- svc-infra: cache, db, logging, security, http modules
- fin-infra: Account/Transaction models, BankingProvider ABC

## Implementation Notes

**Phase 1**: Teller provider (real implementation)
**Phase 2**: Plaid provider (upgrade from skeleton)
**Phase 3**: easy_banking() + add_banking() helpers
**Phase 4**: Acceptance tests with sandbox credentials
**Phase 5**: Documentation with examples
