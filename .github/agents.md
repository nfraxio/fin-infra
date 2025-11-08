# agents.md (fin-infra)

## What this repo is
- `fin-infra` is a **generic, reusable financial infrastructure package** for ANY fintech application: personal finance apps, wealth management platforms, banking apps, investment trackers, budgeting tools, etc.
- **NOT application-specific**: fin-infra is designed to serve MANY applications and teams building fintech products. It provides the financial primitives; each application builds its own UI and business logic on top.
- **NOT a backend framework**: fin-infra provides ONLY financial-specific integrations. All backend infrastructure (API, auth, DB, cache, jobs, webhooks) comes from `svc-infra`.
- Supported Python: 3.11–3.13. Publish-ready package via Poetry; CLI entrypoint `fin-infra`.

## Product goal
- **Generic fintech toolkit**: Serve ANY team building fintech applications (personal finance, wealth management, banking, budgeting, investment tracking, tax planning, etc.)
- **Reusable primitives**: Banking connections, brokerage integrations, market data, credit scores, tax calculations, cashflow analysis, portfolio analytics, transaction categorization, recurring detection, etc.
- **Multi-application design**: fin-infra-web is ONE example application using fin-infra; many other teams can build different apps with the same package
- **Provider-agnostic**: Support multiple providers per domain (Plaid/Teller/MX for banking, Alpaca/IB for brokerage, Alpha Vantage/Yahoo/Polygon for market data)
- **Easy integration**: One-call setup per capability with sensible defaults and minimal configuration
- **Mandatory reuse**: Always use svc-infra for backend concerns; never duplicate infrastructure code
- **Developer ergonomics**: Consistent APIs, clear models, comprehensive tests and docs

## Example Use Cases (fin-infra serves ALL of these)
1. **Personal Finance Apps** (like Mint, YNAB, Personal Capital): Budget tracking, net worth, transactions, goals
2. **Investment Platforms** (like Robinhood, Webull, E*TRADE): Brokerage integration, portfolio analytics, market data
3. **Banking Apps** (like Chime, Revolut, N26): Account aggregation, transaction categorization, spending insights
4. **Wealth Management** (like Betterment, Wealthfront, Vanguard): Portfolio rebalancing, tax-loss harvesting, financial planning
5. **Budgeting Tools** (like Simplifi, PocketGuard): Cash flow analysis, recurring detection, budget management
6. **Tax Planning Apps** (like TurboTax, H&R Block): Tax liability estimation, crypto gains, document management
7. **Credit Monitoring** (like Credit Karma, Credit Sesame): Credit score tracking, report analysis
8. **Crypto Platforms** (like Coinbase, Crypto.com): Crypto portfolio tracking, tax reporting, market data

**fin-infra-web** is a comprehensive reference implementation showing most capabilities, but other teams will build different UIs and workflows using the same fin-infra primitives.

## Critical Boundaries: fin-infra vs svc-infra vs ai-infra

**Golden Rule**: ALWAYS check svc-infra AND ai-infra FIRST before implementing any feature.

### fin-infra scope (ONLY financial integrations)
- ✅ Banking provider adapters (Plaid, Teller, MX)
- ✅ Brokerage integrations (Alpaca, Interactive Brokers, SnapTrade)
- ✅ Market data (stocks, crypto, forex via Alpha Vantage, CoinGecko, Yahoo, Polygon)
- ✅ Credit scores (Experian, Equifax, TransUnion)
- ✅ Tax data (IRS, TaxBit, document management, crypto gains)
- ✅ Financial calculations (NPV, IRR, PMT, FV, PV, loan amortization, portfolio analytics)
- ✅ Financial data models (accounts, transactions, quotes, holdings, credit reports, goals, budgets)
- ✅ Provider normalization (symbol resolution, currency conversion, institution mapping)
- ✅ Transaction categorization (rule-based + ML models with financial context)
- ✅ Recurring detection (subscription identification, bill tracking)
- ✅ Net worth tracking (multi-account aggregation, snapshots, financial insights)
- ✅ Budget management (budget CRUD, tracking, overspending alerts)
- ✅ Cash flow analysis (income vs expenses, forecasting, projections)
- ✅ Portfolio analytics (returns, allocation, benchmarking, rebalancing)
- ✅ Goal management (goal CRUD, progress tracking, validation, recommendations)
- ✅ **Financial-specific LLM prompts** (few-shot examples with merchant names, financial advice, budget recommendations)
- ✅ **Financial domain logic** (FIFO/LIFO calculations, compound interest, amortization schedules)

