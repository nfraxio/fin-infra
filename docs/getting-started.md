# Getting Started

This guide will help you get started with fin-infra in your fintech application.

## Installation

```bash
pip install fin-infra
```

### Optional Dependencies

fin-infra has several optional extras for different providers:

| Extra | Description |
|-------|-------------|
| `plaid` | Plaid banking integration |
| `teller` | Teller banking integration |
| `alpaca` | Alpaca brokerage |
| `crypto` | Cryptocurrency market data |
| `all` | All providers |

Example:

```bash
pip install fin-infra[plaid,alpaca]
```

## Quick Start

### 1. Set Up Banking Connection

```python
from fin_infra.banking import easy_banking

# Initialize Plaid client
banking = easy_banking(provider="plaid")

# Exchange public token for access token
access_token = await banking.exchange_token(public_token)

# Get accounts
accounts = await banking.get_accounts(access_token)
for account in accounts:
    print(f"{account.name}: ${account.balance}")
```

### 2. Get Market Data

```python
from fin_infra.markets import easy_market

# Initialize market data provider
market = easy_market(provider="alphavantage")

# Get stock quote
quote = market.quote("AAPL")
print(f"Apple: ${quote.price} ({quote.change_percent}%)")

# Get crypto price
crypto = market.crypto_quote("BTC", "USD")
print(f"Bitcoin: ${crypto.price}")
```

### 3. Track Net Worth

```python
from fin_infra.net_worth import calculate_net_worth

# Get all accounts
bank_accounts = await banking.get_accounts(bank_token)
brokerage_accounts = await brokerage.get_accounts(broker_token)

# Calculate net worth
net_worth = calculate_net_worth(
    bank_accounts=bank_accounts,
    brokerage_accounts=brokerage_accounts,
)

print(f"Total Assets: ${net_worth.total_assets}")
print(f"Total Liabilities: ${net_worth.total_liabilities}")
print(f"Net Worth: ${net_worth.net_worth}")
```

### 4. Categorize Transactions

```python
from fin_infra.categorization import easy_categorization

categorizer = easy_categorization()

# Categorize a transaction
category = categorizer.categorize("STARBUCKS #12345")
print(f"Category: {category.name}")  # "Food & Drink"
```

## Environment Variables

Configure your providers with environment variables:

```bash
# Banking
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # sandbox, development, production

# Market Data
ALPHAVANTAGE_API_KEY=your_api_key

# Brokerage
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_PAPER=true  # Use paper trading
```

## Integration with svc-infra

fin-infra is designed to work seamlessly with svc-infra for backend infrastructure:

```python
from svc_infra import easy_service_app
from svc_infra.cache import init_cache
from fin_infra.banking import add_banking
from fin_infra.markets import add_market_data

# Create service with svc-infra
app = easy_service_app(name="FinanceAPI")

# Initialize cache for market data
await init_cache(url="redis://localhost")

# Add fin-infra capabilities
add_banking(app, provider="plaid", prefix="/banking")
add_market_data(app, provider="alphavantage", prefix="/market")
```

## Next Steps

- [Banking](banking/index.md) - Set up bank account aggregation
- [Market Data](market-data.md) - Get real-time quotes
- [Brokerage](brokerage.md) - Trading integration
- [Net Worth](net-worth.md) - Track net worth over time
