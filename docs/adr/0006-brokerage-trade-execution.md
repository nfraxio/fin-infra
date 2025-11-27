# ADR-0006: Brokerage Trade Execution Flow

**Status**: Accepted  
**Date**: 2025-01-15  
**Authors**: fin-infra team

## Context

fin-infra needs to provide unified interfaces for connecting to brokerage accounts for automated trading, portfolio management, and position tracking. The implementation must support both paper trading (sandbox) and live trading with robust safety mechanisms.

Key requirements:
1. Support multiple brokerage providers (Alpaca primary, Interactive Brokers/TD Ameritrade future)
2. Provide paper trading as default mode (safety-first design)
3. Enable programmatic order management (submit, list, get, cancel)
4. Track positions and portfolio value over time
5. Integrate with svc-infra for FastAPI routing, logging, and observability

Critical considerations:
- **Trading involves real money and substantial risk**
- **Regulatory compliance** (SEC, FINRA, pattern day trader rules)
- **Safety mechanisms** to prevent accidental live trading
- **Error handling** for network failures, insufficient funds, invalid orders
- **Rate limiting** to respect broker API limits

## svc-infra Reuse Assessment

### What was checked in svc-infra?
- [x] Searched svc-infra README for related functionality
- [x] Reviewed svc-infra modules: `api/fastapi`, `logging`, `obs`, `http`, `cache`, `security`
- [x] Checked svc-infra docs: FastAPI scaffolding, dual routers, observability
- [x] Examined svc-infra source: `api/fastapi/dual/public.py`, `http/`, `logging/`

### Findings
- **Does svc-infra provide this functionality?** No
- **If No**: svc-infra provides backend infrastructure (API framework, logging, HTTP clients, caching), but does NOT provide:
  - Trading/brokerage provider integrations
  - Order management APIs
  - Position tracking
  - Portfolio management
  - Financial regulatory compliance logic

### Classification
- [x] Type A: Financial-specific (brokerage operations are trading-domain specific)
- [ ] Type B: Backend infrastructure (must use svc-infra)
- [x] Type C: Hybrid (use svc-infra for infrastructure, fin-infra for provider logic)

### Reuse Plan
fin-infra brokerage module will:
```python
# FastAPI routing
from svc_infra.api.fastapi.dual.public import public_router  # Dual route registration
from svc_infra.api.fastapi.docs.scoped import add_prefixed_docs  # Landing page cards

# Logging
from svc_infra.logging import setup_logging  # Structured logging for trades

# Observability
from svc_infra.obs import add_observability  # Metrics for order success/failure rates

# HTTP client (used by Alpaca provider)
import httpx  # Provider SDK already uses httpx with retries
```

## Decision

### Architecture

**fin-infra will implement**:
1. **Provider Abstraction**: `BrokerageProvider` ABC defining interface for all brokers
2. **Alpaca Provider**: `AlpacaBrokerageProvider` implementing paper and live trading
3. **Easy Builder**: `easy_brokerage()` function with zero-config defaults
4. **FastAPI Integration**: `add_brokerage()` mounting routes with svc-infra dual routers
5. **Data Models**: Order, Position, Account DTOs (Pydantic v2)
6. **Safety Design**:
   - Defaults to paper trading mode
   - Requires explicit `mode="live"` for real trading
   - Separate credential detection for paper vs live
7. **Error Handling**: Comprehensive exception handling with user-friendly messages

**svc-infra will provide**:
1. FastAPI application scaffolding (`easy_service_app`)
2. Dual router registration (no 307 redirects)
3. Structured logging with PII filtering
4. Prometheus metrics collection
5. HTTP retry logic (via httpx)
6. OpenAPI documentation generation

### Safety Mechanisms

#### Paper Trading Default
```python
# Default behavior (SAFE)
brokerage = easy_brokerage()  # mode="paper" by default
```

#### Explicit Live Mode Opt-In
```python
# Live trading requires explicit opt-in
brokerage = easy_brokerage(
    mode="live",  # Must be explicitly set
    api_key=os.getenv("ALPACA_LIVE_API_KEY"),  # Separate credentials
    api_secret=os.getenv("ALPACA_LIVE_SECRET_KEY")
)
```

#### Credential Separation
- Paper trading: `ALPACA_PAPER_API_KEY` and `ALPACA_PAPER_SECRET_KEY`
- Live trading: `ALPACA_LIVE_API_KEY` and `ALPACA_LIVE_SECRET_KEY`
- No credential reuse between modes

### Order Execution Flow

```
1. Order Request
   ├─> Validate (symbol, qty, price, type, time_in_force)
   ├─> Check buying power (via get_account())
   ├─> Submit to provider API
   └─> Return order object with ID

2. Order Tracking
   ├─> Get order by ID (get_order)
   ├─> List orders with filters (status, symbol, limit)
   └─> Poll for status updates (new → accepted → filled)

3. Order Cancellation
   ├─> Check if order is cancelable (not filled/canceled)
   ├─> Submit cancel request
   └─> Confirm cancellation

4. Position Management
   ├─> List all positions
   ├─> Get position by symbol
   ├─> Close position (submit market order to exit)
   └─> Track P&L (unrealized and realized)
```

