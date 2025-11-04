# copilot-instructions.md (fin-infra)

## What this repo is
- `fin-infra` is a provider-agnostic financial infrastructure toolkit: market data (equities/crypto), banking aggregation adapters, cashflows, and utilities (settings, caching, retries).
- Supported Python: 3.11–3.13. Publish-ready package via Poetry; CLI entrypoint `fin-infra`.

## Product goal
- Make finance primitives trivial to adopt: typed adapters with sane defaults and minimal configuration.
- Provide extensibility for multiple providers per domain (market, crypto, banking, identity, credit).
- Prioritize developer ergonomics: consistent APIs, clear models, tests, and docs.

## What this repo is
- `fin-infra` is a provider-agnostic **financial data integration toolkit** for fintech applications: banking connections, brokerage accounts, market data, credit scores, tax data, and cashflow calculations.
- **NOT a backend framework**: fin-infra provides ONLY financial-specific integrations. All backend infrastructure (API, auth, DB, cache, jobs, webhooks) comes from `svc-infra`.
- Supported Python: 3.11–3.13. Publish-ready package via Poetry; CLI entrypoint `fin-infra`.

## Critical Boundary: fin-infra vs svc-infra

### fin-infra scope (ONLY financial integrations)
- ✅ Banking provider adapters (Plaid, Teller, MX)
- ✅ Brokerage integrations (Alpaca, Interactive Brokers)
- ✅ Market data (stocks, crypto, forex via Alpha Vantage, CoinGecko, Yahoo)
- ✅ Credit scores (Experian, Equifax, TransUnion)
- ✅ Tax data (IRS, TaxBit, document management)
- ✅ Financial calculations (NPV, IRR, loan amortization, portfolio analytics)
- ✅ Financial data models (accounts, transactions, quotes, holdings, credit reports)
- ✅ Provider normalization (symbol resolution, currency conversion)

### svc-infra scope (USE, don't duplicate)
- ✅ API framework (FastAPI scaffolding, routing, middleware)
- ✅ Auth & security (OAuth, sessions, MFA, password policies, JWT)
- ✅ Database (SQL/Mongo migrations, ORM, connection management)
- ✅ Caching (Redis, cache decorators, TTL management, invalidation)
- ✅ Logging & observability (structured logs, Prometheus metrics, Grafana, OpenTelemetry)
- ✅ Job queues (background tasks, workers, schedulers, retry logic)
- ✅ Webhooks (signing, delivery, retry, subscription management)
- ✅ Rate limiting (middleware, decorators, distributed limiting)
- ✅ Billing & payments (Stripe/Adyen integration, subscriptions, invoices)
- ✅ HTTP utilities (retry logic with tenacity, timeout management)

