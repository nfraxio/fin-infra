# fin-infra Examples

This directory contains example applications demonstrating fin-infra capabilities.

## Quick Start Examples

### Banking Connection Example
Shows how to connect bank accounts and fetch transactions:

```bash
cd examples/banking
python banking_example.py
```

### Market Data Example
Demonstrates fetching stock quotes and crypto prices:

```bash
cd examples/market_data
python market_data_example.py
```

### Cashflow Analysis Example
Shows financial calculations (NPV, IRR, loan amortization):

```bash
cd examples/cashflows
python cashflow_example.py
```

### Full Integration Example
Complete fintech app with all features integrated:

```bash
cd examples/full_app
poetry install
poetry run python app.py
```

## Example Structure

Each example directory contains:
- `README.md` - Example-specific documentation
- `.env.example` - Required environment variables
- Source code demonstrating the feature
- Tests for the example code

## Environment Setup

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
# Banking providers (sandbox/test mode)
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox

# Market data providers
ALPHAVANTAGE_API_KEY=your_api_key

# Optional: Credit providers
EXPERIAN_USERNAME=your_username
EXPERIAN_PASSWORD=your_password
```

## Running Examples

All examples require fin-infra to be installed:

```bash
# From repo root
poetry install

# Run any example
cd examples/banking
poetry run python banking_example.py
```

## Example List

- **banking/** - Bank account connections and transaction fetching
- **market_data/** - Stock and crypto market data
- **cashflows/** - Financial calculations (NPV, IRR, etc.)
- **credit/** - Credit score fetching and monitoring
- **full_app/** - Complete fintech application with all features

## Next Steps

- See [main README](../README.md) for full documentation
- Check [Getting Started Guide](../src/fin_infra/docs/getting-started.md)
- Review [Contributing Guide](../src/fin_infra/docs/contributing.md)
