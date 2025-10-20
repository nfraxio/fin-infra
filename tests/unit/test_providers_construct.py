from fin_infra.providers.market.yahoo import YahooMarketData
from fin_infra.providers.market.ccxt_crypto import CCXTCryptoData


def test_providers_construct():
    y = YahooMarketData()
    assert y is not None
    c = CCXTCryptoData("binance")
    assert c is not None
