# copilot-instructions.md (fin-infra)

## What this repo is
- `fin-infra` is a provider-agnostic financial infrastructure toolkit: market data (equities/crypto), banking aggregation adapters, cashflows, and utilities (settings, caching, retries).
- Supported Python: 3.11–3.13. Publish-ready package via Poetry; CLI entrypoint `fin-infra`.

## Product goal
- Make finance primitives trivial to adopt: typed adapters with sane defaults and minimal configuration.
- Provide extensibility for multiple providers per domain (market, crypto, banking, identity, credit).
- Prioritize developer ergonomics: consistent APIs, clear models, tests, and docs.
- Emphasize one-call setup per capability (like svc-infra’s easy builders):
  - `easy_market()` returns a market data provider wired with defaults.
  - `easy_crypto()` returns a crypto data provider wired with defaults.
  - `easy_banking()` returns a banking adapter skeleton wired for local/dev.
  - `easy_cashflows()` exposes cashflow helpers directly.

## Dev setup and checks
- Install with Poetry: `poetry install`. Activate via `poetry shell` or prefix `poetry run`.
- Format: `ruff format` (optional); Lint: `ruff check`.
- Type check: `mypy src`.
- Tests: `pytest -q` (acceptance under `-m acceptance`).

## Architecture map (key modules)
- Providers (`src/fin_infra/providers/*`)
  - Market: `alphavantage`, `yahoo`, Crypto: `coingecko`, `ccxt_crypto`
  - Banking: `teller_client` (skeleton), `plaid_client` (optional)
  - Identity: `stripe_identity` (skeleton)
  - Credit: `experian` (skeleton)
- Cashflows (`src/fin_infra/cashflows`): NPV/IRR
- Utils: `utils/http.py` (tenacity/httpx), `utils/cache.py` (cashews), `utils/retry.py`
- Settings: `settings.py` (pydantic-settings)

## External deps
- Providers: yahooquery, ccxt, plaid-python, httpx; AlphaVantage via httpx.
- Utils: tenacity, cashews[redis], loguru; math: numpy + numpy-financial.

## Typical workflows
- One-call setup:
  - `from fin_infra.easy import easy_market, easy_crypto`
  - `md = easy_market(); md.quote("AAPL")`
  - `cg = easy_crypto(); cg.ticker("BTC/USDT")`
- Direct usage (advanced):
  - Get quotes: `AlphaVantageMarketData().quote("AAPL")`
  - Crypto price: `CoinGeckoCryptoData().ticker("BTC/USDT")`
- Cashflows: `npv(0.08, cf); irr(cf)`
- Run acceptance: `make accept` (requires env keys for some tests)

## Contribution expectations
- Keep adapters small and typed; add or update tests when changing behavior.
- Run ruff/mypy/pytest before submitting PRs.

## Agent workflow expectations
- Plan before edits; follow hard gates: Research → Design → Implement → Tests → Verify → Docs.
- Run tests locally before finishing and report quality gates.
