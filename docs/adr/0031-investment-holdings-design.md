# ADR-0031: Investment Holdings Module Design

**Status**: Accepted  
**Date**: 2025-11-20  
**Authors**: fin-infra team  
**Tags**: investments, portfolio, holdings, plaid, snaptrade, architecture

## Context

Fintech applications require access to investment holdings data to calculate real profit/loss, track portfolio performance, and provide asset allocation analysis. Currently, the analytics module (ADR-0023) uses account balances for portfolio calculations, which lacks critical data: cost basis, individual securities, unrealized gains/losses, and accurate asset allocation.

**Current State Problems**:
1. **No cost basis**: Cannot calculate real P/L (profit/loss)
2. **Balance-only data**: No breakdown by security (stocks, bonds, ETFs)
3. **Mock asset allocation**: Estimated from account types, not actual holdings
4. **No transaction history**: Cannot track buys/sells for realized gains
5. **No security details**: Missing ticker symbols, CUSIPs, security types

**User Need**:
- Personal finance apps: "Show my portfolio performance across all accounts"
- Robo-advisors: "Calculate current allocation and suggest rebalancing trades"
- Wealth management: "Generate client reports with P/L and tax implications"
- Tax tools: "Report cost basis and capital gains for tax year 2024"
- Net worth tracking: "Combine banking + investment accounts for total net worth"

**Requirements**:
1. **Holdings data**: Security, quantity, cost basis, current value, P/L
2. **Transaction history**: Buy/sell orders, dividends, fees with dates
3. **Account information**: Investment account types (401k, IRA, taxable)
4. **Asset allocation**: Calculate allocation by asset class (stocks/bonds/cash)
5. **Securities details**: Ticker symbols, names, types, identifiers (CUSIP/ISIN)
6. **Multi-provider support**: Plaid (primary), SnapTrade (alternative), Teller/MX (future)
7. **Real P/L calculations**: Replace mock data in analytics module
8. **Read-only**: This module views data, does NOT execute trades (separate from brokerage)

## svc-infra Reuse Assessment

**MANDATORY: Complete BEFORE proposing solution**

### What was checked in svc-infra?
- [x] Searched svc-infra README for related functionality
- [x] Reviewed svc-infra modules: API (FastAPI ease, dual routers), cache, logging, observability
- [x] Checked svc-infra docs: API scaffolding, caching, HTTP client
- [x] Examined svc-infra source: `src/svc_infra/api/fastapi/`, `src/svc_infra/cache/`, `src/svc_infra/http/`

### Findings
- **Does svc-infra provide this functionality?** No
- **What svc-infra provides**:
  - FastAPI scaffolding (`easy_service_app`, dual routers with `public_router`, `user_router`)
  - Caching infrastructure (`cache_read`, `cache_write`, TTL management, Redis integration)
  - HTTP client with retry logic (`http_client_with_retry`, tenacity integration)
  - Logging & observability (structured logs, Prometheus metrics, tracing)
  - Security primitives (token encryption/decryption, PII handling)
- **What svc-infra does NOT provide**:
  - Investment provider integrations (Plaid Investment API, SnapTrade, Teller)
  - Financial data models (Holding, Security, InvestmentTransaction, AssetAllocation)
  - Data normalization across providers (SecurityType enum, cost basis handling)
  - Portfolio calculations (P/L, allocation, performance metrics)

### Classification
- [x] Type C: Hybrid (use svc-infra for infrastructure, fin-infra for financial logic)

### Reuse Plan
```python
# Backend infrastructure (svc-infra)
from svc_infra.api.fastapi.dual.public import public_router  # For investments endpoints
from svc_infra.cache import cache_read, cache_write, init_cache  # Cache holdings/transactions
from svc_infra.logging import setup_logging, get_logger  # Structured logging
from svc_infra.http import http_client_with_retry  # Plaid/SnapTrade API calls
from svc_infra.security import encrypt_token, decrypt_token  # Secure token storage

# Financial logic (fin-infra)
from fin_infra.investments import easy_investments, add_investments  # Investments engine
from fin_infra.investments.models import (  # Financial models
    Holding, Security, InvestmentTransaction, AssetAllocation
)
from fin_infra.investments.providers import PlaidInvestmentProvider, SnapTradeInvestmentProvider
```

