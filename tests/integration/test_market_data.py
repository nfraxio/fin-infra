"""Integration tests for market data providers.

These tests require API keys for some providers:
- Alpha Vantage: ALPHA_VANTAGE_API_KEY or ALPHAVANTAGE_API_KEY
- Yahoo Finance: No API key needed (uses yahooquery package)

Run with: pytest tests/integration/test_market_data.py -v
"""

from __future__ import annotations

import os
from datetime import UTC
from decimal import Decimal

import pytest

# Check if yahooquery is available
try:
    from yahooquery import Ticker as _Ticker  # noqa: F401

    HAS_YAHOOQUERY = True
except ImportError:
    HAS_YAHOOQUERY = False

# Skip markers
SKIP_NO_ALPHAVANTAGE = pytest.mark.skipif(
    not (os.environ.get("ALPHA_VANTAGE_API_KEY") or os.environ.get("ALPHAVANTAGE_API_KEY")),
    reason="ALPHA_VANTAGE_API_KEY not set",
)

SKIP_NO_YAHOOQUERY = pytest.mark.skipif(
    not HAS_YAHOOQUERY,
    reason="yahooquery package not installed",
)


# =============================================================================
# Yahoo Finance Tests (Free, no API key)
# =============================================================================


@SKIP_NO_YAHOOQUERY
@pytest.mark.integration
class TestYahooFinanceProvider:
    """Integration tests for Yahoo Finance market data provider."""

    def test_quote_single_stock(self):
        """Test fetching a single stock quote."""
        from fin_infra.models import Quote
        from fin_infra.providers.market.yahoo import YahooFinanceMarketData

        provider = YahooFinanceMarketData()
        quote = provider.quote("AAPL")

        assert isinstance(quote, Quote)
        assert quote.symbol == "AAPL"
        assert quote.price > Decimal(0)
        assert quote.currency == "USD"

    def test_quote_multiple_stocks(self):
        """Test fetching quotes for multiple stocks."""
        from fin_infra.models import Quote
        from fin_infra.providers.market.yahoo import YahooFinanceMarketData

        provider = YahooFinanceMarketData()

        # Fetch quotes individually (no bulk method)
        symbols = ["AAPL", "GOOGL", "MSFT"]
        quotes = [provider.quote(sym) for sym in symbols]

        assert isinstance(quotes, list)
        assert len(quotes) == 3
        assert all(isinstance(q, Quote) for q in quotes)

        # Verify we got different symbols
        returned_symbols = {q.symbol for q in quotes}
        assert "AAPL" in returned_symbols
        assert "GOOGL" in returned_symbols
        assert "MSFT" in returned_symbols

    def test_historical_data(self):
        """Test fetching historical OHLCV data."""
        from fin_infra.models import Candle
        from fin_infra.providers.market.yahoo import YahooFinanceMarketData

        provider = YahooFinanceMarketData()
        candles = provider.history("AAPL", period="1mo")

        assert isinstance(candles, list)
        assert len(candles) > 0
        assert all(isinstance(c, Candle) for c in candles)

        # Verify data structure
        first_candle = candles[0]
        assert first_candle.ts > 0
        assert first_candle.open > Decimal(0)
        assert first_candle.high > Decimal(0)
        assert first_candle.low > Decimal(0)
        assert first_candle.close > Decimal(0)

    def test_invalid_symbol(self):
        """Test handling of invalid symbol."""
        from fin_infra.providers.market.yahoo import YahooFinanceMarketData

        provider = YahooFinanceMarketData()

        # Yahoo Finance may return various error types for invalid symbols
        with pytest.raises((ValueError, KeyError, AttributeError, TypeError)):
            provider.quote("INVALID_SYMBOL_XYZ123456789")


# =============================================================================
# Alpha Vantage Tests (Requires API key)
# =============================================================================


