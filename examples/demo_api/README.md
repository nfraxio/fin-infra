# Fintech API Demo

Minimal production-ready fintech API demonstrating **fin-infra + svc-infra** integration.

## Features

- ✅ **Banking** - Connect bank accounts via Plaid/Teller
- ✅ **Market Data** - Real-time stock quotes and crypto prices
- ✅ **Observability** - Prometheus metrics with financial route classification
- ✅ **Logging** - Structured logging with svc-infra
- ✅ **Auto Docs** - OpenAPI/Swagger documentation
- ✅ **Production Ready** - Proper error handling, health checks, metrics

## Quick Start

### 1. Install Dependencies

```bash
# Install both packages
pip install svc-infra fin-infra

# Or use Poetry
poetry add svc-infra fin-infra
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API credentials:
# - PLAID_CLIENT_ID, PLAID_SECRET (for banking)
# - ALPHAVANTAGE_API_KEY (for market data)
```

### 3. Run the Server

```bash
# Run directly
python app.py

# Or with uvicorn
uvicorn app:app --reload
```

### 4. Test the API

Visit http://localhost:8000/docs to see interactive API documentation.

**Example requests:**

```bash
# Health check
curl http://localhost:8000/health

# Get stock quote (requires Alpha Vantage API key)
curl http://localhost:8000/market/quote/AAPL

# Get crypto ticker (uses free CoinGecko API)
curl http://localhost:8000/market/crypto/bitcoin

# View Prometheus metrics
curl http://localhost:8000/metrics
```

## API Endpoints

### General

- `GET /` - API root with available endpoints
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /metrics` - Prometheus metrics

### Banking (`/banking`)

Requires Plaid or Teller credentials configured.

- `GET /banking/accounts` - List connected bank accounts
- `GET /banking/transactions` - Get account transactions
- `GET /banking/balances` - Get account balances

See `/docs` for full parameters and responses.

### Market Data (`/market`)

Requires Alpha Vantage API key (or uses free CoinGecko for crypto).

- `GET /market/quote/{symbol}` - Get stock quote (e.g., AAPL, GOOGL)
- `GET /market/search?query=apple` - Search for stocks
- `GET /market/crypto/{symbol}` - Get crypto price (e.g., bitcoin, ethereum)

See `/docs` for full parameters and responses.

## Architecture

```
fin-infra (Financial Providers)
    ├── Banking: Plaid, Teller
    ├── Market Data: Alpha Vantage, CoinGecko
    └── Observability: financial_route_classifier

svc-infra (Backend Infrastructure)
    ├── API Framework: FastAPI setup
    ├── Logging: Structured logs
    ├── Observability: Prometheus metrics
    └── Middleware: CORS, security headers

app.py (Your Application)
    ├── Wire fin-infra providers
    ├── Use svc-infra infrastructure
    └── Add custom business logic
```

## Code Walkthrough

```python
from fastapi import FastAPI
from svc_infra.logging import setup_logging
from svc_infra.obs import add_observability
from fin_infra.banking import add_banking
from fin_infra.markets import add_market_data
from fin_infra.obs import financial_route_classifier

# 1. Setup logging (svc-infra)
setup_logging()

# 2. Create FastAPI app
app = FastAPI(title="Fintech API")

# 3. Add observability with financial route classification
add_observability(app, route_classifier=financial_route_classifier)

# 4. Add financial capabilities (fin-infra)
add_banking(app, provider="plaid")
add_market_data(app, provider="alphavantage")

# All routes automatically instrumented with metrics!
# Financial routes labeled as |financial in metrics
# Can filter in Grafana: route=~".*\\|financial"
```

## Observability

### Metrics

The API automatically exposes Prometheus metrics at `/metrics`:

```promql
# Request count by route class
http_server_requests_total{route=~".*\\|financial"}

# P95 latency for financial routes
histogram_quantile(0.95,
  rate(http_server_request_duration_seconds_bucket{route=~".*\\|financial"}[5m])
)
```

### Logs

Structured logs are automatically enabled:

```json
{
  "timestamp": "2025-11-06T12:34:56.789Z",
  "level": "INFO",
  "message": "Request completed",
  "method": "GET",
  "path": "/market/quote/AAPL",
  "status_code": 200,
  "duration_ms": 123.45
}
```

## Provider Configuration

### Banking Providers

**Plaid** (Default):
```env
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # or production
```

**Teller** (Alternative):
```env
TELLER_APP_ID=your_app_id
TELLER_CERTIFICATE=./cert.pem
TELLER_PRIVATE_KEY=./key.pem
TELLER_ENV=sandbox  # or production
```

### Market Data Providers

**Alpha Vantage** (Default for stocks):
```env
ALPHAVANTAGE_API_KEY=your_api_key
```

**CoinGecko** (Free, no API key needed for crypto):
```env
# No configuration needed - uses public API
```

## Extending the Demo

### Add Credit Scores

```python
from fin_infra.credit import add_credit_monitoring

credit = add_credit_monitoring(app, provider="experian")
```

### Add Brokerage

```python
from fin_infra.brokerage import add_brokerage

brokerage = add_brokerage(app, provider="alpaca")
```

### Add Custom Endpoints

```python
@app.get("/portfolio/summary")
def get_portfolio_summary():
    # Use fin-infra providers directly
    accounts = banking.get_accounts(token)
    positions = brokerage.get_positions()
    
    return {
        "cash": sum(a.balance for a in accounts),
        "investments": sum(p.value for p in positions),
    }
```

## Production Deployment

For production, use svc-infra's full setup:

```python
from svc_infra.api.fastapi import setup_service_api, ServiceInfo, APIVersionSpec

app = setup_service_api(
    service=ServiceInfo(
        name="fintech-api",
        description="Production fintech API",
        release="1.0.0",
    ),
    versions=[
        APIVersionSpec(tag="v1", routers_package="your_app.api.v1"),
    ],
)

# Add fin-infra providers
add_banking(app)
add_market_data(app)

# Add svc-infra features
from svc_infra.security.add import add_security
from svc_infra.api.fastapi.ops.add import add_probes, add_maintenance_mode

add_security(app)  # Security headers, CORS
add_probes(app)    # Kubernetes probes
add_maintenance_mode(app)  # Graceful degradation
```

See [svc-infra examples](https://github.com/Aliikhatami94/svc-infra/tree/main/examples) for full production setup.

## Troubleshooting

### Provider Credentials Not Found

**Error**: `ProviderNotConfiguredError: Missing PLAID_CLIENT_ID`

**Solution**: Copy `.env.example` to `.env` and add your credentials.

### API Key Invalid

**Error**: `401 Unauthorized` from provider

**Solution**: Verify your API keys are correct and active. For sandbox environments, ensure you're using sandbox keys.

### Metrics Not Showing

**Error**: `/metrics` endpoint returns 404

**Solution**: Ensure `METRICS_ENABLED=true` in `.env` or environment.

## Learn More

- [fin-infra Documentation](../../src/fin_infra/docs/)
- [svc-infra Documentation](https://github.com/Aliikhatami94/svc-infra/tree/main/src/svc_infra/docs)
- [Banking Integration Guide](../../src/fin_infra/docs/banking.md)
- [Market Data Guide](../../src/fin_infra/docs/market-data.md)
- [Observability Guide](../../src/fin_infra/docs/observability.md)

## License

MIT
