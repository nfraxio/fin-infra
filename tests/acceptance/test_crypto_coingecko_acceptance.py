import pytest

from fin_infra.models import Candle, Quote
from fin_infra.providers.market.coingecko import CoinGeckoCryptoData

pytestmark = [pytest.mark.acceptance]


def test_coingecko_ticker_and_ohlcv_smoke():
    cg = CoinGeckoCryptoData()
    t = cg.ticker("BTC/USDT")
    assert isinstance(t, Quote)
    o = cg.ohlcv("ETH/USDT", timeframe="1d", limit=5)
    assert isinstance(o, list)
    if o:
        assert isinstance(o[0], Candle)
