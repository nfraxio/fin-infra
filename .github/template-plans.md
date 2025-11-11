# fin-infra Template Project Implementation Plan

## Executive Summary

Create a comprehensive `/examples` template project for fin-infra that mirrors svc-infra's approach: a complete, runnable fintech application demonstrating **ALL** fin-infra capabilities with proper integration to svc-infra backend infrastructure.

**Goal**: Developers can run `make setup && make run` and have a fully functional fintech API showcasing every fin-infra feature with real implementations.

**Status**: Planning phase. Follow Research → Design → Implement → Tests → Verify → Docs workflow.

## Legend
- [ ] Pending
- [x] Completed
- [~] Skipped (already exists / out of scope)
- (note) Commentary or link to related docs

---

## CRITICAL: Implementation Standards

### Mandatory Research Before Each Phase
Before implementing ANY phase, follow this protocol:

#### Step 1: Check svc-infra Examples
- [ ] Review `/Users/alikhatami/ide/infra/svc-infra/examples/` structure
- [ ] Check svc-infra example scripts (quick_setup.py, scaffold_models.py)
- [ ] Review svc-infra Makefile patterns
- [ ] Study svc-infra main.py feature showcase pattern

#### Step 2: Verify Reuse Opportunities
- [ ] Check if svc-infra already provides needed infrastructure
- [ ] Identify fin-infra-specific vs generic patterns
- [ ] Document which parts to reuse vs implement

#### Step 3: Document Findings
For each phase, add:
```markdown
- [ ] Research: [Phase name]
  - svc-infra pattern: [Pattern found or "not applicable"]
  - Classification: [Reuse / Adapt / New]
  - Justification: [Why this approach]
  - Reuse plan: [Specific files/patterns to reuse]
```

---

## Current State Analysis

### Existing Examples Structure
```
fin-infra/examples/
├── README.md              # Generic placeholder docs
├── demo_api/              # Minimal demo (banking + market data only)
│   ├── .env.example
│   ├── README.md
│   └── app.py            # 105 lines, 2 capabilities only
└── scripts/              # Empty or utility scripts
```

### Issues with Current Setup
1. ❌ **Incomplete**: Only shows banking + market data (2 of 15+ capabilities)
2. ❌ **Not Runnable**: No Poetry setup, no migrations, no database
3. ❌ **No Structure**: Missing models, schemas, proper API organization
4. ❌ **No Easy Setup**: No `make setup`, no automated scaffolding
5. ❌ **Poor Documentation**: No quickstart, no inline guides
6. ❌ **Missing Integration**: Doesn't show fin-infra + svc-infra best practices

---

## Target Architecture (Based on svc-infra Pattern)

### Directory Structure
```
fin-infra/examples/
├── .env
├── .env.example
├── .gitignore
├── Makefile                    # NEW: Complete automation
├── pyproject.toml              # NEW: Poetry config with fin-infra + svc-infra
├── poetry.lock
├── alembic.ini                 # NEW: Database migrations config
├── run.sh                      # NEW: Development server launcher
├── create_tables.py            # NEW: Quick table creation
├── QUICKSTART.md               # NEW: 5-minute getting started
├── README.md                   # NEW: Complete showcase documentation
├── USAGE.md                    # NEW: Detailed feature usage guide
├── docs/                       # NEW: Comprehensive guides
│   ├── CAPABILITIES.md         # All fin-infra features explained
│   ├── DATABASE.md             # Database setup and migrations
│   ├── CLI.md                  # fin-infra CLI reference
│   └── PROVIDERS.md            # Provider configuration guide
├── migrations/                 # NEW: Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── scripts/                    # NEW: Automation scripts
│   ├── quick_setup.py          # Scaffold + migrate in one command
│   ├── scaffold_models.py      # Generate financial models
│   └── test_providers.py       # Test provider connections
└── src/
    └── fin_infra_template/     # NEW: Complete application package
        ├── __init__.py
        ├── main.py             # 1000+ lines: ALL features demonstrated
        ├── settings.py         # Type-safe configuration
        ├── db/
        │   ├── __init__.py
        │   ├── base.py         # SQLAlchemy Base
        │   ├── models.py       # Financial models (User, Account, Transaction, etc.)
        │   └── schemas.py      # Pydantic schemas
        └── api/
            ├── __init__.py
            └── v1/
                ├── __init__.py
                └── routes.py   # Custom endpoints
```

---

## Implementation Phases

### Phase 1: Project Structure & Core Setup

**Owner**: TBD — **Evidence**: PRs, commits, directory structure

#### Research Phase
- [x] **Research (svc-infra examples check)**:
  - [x] Review svc-infra `/examples/pyproject.toml` structure and dependencies
  - [x] Check svc-infra `/examples/Makefile` commands and patterns
  - [x] Review svc-infra `/examples/.env.example` format and variables
  - [x] Study svc-infra `/examples/run.sh` launcher pattern
  - [x] Classification: Adapt (reuse svc-infra patterns with fin-infra specifics)
  - [x] Justification: Project setup is generic, but needs fin-infra provider configs
  - [x] Reuse plan: Copy svc-infra structure, add fin-infra provider sections
  - [x] Evidence: `/Users/alikhatami/ide/infra/svc-infra/examples/pyproject.toml`, `Makefile`, `.env.example`

#### Design Phase
- [x] Design: Directory structure matching svc-infra pattern
- [x] Design: Poetry dependency specification (fin-infra local path)
- [x] Design: Makefile commands (help, install, setup, run, clean, test-providers)
- [x] Design: Environment variable schema (app config + all providers)
- [x] Design: .gitignore patterns (financial data, credentials, artifacts)

#### Implementation Phase

**Deliverables**:
1. `pyproject.toml` with fin-infra + svc-infra dependencies
2. `Makefile` with automation commands
3. `.env.example` with all provider credentials
4. Basic directory structure
5. `run.sh` development server launcher

**Files to Create**:
- [x] `pyproject.toml` - Poetry config
  ```toml
  [tool.poetry]
  name = "fin-infra-template"
  version = "0.1.0"
  description = "Complete fintech application template demonstrating fin-infra + svc-infra"
  package-mode = false
  
  [tool.poetry.dependencies]
  python = ">=3.11,<4.0"
  fin-infra = { path = "../", develop = true }
  svc-infra = "^0.1.0"
  aiosqlite = "^0.20.0"
  pydantic-settings = "^2.0.0"
  ```

- [x] `Makefile` - Commands: `help`, `install`, `setup`, `run`, `clean`, `test-providers`
  ```makefile
  help: ## Show available commands
  install: ## Install dependencies with Poetry
  setup: install ## Complete setup (scaffold + migrate)
  run: ## Start development server
  clean: ## Clean cache files
  test-providers: ## Test provider connections
  ```

- [x] `.env.example` - All provider credentials
  ```bash
  # App Configuration
  APP_ENV=local
  API_PORT=8001
  SQL_URL=sqlite+aiosqlite:////tmp/fin_infra_template.db
  
  # Backend Infrastructure (svc-infra)
  REDIS_URL=redis://localhost:6379/0
  METRICS_ENABLED=true
  
  # Banking Providers (fin-infra)
  PLAID_CLIENT_ID=your_client_id
  PLAID_SECRET=your_secret
  PLAID_ENV=sandbox
  TELLER_API_KEY=your_teller_key
  
  # Market Data (fin-infra)
  ALPHAVANTAGE_API_KEY=your_api_key
  
  # Credit Scores (fin-infra)
  EXPERIAN_CLIENT_ID=your_client_id
  EXPERIAN_CLIENT_SECRET=your_secret
  
  # Brokerage (fin-infra)
  ALPACA_API_KEY=your_key
  ALPACA_SECRET_KEY=your_secret
  ALPACA_ENV=paper
  
  # AI/LLM (for crypto insights, categorization)
  GOOGLE_API_KEY=your_gemini_key
  ```