### svc-infra scope (USE, don't duplicate)
- ✅ API framework (FastAPI scaffolding, routing, middleware, dual routers)
- ✅ Auth & security (OAuth, sessions, MFA, password policies, JWT)
- ✅ Database (SQL/Mongo migrations, ORM, connection management)
- ✅ Caching (Redis, cache decorators, TTL management, invalidation)
- ✅ Logging & observability (structured logs, Prometheus metrics, Grafana, OpenTelemetry)
- ✅ Job queues (background tasks, workers, schedulers, retry logic)
- ✅ Webhooks (signing, delivery, retry, subscription management)
- ✅ Rate limiting (middleware, decorators, distributed limiting)
- ✅ Billing & payments (Stripe/Adyen integration, subscriptions, invoices)
- ✅ HTTP utilities (retry logic with tenacity, timeout management)

### ai-infra scope (USE, don't duplicate)
- ✅ **LLM inference** (CoreLLM with multi-provider support: OpenAI, Anthropic, Google, etc.)
- ✅ **Structured output** (Pydantic schema validation, with_structured_output, output_schema parameter)
- ✅ **Conversation management** (FinancialPlanningConversation for multi-turn Q&A)
- ✅ **Context management** (conversation history, session storage, context windows)
- ✅ **LLM utilities** (token counting, cost tracking, retry logic, rate limiting)
- ✅ **Provider abstraction** (unified interface for OpenAI/Anthropic/Google/etc.)
- ✅ **Agent framework** (LangGraph integration, tool calling, multi-step reasoning)

### Integration Pattern (fin-infra + svc-infra + ai-infra)

```python
# Backend infrastructure from svc-infra
from svc_infra.api.fastapi.dual.public import public_router
from svc_infra.cache import cache_read, cache_write
from svc_infra.jobs import easy_jobs

# AI infrastructure from ai-infra
from ai_infra.llm import CoreLLM
from ai_infra.conversation import FinancialPlanningConversation

# Financial logic from fin-infra
from fin_infra.banking import easy_banking
from fin_infra.categorization import easy_categorization

# fin-infra provides ONLY financial domain logic and prompts
# All LLM calls go through ai-infra.llm.CoreLLM
# All backend features use svc-infra
```

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

## Router & API Standards (MANDATORY)

### All fin-infra Routers MUST Use svc-infra Dual Routers
**CRITICAL**: Never use generic `fastapi.APIRouter`. Always use svc-infra dual routers for consistent auth, OpenAPI, and trailing slash handling.

#### Router Selection Guide
- **Public data** (market quotes, public tax forms): `from svc_infra.api.fastapi.dual.public import public_router`
- **Provider-specific tokens** (banking with Plaid/Teller tokens): `from svc_infra.api.fastapi.dual.public import public_router` + custom token validation
- **User-authenticated** (brokerage trades, credit reports): `from svc_infra.api.fastapi.dual.protected import user_router`
- **Service-only** (provider webhooks, admin): `from svc_infra.api.fastapi.dual.protected import service_router`

#### Implementation Pattern
```python
# ❌ WRONG: Never use generic FastAPI router
from fastapi import APIRouter
router = APIRouter(prefix="/market")

# ✅ CORRECT: Use svc-infra dual router
from svc_infra.api.fastapi.dual.public import public_router
router = public_router(prefix="/market", tags=["Market Data"])

# ✅ CORRECT: Protected user routes
from svc_infra.api.fastapi.dual.protected import user_router
router = user_router(prefix="/brokerage", tags=["Brokerage"])
```