@SKIP_NO_ALPHAVANTAGE
@pytest.mark.integration
class TestAlphaVantageProvider:
    """Integration tests for Alpha Vantage market data provider.

    Note: Alpha Vantage has strict rate limits (5 req/min free tier).
    Tests may be skipped if rate limited.
    """

    def test_quote_single_stock(self):
        """Test fetching a single stock quote."""
        from fin_infra.models import Quote
        from fin_infra.providers.market.alphavantage import AlphaVantageMarketData

        provider = AlphaVantageMarketData()

        try:
            quote = provider.quote("AAPL")
        except ValueError as e:
            if "rate limit" in str(e).lower() or "No data" in str(e):
                pytest.skip(f"Alpha Vantage rate limited: {e}")
            raise

        assert isinstance(quote, Quote)
        assert quote.symbol == "AAPL"
        assert quote.price > Decimal(0)
        assert quote.currency == "USD"

    def test_historical_data(self):
        """Test fetching historical data."""
        from fin_infra.models import Candle
        from fin_infra.providers.market.alphavantage import AlphaVantageMarketData

        provider = AlphaVantageMarketData()

        try:
            candles = provider.history("AAPL", period="1mo")
        except ValueError as e:
            if "rate limit" in str(e).lower() or "No data" in str(e):
                pytest.skip(f"Alpha Vantage rate limited: {e}")
            raise

        if len(candles) == 0:
            pytest.skip("Alpha Vantage returned empty results (rate limited)")

        assert isinstance(candles, list)
        assert all(isinstance(c, Candle) for c in candles)

    def test_symbol_search(self):
        """Test symbol search functionality."""
        from fin_infra.providers.market.alphavantage import AlphaVantageMarketData

        provider = AlphaVantageMarketData()

        try:
            results = provider.search("Apple")
        except ValueError as e:
            if "rate limit" in str(e).lower():
                pytest.skip(f"Alpha Vantage rate limited: {e}")
            raise

        if len(results) == 0:
            pytest.skip("Alpha Vantage returned empty results (rate limited)")

        assert isinstance(results, list)
        # AAPL should be in search results
        symbols = [r.get("symbol") for r in results]
        assert "AAPL" in symbols


# =============================================================================
# Easy Market Factory Tests
# =============================================================================


@pytest.mark.integration
class TestEasyMarketFactory:
    """Integration tests for easy_market factory function."""

    @SKIP_NO_YAHOOQUERY
    def test_easy_market_auto_detects_yahoo(self):
        """Test that easy_market falls back to Yahoo without API keys."""
        from fin_infra.markets import easy_market

        # Clear Alpha Vantage key temporarily (if set)
        av_key = os.environ.pop("ALPHA_VANTAGE_API_KEY", None)
        av_key2 = os.environ.pop("ALPHAVANTAGE_API_KEY", None)

        try:
            provider = easy_market()

            # Should create Yahoo provider when no AV key
            from fin_infra.providers.market.yahoo import YahooFinanceMarketData

            assert isinstance(provider, YahooFinanceMarketData)
        finally:
            # Restore keys
            if av_key:
                os.environ["ALPHA_VANTAGE_API_KEY"] = av_key
            if av_key2:
                os.environ["ALPHAVANTAGE_API_KEY"] = av_key2

    @SKIP_NO_YAHOOQUERY
    def test_easy_market_explicit_yahoo(self):
        """Test explicit Yahoo provider selection."""
        from fin_infra.markets import easy_market
        from fin_infra.providers.market.yahoo import YahooFinanceMarketData

        provider = easy_market(provider="yahoo")
        assert isinstance(provider, YahooFinanceMarketData)

    @SKIP_NO_ALPHAVANTAGE
    def test_easy_market_explicit_alphavantage(self):
        """Test explicit Alpha Vantage provider selection."""
        from fin_infra.markets import easy_market
        from fin_infra.providers.market.alphavantage import AlphaVantageMarketData

        provider = easy_market(provider="alphavantage")
        assert isinstance(provider, AlphaVantageMarketData)

    def test_easy_market_invalid_provider(self):
        """Test error handling for invalid provider."""
        from fin_infra.markets import easy_market

        with pytest.raises(ValueError, match="Unknown market data provider"):
            easy_market(provider="invalid_provider")


# =============================================================================
# Market Data Model Tests
# =============================================================================


@pytest.mark.integration
class TestMarketDataModels:
    """Integration tests for market data models."""

    def test_quote_model_serialization(self):
        """Test Quote model can be serialized to JSON."""
        from datetime import datetime

        from fin_infra.models import Quote

        quote = Quote(
            symbol="AAPL",
            price=Decimal("175.50"),
            currency="USD",
            as_of=datetime.now(UTC),
            change=Decimal("2.30"),
            change_pct=Decimal("1.33"),
        )

        # Pydantic model should be serializable
        data = quote.model_dump()
        assert data["symbol"] == "AAPL"
        assert "price" in data

    def test_candle_model_serialization(self):
        """Test Candle model can be serialized to JSON."""
        import time

        from fin_infra.models import Candle

        candle = Candle(
            ts=int(time.time()),
            open=Decimal("170.00"),
            high=Decimal("176.00"),
            low=Decimal("169.00"),
            close=Decimal("175.50"),
            volume=Decimal("50000000"),
        )

        # Pydantic model should be serializable
        data = candle.model_dump()
        assert data["open"] == Decimal("170.00")
        assert data["close"] == Decimal("175.50")
