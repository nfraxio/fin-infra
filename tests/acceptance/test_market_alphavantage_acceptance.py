import os
import pytest

from fin_infra.providers.market.alphavantage import AlphaVantageMarketData
from fin_infra.models import Quote, Candle


pytestmark = [pytest.mark.acceptance]


@pytest.mark.skipif(not os.getenv("ALPHAVANTAGE_API_KEY"), reason="No Alpha Vantage key in env")
def test_alphavantage_quote_and_history_smoke():
    md = AlphaVantageMarketData()
    q = md.quote("AAPL")
    assert isinstance(q, Quote)
    hist = md.history("AAPL")
    assert isinstance(hist, list)
    if hist:
        row = hist[0]
        assert isinstance(row, Candle)