### Supported Order Types

| Order Type | Description | Required Fields |
|------------|-------------|-----------------|
| `market` | Execute immediately at current market price | symbol, qty, side, time_in_force |
| `limit` | Execute only at specified price or better | symbol, qty, side, limit_price, time_in_force |
| `stop` | Trigger market order when stop price reached | symbol, qty, side, stop_price, time_in_force |
| `stop_limit` | Trigger limit order when stop price reached | symbol, qty, side, limit_price, stop_price, time_in_force |

### Time in Force Options

| TIF | Description |
|-----|-------------|
| `day` | Order valid until market close |
| `gtc` | Good-til-canceled (valid until explicitly canceled) |
| `opg` | Execute at market open or cancel |
| `cls` | Execute at market close or cancel |
| `ioc` | Immediate-or-cancel (fill immediately, cancel remainder) |
| `fok` | Fill-or-kill (fill entire order immediately or cancel) |

## Consequences

### Positive
1. **Safety-First Design**: Paper trading default prevents accidental live trading
2. **Developer Ergonomics**: Zero-config setup with sensible defaults
3. **Consistent API**: Same interface for paper and live trading
4. **Comprehensive**: Supports all major order types and position management
5. **svc-infra Integration**: Leverages existing infrastructure for logging, metrics, routing
6. **Type Safety**: Pydantic v2 models ensure valid data
7. **Error Handling**: Clear error messages for common failures (insufficient funds, invalid params)
8. **Rate Limit Aware**: Alpaca provider respects 200 req/min limit
9. **Testable**: Mock-based unit tests, optional acceptance tests with paper trading

### Negative
1. **Real Money Risk**: Live trading involves financial risk despite safety mechanisms
2. **Regulatory Complexity**: Must ensure compliance with trading regulations
3. **Single Provider**: Only Alpaca implemented (Interactive Brokers/TD Ameritrade future)
4. **No Watchlist**: Watchlist management deferred to fast-follow
5. **No Multi-Leg Orders**: Complex options strategies not supported
6. **Polling-Based**: Order status requires polling (no websocket notifications yet)

### Neutral
1. **Provider-Specific Features**: Some Alpaca features may not translate to other brokers
2. **Paper vs Live Differences**: Paper trading has unlimited funds, live trading has real constraints
3. **Market Hours**: Orders only execute during market hours (9:30 AM - 4:00 PM ET)

## Implementation Notes

### svc-infra Integration

#### FastAPI Routes
```python
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.api.fastapi.dual.public import public_router
from fin_infra.brokerage import add_brokerage

app = easy_service_app(name="TradingAPI")
brokerage = add_brokerage(app, mode="paper")

# Routes mounted at /brokerage/*
# - GET /brokerage/account
# - GET /brokerage/positions
# - GET /brokerage/positions/{symbol}
# - DELETE /brokerage/positions/{symbol}
# - POST /brokerage/orders
# - GET /brokerage/orders
# - GET /brokerage/orders/{order_id}
# - DELETE /brokerage/orders/{order_id}
# - GET /brokerage/portfolio/history
```

#### Logging Integration
```python
from svc_infra.logging import setup_logging
from fin_infra.brokerage import easy_brokerage

setup_logging(level="INFO")  # Structured JSON logs in production
brokerage = easy_brokerage(mode="paper")

# All API calls automatically logged with context
order = brokerage.submit_order(...)  # Logs: order_id, symbol, qty, side, status
```

#### Observability Integration
```python
from svc_infra.obs import add_observability
from fin_infra.brokerage import add_brokerage

app = easy_service_app(name="TradingAPI")
add_observability(app)  # Prometheus metrics at /metrics
brokerage = add_brokerage(app, mode="paper")

# Metrics exposed:
# - http_requests_total{method="POST", path="/brokerage/orders", status="200"}
# - http_request_duration_seconds{...}
# Future: brokerage_orders_total{status="filled|rejected"}
```

### fin-infra Implementation

#### Modules Created
```
src/fin_infra/
├── brokerage/
│   └── __init__.py  # easy_brokerage(), add_brokerage() (388 lines)
├── providers/
│   └── brokerage/
│       ├── alpaca.py  # AlpacaBrokerageProvider (230+ lines)
│       └── __init__.py
├── models/
│   └── brokerage.py  # Order, Position, Account DTOs (157 lines)
└── docs/
    ├── brokerage.md  # User guide (492 lines)
    └── adr/
        └── 0006-brokerage-trade-execution.md  # This file
```

#### Provider Interface
```python
from abc import ABC, abstractmethod

class BrokerageProvider(ABC):
    """Abstract base for brokerage providers."""
    
    @abstractmethod
    def submit_order(self, **kwargs) -> dict:
        """Submit a new order."""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        """Get order details by ID."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def list_orders(self, **kwargs) -> list[dict]:
        """List orders with optional filters."""
        pass
    
    @abstractmethod
    def positions(self) -> list[dict]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> dict:
        """Get position for a symbol."""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> dict:
        """Close a position."""
        pass
    
    @abstractmethod
    def get_account(self) -> dict:
        """Get account information."""
        pass
    
    @abstractmethod
    def get_portfolio_history(self, **kwargs) -> dict:
        """Get portfolio value history."""
        pass
```

