"""
Minimal Fintech API Demo - fin-infra + svc-infra Integration

This demo shows how to build a production-ready fintech API by combining:
- fin-infra: Financial data providers (banking, market data, crypto)
- svc-infra: Backend infrastructure (API framework, observability, logging)

Features demonstrated:
✅ FastAPI app setup with svc-infra
✅ Financial provider integration with fin-infra
✅ Observability with financial route classification
✅ Banking endpoints (Plaid/Teller)
✅ Market data endpoints (stocks, crypto)
✅ Proper error handling and logging

Run:
    python app.py
    # or
    uvicorn app:app --reload

Then visit:
    http://localhost:8000/docs - API documentation
    http://localhost:8000/metrics - Prometheus metrics
"""

from fastapi import FastAPI, HTTPException
from svc_infra.logging import setup_logging
from svc_infra.obs import add_observability

# fin-infra imports
from fin_infra.banking import add_banking
from fin_infra.markets import add_market_data
from fin_infra.obs import financial_route_classifier

# ============================================================================
# STEP 1: Logging Setup
# ============================================================================
setup_logging()

# ============================================================================
# STEP 2: Create FastAPI App
# ============================================================================
app = FastAPI(
    title="Fintech API Demo",
    description="Production-ready fintech API using fin-infra + svc-infra",
    version="1.0.0",
)

# ============================================================================
# STEP 3: Add Observability (with financial route classification)
# ============================================================================
# This automatically instruments ALL routes and adds Prometheus metrics
# The financial_route_classifier labels routes as "financial" or "public"
add_observability(app, route_classifier=financial_route_classifier)

# ============================================================================
# STEP 4: Add Financial Capabilities
# ============================================================================
# Each add_* function mounts routes, configures providers, and returns the provider instance

# Banking (Plaid/Teller) - requires credentials in .env
banking = add_banking(
    app,
    provider="plaid",  # or "teller"
    prefix="/banking",
)

# Market Data (Alpha Vantage) - requires API key in .env
market = add_market_data(
    app,
    provider="alphavantage",  # or "yahoo", "coingecko"
    prefix="/market",
)

# ============================================================================
# STEP 5: Add Custom Endpoints (Optional)
# ============================================================================


@app.get("/")
def root():
    """API root - shows available endpoints."""
    return {
        "message": "Fintech API Demo",
        "version": "1.0.0",
        "docs": "/docs",
        "metrics": "/metrics",
        "endpoints": {
            "banking": "/banking",
            "market": "/market",
        },
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# STEP 6: Run the App
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
