# Acceptance Testing

This guide covers acceptance testing for fin-infra, including setup, running tests, and writing new acceptance tests.

## Overview

Acceptance tests verify integration with real provider APIs (in sandbox/test mode). They are:

- Marked with `@pytest.mark.acceptance`
- Excluded from default test runs
- Require provider API credentials
- Run against sandbox/test environments

## Quick Start

### 1. Set Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your sandbox credentials
# Banking
PLAID_CLIENT_ID=your_sandbox_client_id
PLAID_SECRET=your_sandbox_secret
PLAID_ENV=sandbox

# Market Data
ALPHAVANTAGE_API_KEY=your_api_key

# Credit (optional)
EXPERIAN_USERNAME=your_test_username
EXPERIAN_PASSWORD=your_test_password
```

### 2. Run Acceptance Tests

```bash
# All acceptance tests
make accept

# Or directly with pytest
poetry run pytest -q -m acceptance

# Specific test file
poetry run pytest -q -m acceptance tests/acceptance/test_banking_plaid_acceptance.py
```

## Test Structure

Acceptance tests are in `tests/acceptance/`:

```
tests/acceptance/
├── app.py                                # Test FastAPI app
├── conftest.py                           # Shared fixtures
├── test_banking_teller_acceptance.py     # Teller banking tests
├── test_crypto_coingecko_acceptance.py   # CoinGecko crypto tests
├── test_market_alphavantage_acceptance.py # Alpha Vantage tests
└── test_smoke_ping.py                    # Basic smoke test
```

## Writing Acceptance Tests

### Basic Structure

```python
import pytest
from fin_infra.banking import easy_banking

@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_get_accounts():
    """Test fetching accounts from Plaid sandbox."""
    banking = easy_banking(provider="plaid")
    
    # Use sandbox access token
    access_token = "access-sandbox-xxx"
    
    accounts = await banking.get_accounts(access_token)
    
    assert len(accounts) > 0
    assert accounts[0].account_id is not None
    assert accounts[0].name is not None
```

### Using Fixtures

```python
# conftest.py
import pytest
from fin_infra.banking import easy_banking

@pytest.fixture
async def plaid_banking():
    """Provide configured Plaid banking client."""
    return easy_banking(provider="plaid")

@pytest.fixture
def sandbox_access_token():
    """Provide sandbox access token."""
    return "access-sandbox-xxx"

# test file
@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_with_fixtures(plaid_banking, sandbox_access_token):
    accounts = await plaid_banking.get_accounts(sandbox_access_token)
    assert len(accounts) > 0
```

### Conditional Tests

Skip tests if credentials are not available:

```python
import pytest
import os

@pytest.mark.acceptance
@pytest.mark.skipif(
    not os.getenv("PLAID_CLIENT_ID"),
    reason="PLAID_CLIENT_ID not set"
)
@pytest.mark.asyncio
async def test_plaid_integration():
    # Test implementation
    pass
```

## Provider-Specific Testing

### Banking (Plaid)

```python
@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_plaid_transactions():
    from datetime import date, timedelta
    from fin_infra.banking import easy_banking
    
    banking = easy_banking(provider="plaid")
    
    transactions = await banking.get_transactions(
        access_token="access-sandbox-xxx",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
    )
    
    assert len(transactions) > 0
    assert transactions[0].amount is not None
```

### Market Data (Alpha Vantage)

```python
@pytest.mark.acceptance
def test_alphavantage_quote():
    from fin_infra.markets import easy_market
    
    market = easy_market(provider="alphavantage")
    quote = market.quote("AAPL")
    
    assert quote.symbol == "AAPL"
    assert quote.price > 0
```

### Crypto (CoinGecko)

```python
@pytest.mark.acceptance
def test_coingecko_ticker():
    from fin_infra.markets import easy_crypto
    
    crypto = easy_crypto(provider="coingecko")
    ticker = crypto.ticker("BTC/USDT")
    
    assert ticker.symbol == "BTC/USDT"
    assert ticker.last > 0
```

## CI/CD Integration

### GitHub Actions

Acceptance tests run in CI when provider secrets are configured:

```yaml
# .github/workflows/acceptance.yml
name: Acceptance Tests

on: [push, pull_request]

jobs:
  acceptance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run acceptance tests
        env:
          ALPHAVANTAGE_API_KEY: ${{ secrets.ALPHAVANTAGE_API_KEY }}
          PLAID_CLIENT_ID: ${{ secrets.PLAID_CLIENT_ID }}
          PLAID_SECRET: ${{ secrets.PLAID_SECRET }}
        run: poetry run pytest -q -m acceptance
```

### Required Secrets

Add these to GitHub Settings → Secrets and variables → Actions:

- `ALPHAVANTAGE_API_KEY`
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `EXPERIAN_USERNAME` (optional)
- `EXPERIAN_PASSWORD` (optional)

## Documents Acceptance Tests

Financial document management acceptance tests (Layer 2 features):

### Test Coverage

- **A_FIN_DOC_01**: Upload financial document with DocumentType
- **A_FIN_DOC_02**: OCR extraction with default provider
- **A_FIN_DOC_03**: OCR with specific provider selection
- **A_FIN_DOC_04**: W-2 field extraction (employer, wages, taxes)
- **A_FIN_DOC_05**: AI analysis generates financial insights
- **A_FIN_DOC_06**: Analysis includes professional advisor disclaimer
- **A_FIN_DOC_07**: List documents filtered by type

### Running Documents Tests

```bash
# Run all documents acceptance tests
poetry run pytest -q -m acceptance tests/acceptance/test_documents_acceptance.py

# Run specific test
poetry run pytest -q -m acceptance tests/acceptance/test_documents_acceptance.py::test_a_fin_doc_02_ocr_extraction_default_provider
```

### No Credentials Required

Documents acceptance tests use in-memory storage and mock OCR/analysis providers, so no external API credentials are needed.

## Best Practices

1. **Use Sandbox/Test Environments**: Never use production credentials
2. **Rate Limiting**: Respect provider rate limits
3. **Test Data**: Use provider test data where available
4. **Cleanup**: Clean up test data after tests
5. **Idempotency**: Make tests idempotent where possible
6. **Documentation**: Document required credentials and setup

## Troubleshooting

### Tests Skipped

If tests are skipped, check:
- Environment variables are set correctly
- Credentials are valid for sandbox/test environment
- Provider API is accessible

### Rate Limiting

If you hit rate limits:
- Add delays between tests: `await asyncio.sleep(1)`
- Use caching for repeated calls
- Request higher rate limits from provider

### Authentication Errors

If authentication fails:
- Verify credentials are correct
- Check environment variable names
- Ensure using correct environment (sandbox vs production)

## Next Steps

- [Contributing Guide](contributing.md)
- [Banking Integration](banking.md)
- [Market Data Integration](market-data.md)
