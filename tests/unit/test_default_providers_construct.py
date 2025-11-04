from fin_infra.providers.market.alphavantage import AlphaVantageMarketData
from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
from fin_infra.providers.banking.teller_client import TellerClient
from fin_infra.providers.identity.stripe_identity import StripeIdentity
from fin_infra.providers.credit.experian import ExperianCredit


def test_default_providers_construct():
    assert AlphaVantageMarketData() is not None
    assert CoinGeckoCryptoData() is not None
    assert TellerClient() is not None
    assert StripeIdentity() is not None
    assert ExperianCredit() is not None