## Decision

Create a **separate investments module** in fin-infra to provide READ-ONLY access to investment holdings, transactions, and portfolio data from external providers (Plaid, SnapTrade, Teller, MX).

**Key Design Decisions**:

### 1. Separate Module (Not Embedded)

**Decision**: Create `fin_infra/investments/` as standalone module

**Why separate from banking?**
- **Complexity**: Investment data is more complex (securities, cost basis, transactions, allocation)
- **Provider coverage**: Not all banking providers support investment APIs (Plaid does, Teller doesn't yet)
- **Different use cases**: Banking = cash flow, Investments = portfolio performance
- **Optional feature**: Apps without investment features don't load this module
- **Data models**: Holdings/securities are distinct from accounts/transactions

**Why separate from brokerage?**
- **READ vs WRITE**: Investments = view data, Brokerage = execute trades
- **Different providers**: Investments = Plaid/Teller/MX (aggregators), Brokerage = Alpaca/IB (trading platforms)
- **Different accounts**: Investments = external 401k/IRA, Brokerage = trading accounts
- **Regulatory separation**: Viewing data vs executing orders (different compliance requirements)

**Why separate from analytics?**
- **Data source vs analysis**: Investments = fetch holdings, Analytics = calculate metrics
- **Provider dependency**: Investments requires Plaid/SnapTrade, Analytics works with any data
- **Reusability**: Same holdings data used in multiple analytics (portfolio, tax, net worth)

### 2. Abstract Provider Pattern

**Decision**: Use abstract base class `InvestmentProvider` with concrete implementations

```python
# Abstract base class
class InvestmentProvider(ABC):
    @abstractmethod
    async def get_holdings(self, *, access_token: str, account_ids: list[str] | None = None) -> list[Holding]:
        """Fetch investment holdings."""
        pass
    
    @abstractmethod
    async def get_transactions(self, *, access_token: str, start_date: date, end_date: date) -> list[InvestmentTransaction]:
        """Fetch investment transactions."""
        pass

# Concrete implementations
class PlaidInvestmentProvider(InvestmentProvider):
    """Plaid Investment API implementation."""
    pass

class SnapTradeInvestmentProvider(InvestmentProvider):
    """SnapTrade API implementation."""
    pass
```

**Why?**
- **Multi-provider support**: Easy to add Teller, MX, Yodlee, Finicity
- **Provider fallback**: Try Plaid, fall back to SnapTrade
- **Testability**: Mock provider for unit tests
- **Flexibility**: Apps can choose provider or combine multiple providers

### 3. Normalized Data Models

**Decision**: Define standard Pydantic models that normalize provider-specific data

```python
class SecurityType(str, Enum):
    """Standard security types across all providers."""
    equity = "equity"
    etf = "etf"
    mutual_fund = "mutual_fund"
    bond = "bond"
    cash = "cash"
    derivative = "derivative"
    other = "other"

class Holding(BaseModel):
    """Normalized holding model (works with Plaid, SnapTrade, etc.)."""
    account_id: str
    security: Security
    quantity: Decimal
    institution_price: Decimal
    institution_value: Decimal
    cost_basis: Decimal | None
    iso_currency_code: str
```

**Why?**
- **Provider independence**: Applications don't depend on provider-specific schemas
- **Type safety**: Pydantic validation catches data quality issues
- **Consistency**: Same field names regardless of provider
- **Migration**: Easy to switch providers without breaking application code

### 4. Dual API Surface

**Decision**: Provide both programmatic (`easy_investments()`) and REST API (`add_investments()`)

```python
# Programmatic API (for scripts, background jobs)
from fin_infra.investments import easy_investments

investments = easy_investments(provider="plaid")
holdings = await investments.get_holdings(access_token="...")

# REST API (for web applications)
from fin_infra.investments import add_investments
from fastapi import FastAPI

app = FastAPI()
provider = add_investments(app, prefix="/investments")

# Now available:
# POST /investments/holdings
# POST /investments/transactions
# POST /investments/accounts
# POST /investments/allocation
# POST /investments/securities
```

**Why?**
- **Flexibility**: Supports both direct Python usage and HTTP APIs
- **Consistency**: Same provider logic, different interfaces
- **Reusability**: One implementation serves multiple use cases

### 5. Integration with Analytics Module

**Decision**: Extend analytics module to optionally use real holdings data

```python
# Before: Mock-based portfolio metrics (balance only)
from fin_infra.analytics import easy_analytics

analytics = easy_analytics()
metrics = await analytics.portfolio_metrics(user_id="user123")
# Uses mock data from _generate_mock_holdings()

# After: Real holdings-based portfolio metrics
from fin_infra.investments import easy_investments
from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

investments = easy_investments(provider="plaid")
holdings = await investments.get_holdings(access_token="...")

metrics = portfolio_metrics_with_holdings(holdings)
# Uses real cost basis, real P/L, real allocation
```

**Why?**
- **Backward compatibility**: Analytics still works without investments module
- **Gradual adoption**: Apps can start with mock data, upgrade to real holdings later
- **Separation of concerns**: Analytics doesn't depend on specific providers

### 6. Application-Managed Persistence

**Decision**: Module does NOT persist data; applications choose if/how to persist

**What module provides**:
- ✅ Fetch holdings from provider
- ✅ Normalize data to standard models
- ✅ Calculate metrics from holdings

**What applications must do**:
- ⏳ Store daily snapshots (for day change tracking)
- ⏳ Store monthly/yearly snapshots (for YTD/MTD returns)
- ⏳ Store transaction history (for realized gains)
- ⏳ Store tax lots (for cost basis tracking)

**Why?**
- **Library philosophy**: fin-infra is a library, not a framework (no database opinions)
- **Flexibility**: Apps choose PostgreSQL, MongoDB, or no persistence
- **Simplicity**: Module focuses on data fetching, not storage patterns
- **Example patterns**: Documentation provides SQLAlchemy examples for common patterns

## Alternatives Considered

### Alternative 1: Embed in Banking Module

**Approach**: Add holdings/transactions to existing `banking` module

**Pros**:
- Reuses Plaid client (banking + investments share credentials)
- One module for all financial accounts

**Cons**:
- ❌ Conflates different concerns (cash flow vs portfolio performance)
- ❌ Investment data is more complex (securities, cost basis, allocation)
- ❌ Not all banking providers support investments (Teller doesn't yet)
- ❌ Harder to test (module becomes too large)
- ❌ Optional feature forces all banking users to load investment code

**Decision**: Rejected

### Alternative 2: Embed in Brokerage Module

**Approach**: Add holdings to existing `brokerage` module (trading)

**Pros**:
- Both deal with investments

**Cons**:
- ❌ **READ vs WRITE**: Viewing data is fundamentally different from executing trades
- ❌ **Different providers**: Aggregators (Plaid/Teller) vs brokers (Alpaca/IB)
- ❌ **Different accounts**: External 401k/IRA vs trading accounts
- ❌ **Regulatory**: Viewing data has different compliance requirements than trading
- ❌ **Use cases**: Portfolio tracking vs active trading are different workflows

**Decision**: Rejected

### Alternative 3: Create Separate "investments" App

**Approach**: Create standalone `investments-api` application (not a library module)

**Pros**:
- Complete isolation
- Can have its own database, API, deployment

**Cons**:
- ❌ Violates fin-infra library philosophy (no applications, only libraries)
- ❌ Too heavyweight for a data fetching layer
- ❌ Hard to integrate programmatically (requires HTTP calls)
- ❌ Cannot reuse Plaid client from banking module

**Decision**: Rejected

### Alternative 4: Single "finance" Module

**Approach**: Combine banking + investments + brokerage into one giant module

**Pros**:
- One import for everything financial

**Cons**:
- ❌ Conflates different concerns (accounts, holdings, trading)
- ❌ Hard to test (too many dependencies)
- ❌ Inflexible (can't use banking without loading investment code)
- ❌ Provider confusion (Plaid for banking/investments, Alpaca for brokerage)

**Decision**: Rejected

## Comparison: Investments vs Brokerage

| Feature               | Investments Module            | Brokerage Module              |
|-----------------------|-------------------------------|-------------------------------|
| **Purpose**           | READ portfolio data           | WRITE trading orders          |
| **Primary Operation** | Fetch holdings, view P/L      | Execute buy/sell orders       |
| **Providers**         | Plaid, SnapTrade, Teller, MX  | Alpaca, IB, TD Ameritrade     |
| **Provider Type**     | Aggregators (connect to banks)| Brokers (trading platforms)   |
| **Data Source**       | Bank-connected accounts       | Trading platform accounts     |
| **Account Types**     | 401k, IRA, external brokerage | Trading accounts (self-directed) |
| **Cost Basis**        | ✅ From provider              | ✅ Tracked by platform        |
| **Real-time Data**    | Daily updates (some real-time)| Real-time quotes              |
| **Operations**        | `get_holdings()`, `get_transactions()` | `place_order()`, `cancel_order()` |
| **User Question**     | "What do I own?"              | "Execute buy order for AAPL"  |
| **Compliance**        | Account aggregation (lighter) | Trading (heavier regulation)  |
| **Use Case**          | Portfolio tracking            | Active trading                |
| **Integration**       | Combines with analytics       | Combines with market data     |

**SnapTrade Hybrid**: SnapTrade is BOTH - use in investments module (read holdings) AND brokerage module (execute trades in same accounts)

## Real P/L Calculation Approach

### Current State (Mock Data)

```python
# analytics/portfolio.py (before investments module)
def _generate_mock_holdings(accounts: list[Account]) -> list[dict]:
    """Generate mock holdings based on account balances."""
    # Estimates allocation from account types
    # No real cost basis, no real securities
    pass
```

### New State (Real Holdings)

```python
# investments/providers/plaid.py
async def get_holdings(self, access_token: str) -> list[Holding]:
    """Fetch real holdings from Plaid Investment API."""
    # Returns: security, quantity, cost_basis, current_value
    pass

# analytics/portfolio.py (enhanced)
def portfolio_metrics_with_holdings(holdings: list[Holding]) -> PortfolioMetrics:
    """Calculate metrics from REAL holdings data."""
    
    # Real cost basis
    total_cost_basis = sum(h.cost_basis for h in holdings if h.cost_basis)
    
    # Real current value
    total_value = sum(h.institution_value for h in holdings)
    
    # Real P/L
    total_return = total_value - total_cost_basis
    total_return_percent = (total_return / total_cost_basis) * 100 if total_cost_basis > 0 else 0
    
    # Real allocation (from security types)
    allocation = _calculate_allocation_from_holdings(holdings, total_value)
    
    return PortfolioMetrics(
        total_value=total_value,
        total_return=total_return,
        total_return_percent=total_return_percent,
        allocation_by_asset_class=allocation,
    )
```

**Calculations Provided**:
- ✅ `total_value = sum(holding.institution_value)`
- ✅ `total_cost_basis = sum(holding.cost_basis)`
- ✅ `total_return = total_value - total_cost_basis`
- ✅ `total_return_percent = (total_return / total_cost_basis) * 100`
- ✅ `allocation = calculate_allocation_from_holdings(holdings)` (based on Security.type)

**Calculations Requiring Persistence** (application responsibility):
- ⏳ `day_change`: Requires yesterday's holdings snapshot
- ⏳ `ytd_return`: Requires Jan 1 holdings snapshot
- ⏳ `mtd_return`: Requires month start holdings snapshot
- ⏳ `realized_gains`: Requires transaction history analysis (combine holdings + transactions)

**Implementation**:
```python
# Day change calculation (requires persistence)
from fin_infra.analytics.portfolio import calculate_day_change_with_snapshot

current_holdings = await investments.get_holdings(access_token=token)
previous_holdings = load_snapshot_from_db(user_id, date=yesterday)

day_change = calculate_day_change_with_snapshot(current_holdings, previous_holdings)
# Returns: {"day_change_dollars": 1234.56, "day_change_percent": 2.45}
```

## Integration Points

### 1. Banking Module Integration

**Shared Plaid Client**: Reuse credentials and client instance

```python
from fin_infra.banking import easy_banking
from fin_infra.investments import easy_investments

# Both use same Plaid client and credentials
banking = easy_banking(provider="plaid")
investments = easy_investments(provider="plaid")

# Same access_token for both
accounts = await banking.get_accounts(access_token=token)
holdings = await investments.get_holdings(access_token=token)

# Combined view
total_net_worth = (
    sum(acc.balance for acc in accounts) +
    sum(h.institution_value for h in holdings)
)
```

### 2. Analytics Module Integration

**Enhanced Portfolio Metrics**: Replace mock data with real holdings

```python
from fin_infra.investments import easy_investments
from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

# Fetch real holdings
investments = easy_investments(provider="plaid")
holdings = await investments.get_holdings(access_token=token)

# Calculate real P/L
metrics = portfolio_metrics_with_holdings(holdings)

print(f"Total value: ${metrics.total_value:,.2f}")
print(f"Total return: ${metrics.total_return:,.2f} ({metrics.total_return_percent:.2f}%)")

# Real allocation
for allocation in metrics.allocation_by_asset_class:
    print(f"{allocation.asset_class}: {allocation.percentage:.1f}%")
```

**API Integration**: Update `/analytics/portfolio` endpoint

```python
# analytics/add.py (enhanced)
@router.get("/portfolio", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    user_id: str,
    accounts: Optional[list[str]] = None,
    with_holdings: bool = False,  # NEW parameter
    access_token: Optional[str] = None,  # NEW parameter
):
    """Calculate portfolio metrics with optional real holdings."""
    
    if with_holdings and access_token:
        # Fetch real holdings from investment provider
        investment_provider = app.state.investment_provider
        holdings = await investment_provider.get_holdings(access_token=access_token)
        
        # Calculate with real data
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings
        return portfolio_metrics_with_holdings(holdings)
    
    # Fall back to balance-only calculation
    return await provider.portfolio_metrics(user_id, accounts=accounts)
```

### 3. Brokerage Module Integration

**Unified Portfolio View**: Combine external holdings + trading positions

```python
from fin_infra.investments import easy_investments
from fin_infra.brokerage import easy_brokerage

# External holdings (401k, IRA, taxable accounts via Plaid)
plaid_investments = easy_investments(provider="plaid")
external_holdings = await plaid_investments.get_holdings(plaid_token)

# Active trading positions (Alpaca brokerage account)
alpaca_broker = easy_brokerage(provider="alpaca")
trading_positions = await alpaca_broker.positions()

# Unified portfolio
total_portfolio = {
    "external": {
        "value": sum(h.institution_value for h in external_holdings),
        "holdings": external_holdings,
    },
    "trading": {
        "value": sum(p.market_value for p in trading_positions),
        "positions": trading_positions,
    },
    "total": (
        sum(h.institution_value for h in external_holdings) +
        sum(p.market_value for p in trading_positions)
    ),
}
```

### 4. Scaffold Module Integration

**Optional Persistence Models**: Applications can scaffold holdings tables

```python
# Application scaffolds holdings model (optional)
from sqlalchemy import Column, String, Float, Date, JSON

class UserHolding(Base):
    """Persist holdings for historical tracking."""
    __tablename__ = "user_holdings"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    account_id = Column(String)
    security_id = Column(String)
    snapshot_date = Column(Date, index=True)
    
    quantity = Column(Float)
    institution_price = Column(Float)
    institution_value = Column(Float)
    cost_basis = Column(Float, nullable=True)
    security_data = Column(JSON)

# Store daily snapshots
async def store_daily_snapshot(user_id: str):
    holdings = await investments.get_holdings(access_token=token)
    for holding in holdings:
        db.add(UserHolding(
            user_id=user_id,
            snapshot_date=today,
            quantity=holding.quantity,
            institution_value=holding.institution_value,
            cost_basis=holding.cost_basis,
            # ...
        ))
    db.commit()
```

### 5. Market Data Module Integration

**Live Portfolio Value**: Combine holdings with real-time quotes

```python
from fin_infra.investments import easy_investments
from fin_infra.market_data import easy_market_data

# Fetch holdings
investments = easy_investments(provider="plaid")
holdings = await investments.get_holdings(access_token=token)

# Get live quotes
market_data = easy_market_data(provider="alpha_vantage")
tickers = [h.security.ticker_symbol for h in holdings]
quotes = await market_data.get_quotes(tickers)

# Calculate live portfolio value
live_value = sum(
    h.quantity * quotes[h.security.ticker_symbol].price
    for h in holdings
    if h.security.ticker_symbol in quotes
)
```

## Provider Extensibility

### Abstract Base Class

```python
# investments/providers/base.py
from abc import ABC, abstractmethod

class InvestmentProvider(ABC):
    """Abstract base for investment data providers."""
    
    @abstractmethod
    async def get_holdings(
        self,
        *,
        access_token: str | None = None,
        user_id: str | None = None,
        user_secret: str | None = None,
        account_ids: list[str] | None = None,
    ) -> list[Holding]:
        """Fetch investment holdings."""
        pass
    
    @abstractmethod
    async def get_transactions(
        self,
        *,
        access_token: str | None = None,
        start_date: date,
        end_date: date,
        account_ids: list[str] | None = None,
    ) -> list[InvestmentTransaction]:
        """Fetch investment transactions."""
        pass
    
    @abstractmethod
    async def get_accounts(
        self,
        *,
        access_token: str | None = None,
    ) -> list[InvestmentAccount]:
        """Fetch investment accounts."""
        pass
```

### Adding New Providers

```python
# investments/providers/mx.py (future)
class MXInvestmentProvider(InvestmentProvider):
    """MX investment data provider."""
    
    async def get_holdings(self, *, access_token: str, account_ids: list[str] | None = None) -> list[Holding]:
        # 1. Call MX API
        response = await self.client.get("/holdings", params={"token": access_token})
        
        # 2. Normalize to standard Holding model
        holdings = [
            Holding(
                account_id=item["account_guid"],
                security=Security(
                    security_id=item["cusip"],
                    ticker_symbol=item["symbol"],
                    type=self._map_security_type(item["type"]),
                    # ...
                ),
                quantity=Decimal(str(item["shares"])),
                institution_value=Decimal(str(item["market_value"])),
                cost_basis=Decimal(str(item["cost_basis"])) if item.get("cost_basis") else None,
                # ...
            )
            for item in response["holdings"]
        ]
        
        return holdings
    
    def _map_security_type(self, mx_type: str) -> SecurityType:
        """Map MX security types to standard SecurityType enum."""
        mapping = {
            "EQUITY": SecurityType.equity,
            "ETF": SecurityType.etf,
            "MUTUAL_FUND": SecurityType.mutual_fund,
            # ...
        }
        return mapping.get(mx_type, SecurityType.other)
```

### Provider Comparison Matrix

| Provider   | Coverage (US)    | Coverage (Intl) | Cost Basis | Real-time | Trading Support | Pricing      |
|------------|------------------|-----------------|------------|-----------|-----------------|--------------|
| **Plaid**  | 12,000+ (excellent) | Limited      | ✅ Yes     | Daily     | ❌ No           | Pay-per-use  |
| **SnapTrade** | 5,000+ (good) | Canada, Europe  | ✅ Yes     | Real-time | ✅ Yes          | Tiered       |
| **Teller** | 500+ (limited)   | None            | ⚠️ TBD     | TBD       | ❌ No           | Free/open    |
| **MX**     | 16,000+ (best)   | Limited         | ✅ Yes     | Daily     | ❌ No           | Enterprise   |
| **Yodlee** | 15,000+ (excellent) | Global       | ✅ Yes     | Daily     | ❌ No           | Enterprise   |
| **Finicity** | 16,000+ (excellent) | Limited    | ✅ Yes     | Daily     | ❌ No           | Pay-per-use  |

**Recommendation**:
- **Primary**: Plaid (best balance of coverage, cost, reliability)
- **Secondary**: SnapTrade (alternative + trading support)
- **Future**: Teller (privacy-focused), MX (broader coverage)

## Consequences

### Positive

✅ **Clear separation of concerns**:
- Banking = accounts and transactions (cash flow)
- Investments = holdings and securities (portfolio performance)
- Brokerage = order execution (active trading)
- Analytics = calculations (metrics, insights)

✅ **Optional feature**:
- Apps without investment tracking don't load this module
- No database/cache dependencies for non-investment apps

✅ **Multi-provider support**:
- Easy to add Teller, MX, Yodlee, Finicity
- Provider fallback strategies for maximum coverage
- Abstract base class makes providers swappable

✅ **Reuses Plaid client**:
- Banking and investments share same Plaid credentials
- One Link flow for both account types
- Reduced integration complexity

✅ **Real P/L calculations**:
- Replaces mock data in analytics module
- Accurate cost basis from providers
- Real asset allocation from security types

✅ **Testability**:
- Mock provider for unit tests
- Plaid sandbox for integration tests
- No database required for core functionality

✅ **Library philosophy**:
- No persistence layer (applications choose)
- No framework opinions (FastAPI optional)
- Composable with other modules

### Negative

⚠️ **Provider dependency**:
- Requires Plaid/SnapTrade API credentials
- Subject to provider rate limits
- Provider downtime affects functionality

⚠️ **No historical data**:
- Day change requires application persistence
- YTD/MTD returns require time-series storage
- Module focuses on current data only

⚠️ **Cost basis limitations**:
- Some providers/accounts don't have cost basis
- Applications must handle missing cost basis gracefully
- May require fallback to transaction history

⚠️ **Data freshness**:
- Some accounts update daily (not real-time)
- 401(k) data often delayed (weekly updates)
- Applications must communicate data age to users

### Migration Path

For existing applications with mock portfolio data:

```python
# Phase 1: Keep using mock data (no changes)
from fin_infra.analytics import easy_analytics
analytics = easy_analytics()
metrics = await analytics.portfolio_metrics(user_id)

# Phase 2: Add investments module (opt-in)
from fin_infra.investments import easy_investments
investments = easy_investments(provider="plaid")

# Phase 3: Use real holdings when available
holdings = await investments.get_holdings(access_token=token)
if holdings:
    from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings
    metrics = portfolio_metrics_with_holdings(holdings)
else:
    # Fall back to mock data
    metrics = await analytics.portfolio_metrics(user_id)
```

### API Surface

**Programmatic API**:
```python
from fin_infra.investments import easy_investments

investments = easy_investments(provider="plaid")

# Core operations
holdings = await investments.get_holdings(access_token="...")
transactions = await investments.get_transactions(access_token="...", start_date=..., end_date=...)
accounts = await investments.get_accounts(access_token="...")
allocation = await investments.get_allocation(access_token="...")
securities = await investments.get_securities(access_token="...", security_ids=["AAPL", "GOOGL"])
```

**REST API**:
```python
from fin_infra.investments import add_investments
from fastapi import FastAPI

app = FastAPI()
provider = add_investments(app, prefix="/investments")

# Endpoints:
# POST /investments/holdings
# POST /investments/transactions
# POST /investments/accounts
# POST /investments/allocation
# POST /investments/securities
```

## Related ADRs

- **ADR-0023**: Analytics Module Design (portfolio metrics, now enhanced with real holdings)
- **ADR-0006**: Brokerage Trade Execution (separate from read-only investments)
- **ADR-0003**: Banking Integration (shared Plaid client with investments)
- **ADR-0030**: Investment Holdings API Research (provider comparison, findings)

## References

- [Plaid Investment API Documentation](https://plaid.com/docs/api/products/investments/)
- [SnapTrade API Documentation](https://snaptrade.com/docs)
- [Investment Holdings Documentation](../../docs/investments.md)
- [Analytics Module Documentation](../../docs/analytics.md)
- [Brokerage Module Documentation](../../docs/brokerage.md)

---

**Implementation Status**: ✅ Complete (Tasks 1-10 done)
- [x] Models, providers, ease/add helpers implemented
- [x] Plaid and SnapTrade providers working
- [x] Analytics integration (portfolio_metrics_with_holdings)
- [x] API endpoints mounted with FastAPI
- [x] Comprehensive documentation written
- [x] ADR documented

**Next Steps**:
1. Unit tests: 80+ tests across models, providers, ease/add helpers
2. Integration tests: Plaid sandbox, API endpoints
3. Code quality: ruff format/check, mypy type checking
4. README update (if new top-level capability)
