# fin-infra Template

A comprehensive example demonstrating **ALL** fin-infra capabilities for building production-ready fintech applications.

## ⚡ Quick Setup

**Get started in 2 commands:**

```bash
cd examples
make setup    # Installs deps, scaffolds models, runs migrations
make run      # Starts the server at http://localhost:8001
```

**✨ Features:**
- 🛡️ Safe: Won't overwrite existing models (use `--overwrite` if needed)
- 📚 Educational: Demonstrates ALL 20+ fin-infra capabilities with inline documentation
- 🎯 Complete: Full integration with svc-infra backend and ai-infra LLM features
- 🚀 Production-Ready: Shows best practices for fintech application development

📖 **See [QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide  
📚 **See [USAGE.md](USAGE.md)** - Detailed feature usage examples  
🛠️ **See [Make Commands](#-available-make-commands)** - All available commands

## 🎯 What This Template Showcases

This is a **complete, working example** that demonstrates **ALL 20+ fin-infra capabilities**:

### 🏦 Core Financial Data (Provider Integrations)
✅ **Banking Integration** - Plaid/Teller/MX account aggregation (6 endpoints)  
✅ **Market Data** - Alpha Vantage/Yahoo/Polygon stocks & ETFs (3 endpoints)  
✅ **Crypto Data** - CoinGecko/Yahoo/CCXT crypto market data (3 endpoints)  
✅ **Credit Scores** - Experian FICO/VantageScore monitoring (4 endpoints)  
✅ **Brokerage** - Alpaca paper/live trading (4 endpoints)  
✅ **Tax Data** - IRS/TaxBit forms & calculations (5 endpoints)

### 🧠 Financial Intelligence (Analytics & AI)
✅ **Analytics** - Cash flow, savings rate, spending insights, AI advice (7 endpoints)  
✅ **Categorization** - 56 MX categories, 100+ rules, LLM fallback (2 endpoints)  
✅ **Recurring Detection** - Fixed subscriptions, variable bills (2 endpoints)  
✅ **Insights Feed** - Unified dashboard from 7 sources (2 endpoints)

### 📊 Financial Planning (Goals & Budgets)
✅ **Budgets** - Multi-type, templates (50/30/20, Zero-Based), rollover (8 endpoints)  
✅ **Goals** - Milestones, multi-account funding, progress tracking (13 endpoints)  
✅ **Net Worth Tracking** - Multi-provider aggregation, snapshots (4 endpoints)

### 📄 Document & Compliance
✅ **Documents** - OCR (Tesseract/Textract), AI analysis (3 endpoints)  
✅ **Security** - PII detection, encryption, audit logging (middleware)  
✅ **Compliance** - PII classification, data retention, erasure workflows

### 🛠️ Utilities & Cross-Cutting
✅ **Normalization** - Symbol resolution, currency conversion (2 endpoints)  
✅ **Observability** - Financial route metrics, provider tracking  
✅ **Cashflows** - NPV, IRR, PMT, FV, PV calculations (5 endpoints)  
✅ **Conversation** - AI financial chat via ai-infra (3 endpoints)  
✅ **Scaffolding** - Code generation CLI for models/schemas/repos

## 🚀 Quick Start

### Option 1: Automated Setup with Make (Recommended)

The easiest way to get started:

```bash
cd examples
make setup    # Installs deps, scaffolds models, runs migrations
make run      # Starts the server
```

The `make setup` command will:
- Install dependencies via Poetry
- Create .env from template
- Generate financial models (Account, Transaction, etc.)
- Initialize Alembic migrations
- Create and apply migrations
- Provide next steps for enabling features

### Option 2: Manual Script Execution

If you prefer more control:

```bash
# 1. Navigate to examples directory
cd examples

# 2. Install dependencies
poetry install

# 3. Copy environment template
cp .env.example .env

# 4. Run automated setup (generates models + migrations)
python scripts/quick_setup.py

# 5. Start the server
make run
```

Server starts at **http://localhost:8001**

- OpenAPI docs: http://localhost:8001/docs
- Scoped banking docs: http://localhost:8001/banking/docs
- Scoped analytics docs: http://localhost:8001/analytics/docs
- Metrics: http://localhost:8001/metrics
- Health: http://localhost:8001/_health

## 📚 Documentation Structure

- **[README.md](README.md)** (this file) - Complete overview and quick start
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute getting started guide
- **[USAGE.md](USAGE.md)** - Detailed feature usage examples with code
- **[docs/CAPABILITIES.md](docs/CAPABILITIES.md)** - All fin-infra features explained
- **[docs/DATABASE.md](docs/DATABASE.md)** - Database setup and migration guide
- **[docs/PROVIDERS.md](docs/PROVIDERS.md)** - Provider configuration guide
- **[docs/CLI.md](docs/CLI.md)** - fin-infra CLI reference

## 🔧 Configuration

### Environment Variables

Edit `.env` to configure providers:

```bash
# Core Settings
APP_ENV=local
API_PORT=8001
SQL_URL=sqlite+aiosqlite:////tmp/fin_infra_template.db

# Banking Provider (Plaid Sandbox)
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox

# Market Data Provider (Alpha Vantage)
ALPHAVANTAGE_API_KEY=your_api_key

# Crypto Data Provider (CoinGecko - Free, no key required)
# COINGECKO_API_KEY=your_api_key  # Optional for higher rate limits

# Credit Score Provider (Experian Sandbox)
# EXPERIAN_CLIENT_ID=your_client_id
# EXPERIAN_CLIENT_SECRET=your_secret
# EXPERIAN_ENV=sandbox

# Brokerage Provider (Alpaca Paper Trading)
# ALPACA_API_KEY=your_api_key
# ALPACA_SECRET_KEY=your_secret_key
# ALPACA_PAPER=true

# AI Features (Google Gemini - Default)
# GOOGLE_API_KEY=your_api_key  # For conversation and AI analytics

# Caching (Optional)
# REDIS_URL=redis://localhost:6379/0

# Observability
METRICS_ENABLED=true
```

**See [docs/PROVIDERS.md](docs/PROVIDERS.md)** for complete provider setup instructions.

## 🧪 Testing Features

### Banking Integration

```bash
# Get link token (sandbox mode - no real credentials needed)
curl http://localhost:8001/banking/link

# The response includes instructions for using Plaid sandbox credentials
# Use username: user_good, password: pass_good
```

### Market Data

```bash
# Get stock quote
curl http://localhost:8001/market/quote/AAPL

# Get crypto price
curl http://localhost:8001/crypto/quote/BTC
```

### Analytics

```bash
# Get cash flow analysis
curl http://localhost:8001/analytics/cash-flow/user_123

# Get AI-powered financial advice
curl http://localhost:8001/analytics/advice/user_123
```

### Categorization

```bash
# Categorize a transaction
curl -X POST http://localhost:8001/categorize \
  -H "Content-Type: application/json" \
  -d '{"description": "STARBUCKS COFFEE", "amount": 5.75}'
```

### Cashflow Calculations

```bash
# Calculate NPV
curl -X POST http://localhost:8001/cashflows/npv \
  -H "Content-Type: application/json" \
  -d '{"rate": 0.08, "cashflows": [-10000, 3000, 4000, 5000]}'

# Calculate IRR
curl -X POST http://localhost:8001/cashflows/irr \
  -H "Content-Type: application/json" \
  -d '{"cashflows": [-10000, 3000, 4000, 5000]}'
```

**See [USAGE.md](USAGE.md)** for complete examples for ALL 20+ capabilities.

## 📦 Project Structure

```
examples/
├── README.md                 # This file
├── QUICKSTART.md            # 5-minute setup guide
├── USAGE.md                 # Detailed usage examples
├── pyproject.toml           # Dependencies
├── .env.example             # Environment template
├── Makefile                 # Automation commands
├── alembic.ini             # Migration configuration
├── create_tables.py        # Quick table creation (dev mode)
├── run.sh                  # Server startup script
├── docs/                   # Documentation
│   ├── CAPABILITIES.md     # Feature reference
│   ├── DATABASE.md         # Database guide
│   ├── PROVIDERS.md        # Provider setup
│   └── CLI.md             # CLI reference
├── migrations/             # Alembic migrations
│   ├── env.py
│   └── versions/
├── scripts/                # Automation scripts
│   ├── quick_setup.py      # Automated setup
│   ├── scaffold_models.py  # Model generator
│   └── test_providers.py   # Provider tester
├── src/                    # Application code
│   └── fin_infra_template/
│       ├── main.py         # FastAPI app (1500+ lines, 150+ comments)
│       ├── settings.py     # Configuration
│       ├── api/           # API routes
│       └── db/            # Database models
└── tests/                 # Integration tests
    └── test_main.py
```

## 🛠️ Available Make Commands

```bash
make help              # Show all commands with descriptions
make install           # Install dependencies via Poetry
make setup             # Complete setup (install + scaffold + migrate)
make run               # Start development server
make run-template      # Run with all capabilities enabled
make clean             # Clean cache and temporary files
make test              # Run all tests
make lint              # Run linters (ruff)
make format            # Format code (ruff format)
make scaffold-models   # Generate database models
make db-migrate        # Run database migrations
```

## 🏗️ Architecture Highlights

### Backend Integration (svc-infra)

This template fully integrates with **svc-infra** for backend infrastructure:

- ✅ **Dual Routers** - Uses `user_router` and `public_router` for consistent auth
- ✅ **Observability** - Prometheus metrics with financial route classification
- ✅ **Caching** - Redis integration with 24h TTL for expensive operations
- ✅ **Background Jobs** - For heavy computations and scheduled tasks
- ✅ **Structured Logging** - Environment-aware with request ID tracking
- ✅ **Health Checks** - Liveness, readiness, startup probes
- ✅ **Scoped Docs** - Each capability has its own OpenAPI documentation

### AI Integration (ai-infra)

Powered by **ai-infra** for LLM features:

- ✅ **CoreLLM** - Multi-provider support (Google Gemini default)
- ✅ **FinancialPlanningConversation** - Multi-turn Q&A with context
- ✅ **Structured Output** - Pydantic schema validation for categorization
- ✅ **Cost Tracking** - Budget enforcement ($0.10/day, $2/month caps)
- ✅ **Safety Filters** - Sensitive question detection (SSN, passwords)

### Financial Domain Logic (fin-infra)

Demonstrates **fin-infra** financial primitives:

- ✅ **Provider Abstraction** - Easy switching between providers
- ✅ **Data Normalization** - Unified models across providers
- ✅ **Financial Calculations** - NPV, IRR, compound interest, FIFO/LIFO
- ✅ **Transaction Categorization** - Rule-based + ML hybrid
- ✅ **Recurring Detection** - Subscription and bill identification
- ✅ **Net Worth Tracking** - Multi-account aggregation with snapshots

## 🎓 Learning Path

1. **Read `main.py`** - 1500+ lines with 150+ educational comments explaining every feature
2. **Run the example** - See it work with `make run`
3. **Enable providers** - Configure in `.env`, restart server to see new endpoints
4. **Test features** - Use curl examples from [USAGE.md](USAGE.md)
5. **Add custom logic** - Extend `api/v1/routes.py` with your business logic
6. **Customize models** - Modify `db/models.py` for your domain

## 📈 Cost Estimates (with real providers)

### Development (Free/Sandbox)
- **Banking**: Plaid sandbox (free)
- **Market Data**: Alpha Vantage free tier (5 calls/min, 100/day)
- **Crypto**: CoinGecko free (50 calls/min)
- **Brokerage**: Alpaca paper trading (free)
- **AI**: Google Gemini free tier (15 RPM)
- **Total**: $0/month

### Production (Low Volume)
- **Banking**: Plaid Essential ($0.11/item/month)
- **Market Data**: Alpha Vantage Premium ($50/month)
- **Credit**: Experian ($1-5/pull)
- **AI**: Google Gemini ($0.075/1M input tokens, $0.30/1M output)
- **Estimated**: $50-100/month for 100 users

**See [docs/PROVIDERS.md](docs/PROVIDERS.md)** for detailed pricing breakdown.

## 🐛 Troubleshooting

### Server won't start

```bash
# Check Python version (requires 3.11+)
python --version

# Reinstall dependencies
rm -rf .venv poetry.lock
make install

# Check for port conflicts
lsof -i :8001
```

### Provider errors

```bash
# Test provider configuration
python scripts/test_providers.py

# Verify environment variables
cat .env | grep PLAID
```

### Database errors

```bash
# Reset database
rm -f /tmp/fin_infra_template.db
python create_tables.py

# Or use migrations
poetry run alembic upgrade head
```

**See [docs/CAPABILITIES.md](docs/CAPABILITIES.md)** for capability-specific troubleshooting.

## 🤝 Contributing

This template is part of the fin-infra project. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This template is part of fin-infra and follows the same license.

## 🔗 Related Projects

- **[svc-infra](https://github.com/yourusername/svc-infra)** - Backend infrastructure primitives
- **[ai-infra](https://github.com/yourusername/ai-infra)** - AI/LLM infrastructure
- **[fin-infra](https://github.com/yourusername/fin-infra)** - Financial primitives (this project)

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/fin-infra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fin-infra/discussions)

---

**Built with ❤️ using fin-infra, svc-infra, and ai-infra**