### Tests Required
1. **Unit Tests** (14 tests, all passing):
   - `TestEasyBrokerage`: 7 tests (default mode, explicit mode, provider selection, credentials, live mode safety)
   - `TestAddBrokerage`: 3 tests (route mounting, custom prefix, provider instance)
   - `TestBrokerageRoutes`: 4 tests (submit order, list orders, get position, close position)

2. **Acceptance Tests** (pending):
   - Real Alpaca paper trading API calls
   - Requires `ALPACA_PAPER_API_KEY` and `ALPACA_PAPER_SECRET_KEY`
   - Test: get_account, submit_order, get_order, list_orders, get_positions

## References

- Related ADRs:
  - [ADR-0003: Banking Integration](0003-banking-integration.md)
  - [ADR-0004: Market Data Integration](0004-market-data-integration.md)
- svc-infra modules:
  - [Dual Routers](../../svc-infra/src/svc_infra/api/fastapi/dual/)
  - [Logging](../../svc-infra/src/svc_infra/logging/)
  - [Observability](../../svc-infra/src/svc_infra/obs/)
- External docs:
  - [Alpaca Trading API](https://alpaca.markets/docs/api-references/trading-api/)
  - [Alpaca Paper Trading](https://alpaca.markets/docs/trading/paper-trading/)
  - [SEC Pattern Day Trader Rules](https://www.sec.gov/investor/pubs/daytips.htm)

## Example Integrations

### Minimal Production App
```python
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.logging import setup_logging
from svc_infra.obs import add_observability
from fin_infra.brokerage import add_brokerage

# Backend (svc-infra)
setup_logging()
app = easy_service_app(name="TradingAPI")
add_observability(app)

# Financial integration (fin-infra)
brokerage = add_brokerage(app, mode="paper")  # SAFE: paper trading

# Ready to run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Programmatic Trading (No FastAPI)
```python
from fin_infra.brokerage import easy_brokerage
from fin_infra.markets import easy_market

# Initialize providers
brokerage = easy_brokerage(mode="paper")
market = easy_market()

# Get quote and submit order
quote = market.quote("AAPL")
print(f"AAPL: ${quote.price}")

if float(quote.price) < 150.00:  # Buy if under $150
    order = brokerage.submit_order(
        symbol="AAPL",
        qty=10,
        side="buy",
        type="market",
        time_in_force="day"
    )
    print(f"Order submitted: {order['id']}")
```

### Background Rebalancing Job
```python
from svc_infra.jobs.easy import easy_jobs
from fin_infra.brokerage import easy_brokerage
from fin_infra.markets import easy_market

brokerage = easy_brokerage(mode="paper")
market = easy_market()
worker, scheduler = easy_jobs(app, broker_url="redis://localhost")

@scheduler.scheduled_job("cron", hour=9, minute=30)  # Daily at 9:30 AM ET
async def daily_rebalance():
    """Rebalance portfolio to target allocation."""
    targets = {"AAPL": 0.40, "GOOGL": 0.30, "MSFT": 0.30}
    
    account = brokerage.get_account()
    portfolio_value = float(account['portfolio_value'])
    
    for symbol, target_pct in targets.items():
        target_value = portfolio_value * target_pct
        quote = market.quote(symbol)
        target_qty = int(target_value / float(quote.price))
        
        # Calculate rebalancing trade
        positions = brokerage.positions()
        current_qty = sum(int(p['qty']) for p in positions if p['symbol'] == symbol)
        qty_diff = target_qty - current_qty
        
        if qty_diff != 0:
            side = "buy" if qty_diff > 0 else "sell"
            brokerage.submit_order(
                symbol=symbol,
                qty=abs(qty_diff),
                side=side,
                type="market",
                time_in_force="day"
            )
```

## Future Enhancements

1. **Watchlist Management**: Add watchlist CRUD operations (create, get, delete, add/remove symbols)
2. **WebSocket Support**: Real-time order updates via Alpaca websockets
3. **Multi-Leg Orders**: Support for spreads, straddles, and other complex strategies
4. **Interactive Brokers**: Add IB provider for institutional trading
5. **TD Ameritrade**: Add TD provider for retail trading
6. **Position Alerts**: Notify when P&L exceeds thresholds
7. **Risk Management**: Built-in position sizing and stop-loss enforcement
8. **Backtesting**: Historical simulation mode for strategy testing
9. **Crypto Trading**: Extend to crypto brokers (Coinbase, Kraken)
10. **Options Trading**: Full options chain support with Greeks

## Approval

- [x] svc-infra reuse assessment complete
- [x] Classification identified (Type C: Hybrid)
- [x] svc-infra imports documented
- [x] No duplication of svc-infra functionality
- [x] Safety mechanisms implemented
- [x] Tests passing (14/14 unit tests)
- [x] Documentation complete (492 lines)
- [ ] Acceptance test pending (requires paper trading credentials)

**Decision**: Accepted  
**Date**: 2025-01-15
