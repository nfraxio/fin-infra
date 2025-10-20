# fin-infra

Financial infrastructure toolkit for production-grade apps. Connect to banks, brokerages, and market data; compute cashflows; fetch credit scores; and build rich finance features quickly.

## Goals
- Unified, typed SDK for common financial tasks (banking, markets, credit, cashflows)
- Pluggable providers (Plaid, broker APIs, market data vendors, crypto exchanges)
- Ergonomic defaults with escape hatches; minimal configuration via env
- Production-ready foundations: retries, rate limiting hooks, tracing, metrics (future)

## Status
Alpha. Surface is intentionally small while we stabilize core models and client contracts.

## Install (developer)
- Requires Python 3.11+

```bash
# From repo root (this folder)
poetry install
poetry run pytest -q
```

## Package layout
```
src/
  fin_infra/
    __init__.py
    py.typed
    utils.py            # helpers, retry/backoff building blocks
    models/             # Pydantic models: accounts, holdings, transactions, quotes
    clients/            # Base and provider clients (plaid, brokers)
      base.py
      plaid.py          # thin wrapper + typed responses (optional extra)
    markets/            # Market data interfaces (equity/crypto/forex)
      base.py
    credit/             # Credit score providers and models
      base.py
```

## Quickstart
One-call setup for each capability:
```python
from fin_infra.easy import easy_market, easy_crypto, easy_banking

md = easy_market()      # market data provider with sane defaults
q = md.quote("AAPL")    # Quote model

cg = easy_crypto()      # crypto data provider
t = cg.ticker("BTC/USDT")

bank = easy_banking()   # banking adapter skeleton for local/dev
accts = bank.accounts("test-access-token")
```

Advanced: implement a custom client
```python
from fin_infra.clients.base import BankingClient

class MyBanking(BankingClient):
    async def get_accounts(self, user_id: str):
        return []

# or use provider-specific client when available
```

## Roadmap
- Banking
  - Plaid client with link token, item access, accounts, balances, transactions
  - Normalized account/transaction schema across providers
- Markets
  - Equities/crypto quotes, OHLCV, fundamentals via adapters (yfinance, CCXT, Finnhub)
- Brokerages
  - Basic portfolio/positions/orders via adapter(s) (e.g., Alpaca)
- Credit
  - Provider-agnostic scores + history
- Core
  - Retries/backoff, rate-limit handling, tracing/metrics hooks
  - Cursors/pagination helpers and resilient HTTP utilities

## Acceptance tests and CI
- Acceptance tests are marked with `@pytest.mark.acceptance` and are excluded by default.
- To run locally, export any required API keys (only Alpha Vantage is needed by default):
  - `ALPHAVANTAGE_API_KEY` – required for Alpha Vantage market data tests.
- Run: `poetry run pytest -q -m acceptance`.

### GitHub Actions secrets
The acceptance workflow in `.github/workflows/acceptance.yml` expects:
- `ALPHAVANTAGE_API_KEY` – add it under Repository Settings → Secrets and variables → Actions → New repository secret.

If the secret isn’t configured, acceptance tests will still run and CoinGecko tests (public) will pass, but Alpha Vantage tests will be skipped.

## Contributing
- Keep APIs small and typed. Prefer Pydantic models for IO boundaries.
- Add or update tests for any behavior changes. Keep `pytest` passing and `mypy` clean.

License: MIT