## Product goal
- Make finance primitives trivial to adopt: typed adapters with sane defaults and minimal configuration.
- Enable fintech apps like Mint, Credit Karma, Robinhood, Personal Capital (fin-infra provides data; svc-infra provides backend).
- Provide extensibility for multiple providers per domain (market, crypto, banking, brokerage, credit, tax).
- Prioritize developer ergonomics: consistent APIs, clear models, comprehensive tests and docs.
- **Mandatory reuse**: Always use svc-infra for backend concerns; never duplicate.
- Emphasize one-call setup per capability (like svc-infra's easy builders):
  - `easy_market()` returns a market data provider wired with defaults.
  - `easy_crypto()` returns a crypto data provider wired with defaults.
  - `easy_banking()` returns a banking adapter wired for sandbox/production.
  - `easy_brokerage()` returns a brokerage client for paper/live trading.
  - `easy_credit()` returns a credit score provider.
  - Cashflow functions: `npv()`, `irr()`, `xnpv()`, `xirr()`.

## Dev setup and checks
- Install with Poetry: `poetry install`. Activate via `poetry shell` or prefix `poetry run`.
- Format: `ruff format` (optional); Lint: `ruff check`.
- Type check: `mypy src`.
- Tests: `pytest -q` (acceptance under `-m acceptance`).

## Architecture map (key modules)
- **Banking** (`src/fin_infra/banking/`): Bank account aggregation
  - Plaid adapter, Teller adapter, MX adapter (future)
- **Brokerage** (`src/fin_infra/brokerage/`): Trading account connections
  - Alpaca adapter (paper/live), Interactive Brokers (future)
- **Credit** (`src/fin_infra/credit/`): Credit score providers
  - Experian, Equifax (future), TransUnion (future)
- **Markets** (`src/fin_infra/markets/`): Market data (equities/crypto/forex)
  - Alpha Vantage (default), Yahoo Finance, CoinGecko, CCXT
- **Tax** (`src/fin_infra/tax/`): Tax document and data management
  - IRS integration, TaxBit, document parsers
- **Cashflows** (`src/fin_infra/cashflows/`): Financial calculations
  - NPV, IRR, XNPV, XIRR, PMT, FV, PV, loan amortization
- **Models** (`src/fin_infra/models/`): Pydantic data models
  - Accounts, transactions, quotes, holdings, credit reports
- **Providers** (`src/fin_infra/providers/`): Base classes and registry
  - Provider ABCs, dynamic loading, fallback chains
- **CLI** (`src/fin_infra/cli/`): Command-line utilities
  - Provider testing, data validation, configuration helpers

## External deps (financial-specific only)
- **Provider SDKs**: plaid-python, yahooquery, ccxt, stripe (for identity)
- **Financial math**: numpy, numpy-financial
- **Data validation**: pydantic, pydantic-settings
- **HTTP**: httpx (lightweight; heavy retry/timeout logic from svc-infra)
- **Backend infrastructure**: svc-infra (auth, API, cache, jobs, DB, logging, observability)

## Typical workflows (fin-infra + svc-infra integration)

### Building a fintech API (use BOTH packages)
```python
# Backend framework from svc-infra
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.logging import setup_logging
from svc_infra.cache import init_cache
from svc_infra.obs import add_observability

# Financial integrations from fin-infra
from fin_infra.banking import easy_banking
from fin_infra.markets import easy_market
from fin_infra.credit import easy_credit

# Setup backend (svc-infra)
setup_logging()
app = easy_service_app(name="FinanceAPI")
init_cache(url="redis://localhost")
add_observability(app)

# Wire financial providers (fin-infra)
banking = easy_banking(provider="plaid")
market = easy_market(provider="alphavantage")

@app.get("/accounts")
async def get_accounts(token: str):
    return await banking.get_accounts(token)

@app.get("/quote/{symbol}")
async def get_quote(symbol: str):
    return market.quote(symbol)
```

### Financial calculations (fin-infra only)
```python
from fin_infra.cashflows import npv, irr, xnpv

cashflows = [-10000, 3000, 4000, 5000]
net_value = npv(0.08, cashflows)
rate = irr(cashflows)
```

### Provider testing
```bash
make accept              # Run acceptance tests
make unit                # Run unit tests
fin-infra providers ls   # List available providers
```

## Contribution expectations
- **MANDATORY: Check svc-infra first**: Before adding any feature, verify svc-infra doesn't already provide it.
- **Document reuse**: Always document which svc-infra modules are used and why.
- **Financial-only**: Keep adapters focused on financial data; delegate all backend concerns to svc-infra.
- **Type safety**: All provider methods must have full type hints and Pydantic models.
- **Testing**: Add unit tests for logic; acceptance tests for provider integrations.
- **Quality gates**: Run format, lint, type, test before submitting PRs.

## Agent workflow expectations
- **Hard gate: Research svc-infra FIRST**: Before implementing ANY feature, check if svc-infra provides it.
- **Stage gates**: Research → Design → Implement → Tests → Verify → Docs (no skipping).
- **Reuse documentation**: Document all svc-infra imports and why they're used.
- **Examples**: Show fin-infra + svc-infra integration patterns in docs.
- **Quality report**: Run all checks (format, lint, type, test) and report results before finishing.
