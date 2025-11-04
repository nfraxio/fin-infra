# Banking Integration

fin-infra provides unified interfaces for connecting to users' bank accounts, pulling transactions, statements, and account balances through various banking aggregation providers.

## Supported Providers

- **Plaid**: Primary banking aggregation service
- **Teller**: Alternative banking aggregation
- More providers coming soon (Finicity, Yodlee, MX)

## Quick Setup

### Using Easy Builder
```python
from fin_infra.banking import easy_banking

# Auto-configured from environment variables
banking = easy_banking()
```

### Manual Configuration
```python
from fin_infra.providers.banking import PlaidBankingProvider
from fin_infra.settings import Settings

settings = Settings()
banking = PlaidBankingProvider(
    client_id=settings.plaid_client_id,
    secret=settings.plaid_secret,
    environment=settings.plaid_env  # sandbox, development, production
)
```

## Core Operations

### 1. Link Token Creation
Create a link token for Plaid Link initialization:

```python
link_token = await banking.create_link_token(
    user_id="user_123",
    client_name="My Fintech App"
)
# Return link_token to frontend for Plaid Link widget
```

### 2. Exchange Public Token
Exchange public token from Plaid Link for access token:

```python
access_token = await banking.exchange_public_token(public_token="public-sandbox-xxx")
# Store access_token securely for this user
```

### 3. Fetch Accounts
```python
from fin_infra.models.accounts import AccountType

accounts = await banking.get_accounts(access_token="access-sandbox-xxx")

for account in accounts:
    print(f"Account: {account.name}")
    print(f"Type: {account.account_type}")  # AccountType.CHECKING, SAVINGS, etc.
    print(f"Balance: {account.balances.current}")
    print(f"Available: {account.balances.available}")
```

### 4. Fetch Transactions
```python
from datetime import date, timedelta

end_date = date.today()
start_date = end_date - timedelta(days=30)

transactions = await banking.get_transactions(
    access_token="access-sandbox-xxx",
    start_date=start_date,
    end_date=end_date
)

for txn in transactions:
    print(f"{txn.date}: {txn.name} - ${txn.amount}")
    print(f"Category: {txn.category}")
```

### 5. Fetch Identity
```python
identity = await banking.get_identity(access_token="access-sandbox-xxx")

for owner in identity.owners:
    print(f"Name: {owner.names[0]}")
    print(f"Email: {owner.emails[0].data}")
    print(f"Phone: {owner.phone_numbers[0].data}")
    print(f"Address: {owner.addresses[0].data.street}")
```

### 6. Balance Updates
```python
balances = await banking.get_balance(access_token="access-sandbox-xxx")

for account_balance in balances:
    print(f"Account: {account_balance.account_id}")
    print(f"Current: ${account_balance.balances.current}")
    print(f"Available: ${account_balance.balances.available}")
```

## Data Models

### Account
```python
from fin_infra.models.accounts import Account, AccountType, Balance

class Account:
    account_id: str
    name: str
    official_name: str | None
    account_type: AccountType
    account_subtype: str | None
    balances: Balance
    mask: str | None  # Last 4 digits
```

### Transaction
```python
from fin_infra.models.transactions import Transaction

class Transaction:
    transaction_id: str
    account_id: str
    amount: Decimal
    date: date
    name: str
    merchant_name: str | None
    category: list[str]
    pending: bool
    iso_currency_code: str
```

## Webhooks

Handle real-time updates from banking providers:

```python
from fastapi import FastAPI, Request
from fin_infra.banking.webhooks import verify_plaid_webhook

app = FastAPI()

@app.post("/webhooks/plaid")
async def plaid_webhook(request: Request):
    payload = await request.json()
    
    # Verify webhook signature
    if not verify_plaid_webhook(request.headers, payload):
        return {"error": "Invalid signature"}
    
    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    
    if webhook_type == "TRANSACTIONS":
        if webhook_code == "INITIAL_UPDATE":
            # Initial transaction data available
            pass
        elif webhook_code == "DEFAULT_UPDATE":
            # New transaction data available
            pass
        elif webhook_code == "HISTORICAL_UPDATE":
            # Historical transaction data available
            pass
    
    return {"status": "received"}
```

## Error Handling

```python
from fin_infra.banking.exceptions import (
    BankingProviderError,
    InvalidCredentialsError,
    ItemLoginRequiredError,
    RateLimitError
)

try:
    accounts = await banking.get_accounts(access_token)
except ItemLoginRequiredError:
    # User needs to re-authenticate with their bank
    link_token = await banking.create_link_token(
        user_id="user_123",
        access_token=access_token,  # Update mode
    )
except RateLimitError:
    # Implement exponential backoff
    pass
except BankingProviderError as e:
    # Handle general provider errors
    print(f"Error: {e.message}")
```

## Best Practices

1. **Secure Token Storage**: Store access tokens encrypted in your database
2. **Rate Limiting**: Implement rate limiting for API calls
3. **Webhook Handling**: Use webhooks for real-time updates instead of polling
4. **Error Recovery**: Implement retry logic with exponential backoff
5. **User Communication**: Clearly communicate when re-authentication is needed
6. **Data Retention**: Follow provider guidelines for data retention and deletion

## Testing

```python
import pytest
from fin_infra.banking import easy_banking

@pytest.mark.asyncio
async def test_get_accounts():
    banking = easy_banking()
    
    # Use sandbox credentials
    access_token = "access-sandbox-xxx"
    accounts = await banking.get_accounts(access_token)
    
    assert len(accounts) > 0
    assert accounts[0].account_id is not None
```

## Next Steps

- [Market Data Integration](market-data.md)
- [Credit Score Integration](credit.md)
- [Brokerage Integration](brokerage.md)