#### Benefits of Dual Routers
- Automatic dual route registration (with/without trailing slash, no 307 redirects)
- Consistent OpenAPI security annotations (lock icons in docs)
- Pre-configured auth dependencies (RequireUser, RequireService, etc.)
- Standardized error responses (401, 403, 500)
- Better developer experience matching svc-infra patterns

#### FastAPI Helper Requirements
Every fin-infra capability with an `add_*()` helper must:
1. Use appropriate dual router (public_router, user_router, etc.)
2. Mount with `include_in_schema=True` for OpenAPI visibility
3. Use descriptive tags for doc organization (e.g., "Banking", "Market Data")
4. **CRITICAL**: Call `add_prefixed_docs()` to register landing page card
5. Return provider instance for programmatic access
6. Store provider on `app.state` for route access

Example:
```python
def add_market_data(app: FastAPI, provider=None, prefix="/market") -> MarketDataProvider:
    from svc_infra.api.fastapi.dual.public import public_router
    from svc_infra.api.fastapi.docs.scoped import add_prefixed_docs
    
    market = easy_market(provider=provider)
    router = public_router(prefix=prefix, tags=["Market Data"])
    
    @router.get("/quote/{symbol}")
    async def get_quote(symbol: str):
        return market.quote(symbol)
    
    app.include_router(router, include_in_schema=True)
    
    # Register scoped docs for landing page card (REQUIRED)
    add_prefixed_docs(
        app,
        prefix=prefix,
        title="Market Data",
        auto_exclude_from_root=True,
        visible_envs=None,  # Show in all environments
    )
    
    app.state.market_provider = market
    return market
```

**Why `add_prefixed_docs()` is required**:
- Creates separate documentation card on landing page (like /auth, /payments cards in svc-infra)
- Generates scoped OpenAPI schema at `{prefix}/openapi.json`
- Provides dedicated Swagger UI at `{prefix}/docs`
- Provides dedicated ReDoc at `{prefix}/redoc`
- Excludes capability routes from root docs (keeps root clean)
- Without this call, routes work but don't appear as cards on landing page

### Documentation Card Requirements
Each capability must have:
1. **README section** with capability card (overview, quick start, use cases)
2. **Dedicated doc file** in `docs/` (e.g., `docs/banking.md`, `docs/market-data.md`)
3. **OpenAPI visibility** via dual routers with proper tags
4. **ADR** if architectural decisions were made (e.g., `docs/adr/0003-banking-integration.md`)
5. **Integration examples** showing fin-infra + svc-infra usage

## AI/LLM Integration Standards (MANDATORY)

**CRITICAL**: fin-infra must NEVER duplicate AI infrastructure from ai-infra.

### What fin-infra Provides (Financial Domain Logic)
- ✅ **Financial prompts**: Few-shot examples with merchant names, tax rules, investment advice
- ✅ **Financial schemas**: Pydantic models for financial outputs (CategoryPrediction, CryptoTaxReport, etc.)
- ✅ **Financial context**: Account balances, transaction history, market data for LLM inputs
- ✅ **Financial validation**: Local calculations (compound interest, FIFO/LIFO) to validate LLM outputs

### What ai-infra Provides (AI Infrastructure - REUSE ONLY)
- ✅ **LLM clients**: CoreLLM with multi-provider support (OpenAI, Anthropic, Google, etc.)
- ✅ **Structured output**: Pydantic schema validation, output_schema parameter
- ✅ **Conversation**: FinancialPlanningConversation for multi-turn Q&A with context management
- ✅ **Cost tracking**: Token counting, budget enforcement, daily/monthly caps
- ✅ **Retry logic**: Exponential backoff, rate limit handling, graceful degradation

### Correct LLM Usage Patterns

✅ **DO**: Use ai-infra for ALL LLM infrastructure
```python
from ai_infra.llm import CoreLLM
from ai_infra.conversation import FinancialPlanningConversation

# Single-shot inference with structured output
llm = CoreLLM(provider="google_genai", model="gemini-2.0-flash-exp")
result = await llm.achat(
    messages=[{"role": "user", "content": financial_prompt}],
    output_schema=CategoryPrediction,  # fin-infra Pydantic model
    output_method="prompt",
)

# Multi-turn conversation
conversation = FinancialPlanningConversation(llm=llm)
response = await conversation.ask(
    user_id="user123",
    question="How can I save more money?",
    net_worth=net_worth_data,  # fin-infra provides financial context
    goals=goals_data,
)
```

