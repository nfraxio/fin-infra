"""Integration tests for fin-infra.

These tests require actual API credentials to run:
- PLAID_CLIENT_ID / PLAID_SECRET: Plaid credentials
- ALPHA_VANTAGE_API_KEY: Alpha Vantage API key
- yahooquery package: For Yahoo Finance (no API key needed)

Run integration tests:
    pytest tests/integration -v

Skip integration tests:
    pytest tests/integration -v -m "not integration"
"""
