# Production Readiness Punch List (v1 Framework Release)

Comprehensive checklist for making fin-infra production‑ready. Each section follows: Research → Design → Implement → Tests → Verify → Docs. We will not implement until reviewed; existing functionality will be reused (skipped) when discovered during research.

## CRITICAL: Repository Boundaries & Reuse Policy

**fin-infra is ONLY for financial data integrations.** It is NOT a backend framework.

### What fin-infra IS
- Financial provider integrations (banking, brokerage, market data, credit, tax)
- Financial calculations (cashflows, NPV, IRR, tax calculations)
- Financial data models (accounts, transactions, quotes, holdings)
- Provider adapters and normalization (symbol resolution, currency conversion)

### What fin-infra IS NOT (use svc-infra instead)
- ❌ Backend framework (API scaffolding, middleware, routing)
- ❌ Auth/security (OAuth, sessions, MFA, password policies)
- ❌ Database operations (migrations, ORM, connection pooling)
- ❌ Caching infrastructure (Redis, cache decorators, TTL management)
- ❌ Logging/observability (structured logging, metrics, tracing)
- ❌ Job queues/background tasks (workers, schedulers, retries)
- ❌ Webhooks infrastructure (signing, delivery, retry logic)
- ❌ Rate limiting middleware
- ❌ Billing/payments infrastructure (use svc-infra's billing module)

### Mandatory Research Protocol Before ANY New Feature

**BEFORE implementing ANY new functionality, follow this research protocol:**

#### Step 1: Check svc-infra Comprehensively
- [ ] Search svc-infra README for related functionality
- [ ] Check svc-infra source tree: `src/svc_infra/*/` for relevant modules
- [ ] Review svc-infra docs: `src/svc_infra/docs/*.md` for guides
- [ ] Grep svc-infra codebase for similar functions/classes
- [ ] Check svc-infra's easy_* builders and add_* helpers

#### Step 2: Categorize the Functionality
Determine if the feature is:
- **Type A (Financial-specific)**: Banking API, market data, credit scores, tax forms, cashflow calculations
  → Implement in fin-infra
- **Type B (Backend infrastructure)**: API scaffolding, auth, caching, logging, jobs, webhooks, DB
  → MUST use svc-infra; mark as `[~]` in plans
- **Type C (Hybrid)**: Financial feature that needs backend support (e.g., provider metrics)
  → Use svc-infra for backend parts; fin-infra only for provider-specific logic

#### Step 3: Document Research Findings
For each item in plans.md, add a research note:
```markdown
- [ ] Research: [Feature name]
  - svc-infra check: [Module found or "not applicable"]
  - Classification: [Type A/B/C]
  - Justification: [Why fin-infra needs it or why reusing svc-infra]
  - Reuse plan: [Specific svc-infra imports if Type B/C]
```

#### Step 4: Get Approval for Implementation
- **Type A**: Proceed with fin-infra implementation
- **Type B**: Mark `[~]` and document svc-infra import pattern
- **Type C**: Design document showing clear separation (fin-infra for data, svc-infra for infrastructure)

#### Step 5: Implementation Rules
If approved for fin-infra implementation:
- No duplication of svc-infra functionality
- Import svc-infra modules where needed
- Document integration patterns in examples/
- Add tests showing fin-infra + svc-infra working together

### Examples of Correct Reuse
```python
# ✅ CORRECT: Use svc-infra for backend concerns
from svc_infra.logging import setup_logging
from svc_infra.cache import cache_read, cache_write, init_cache
from svc_infra.http import http_client_with_retry

# ✅ CORRECT: fin-infra provides financial-specific logic
from fin_infra.banking import easy_banking
from fin_infra.markets import easy_market
from fin_infra.cashflows import npv, irr
```

### Examples of INCORRECT Duplication
```python
# ❌ WRONG: Don't reimplement caching (use svc-infra)
from fin_infra.cache import cache_decorator  # NO!

# ❌ WRONG: Don't reimplement logging (use svc-infra)
from fin_infra.logging import setup_logger  # NO!

# ❌ WRONG: Don't reimplement HTTP retry logic (use svc-infra)
from fin_infra.http import RetryClient  # NO!

# ❌ WRONG: Don't implement billing (use svc-infra.billing)
from fin_infra.billing import create_subscription  # NO!
```

### Target Applications
fin-infra enables building apps like:
- **Mint**: Personal finance management, account aggregation, budgeting
- **Credit Karma**: Credit monitoring, score tracking, financial health
- **Robinhood**: Brokerage, trading, portfolio management
- **Personal Capital**: Wealth management, investment tracking
- **YNAB**: Budgeting with bank connections and transaction imports

For ALL backend infrastructure needs (API, auth, DB, cache, jobs), these apps use svc-infra.

## Legend
- [ ] Pending
- [x] Completed
- [~] Skipped (already exists in svc-infra / out of scope)
(note) Commentary or link to ADR / PR / svc-infra module.

⸻

## Must‑have (Ship with v1)

### A0. Acceptance Harness & CI Promotion Gate (new)
- [x] Design: Acceptance env contract (ports, env, seed keys, base URL). (ADR‑0001 — docs/acceptance.md)
- [x] Implement: docker-compose.test.yml + Makefile targets (accept/up/wait/seed/down).
	- Files: docker-compose.test.yml, Makefile
- [x] Implement: minimal acceptance app and first smoke test.
	- Files: tests/acceptance/app.py, tests/acceptance/test_smoke_ping.py, tests/acceptance/conftest.py
- [x] Implement: wait-for helper (Makefile curl loop) and tester container.
- [x] Verify: CI job to run acceptance matrix and teardown.
	- Files: .github/workflows/acceptance.yml
- [x] Docs: docs/acceptance.md and docs/acceptance-matrix.md updated for tester and profiles.
- [x] Supply-chain: generate SBOM and image scan (Trivy) with severity gate; upload SBOM as artifact. (acceptance.yml)
- [x] Provenance: sign SBOM artifact (cosign keyless) — best-effort for v1. (acceptance.yml)
- [~] Backend matrix: run acceptance against in‑memory + Redis (cache) profiles. (Reuse svc‑infra caching; Redis profile coverage is handled in svc‑infra contexts.)

### 0. Backfill Coverage for Base Modules (current repo)

Owner: TBD — Evidence: PRs, tests, CI runs
- Core: settings.py (timeouts/retries provided by svc‑infra; no local http wrapper)
- [~] Research: ensure pydantic‑settings (networking concerns covered in svc‑infra).
- [~] Skipped: unit tests for HTTP timeouts/retries (covered by svc‑infra).
- [ ] Docs: quickstart for settings (link to svc‑infra for timeouts/retries & caching).
- Providers skeletons:
	- Market: providers/market/yahoo.py (proto) → swap to chosen vendor(s) below.
	- Crypto: providers/market/ccxt_crypto.py (proto)
	- Banking: providers/banking/plaid_client.py (proto) → replace with default pick.
	- Brokerage: providers/brokerage/alpaca.py (paper trading)

### 1. Provider Registry & Interfaces (plug‑and‑play)
- [ ] Research: ABCs for BankingProvider, MarketDataProvider, CryptoDataProvider, BrokerageProvider.
- [ ] Design: provider registry with entry‑points + YAML mapping. (ADR‑0002)
- [ ] Implement: fin_infra/providers/base.py ABCs + registry.py loader (resolve("banking:teller")).
- [ ] Tests: dynamic import, fallback on missing providers, feature flags.
- [ ] Docs: docs/providers.md with examples + configuration table.

### 2. Banking / Account Aggregation (default: Teller)
- [ ] Research: free dev tier limits, token exchange, accounts/transactions endpoints.
- [ ] Design: auth flow contracts; token storage interface; PII boundary. (ADR‑0003)
- [ ] Implement: providers/banking/teller_client.py with typed DTOs; sandbox seed.
- [ ] Tests: integration (mocked HTTP) + acceptance: link‑token stub → accounts list → transactions list.
- [ ] Verify: acceptance profile banking=teller green.
- [ ] Docs: docs/banking.md (env vars, limits, migration path to Plaid/MX later).

### 3. Equities/FX Market Data (default: Alpha Vantage)
- [ ] Research: free tier + throttling; endpoint coverage (quote, OHLC, FX).
- [ ] Design: rate‑aware adapter with backoff. (ADR‑0004) Caching is via svc‑infra if/when endpoints are made async.
- [ ] Implement: providers/market/alpha_vantage.py (quotes, time series daily/intraday, FX). (Optionally adopt svc‑infra caching if migrating to async.)
- [ ] Tests: unit for symbol normalization; acceptance: price fetch burst obeys limits.
- [ ] Verify: acceptance profile market=alpha_vantage green.
- [ ] Docs: docs/market-data.md (quotas, caching guidance, fallbacks).

### 4. Crypto Market Data (default: CoinGecko)
- [ ] Research: free plan quotas; mapping symbol → CoinGecko id; vs CCXT.
- [ ] Design: id mapping store; normalize by asset{type, symbol, exchange?}. (ADR‑0005)
- [ ] Implement: providers/crypto/coingecko.py (spot prices, metadata) + optional ccxt candles.
- [ ] Tests: id resolution edge cases (e.g., BTC, WBTC, BTC.B), OHLC sanity.
- [ ] Verify: acceptance profile crypto=coingecko green.
- [ ] Docs: docs/crypto-data.md.

### 5. Brokerage (default: Alpaca Paper Trading)
- [ ] Research: orders, positions, clock; paper trading free.
- [ ] Design: order idempotency + replay safety; clock‑guard + risk checks. (ADR‑0006)
- [ ] Implement: providers/brokerage/alpaca.py (submit_order, positions) with idempotency key + server replay detection.
- [ ] Tests: unit for order param validation; acceptance: buy/sell happy path + duplicate submission → one order.
- [ ] Verify: acceptance profile brokerage=alpaca_paper green.
- [ ] Docs: docs/brokerage.md (keys, paper vs live, risk notes).

### 6. Caching, Rate Limits & Retries (cross‑cutting)
- [~] **REUSE svc-infra**: All caching via `svc_infra.cache` (init_cache, cache_read, cache_write)
- [~] **REUSE svc-infra**: Rate limiting via `svc_infra.api.fastapi.middleware.rate_limit`
- [~] **REUSE svc-infra**: HTTP retries via `svc_infra.http` with tenacity/httpx wrappers
- [ ] Research: Document which svc-infra modules to import for provider rate limiting
- [ ] Docs: Add examples showing svc-infra cache integration with fin-infra providers

### 7. Data Normalization: Symbols, Currencies, Time
- [ ] Research: symbol clashes (e.g., BTI across regions), ISO‑4217, crypto tickers.
- [ ] Design: canonical InstrumentKey (namespace:symbol) + FX normalization + tz handling. (ADR‑0008)
- [ ] Implement: fin_infra/normalize.py (instrument key, currency → decimal places, timezone utils, trading calendar shim).
- [ ] Tests: round‑trips across providers; FX conversions sanity.
- [ ] Docs: docs/normalization.md.

### 8. Security, Secrets & PII boundaries
- [~] **REUSE svc-infra**: Auth/sessions via `svc_infra.api.fastapi.auth`
- [~] **REUSE svc-infra**: Security middleware via `svc_infra.security`
- [~] **REUSE svc-infra**: Logging via `svc_infra.logging.setup_logging`
- [~] **REUSE svc-infra**: Secrets management via `svc_infra` settings patterns
- [ ] Research: Document PII handling specific to financial providers (SSN, account numbers)
- [ ] Design: PII encryption boundaries for provider tokens (store in svc-infra DB with encryption)
- [ ] Docs: Security guide showing svc-infra integration for auth + fin-infra provider security

### 9. Observability & SLOs
- [~] **REUSE svc-infra**: Prometheus metrics via `svc_infra.obs.add_observability`
- [~] **REUSE svc-infra**: OpenTelemetry tracing via `svc_infra.obs` instrumentation
- [~] **REUSE svc-infra**: Grafana dashboards via `svc_infra.obs` templates
- [ ] Research: Provider-specific SLIs (API availability, response times, error rates)
- [ ] Design: Financial provider SLO definitions (ADR‑0010)
- [ ] Implement: Provider call wrapper that emits metrics to svc-infra's Prometheus
- [ ] Tests: Verify provider metrics appear in svc-infra's observability stack
- [ ] Docs: Guide on wiring fin-infra providers with svc-infra observability

### 10. Demo API & SDK Surface (optional but helpful)
- [~] **REUSE svc-infra**: FastAPI app scaffolding via `svc_infra.api.fastapi.ease.easy_service_app`
- [~] **REUSE svc-infra**: Middleware (CORS, auth, rate limiting) via svc-infra
- [~] **REUSE svc-infra**: OpenAPI docs via `svc_infra.api.fastapi.docs`
- [ ] Research: Minimal financial endpoints needed for demo
- [ ] Design: Demo endpoints using svc-infra scaffolding + fin-infra providers
- [ ] Implement: examples/demo_api/ showing svc-infra + fin-infra integration
  - Use easy_service_app for FastAPI setup
  - Wire fin-infra providers as dependencies
  - Add endpoints: /banking/accounts, /market/quote, /crypto/ticker
- [ ] Tests: Integration tests using svc-infra test patterns
- [ ] Docs: docs/api.md showing how to build fintech API with both packages

### 11. DX & Quality Gates
- [ ] Research: CI pipeline steps & gaps.
- [ ] Design: gating order (ruff, mypy, pytest, SBOM, SAST stub), version bump + changelog.
- [ ] Implement: CI workflow templates under dx/ + .github/workflows/ci.yml.
- [ ] Tests: dx helpers unit tests.
- [ ] Docs: docs/contributing.md and release process.

### 12. Legal/Compliance Posture (v1 lightweight)
- [ ] Research: vendor ToS (no data resale; attribution); storage policy for PII and tokens.
- [ ] Design: data map + retention notes; toggle to disable sensitive modules.
- [ ] Implement: compliance notes page + code comments marking PII boundaries.
- [ ] Docs: docs/compliance.md (not a substitute for legal review).

⸻

## Nice‑to‑have (Fast Follows)

### 13. Multi‑Broker Aggregation (read‑only)
- [ ] Research: SnapTrade pricing and coverage.
- [ ] Design: BrokerageAggregatorProvider + account/positions sync cadence.
- [ ] Implement: providers/brokerage/snaptrade.py (read‑only holdings, transactions).
- [ ] Tests: diff‑merge holdings; symbol normalization across brokers.
- [ ] Docs: enablement + limits.

### 14. Portfolio Analytics & Optimization
- [ ] Research: PyPortfolioOpt, QuantStats, Empyrical, Statsmodels.
- [ ] Design: analytics module surface (returns, risk, factor-ish metrics; frontier/HRP optional).
- [ ] Implement: analytics/portfolio.py + examples.
- [ ] Tests: reproducibility (seeded), unit for metrics.
- [ ] Docs: docs/analytics.md.

### 15. Statements & OCR (import)
- [ ] Research: CoinGecko/CCXT statement gaps; Ocrolus/Veryfi vs Tesseract.
- [ ] Design: document ingestion pipeline; schema for transactions.
- [ ] Implement: imports/statements/* + pluggable parser interface.
- [ ] Tests: sample PDFs; redaction.
- [ ] Docs: docs/imports.md.

### 16. Identity/KYC (Stripe Identity)
- [ ] Research: free allowances; required verifications.
- [ ] Design: provider interface IdentityProvider.
- [ ] Implement: providers/identity/stripe_identity.py (start/verify/status).
- [ ] Tests: mocked integration; rate limits.
- [ ] Docs: docs/identity.md.

### 17. Payments
- [~] **REUSE svc-infra**: Payment infrastructure via `svc_infra.billing` and `svc_infra.apf_payments`
- [~] **REUSE svc-infra**: Stripe/Adyen integration via svc-infra modules
- [~] **REUSE svc-infra**: Webhook verification via `svc_infra.webhooks`
- [~] **REUSE svc-infra**: Idempotency via `svc_infra.api.fastapi.middleware.idempotency`
- [ ] Research: Financial-specific payment flows (ACH for bank transfers, brokerage funding)
- [ ] Design: Payment provider adapters for financial use cases (if different from svc-infra billing)
- [ ] Docs: Guide showing svc-infra payment integration with fin-infra banking connections

### 18. Feature Flags & Experiments
- [~] **REUSE svc-infra**: Feature flags will be provided by svc-infra (planned feature)
- [ ] Research: Financial-specific feature flags (provider switches, regulatory compliance)
- [ ] Docs: Document provider selection via flags using svc-infra's flag system

### 19. Internationalization & Trading Calendars
- [ ] Research: market calendars (NYSE, NASDAQ, LSE, crypto 24/7).
- [ ] Design: calendar abstraction; localized formatting.
- [ ] Implement: calendars/* + i18n helpers.
- [ ] Tests: open/closed behavior, holiday rules.
- [ ] Docs: docs/time-and-calendars.md.

⸻

## Quick Wins (Implement Early)

### 20. Immediate Enhancements
- [ ] Implement: per‑provider rate‑limit headers surfaced to callers. (Optional if svc‑infra layer used.)
- [ ] Implement: common error model (Problem+JSON) + error codes registry.
- [ ] Implement: order idempotency key middleware (brokerage).
- [ ] Implement: provider health‑check endpoints for demo API.
- [ ] Implement: symbol lookup endpoint (/symbols/search?q=). (Caching, if needed, via svc‑infra.)
- [ ] Implement: CLI utilities (fin‑infra):
	- keys verify, demo run, providers ls. (Remove cache‑warm; rely on svc‑infra if needed.)

⸻

## Tracking & Ordering

Prioritize Must‑have top→bottom. Interleave Quick Wins if they unlock infrastructure (e.g., retries/backoff before Alpha Vantage adapter if not using svc‑infra). Each section requires: Research complete → Design approved → Implementation + Tests → Verify → Docs.

## Notes / Decisions Log

Record ADRs for: provider registry, Alpha Vantage rate/backoff strategy (caching via svc‑infra if adopted), CoinGecko id mapping, order idempotency semantics, symbol normalization, SLOs/metrics taxonomy, PII/secret boundaries, CI gates.

**All ADRs must include a "svc-infra Reuse Assessment" section documenting:**
- What was checked in svc-infra
- Why svc-infra's solution was/wasn't suitable
- Which svc-infra modules are being reused (if any)

⸻

## svc-infra Reuse Tracking

Track all svc-infra imports and their usage:

### Already Integrated
- `svc-infra` dependency in pyproject.toml (path dependency for development)
- Backend infrastructure ready for use

### Planned Integrations (Must-have for v1)
- [ ] **Logging**: `from svc_infra.logging import setup_logging` in demo API
- [ ] **Caching**: `from svc_infra.cache import init_cache, cache_read, cache_write` for provider responses
- [ ] **API Scaffolding**: `from svc_infra.api.fastapi.ease import easy_service_app` in examples
- [ ] **Observability**: `from svc_infra.obs import add_observability` for provider metrics
- [ ] **HTTP Retry**: Use svc-infra's HTTP utilities for provider calls

### Documentation Requirements
- [ ] Create examples/demo_api/ showing full svc-infra + fin-infra integration
- [ ] Document in each provider's docs which svc-infra features to use
- [ ] Add troubleshooting guide for common integration issues

⸻

## Global Verification & Finalization
- Run full pytest suite after each major category completion.
- Re‑run flaky markers (x3) to ensure stability.
- Update this checklist with PR links & skip markers (~) for existing features.
- **Verify svc-infra reuse**: Ensure no duplicate functionality exists in fin-infra
- **Integration tests**: Test fin-infra providers with svc-infra backend components
- Produce release readiness report summarizing completed items.
- Tag version & generate changelog.

Updated: Production‑readiness plan for fin‑infra with mandatory svc-infra reuse policy. fin-infra provides ONLY financial data integrations; ALL backend infrastructure comes from svc-infra.