❌ **DON'T**: Build custom LLM clients or conversation managers
```python
# WRONG: Custom LLM client (ai-infra provides CoreLLM)
import openai
client = openai.Client(api_key="...")

# WRONG: Custom conversation manager (ai-infra provides FinancialPlanningConversation)
class ChatHistory:
    def __init__(self):
        self.messages = []
    def add_message(self, role, content): ...

# WRONG: Custom structured output (ai-infra provides with_structured_output)
def parse_llm_json(response_text):
    return json.loads(response_text)
```

### Decision Tree: When to Use Structured Output vs Natural Dialogue

**Use `output_schema` (structured)** for:
- ✅ Single-shot inference (categorization, insights, normalization)
- ✅ Data extraction (parse tax forms, extract transaction details)
- ✅ Classification (assign category, detect recurring pattern)
- ✅ Validation (check goal feasibility, verify budget allocation)

**Use natural dialogue (NO output_schema)** for:
- ✅ Multi-turn conversation (financial planning Q&A)
- ✅ Explanations (why did this transaction categorize as X?)
- ✅ Recommendations (what should I do to reach my goal?)
- ✅ Follow-up questions (user asks for clarification)

### Cost Management (MANDATORY for all LLM features)
- [ ] Track daily/monthly spend per user
- [ ] Enforce budget caps ($0.10/day, $2/month default)
- [ ] Use svc-infra cache for expensive operations (24h TTL for insights, 7d for normalizations)
- [ ] Target: <$0.10/user/month with caching
- [ ] Graceful degradation when budget exceeded (fall back to rule-based logic)

### Safety & Disclaimers (MANDATORY)
- [ ] Add "Not a substitute for certified financial advisor" in all financial advice prompts
- [ ] Filter sensitive questions (SSN, passwords, account numbers) before sending to LLM
- [ ] Log all LLM calls for compliance (use svc-infra logging)
- [ ] Never send PII to LLM without user consent

## Contribution expectations
- **MANDATORY: Check svc-infra AND ai-infra first**: Before adding ANY feature, verify neither svc-infra nor ai-infra already provide it.
- **MANDATORY: Use dual routers**: All FastAPI routers must use svc-infra dual routers (public_router, user_router, etc.)
- **MANDATORY: Use ai-infra for LLM**: All LLM calls must go through ai-infra.llm.CoreLLM (never custom LLM clients)
- **Document reuse**: Always document which svc-infra and ai-infra modules are used and why.
- **Financial-only**: Keep adapters focused on financial data; delegate backend to svc-infra, AI to ai-infra.
- **Type safety**: All provider methods must have full type hints and Pydantic models.
- **Documentation cards**: Each capability needs README card, dedicated doc, and OpenAPI visibility.
- **Testing**: Add unit tests for logic; acceptance tests for provider integrations; mock LLM calls in unit tests.
- **Quality gates**: Run format, lint, type, test before submitting PRs.

## Agent workflow expectations
- **Hard gate: Research svc-infra AND ai-infra FIRST**: Before implementing ANY feature, check if svc-infra OR ai-infra provides it.
- **Hard gate: Use dual routers**: Never use generic APIRouter; always use svc-infra dual routers.
- **Hard gate: Use ai-infra LLM**: Never build custom LLM clients; always use ai-infra.llm.CoreLLM.
- **Stage gates**: Research → Design → Implement → Tests → Verify → Docs (no skipping).
- **Reuse documentation**: Document all svc-infra and ai-infra imports and why they're used.
- **Documentation complete**: Ensure README card, dedicated doc file, and OpenAPI visibility for each capability.
- **Examples**: Show fin-infra + svc-infra + ai-infra integration patterns in docs.
- **Quality report**: Run all checks (format, lint, type, test) and report results before finishing.
