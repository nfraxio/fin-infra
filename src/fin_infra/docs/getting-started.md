# Getting Started with fin-infra

fin-infra is a financial infrastructure toolkit that provides production-grade building blocks for fintech applications. It handles banking connections, market data, credit scores, tax data, trading accounts, and personal financial information management.

## Installation

### From PyPI (when published)
```bash
pip install fin-infra
```

### For development
```bash
# Clone the repository
git clone https://github.com/your-org/fin-infra
cd fin-infra

# Install with Poetry
poetry install
poetry shell
```

## Quick Start

### Banking Connections
```python
from fin_infra.banking import easy_banking

# Initialize banking client with defaults
banking = easy_banking()

# Connect user's bank account (Plaid/Teller)
accounts = await banking.get_accounts(access_token="user_token")
transactions = await banking.get_transactions(account_id="acc_123")
```

### Market Data
```python
from fin_infra.markets import easy_market, easy_crypto

# Equity market data
market = easy_market()
quote = market.quote("AAPL")
historical = market.historical("TSLA", period="1mo")

# Crypto market data
crypto = easy_crypto()
ticker = crypto.ticker("BTC/USDT")
candles = crypto.candles("ETH/USD", timeframe="1h", limit=100)
```

### Credit Scores
```python
from fin_infra.credit import easy_credit

# Initialize credit client
credit = easy_credit()

# Fetch user's credit score
report = await credit.get_credit_report(user_id="user_123")
score = report.fico_score
```

### Cashflow Analysis
```python
from fin_infra.cashflows import npv, irr, xnpv

# Calculate Net Present Value
cashflows = [-1000, 200, 300, 400, 500]
discount_rate = 0.08
net_value = npv(discount_rate, cashflows)

# Calculate Internal Rate of Return
rate_of_return = irr(cashflows)
```

## Architecture Overview

fin-infra is organized into domain-specific modules:

- **banking/**: Bank account aggregation (Plaid, Teller)
- **brokerage/**: Trading account connections (coming soon)
- **credit/**: Credit score and history providers
- **markets/**: Equity and crypto market data
- **tax/**: Tax data and document management (coming soon)
- **cashflows/**: Financial calculations (NPV, IRR, XNPV)
- **models/**: Pydantic models for accounts, transactions, quotes, etc.

## Configuration

fin-infra uses environment variables for provider credentials:

```bash
# Banking providers
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # or development, production

TELLER_APP_ID=your_app_id
TELLER_SECRET=your_secret

# Market data providers
ALPHAVANTAGE_API_KEY=your_api_key

# Credit providers
EXPERIAN_USERNAME=your_username
EXPERIAN_PASSWORD=your_password

# Stripe Identity
STRIPE_SECRET_KEY=sk_test_...
```

## Next Steps

- [Banking Integration Guide](banking.md)
- [Market Data Guide](market-data.md)
- [Credit Scores Guide](credit.md)
- [Brokerage Integration Guide](brokerage.md)
- [Tax Data Guide](tax.md)
- [Cashflows & Financial Calculations](cashflows.md)
- [Contributing Guide](contributing.md)
- [Acceptance Testing](acceptance.md)

## Support

- GitHub Issues: https://github.com/your-org/fin-infra/issues
- Documentation: https://github.com/your-org/fin-infra#readme