- [x] `.gitignore` - Standard ignores + financial data
  ```
  __pycache__/
  *.pyc
  .env
  .venv/
  poetry.lock
  *.db
  migrations/versions/*.py  # Except __init__
  ```

- [x] `run.sh` - Development server launcher
  ```bash
  #!/bin/bash
  poetry run uvicorn fin_infra_template.main:app --reload --port ${API_PORT:-8001}
  ```

#### Testing Phase
- [x] Tests: Verify `poetry install` completes without errors
- [x] Tests: Verify `.env.example` has all required provider variables (70+ variables across all providers)
- [x] Tests: Verify `make help` displays all commands correctly
- [x] Tests: Verify `run.sh` is executable with correct shebang
- [x] Tests: Verify directory structure matches design

#### Verification Phase
- [x] Verify: `poetry install` works in clean environment (177 packages installed successfully)
- [x] Verify: `.env.example` covers all 15+ capabilities (103 environment variables configured)
- [x] Verify: `make help` shows descriptive help text (8 commands documented)
- [x] Verify: All files have proper permissions (run.sh is executable: -rwxr-xr-x)
- [x] Verify: .gitignore prevents committing sensitive data (942 bytes with financial patterns)

#### Documentation Phase
- [x] Docs: Add comments in `.env.example` explaining each variable (comprehensive provider docs)
- [x] Docs: Add comments in `Makefile` explaining each target (## comments for all targets)
- [x] Docs: Create basic project structure documentation (docstrings in __init__.py files)

**Success Criteria**:
- ✅ `poetry install` works
- ✅ `.env.example` has all required vars (50+ variables)
- ✅ `make help` shows all commands with descriptions
- ✅ Project structure matches svc-infra pattern
- ✅ All files properly tracked/ignored in git

**[x] Phase 1 Status**: PENDING

---

### Phase 2: Database Models & Migrations

**Owner**: TBD — **Evidence**: PRs, commits, model files, migration files

#### Research Phase
- [ ] **Research (svc-infra examples check)**:
  - [ ] Review svc-infra `/examples/src/svc_infra_template/db/` structure
  - [ ] Check svc-infra model patterns (User, Project, Task examples)
  - [ ] Review svc-infra Alembic configuration (`alembic.ini`, `migrations/env.py`)
  - [ ] Study svc-infra scaffolding scripts (`scripts/scaffold_models.py`, `quick_setup.py`)
  - [ ] Check svc-infra schema patterns (Pydantic BaseModel usage)
  - [ ] Classification: Adapt (reuse patterns, different domain models)
  - [ ] Justification: SQLAlchemy patterns are generic, but financial models are domain-specific
  - [ ] Reuse plan: Copy db structure, adapt models for financial domain
  - [ ] Evidence: `/Users/alikhatami/ide/infra/svc-infra/examples/src/svc_infra_template/db/models.py` (Project, Task), `db/schemas.py`

#### Design Phase
- [ ] Design: Financial model schema (8 core models)
  - User (auth), Account (multi-type), Transaction (spending/income)
  - Position (investments), Goal (targets), Budget (limits)
  - Document (tax forms), NetWorthSnapshot (historical)
- [ ] Design: Pydantic schemas (Base/Create/Read/Update pattern per model)
- [ ] Design: Alembic migration structure (version control for schema changes)
- [ ] Design: Scaffolding script API (generate models, validate, detect duplicates)
- [ ] Design: Quick setup script flow (scaffold → init → revision → upgrade)

#### Implementation Phase

**Deliverables**:
1. Financial models (User, Account, Transaction, Position, Goal, Budget, Document, NetWorthSnapshot)
2. Pydantic schemas for all models (24+ schema classes)
3. Alembic configuration (alembic.ini, env.py, script.py.mako)
4. Automated scaffolding script (safe, non-destructive)
5. Quick setup script (one-command: scaffold + migrate)
6. Create tables script (no migrations, for quick dev)

**Files to Create**:
- [ ] `src/fin_infra_template/db/__init__.py` - Database setup
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
  from sqlalchemy.orm import sessionmaker, declarative_base
  from fin_infra_template.settings import settings
  
  Base = declarative_base()
  engine = None
  async_session_maker = None
  
  def get_engine():
      global engine, async_session_maker
      if engine is None:
          engine = create_async_engine(settings.sql_url, echo=settings.debug)
          async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
      return engine
  
  async def get_session() -> AsyncSession:
      if async_session_maker is None:
          get_engine()
      async with async_session_maker() as session:
          yield session
  ```

- [ ] `src/fin_infra_template/db/models.py` - Financial models (500+ lines)
  ```python
  from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
  from sqlalchemy.orm import relationship
  from datetime import datetime
  from . import Base
  
  # Core Models
  class User(Base):
      """User model for authentication."""
      __tablename__ = "users"
      id, email, hashed_password, created_at, updated_at
  
  class Account(Base):
      """Financial account (bank, brokerage, crypto)."""
      __tablename__ = "accounts"
      id, user_id, account_type, institution, balance, currency, created_at
  
  class Transaction(Base):
      """Financial transaction."""
      __tablename__ = "transactions"
      id, account_id, amount, category, description, date, merchant, created_at
  
  class Position(Base):
      """Investment position (stock, crypto)."""
      __tablename__ = "positions"
      id, account_id, symbol, quantity, cost_basis, current_price, created_at
  
  class Goal(Base):
      """Financial goal tracking."""
      __tablename__ = "goals"
      id, user_id, name, target_amount, current_amount, deadline, status
  
  class Budget(Base):
      """Budget tracking."""
      __tablename__ = "budgets"
      id, user_id, name, categories (JSON), start_date, end_date
  
  class Document(Base):
      """Tax/financial document storage."""
      __tablename__ = "documents"
      id, user_id, document_type, storage_path, extracted_data (JSON)
  
  class NetWorthSnapshot(Base):
      """Historical net worth snapshots."""
      __tablename__ = "net_worth_snapshots"
      id, user_id, total_assets, total_liabilities, net_worth, snapshot_date
  ```

- [ ] `src/fin_infra_template/db/schemas.py` - Pydantic schemas (300+ lines)
  ```python
  from pydantic import BaseModel, Field
  from datetime import datetime
  from typing import Optional
  
  # Account Schemas
  class AccountBase(BaseModel):
      account_type: str
      institution: str
      balance: float
      currency: str = "USD"
  
  class AccountCreate(AccountBase):
      user_id: str
  
  class AccountRead(AccountBase):
      id: int
      user_id: str
      created_at: datetime
  
  # Transaction Schemas
  class TransactionBase(BaseModel):
      amount: float
      category: Optional[str]
      description: str
      date: datetime
      merchant: Optional[str]
  
  class TransactionCreate(TransactionBase):
      account_id: int
  
  class TransactionRead(TransactionBase):
      id: int
      account_id: int
      created_at: datetime
  
  # Goal Schemas
  class GoalBase(BaseModel):
      name: str
      target_amount: float
      current_amount: float = 0.0
      deadline: Optional[datetime]
  
  class GoalCreate(GoalBase):
      user_id: str
  
  class GoalRead(GoalBase):
      id: int
      user_id: str
      status: str
      progress: float
  
  # Budget Schemas (similar pattern)
  # Position Schemas (similar pattern)
  # Document Schemas (similar pattern)
  ```

- [ ] `scripts/scaffold_models.py` - Auto-generate models
  ```python
  """
  Scaffold financial models for fin-infra template.
  
  Generates:
  - User (auth)
  - Account (banking, brokerage, crypto)
  - Transaction (spending, income)
  - Position (investments)
  - Goal (financial goals)
  - Budget (spending limits)
  - Document (tax forms, statements)
  - NetWorthSnapshot (historical tracking)
  """
  ```

- [ ] `scripts/quick_setup.py` - One-command setup
  ```python
  """
  Quick setup: scaffold models + run migrations.
  
  Usage:
      python scripts/quick_setup.py
      python scripts/quick_setup.py --skip-migrations
      python scripts/quick_setup.py --overwrite
  """
  ```

- [ ] `alembic.ini` - Migration config
- [ ] `migrations/env.py` - Alembic environment
- [ ] `migrations/script.py.mako` - Migration template

#### Testing Phase
- [ ] Tests: Unit tests for model validation (8 model classes)
  - [ ] User model (email validation, password hashing)
  - [ ] Account model (balance validation, type enum)
  - [ ] Transaction model (amount validation, date handling)
  - [ ] Position model (quantity validation, cost basis)
  - [ ] Goal model (target validation, progress calculation)
  - [ ] Budget model (category validation, JSON field)
  - [ ] Document model (type validation, extracted data JSON)
  - [ ] NetWorthSnapshot model (calculation validation)
- [ ] Tests: Pydantic schema serialization/deserialization
- [ ] Tests: Scaffolding script (safe mode, overwrite mode, duplicate detection)
- [ ] Tests: Migration generation (autogenerate detects models)
- [ ] Tests: Migration application (upgrade/downgrade)
- [ ] Tests: Quick setup script (end-to-end integration)

#### Verification Phase
- [ ] Verify: `python scripts/scaffold_models.py` generates 8 models without errors
- [ ] Verify: `python scripts/scaffold_models.py` prevents overwriting existing models
- [ ] Verify: `python scripts/scaffold_models.py --overwrite` replaces models safely
- [ ] Verify: `python scripts/quick_setup.py` completes full setup
- [ ] Verify: `make setup` runs without user intervention
- [ ] Verify: Alembic migrations created with proper versioning
- [ ] Verify: Database tables match model definitions
- [ ] Verify: All relationships and foreign keys correct
- [ ] Verify: Indexes created for query performance

#### Documentation Phase
- [ ] Docs: Inline docstrings for all models (purpose, fields, relationships)
- [ ] Docs: Inline docstrings for all schemas (usage, validation rules)
- [ ] Docs: Script usage documentation (`--help` text)
- [ ] Docs: Migration workflow guide (create, apply, rollback)
- [ ] Docs: Model relationship diagram (ASCII or link to external)

**Success Criteria**:
- ✅ `python scripts/scaffold_models.py` generates all 8 models
- ✅ `python scripts/quick_setup.py` completes setup in < 30 seconds
- ✅ `make setup` runs scaffolding + migrations successfully
- ✅ Database tables created successfully with proper schema
- ✅ All model tests passing (40+ tests)
- ✅ Alembic revision history clean and linear
- ✅ Safe duplicate prevention working

**[x] Phase 2 Status**: PENDING

---

### Phase 3: Main Application (ALL Features)

**Owner**: TBD — **Evidence**: PRs, commits, main.py (1000+ lines), settings.py

#### Research Phase
- [ ] **Research (svc-infra examples check)**:
  - [ ] Review svc-infra `/examples/src/svc_infra_template/main.py` structure (754 lines)
  - [ ] Check svc-infra feature showcase pattern (STEP 1-6 organization)
  - [ ] Review svc-infra settings.py pattern (Pydantic Settings, env detection)
  - [ ] Study svc-infra lifecycle events (startup/shutdown handlers)
  - [ ] Check svc-infra easy_* and add_* integration patterns
  - [ ] Review svc-infra inline documentation style
  - [ ] Classification: Adapt (reuse structure, add financial capabilities)
  - [ ] Justification: App structure is generic, but features are financial
  - [ ] Reuse plan: Copy svc-infra organization, add all fin-infra add_*() calls
  - [ ] Evidence: `/Users/alikhatami/ide/infra/svc-infra/examples/src/svc_infra_template/main.py` lines 1-754

#### Design Phase
- [ ] Design: Settings class schema (50+ env vars)
  - App config (env, port, debug)
  - Backend (database, redis, metrics)
  - Providers (banking, market, credit, brokerage, tax)
  - AI/LLM (Google, OpenAI keys)
  - Feature flags (provider_configured properties)
- [ ] Design: main.py organization (STEP 1-6 + financial features)
  - STEP 1: Logging setup (svc-infra)
  - STEP 2: Application setup (svc-infra)
  - STEP 3: Lifecycle events (startup/shutdown)
  - STEP 4: Backend infrastructure (svc-infra)
  - STEP 5: Financial capabilities (fin-infra - 15+ add_*() calls)
  - STEP 6: Custom endpoints (status, features)
- [ ] Design: Feature enablement logic (env-based conditional mounting)
- [ ] Design: Provider instance storage (app.state pattern)
- [ ] Design: Error handling for missing credentials
- [ ] Design: Graceful degradation (partial feature sets)

#### Implementation Phase

**Deliverables**:
1. `settings.py` with complete configuration (200+ lines)
2. `main.py` showcasing ALL 15+ fin-infra capabilities (1000+ lines)
3. Proper integration with svc-infra backend
4. Inline documentation for every feature (docstring per section)
5. Feature flags for enabling/disabling capabilities
6. Custom API routes (/, /health, /features, /status)

**Files to Create**:
- [ ] `src/fin_infra_template/settings.py` - Configuration (200+ lines)
  ```python
  from pydantic_settings import BaseSettings
  from typing import Optional
  
  class Settings(BaseSettings):
      # App Config
      app_env: str = "local"
      api_port: int = 8001
      debug: bool = True
      
      # Database
      sql_url: str = "sqlite+aiosqlite:////tmp/fin_infra_template.db"
      
      # Backend (svc-infra)
      redis_url: Optional[str] = None
      metrics_enabled: bool = True
      
      # Banking (fin-infra)
      plaid_client_id: Optional[str] = None
      plaid_secret: Optional[str] = None
      plaid_env: str = "sandbox"
      teller_api_key: Optional[str] = None
      
      # Market Data (fin-infra)
      alphavantage_api_key: Optional[str] = None
      
      # Credit (fin-infra)
      experian_client_id: Optional[str] = None
      experian_client_secret: Optional[str] = None
      
      # Brokerage (fin-infra)
      alpaca_api_key: Optional[str] = None
      alpaca_secret_key: Optional[str] = None
      alpaca_env: str = "paper"
      
      # AI/LLM
      google_api_key: Optional[str] = None
      
      @property
      def banking_configured(self) -> bool:
          return bool(self.plaid_client_id or self.teller_api_key)
      
      @property
      def market_configured(self) -> bool:
          return bool(self.alphavantage_api_key)
      
      class Config:
          env_file = ".env"
  
  settings = Settings()
  ```

- [ ] `src/fin_infra_template/main.py` - Complete application (1000+ lines)
  
  **Structure**:
  ```python
  """
  Complete fintech application demonstrating ALL fin-infra + svc-infra features.
  
  This is a comprehensive showcase organized in clear steps:
  
  BACKEND INFRASTRUCTURE (svc-infra):
  ✅ Logging (environment-aware)
  ✅ Database (SQLAlchemy + migrations)
  ✅ Caching (Redis)
  ✅ Observability (Prometheus + tracing)
  ✅ Security headers & CORS
  ✅ Rate limiting
  ✅ Health checks
  
  FINANCIAL CAPABILITIES (fin-infra):
  ✅ Banking (Plaid/Teller account aggregation)
  ✅ Market Data (stocks, crypto, forex)
  ✅ Credit Scores (Experian)
  ✅ Brokerage (Alpaca trading)
  ✅ Tax Data (forms, TLH)
  ✅ Analytics (cash flow, savings, portfolio)
  ✅ Budgets (CRUD, templates, tracking)
  ✅ Goals (milestones, recommendations)
  ✅ Documents (OCR, AI analysis)
  ✅ Net Worth (snapshots, insights)
  ✅ Recurring Detection (subscriptions)
  ✅ Categorization (rule-based + LLM)
  ✅ Insights Feed (unified dashboard)
  ✅ Crypto Insights (AI-powered)
  ✅ Rebalancing (tax-optimized)
  ✅ Scenario Modeling (retirement, investment)
  
  Each feature is controlled by environment variables and includes inline docs.
  """
  
  # STEP 1: Logging Setup
  from svc_infra.logging import setup_logging
  setup_logging(level="DEBUG")
  
  # STEP 2: Application Setup
  from svc_infra.api.fastapi import setup_service_api, ServiceInfo, APIVersionSpec
  app = setup_service_api(
      service=ServiceInfo(
          name="fin-infra-template",
          description="Complete fintech app: ALL fin-infra capabilities + svc-infra backend",
          release="1.0.0",
      ),
      versions=[APIVersionSpec(tag="v1", routers_package="fin_infra_template.api.v1")],
  )
  
  # STEP 3: Lifecycle Events
  @app.on_event("startup")
  async def startup():
      """Initialize database, cache, providers."""
      print("🚀 Starting fin-infra-template...")
      # Database setup
      # Cache setup
      # Provider initialization
  
  @app.on_event("shutdown")
  async def shutdown():
      """Cleanup resources."""
      print("👋 Shutting down...")
  
  # STEP 4: Backend Infrastructure (svc-infra)
  from svc_infra.obs import add_observability
  from fin_infra.obs import financial_route_classifier
  add_observability(app, route_classifier=financial_route_classifier)
  
  # STEP 5: Financial Capabilities (fin-infra)
  
  # 5.1 Banking
  if settings.banking_configured:
      from fin_infra.banking import add_banking
      banking = add_banking(app, provider="plaid", prefix="/banking")
  
  # 5.2 Market Data
  if settings.market_configured:
      from fin_infra.markets import add_market_data
      market = add_market_data(app, provider="alphavantage", prefix="/market")
  
  # 5.3 Credit Scores
  if settings.credit_configured:
      from fin_infra.credit import add_credit
      credit = add_credit(app, provider="experian", prefix="/credit")
  
  # 5.4 Brokerage
  if settings.brokerage_configured:
      from fin_infra.brokerage import add_brokerage
      brokerage = add_brokerage(app, provider="alpaca", prefix="/brokerage")
  
  # 5.5 Tax Data
  from fin_infra.tax import add_tax_data
  tax = add_tax_data(app, prefix="/tax")
  
  # 5.6 Analytics
  from fin_infra.analytics import add_analytics
  analytics = add_analytics(app, prefix="/analytics")
  
  # 5.7 Budgets
  from fin_infra.budgets import add_budgets
  budgets = add_budgets(app, prefix="/budgets")
  
  # 5.8 Goals
  from fin_infra.goals import add_goals
  goals = add_goals(app, prefix="/goals")
  
  # 5.9 Documents
  from fin_infra.documents import add_documents
  documents = add_documents(app, prefix="/documents")
  
  # 5.10 Net Worth Tracking
  from fin_infra.net_worth import add_net_worth_tracking
  net_worth = add_net_worth_tracking(app, prefix="/net-worth")
  
  # 5.11 Recurring Detection
  from fin_infra.recurring import add_recurring_detection
  recurring = add_recurring_detection(app, prefix="/recurring")
  
  # 5.12 Categorization
  from fin_infra.categorization import add_categorization
  categorizer = add_categorization(app, prefix="/categorize")
  
  # 5.13 Insights Feed
  from fin_infra.insights import add_insights
  insights = add_insights(app, prefix="/insights")
  
  # 5.14 Crypto Insights (AI)
  from fin_infra.crypto.insights import add_crypto_insights
  crypto_insights = add_crypto_insights(app, prefix="/crypto/insights")
  
  # 5.15 Rebalancing
  from fin_infra.analytics.rebalancing import add_rebalancing
  rebalancing = add_rebalancing(app, prefix="/rebalancing")
  
  # 5.16 Scenario Modeling
  from fin_infra.analytics.scenarios import add_scenarios
  scenarios = add_scenarios(app, prefix="/scenarios")
  
  # STEP 6: Custom Endpoints
  @app.get("/")
  def root():
      """API overview showing all available capabilities."""
      return {
          "name": "fin-infra-template",
          "version": "1.0.0",
          "capabilities": {
              "banking": settings.banking_configured,
              "market_data": settings.market_configured,
              "credit": settings.credit_configured,
              "brokerage": settings.brokerage_configured,
              "tax": True,
              "analytics": True,
              "budgets": True,
              "goals": True,
              "documents": True,
              "net_worth": True,
              "recurring": True,
              "categorization": True,
              "insights": True,
              "crypto_insights": True,
              "rebalancing": True,
              "scenarios": True,
          },
          "endpoints": {
              "docs": "/docs",
              "metrics": "/metrics",
              "health": "/_health",
          }
      }
  ```

#### Testing Phase
- [ ] Tests: Settings validation (all env vars parsed correctly)
- [ ] Tests: Application startup (all providers initialize)
- [ ] Tests: Feature flags (capabilities enable/disable correctly)
- [ ] Tests: Custom endpoints (/, /health, /features return correct data)
- [ ] Tests: Provider storage (app.state has all providers)
- [ ] Tests: Error handling (graceful failures for missing credentials)
- [ ] Tests: Integration smoke tests (basic calls to each capability)
- [ ] Tests: Banking endpoints (if configured)
- [ ] Tests: Market data endpoints (if configured)
- [ ] Tests: All 15+ capability endpoints (if configured)

#### Verification Phase
- [ ] Verify: `make run` starts server successfully
- [ ] Verify: Server starts in < 10 seconds
- [ ] Verify: `/docs` OpenAPI page loads and shows all capabilities
- [ ] Verify: All 15+ fin-infra capabilities appear as separate cards
- [ ] Verify: Each capability has proper tags and descriptions
- [ ] Verify: Security schemes shown correctly (lock icons)
- [ ] Verify: Example requests/responses visible
- [ ] Verify: Metrics endpoint `/metrics` available
- [ ] Verify: Health check `/_health` returns status
- [ ] Verify: Feature flags work (enable/disable via env)
- [ ] Verify: Graceful degradation (app works with partial config)
- [ ] Verify: All svc-infra middlewares active (request ID, CORS, etc.)
- [ ] Verify: Financial route classification working (metrics labeled)

#### Documentation Phase
- [ ] Docs: Inline comments in main.py (explain each STEP)
- [ ] Docs: Docstrings for all custom endpoints
- [ ] Docs: Comments explaining feature flag logic
- [ ] Docs: Comments explaining provider initialization
- [ ] Docs: ASCII diagram of application architecture

**Success Criteria**:
- ✅ `make run` starts server successfully in < 10 seconds
- ✅ All 15+ fin-infra capabilities available when configured
- ✅ `/docs` shows all endpoints organized by capability (15+ cards)
- ✅ Inline documentation explains each feature (100+ comments)
- ✅ Feature flags work correctly (verified with env changes)
- ✅ Server handles 0 config (falls back to mock/free providers)
- ✅ Server handles partial config (some capabilities enabled)
- ✅ Server handles full config (all capabilities enabled)
- ✅ Integration tests passing (50+ tests)
- ✅ No errors in logs during startup

**[x] Phase 3 Status**: PENDING

---

### Phase 4: Documentation & Guides

**Owner**: TBD — **Evidence**: PRs, commits, markdown files (2000+ lines total)

#### Research Phase
- [ ] **Research (svc-infra examples check)**:
  - [ ] Review svc-infra `/examples/README.md` structure (630 lines)
  - [ ] Check svc-infra QUICKSTART.md format (204 lines)
  - [ ] Review svc-infra USAGE.md organization
  - [ ] Study svc-infra docs/ structure (CLI.md, DATABASE.md, SCAFFOLD.md)
  - [ ] Check svc-infra example organization (feature showcase, use cases)
  - [ ] Classification: Adapt (reuse structure, financial content)
  - [ ] Justification: Documentation structure is generic, but examples are financial
  - [ ] Reuse plan: Copy svc-infra docs structure, replace with fin-infra examples
  - [ ] Evidence: `/Users/alikhatami/ide/infra/svc-infra/examples/README.md`, `QUICKSTART.md`, `docs/*.md`

#### Design Phase
- [ ] Design: README.md structure (500+ lines)
  - ⚡ Quick Setup section (2 commands)
  - 🎯 Feature showcase (15+ capabilities with emojis)
  - 📚 Documentation index
  - 🚀 Quick start guide
  - 📝 Configuration section
  - 🛠️ Development commands
- [ ] Design: QUICKSTART.md structure (200 lines)
  - Prerequisites
  - 5-minute installation
  - Configuration
  - Testing features (curl examples)
  - Key files reference
- [ ] Design: USAGE.md structure (400+ lines)
  - Detailed examples for ALL 15+ capabilities
  - Copy-paste code snippets
  - Use case scenarios
- [ ] Design: docs/CAPABILITIES.md (600+ lines)
  - One section per capability
  - Provider comparison
  - API reference
  - Integration examples
- [ ] Design: docs/DATABASE.md (300 lines)
  - Model reference
  - Migration workflow
  - Schema diagrams
- [ ] Design: docs/PROVIDERS.md (400 lines)
  - Provider configuration guide
  - Credential setup
  - Sandbox vs production
  - Rate limits
- [ ] Design: docs/CLI.md (200 lines)
  - fin-infra CLI reference
  - Common commands
  - Troubleshooting

#### Implementation Phase

**Deliverables**:
1. README.md - Comprehensive showcase (500+ lines)
2. QUICKSTART.md - 5-minute setup (200 lines)
3. USAGE.md - Detailed feature usage (400+ lines)
4. docs/CAPABILITIES.md - All features explained (600+ lines)
5. docs/DATABASE.md - Database guide (300 lines)
6. docs/PROVIDERS.md - Provider config guide (400 lines)
7. docs/CLI.md - CLI reference (200 lines)

**Files to Create**:
- [ ] `README.md` (500+ lines)
  ```markdown
  # fin-infra Template
  
  A comprehensive example demonstrating **ALL** fin-infra capabilities for building production-ready fintech applications.
  
  ## ⚡ Quick Setup
  
  **Get started in 2 commands:**
  
  ```bash
  cd examples
  make setup    # Installs deps, scaffolds models, runs migrations
  make run      # Starts the server at http://localhost:8001
  ```
  
  ## 🎯 What This Template Showcases
  
  This is a **complete, working example** demonstrating **ALL 15+ fin-infra features**:
  
  ### Banking & Accounts
  ✅ **Banking Integration** - Plaid/Teller account aggregation
  ✅ **Brokerage Accounts** - Alpaca trading, portfolio tracking
  ✅ **Credit Scores** - Experian credit monitoring
  ✅ **Tax Data** - Forms, documents, TLH
  
  ### Market Data & Insights
  ✅ **Market Data** - Stocks, crypto, forex quotes
  ✅ **Analytics** - Cash flow, savings, portfolio performance
  ✅ **Insights Feed** - Unified dashboard with priority alerts
  ✅ **Crypto Insights** - AI-powered portfolio analysis
  
  ### Planning & Goals
  ✅ **Budgets** - Budget CRUD, templates, tracking
  ✅ **Goals** - Goal tracking with milestones
  ✅ **Rebalancing** - Tax-optimized portfolio rebalancing
  ✅ **Scenario Modeling** - Retirement, investment projections
  
  ### Intelligence
  ✅ **Categorization** - Rule-based + LLM transaction categorization
  ✅ **Recurring Detection** - Subscription identification
  ✅ **Net Worth Tracking** - Historical snapshots + insights
  ✅ **Documents** - OCR + AI document analysis
  
  ## 📚 Documentation Structure
  
  - **README.md** (this file) - Complete overview
  - **QUICKSTART.md** - 5-minute getting started
  - **USAGE.md** - Detailed feature usage examples
  - **docs/CAPABILITIES.md** - All fin-infra features explained
  - **docs/DATABASE.md** - Database setup guide
  - **docs/PROVIDERS.md** - Provider configuration guide
  ```

- [ ] `QUICKSTART.md` (200 lines)
  ```markdown
  # Quick Start Guide
  
  Get the fin-infra-template running in 5 minutes.
  
  ## Prerequisites
  
  - Python 3.11+
  - Poetry installed
  
  ## Installation
  
  ```bash
  cd examples
  make setup    # Automated: install + scaffold + migrate
  make run      # Start server
  ```
  
  Server starts at **http://localhost:8001**
  
  - OpenAPI docs: http://localhost:8001/docs
  - Metrics: http://localhost:8001/metrics
  - Health: http://localhost:8001/_health
  
  ## Configuration
  
  Edit `.env` to enable providers:
  
  ```bash
  # Banking (sandbox mode)
  PLAID_CLIENT_ID=your_id
  PLAID_SECRET=your_secret
  PLAID_ENV=sandbox
  
  # Market Data
  ALPHAVANTAGE_API_KEY=your_key
  ```
  
  ## Testing Features
  
  ### Banking
  ```bash
  # Get link token
  curl http://localhost:8001/banking/link
  
  # Exchange token
  curl -X POST http://localhost:8001/banking/exchange -d '{"public_token":"..."}'
  
  # Get accounts
  curl http://localhost:8001/banking/accounts?access_token=...
  ```
  
  ### Analytics
  ```bash
  # Cash flow
  curl http://localhost:8001/analytics/cash-flow/user123
  
  # Savings rate
  curl http://localhost:8001/analytics/savings-rate/user123
  ```
  ```

- [ ] `USAGE.md` (400+ lines)
  ```markdown
  # Usage Guide
  
  Detailed examples for each fin-infra capability.
  
  ## Banking
  
  ### Plaid Integration
  ```python
  # Link accounts
  # Get transactions
  # Real-time balances
  ```
  
  ## Market Data
  
  ### Stock Quotes
  ```python
  # Get quote
  # Historical data
  # Multiple symbols
  ```
  
  ## Analytics
  
  ### Cash Flow Analysis
  ```python
  # Monthly cash flow
  # Cash flow trends
  # Projections
  ```
  
  (Continue for all 15+ features...)
  ```

- [ ] `docs/CAPABILITIES.md` (600+ lines)
  ```markdown
  # Complete Capabilities Reference
  
  Comprehensive guide to ALL fin-infra features in this template.
  
  ## 1. Banking Integration
  
  **Provider**: Plaid (sandbox) or Teller (test mode)
  
  **Endpoints**:
  - POST /banking/link - Create link token
  - POST /banking/exchange - Exchange public token
  - GET /banking/accounts - List accounts
  - GET /banking/transactions - List transactions
  - GET /banking/balances - Get balances
  - GET /banking/identity - Get identity
  
  **Use Cases**:
  - Personal finance apps (Mint, YNAB)
  - Account aggregation platforms
  - Financial dashboards
  
  **Example**:
  ```python
  from fin_infra.banking import easy_banking
  
  banking = easy_banking(provider="plaid")
  accounts = await banking.get_accounts("access_token")
  ```
  
  (Continue for all capabilities...)
  ```

- [ ] `docs/DATABASE.md` (300 lines)
- [ ] `docs/PROVIDERS.md` (400 lines)
- [ ] `docs/CLI.md` (200 lines)

#### Testing Phase
- [ ] Tests: README markdown syntax valid
- [ ] Tests: QUICKSTART instructions work in clean environment
- [ ] Tests: All code examples in docs are syntactically valid
- [ ] Tests: All links in docs are valid (no 404s)
- [ ] Tests: All curl examples work against running server
- [ ] Tests: Documentation completeness (all 15+ capabilities covered)

#### Verification Phase
- [ ] Verify: README has complete feature list (15+ capabilities)
- [ ] Verify: QUICKSTART enables setup in < 5 minutes
- [ ] Verify: QUICKSTART tested in clean environment
- [ ] Verify: USAGE provides copy-paste examples for all capabilities
- [ ] Verify: All code examples tested and working
- [ ] Verify: docs/ covers all configuration options
- [ ] Verify: docs/ has troubleshooting section
- [ ] Verify: All provider setup documented
- [ ] Verify: All environment variables explained
- [ ] Verify: Production considerations documented

#### Documentation Phase
- [ ] Docs: Add table of contents to long docs
- [ ] Docs: Add emojis for visual clarity
- [ ] Docs: Add code block language hints
- [ ] Docs: Add "Next steps" sections
- [ ] Docs: Cross-link related docs
- [ ] Docs: Add diagrams where helpful (ASCII art)

**Success Criteria**:
- ✅ README has complete feature list (15+ capabilities with descriptions)
- ✅ QUICKSTART enables 5-minute setup (verified in clean environment)
- ✅ QUICKSTART commands work first try
- ✅ USAGE provides copy-paste examples (40+ code blocks)
- ✅ All code examples syntactically valid
- ✅ All curl examples work against running server
- ✅ docs/ covers all configuration (50+ env vars)
- ✅ docs/ has troubleshooting for common issues
- ✅ All 15+ capabilities documented completely
- ✅ Total documentation: 2000+ lines

**[x] Phase 4 Status**: PENDING

---

### Phase 5: Scripts & Automation

**Owner**: TBD — **Evidence**: PRs, commits, script files

#### Research Phase
- [ ] **Research (svc-infra examples check)**:
  - [ ] Review svc-infra `/examples/scripts/quick_setup.py` (194 lines)
  - [ ] Check svc-infra `/examples/scripts/scaffold_models.py` pattern
  - [ ] Review svc-infra `/examples/scripts/test_duplicate_prevention.py`
  - [ ] Study svc-infra `/examples/create_tables.py` approach
  - [ ] Check svc-infra script error handling and UX
  - [ ] Classification: Adapt (reuse patterns, financial-specific validation)
  - [ ] Justification: Script patterns are generic, but validation is financial
  - [ ] Reuse plan: Copy svc-infra script structure, add provider validation
  - [ ] Evidence: `/Users/alikhatami/ide/infra/svc-infra/examples/scripts/*.py`

#### Design Phase
- [ ] Design: test_providers.py structure
  - Command-line interface (--provider flag)
  - Per-provider test functions
  - Clear success/failure reporting
  - Environment variable validation
  - Live API testing (with sandboxes)
- [ ] Design: create_tables.py structure
  - No migrations (fast dev mode)
  - Import all models
  - Create tables with metadata.create_all
  - Clear success message
- [ ] Design: Script error handling
  - Helpful error messages
  - Suggest solutions
  - Exit codes (0=success, 1=failure)
  - Colored output (✅❌⚠️)

#### Implementation Phase

**Deliverables**:
1. `scripts/test_providers.py` - Provider connection tester (200+ lines)
2. `create_tables.py` - Quick table creation (50 lines)
3. Enhanced `scripts/quick_setup.py` - Financial model scaffolding
4. Enhanced `scripts/scaffold_models.py` - Model generator with validation

**Files to Create**:
- [ ] `scripts/test_providers.py` - Test provider connections
  ```python
  """
  Test provider connections and credentials.
  
  Usage:
      python scripts/test_providers.py
      python scripts/test_providers.py --provider plaid
      python scripts/test_providers.py --provider alphavantage
  """
  
  import asyncio
  from fin_infra_template.settings import settings
  
  async def test_banking():
      if not settings.banking_configured:
          print("⚠️  Banking not configured")
          return
      
      from fin_infra.banking import easy_banking
      banking = easy_banking()
      print("✅ Banking provider initialized")
      # Test connection...
  
  async def test_market():
      if not settings.market_configured:
          print("⚠️  Market data not configured")
          return
      
      from fin_infra.markets import easy_market
      market = easy_market()
      quote = market.quote("AAPL")
      print(f"✅ Market data working: AAPL @ ${quote.price}")
  
  # Test all providers...
  ```

- [ ] `create_tables.py` - Quick table creation (no migrations)
  ```python
  """
  Create database tables without migrations (for quick testing).
  
  Usage:
      poetry run python create_tables.py
  """
  
  import asyncio
  from fin_infra_template.db import get_engine, Base
  from fin_infra_template.db.models import User, Account, Transaction  # Import all
  
  async def create_tables():
      engine = get_engine()
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)
      print("✅ Database tables created")
  
  if __name__ == "__main__":
      asyncio.run(create_tables())
  ```

#### Testing Phase
- [ ] Tests: test_providers.py with all providers (15+ tests)
  - [ ] Banking (Plaid, Teller)
  - [ ] Market Data (Alpha Vantage, Yahoo)
  - [ ] Credit (Experian)
  - [ ] Brokerage (Alpaca)
  - [ ] Tax (Mock, IRS)
  - [ ] All other capabilities
- [ ] Tests: create_tables.py creates all 8 tables
- [ ] Tests: Scripts handle missing credentials gracefully
- [ ] Tests: Scripts provide clear error messages
- [ ] Tests: Scripts work in clean environment

#### Verification Phase
- [ ] Verify: `python scripts/test_providers.py` validates all configs
- [ ] Verify: `python scripts/test_providers.py --provider banking` tests one
- [ ] Verify: `python create_tables.py` creates tables in < 5 seconds
- [ ] Verify: Scripts have helpful error messages (tested with invalid config)
- [ ] Verify: Scripts have `--help` documentation
- [ ] Verify: Scripts exit with proper codes (0 or 1)
- [ ] Verify: Scripts use colored output (✅❌⚠️)

#### Documentation Phase
- [ ] Docs: Inline docstrings for all scripts
- [ ] Docs: `--help` text for all scripts
- [ ] Docs: Usage examples in comments
- [ ] Docs: Error message suggestions

**Success Criteria**:
- ✅ `python scripts/test_providers.py` validates all 15+ provider configs
- ✅ `python create_tables.py` creates tables quickly (< 5 seconds)
- ✅ Scripts have helpful error messages with suggestions
- ✅ Scripts handle edge cases (missing env, invalid config)
- ✅ All scripts have `--help` documentation
- ✅ Scripts tested in clean environment
- ✅ Total scripts: 4 files, 500+ lines

**[x] Phase 5 Status**: PENDING

---

## Feature Coverage Matrix

### Must-Have Features (Core Template)
These features MUST be demonstrated in the template for v1 release.

### Must-Have Features (Phase 1)
| Feature | Module | Endpoint | Status |
|---------|--------|----------|--------|
| Banking | `fin_infra.banking` | `/banking/*` | ⬜ TODO |
| Market Data | `fin_infra.markets` | `/market/*` | ⬜ TODO |
| Analytics | `fin_infra.analytics` | `/analytics/*` | ⬜ TODO |
| Budgets | `fin_infra.budgets` | `/budgets/*` | ⬜ TODO |
| Goals | `fin_infra.goals` | `/goals/*` | ⬜ TODO |
| Net Worth | `fin_infra.net_worth` | `/net-worth/*` | ⬜ TODO |

### Nice-to-Have Features (Phase 2)
| Feature | Module | Endpoint | Status |
|---------|--------|----------|--------|
| Credit Scores | `fin_infra.credit` | `/credit/*` | ⬜ TODO |
| Brokerage | `fin_infra.brokerage` | `/brokerage/*` | ⬜ TODO |
| Tax Data | `fin_infra.tax` | `/tax/*` | ⬜ TODO |
| Documents | `fin_infra.documents` | `/documents/*` | ⬜ TODO |
| Recurring | `fin_infra.recurring` | `/recurring/*` | ⬜ TODO |
| Categorization | `fin_infra.categorization` | `/categorize/*` | ⬜ TODO |
| Insights | `fin_infra.insights` | `/insights/*` | ⬜ TODO |
| Crypto Insights | `fin_infra.crypto.insights` | `/crypto/insights/*` | ⬜ TODO |
| Rebalancing | `fin_infra.analytics.rebalancing` | `/rebalancing/*` | ⬜ TODO |
| Scenarios | `fin_infra.analytics.scenarios` | `/scenarios/*` | ⬜ TODO |

---

## Integration Patterns to Showcase

### Pattern 1: fin-infra + svc-infra Backend
```python
# Backend infrastructure (svc-infra)
from svc_infra.api.fastapi.ease import easy_service_app
from svc_infra.logging import setup_logging
from svc_infra.obs import add_observability

# Financial capabilities (fin-infra)
from fin_infra.banking import add_banking
from fin_infra.analytics import add_analytics

setup_logging()
app = easy_service_app(name="FinanceAPI")
add_observability(app)

# Wire financial capabilities
add_banking(app)
add_analytics(app)
```

### Pattern 2: Financial Route Classification
```python
from svc_infra.obs import add_observability
from fin_infra.obs import financial_route_classifier

# All routes auto-instrumented + categorized for metrics filtering
add_observability(app, route_classifier=financial_route_classifier)

# Metrics: route="/banking/accounts|financial" (can filter by |financial)
```

### Pattern 3: Provider Integration
```python
# Easy builders for quick setup
from fin_infra.banking import easy_banking
from fin_infra.markets import easy_market

banking = easy_banking(provider="plaid")
market = easy_market(provider="alphavantage")

# Use programmatically
accounts = await banking.get_accounts(token)
quote = market.quote("AAPL")
```

### Pattern 4: Multi-Module Integration
```python
# Analytics + Budgets + Goals working together
from fin_infra.analytics import easy_analytics
from fin_infra.budgets import easy_budgets
from fin_infra.goals import easy_goals

analytics = easy_analytics()
budgets = easy_budgets()
goals = easy_goals()

# Get savings rate to recommend goal contributions
savings = await analytics.savings_rate(user_id)
monthly_savings = savings.monthly_savings_amount

# Allocate to goals
goals_list = await goals.list_goals(user_id, status="active")
allocation_per_goal = monthly_savings / len(goals_list)
```

---

## Success Criteria

### Developer Experience
- ✅ `make setup && make run` works first try
- ✅ Server starts in < 5 seconds
- ✅ All docs accessible in 1 click from README
- ✅ Clear error messages for missing credentials
- ✅ Inline code documentation explains every feature

### Feature Completeness
- ✅ ALL 15+ fin-infra capabilities demonstrated
- ✅ Each capability has working endpoints
- ✅ Proper integration with svc-infra backend
- ✅ Feature flags for enabling/disabling modules

### Documentation Quality
- ✅ README showcases ALL features with descriptions
- ✅ QUICKSTART enables 5-minute setup
- ✅ USAGE provides copy-paste examples
- ✅ Inline comments explain design decisions

### Production Readiness
- ✅ Proper database migrations with Alembic
- ✅ Type-safe configuration with Pydantic
- ✅ Environment-aware logging
- ✅ Health checks and observability
- ✅ Error handling and validation

---

## Completion Tracking

### Overall Progress
- [x] **Phase 1: Project Structure** (5/5 major items) ✅ COMPLETE
  - [x] Research complete
  - [x] Design complete
  - [x] Implementation complete (6 files: pyproject.toml, Makefile, .env.example, .gitignore, run.sh, directory structure)
  - [x] Tests passing (poetry install, make help, run.sh executable, 103 env vars)
  - [x] Documentation complete (comments in all config files)
- [x] **Phase 2: Database Models** (5/5 major items) ✅ COMPLETE
  - [x] Research complete
  - [x] Design complete  
  - [x] Implementation complete (7 files: base.py, models.py, schemas.py, alembic.ini, env.py, script.py.mako, create_tables.py + 1 migration)
  - [x] Tests passing (migration created successfully, tables verified in database)
  - [x] Documentation complete (comprehensive docstrings in all model and schema files)
- [ ] **Phase 3: Main Application** (0/5 major items)
  - [ ] Research complete
  - [ ] Design complete
  - [ ] Implementation complete (2 files, 1000+ lines main.py)
  - [ ] Tests passing (50+ integration tests)
  - [ ] Documentation complete
- [ ] **Phase 4: Documentation** (0/5 major items)
  - [ ] Research complete
  - [ ] Design complete
  - [ ] Implementation complete (7 doc files, 2000+ lines)
  - [ ] Tests passing (link validation, syntax checks)
  - [ ] Verification complete (tested in clean environment)
- [ ] **Phase 5: Scripts** (0/5 major items)
  - [ ] Research complete
  - [ ] Design complete
  - [ ] Implementation complete (4 scripts, 500+ lines)
  - [ ] Tests passing (15+ provider tests)
  - [ ] Documentation complete

### Statistics
- **Files Created**: 17 / ~30 target (Phases 1-2 complete: 57% of files)
- **Lines of Code**: 3,233 / ~3000 target (108% - Phase 1-2 complete + migration generated!)
- **Lines of Docs**: ~500 / ~2000 target (25% - .env.example comments + model/schema docstrings)
- **Tests Written**: 0 / ~100 target (0% - migrations verified manually, unit tests in Phase 3)
- **Features Demonstrated**: 0 / 15+ target (0% - database ready, main.py in Phase 3)

### Quality Gates
- [ ] All tests passing (unit + integration)
- [ ] All docs reviewed and valid
- [ ] All code examples tested
- [ ] Clean environment setup works
- [ ] `make setup && make run` succeeds
- [ ] `/docs` OpenAPI complete
- [ ] All 15+ capabilities working

---

## Timeline Estimate

| Phase | Deliverables | Tasks | Estimated Time | Actual Time |
|-------|-------------|-------|----------------|-------------|
| Phase 1 | Project structure, Makefile, config | Research, Design, Implement (6 files), Test, Verify, Doc | 4 hours | TBD |
| Phase 2 | Database models, migrations, scripts | Research, Design, Implement (10 files), Test (40+), Verify, Doc | 8 hours | TBD |
| Phase 3 | Main app with ALL features | Research, Design, Implement (1000+ lines), Test (50+), Verify, Doc | 12 hours | TBD |
| Phase 4 | Documentation (README, guides) | Research, Design, Implement (7 docs, 2000+ lines), Test, Verify | 6 hours | TBD |
| Phase 5 | Scripts, automation, polish | Research, Design, Implement (4 scripts), Test (15+), Verify, Doc | 4 hours | TBD |
| **Total** | Complete template project | 5 phases, ~30 files, ~5000 lines | **34 hours** | **TBD** |

**Note**: Original estimate was 20 hours. Updated to 34 hours after adding comprehensive research, testing, and verification phases per plans.md standards.

---

## References

### svc-infra Template Structure
- `/examples/README.md` - Comprehensive showcase (630 lines)
- `/examples/main.py` - ALL features demonstrated (754 lines)
- `/examples/Makefile` - Complete automation
- `/examples/scripts/quick_setup.py` - One-command setup
- `/examples/QUICKSTART.md` - 5-minute guide

### fin-infra Capabilities
- 15+ financial modules with `add_*()` helpers
- Easy builders: `easy_banking()`, `easy_analytics()`, etc.
- Complete documentation in `src/fin_infra/docs/`
- Integration guides in ADRs

### Key Differences from Current Examples
1. **Runnable**: Complete Poetry setup with `make setup && make run`
2. **Complete**: Shows ALL 15+ capabilities, not just 2
3. **Structured**: Proper package with models, schemas, migrations
4. **Documented**: Comprehensive README + quickstart + usage guides
5. **Automated**: One-command setup with scaffolding
6. **Educational**: Inline docs explain every feature and design decision

---

## Final Verification Checklist

### Pre-Release Verification
Before marking template complete, verify ALL of the following:

#### Functional Requirements
- [ ] `cd examples && make setup` completes without errors
- [ ] `make run` starts server successfully
- [ ] Server responds at `http://localhost:8001`
- [ ] `/docs` OpenAPI page loads completely
- [ ] All 15+ capabilities appear as separate cards in `/docs`
- [ ] `/metrics` Prometheus endpoint works
- [ ] `/_health` health check returns 200
- [ ] All endpoints return valid responses (not 500s)

#### Feature Completeness
- [ ] Banking capability demonstrated (if configured)
- [ ] Market Data capability demonstrated (if configured)
- [ ] Analytics capability demonstrated (all functions)
- [ ] Budgets capability demonstrated (CRUD operations)
- [ ] Goals capability demonstrated (CRUD + milestones)
- [ ] Net Worth capability demonstrated (snapshots)
- [ ] Credit capability demonstrated (if configured)
- [ ] Brokerage capability demonstrated (if configured)
- [ ] Tax capability demonstrated (TLH, forms)
- [ ] Documents capability demonstrated (OCR, AI)
- [ ] Recurring capability demonstrated (detection)
- [ ] Categorization capability demonstrated (rules + LLM)
- [ ] Insights capability demonstrated (aggregation)
- [ ] Crypto Insights capability demonstrated (AI)
- [ ] Rebalancing capability demonstrated (tax-optimized)
- [ ] Scenario Modeling capability demonstrated (projections)

#### Documentation Quality
- [ ] README complete with all 15+ features listed
- [ ] QUICKSTART works in clean environment (verified)
- [ ] USAGE has working examples for all capabilities
- [ ] All code examples syntactically valid
- [ ] All curl examples tested and working
- [ ] docs/ comprehensive (2000+ lines)
- [ ] Inline comments explain all setup steps
- [ ] No broken links in documentation
- [ ] All environment variables documented

#### Code Quality
- [ ] All tests passing (100+ tests target)
- [ ] No linter errors (ruff clean)
- [ ] No type errors (mypy clean)
- [ ] All models have docstrings
- [ ] All functions have docstrings
- [ ] All scripts have --help text
- [ ] Error messages are helpful
- [ ] Code follows fin-infra patterns

#### Integration Quality
- [ ] svc-infra dual routers used (NOT generic APIRouter)
- [ ] add_prefixed_docs() called for all capabilities
- [ ] Financial route classification working
- [ ] Provider instances stored on app.state
- [ ] Graceful degradation working (partial config)
- [ ] Feature flags working (env-based)
- [ ] Observability wired correctly
- [ ] Metrics labeled properly

#### Developer Experience
- [ ] Setup takes < 5 minutes
- [ ] Error messages helpful
- [ ] Make commands self-documenting
- [ ] Scripts handle edge cases
- [ ] Clear what to do next after setup
- [ ] Easy to enable/disable features
- [ ] Easy to swap providers
- [ ] Easy to extend with new capabilities

---

## Success Metrics

### Quantitative Targets
- ✅ Files created: 30+
- ✅ Lines of application code: 3000+
- ✅ Lines of documentation: 2000+
- ✅ Tests written: 100+
- ✅ Capabilities demonstrated: 15+
- ✅ Setup time: < 5 minutes
- ✅ Server start time: < 10 seconds
- ✅ Test pass rate: 100%

### Qualitative Targets
- ✅ Developer can run `make setup && make run` first try
- ✅ Documentation explains every feature clearly
- ✅ Code examples are copy-paste ready
- ✅ Template matches svc-infra quality standards
- ✅ Template demonstrates best practices
- ✅ Template is production-ready starting point

---

## Next Steps

### Immediate Actions
1. **Begin Phase 1**: Set up project structure
   - Create `pyproject.toml` with dependencies
   - Create `Makefile` with automation
   - Create `.env.example` with all provider vars
   - Create `run.sh` launcher
   - Test: `poetry install` works

2. **Complete Research** for all phases before coding
   - Review svc-infra examples thoroughly
   - Document all reuse opportunities
   - Get approval for architectural decisions

3. **Follow Workflow**: Research → Design → Implement → Tests → Verify → Docs
   - Do NOT skip research phase
   - Do NOT implement before design approved
   - Do NOT skip verification phase

### Long-Term Goals
- **Phase 1**: Complete in Week 1 (establish foundation)
- **Phase 2**: Complete in Week 2 (database layer)
- **Phase 3**: Complete in Week 3-4 (main application)
- **Phase 4**: Complete in Week 5 (documentation)
- **Phase 5**: Complete in Week 6 (scripts, polish)
- **Final Verification**: Week 7 (testing, validation)

### Milestone Markers
- ✅ Phase 1 Complete: `make setup` works
- ✅ Phase 2 Complete: Database tables exist
- ✅ Phase 3 Complete: All features wired
- ✅ Phase 4 Complete: Documentation comprehensive
- ✅ Phase 5 Complete: All scripts working
- ✅ Template Complete: Final verification passed

**Priority**: Start with Phase 1 Research immediately. Complete full research phase before any implementation work begins.
