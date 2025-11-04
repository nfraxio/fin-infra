# Brokerage Integration

fin-infra provides unified interfaces for connecting to users' brokerage accounts, pulling portfolio holdings, positions, and transaction history.

## Supported Providers

- **Alpaca**: Commission-free trading API
- **Interactive Brokers**: Via IBKR API (coming soon)
- **TD Ameritrade**: Via thinkorswim API (coming soon)
- **Plaid Investments**: For read-only brokerage data

## Quick Setup

```python
from fin_infra.brokerage import easy_brokerage

# Auto-configured from environment variables
brokerage = easy_brokerage()
```

## Core Operations

### 1. Get Portfolio Summary
```python
portfolio = await brokerage.get_portfolio(account_id="acc_123")

print(f"Total Value: ${portfolio.total_value}")
print(f"Cash: ${portfolio.cash}")
print(f"Equity: ${portfolio.equity}")
print(f"Buying Power: ${portfolio.buying_power}")
```

### 2. Get Holdings
```python
holdings = await brokerage.get_holdings(account_id="acc_123")

for holding in holdings:
    print(f"{holding.symbol}: {holding.quantity} shares @ ${holding.current_price}")
    print(f"  Cost Basis: ${holding.cost_basis}")
    print(f"  Market Value: ${holding.market_value}")
    print(f"  Gain/Loss: ${holding.unrealized_gain_loss} ({holding.unrealized_gain_loss_percent}%)")
```

### 3. Get Positions
```python
positions = await brokerage.get_positions(account_id="acc_123")

for position in positions:
    print(f"{position.symbol}: {position.quantity} @ ${position.avg_entry_price}")
    print(f"  Current: ${position.current_price}")
    print(f"  P&L: ${position.unrealized_pl}")
```

### 4. Get Transaction History
```python
from datetime import date, timedelta

transactions = await brokerage.get_transactions(
    account_id="acc_123",
    start_date=date.today() - timedelta(days=90),
    end_date=date.today()
)

for txn in transactions:
    print(f"{txn.date}: {txn.type} {txn.quantity} {txn.symbol} @ ${txn.price}")
    print(f"  Amount: ${txn.amount}")
```

## Data Models

### Portfolio
```python
from fin_infra.models.portfolio import Portfolio

class Portfolio:
    account_id: str
    total_value: Decimal
    cash: Decimal
    equity: Decimal
    buying_power: Decimal
    day_gain: Decimal
    day_gain_percent: Decimal
    total_gain: Decimal
    total_gain_percent: Decimal
```

### Holding
```python
from fin_infra.models.holdings import Holding

class Holding:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_percent: Decimal
    asset_type: str  # stock, etf, option, crypto
```

## Best Practices

1. **Read-Only Access**: Use read-only connections when possible
2. **Rate Limiting**: Respect broker API rate limits
3. **Real-Time Data**: Use WebSocket connections for real-time updates
4. **Error Handling**: Implement retry logic for transient errors
5. **Data Privacy**: Encrypt and secure portfolio data

## Testing

```python
import pytest
from fin_infra.brokerage import easy_brokerage

@pytest.mark.asyncio
async def test_get_portfolio():
    brokerage = easy_brokerage()
    
    # Use paper trading account
    portfolio = await brokerage.get_portfolio("paper_account")
    
    assert portfolio.total_value >= 0
```

## Next Steps

- [Market Data Integration](market-data.md)
- [Banking Integration](banking.md)
- [Tax Data Integration](tax.md)
