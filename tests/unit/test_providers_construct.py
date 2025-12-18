"""Test that providers can be constructed when optional dependencies are available."""

import pytest

# Check if yahooquery is available
try:
    from yahooquery import Ticker as _Ticker  # noqa: F401

    HAS_YAHOOQUERY = True
except ImportError:
    HAS_YAHOOQUERY = False

# Check if ccxt is available
try:
    import ccxt as _ccxt  # noqa: F401

    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False

from fin_infra.providers.market.ccxt_crypto import CCXTCryptoData
from fin_infra.providers.market.yahoo import YahooFinanceMarketData


@pytest.mark.skipif(not HAS_YAHOOQUERY, reason="yahooquery not installed")
def test_yahoo_provider_construct():
    """Test YahooFinanceMarketData can be constructed."""
    y = YahooFinanceMarketData()
    assert y is not None


@pytest.mark.skipif(not HAS_CCXT, reason="ccxt not installed")
def test_ccxt_provider_construct():
    """Test CCXTCryptoData can be constructed."""
    c = CCXTCryptoData("binance")
    assert c is not None
