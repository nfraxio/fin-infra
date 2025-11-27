# ADR-0007: Data Normalization & Symbol Resolution

**Status**: Accepted  
**Date**: 2025-11-05  
**Context**: Production readiness punch list Section 7  
**Related**: ADR-0003 (Banking), ADR-0004 (Market Data), ADR-0005 (Crypto), ADR-0006 (Brokerage)

---

## Context

Financial applications deal with data from multiple providers, each using different symbol formats, identifiers, and currencies. Users need consistent, normalized views across providers.

### Key Requirements

1. **Symbol Resolution**: Convert between different identifier formats
   - Ticker symbols: `AAPL`, `TSLA`, `BTC-USD`
   - Exchange-qualified: `NASDAQ:AAPL`, `NYSE:TSLA`, `CRYPTO:BTC`
   - CUSIPs: `037833100` (Apple Inc.)
   - ISINs: `US0378331005` (Apple Inc.)
   - Provider-specific: Plaid account IDs, Alpaca asset IDs

2. **Currency Conversion**: Real-time exchange rates
   - USD ↔ EUR, GBP, JPY, CAD, etc.
   - Crypto conversions: BTC → USD, ETH → EUR
   - Historical rates for backtesting

3. **Company Metadata**: Enrich symbols with company info
   - Company name: `AAPL` → `Apple Inc.`
   - Sector/industry classification
   - Market cap, exchange listing

4. **Multi-Provider Consistency**: Same symbol across providers
   - Alpha Vantage ticker → Yahoo Finance ticker → Alpaca symbol
   - Handle provider-specific quirks (e.g., Yahoo uses `BTC-USD`, CoinGecko uses `bitcoin`)

### Critical Considerations

- **Rate Limits**: External APIs (exchange rates, symbol lookup) have quotas
- **Caching**: Symbol mappings rarely change (cache for days); exchange rates change frequently (cache for minutes)
- **Fallback**: Graceful degradation when external APIs fail
- **Cost**: Free tiers often sufficient; paid tiers for high-volume production

---

## svc-infra Reuse Assessment

### Research Findings

**Searched for**:
- Data normalization: `grep -r "normaliz" svc-infra/src/` → No results
- Symbol resolution: `grep -r "symbol|ticker|cusip|isin" svc-infra/src/` → No results
- Currency conversion: `grep -r "currency|exchange.*rate" svc-infra/src/` → No results

**Classification**: **Type A** (Financial-specific)

**Justification**:
- Symbol resolution (ticker → CUSIP → ISIN) is financial domain knowledge
- Currency conversion requires financial data APIs (exchangerate-api.io, etc.)
- Company metadata is financial-specific (sector, market cap, etc.)
- svc-infra provides NO normalization or symbol resolution capabilities

**Reuse Plan**:
- ✅ Use `svc_infra.cache` for symbol mappings (long TTL: 24 hours)
- ✅ Use `svc_infra.cache` for exchange rates (short TTL: 5-15 minutes)
- ✅ Use `svc_infra.http` for API calls to exchange rate providers
- ✅ Use `svc_infra.logging` for normalization errors/warnings

### svc-infra Integration Points

```python
# Cache symbol mappings with long TTL
from svc_infra.cache import cache_read, init_cache

init_cache(url="redis://localhost", prefix="fin", version="v1")

@cache_read(key="symbol:cusip:{cusip}", ttl=86400)  # 24 hours
async def cusip_to_ticker(cusip: str) -> str:
    # Lookup logic here
    pass

# Cache exchange rates with short TTL
@cache_read(key="fx:{from_currency}:{to_currency}", ttl=300)  # 5 minutes
async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    # API call here
    pass

# HTTP client for external APIs
from svc_infra.http import new_async_httpx_client

async with new_async_httpx_client() as client:
    response = await client.get("https://api.exchangerate-api.io/v4/latest/USD")
    rates = response.json()
```

---

## Decision

### Architecture Overview

Implement **two independent singletons** with caching:

1. **SymbolResolver**: Converts between symbol formats
2. **CurrencyConverter**: Handles currency conversions

Both use:
- Internal caches for fast lookups
- External API fallbacks when cache misses
- Graceful degradation on API failures

### Symbol Resolver

**Capabilities**:
```python
class SymbolResolver:
    async def to_ticker(self, identifier: str) -> str:
        """Convert any identifier to ticker symbol."""
        # CUSIP: 037833100 → AAPL
        # ISIN: US0378331005 → AAPL
        # Exchange-qualified: NASDAQ:AAPL → AAPL
        
    async def to_cusip(self, ticker: str) -> str:
        """Convert ticker to CUSIP."""
        # AAPL → 037833100
        
    async def to_isin(self, ticker: str) -> str:
        """Convert ticker to ISIN."""
        # AAPL → US0378331005
        
    async def normalize(self, symbol: str, provider: str) -> str:
        """Normalize provider-specific symbol to standard ticker."""
        # Yahoo: BTC-USD → BTC
        # CoinGecko: bitcoin → BTC
        # Alpaca: BTCUSD → BTC
        
    async def get_metadata(self, ticker: str) -> dict:
        """Get company metadata."""
        # AAPL → {"name": "Apple Inc.", "exchange": "NASDAQ", ...}
        
    async def resolve_batch(self, symbols: list[str]) -> dict[str, str]:
        """Batch resolve symbols (efficient for multiple lookups)."""
```

**Data Sources** (free tiers):
- OpenFIGI API: Ticker ↔ CUSIP ↔ ISIN mappings (250 requests/day free)
- SEC EDGAR: Company tickers and CUSIPs (unlimited, public data)
- Yahoo Finance unofficial API: Ticker metadata (rate limited)
- Static mappings file: Common tickers pre-cached (AAPL, TSLA, GOOGL, etc.)

### Currency Converter

**Capabilities**:
```python
class CurrencyConverter:
    async def convert(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str,
        date: Optional[str] = None  # For historical rates
    ) -> float:
        """Convert amount from one currency to another."""
        # 100 USD → EUR (current rate)
        # 100 USD → EUR (historical: 2023-01-01)
        
    async def get_rate(
        self, 
        from_currency: str, 
        to_currency: str,
        date: Optional[str] = None
    ) -> float:
        """Get exchange rate between two currencies."""
        # USD → EUR: 0.92
        
    async def get_rates(self, base_currency: str) -> dict[str, float]:
        """Get all exchange rates for a base currency."""
        # USD → {"EUR": 0.92, "GBP": 0.79, "JPY": 149.50, ...}
        
    async def supported_currencies(self) -> list[str]:
        """List supported currency codes."""
        # ["USD", "EUR", "GBP", "JPY", "CAD", ...]
```

**Data Sources** (free tiers):
- **exchangerate-api.io**: 1,500 requests/month free (recommended)
  - Real-time rates for 160+ currencies
  - Historical data available
  - Crypto support (BTC, ETH, etc.)
- **fixer.io**: 100 requests/month free (backup)
  - Real-time rates for 170+ currencies
  - Limited historical data on free tier
- **openexchangerates.org**: 1,000 requests/month free (backup)
  - Real-time rates for 200+ currencies
  - Historical data available

### Easy Builder Pattern

**One-liner setup**:
```python
from fin_infra.normalization import easy_normalization

# Returns configured instances
resolver, converter = easy_normalization()

# Use anywhere
ticker = await resolver.to_ticker("037833100")  # CUSIP → AAPL
eur_amount = await converter.convert(100, "USD", "EUR")  # 92.0
```

**Configuration via environment**:
```bash
# Symbol resolution
OPENFIGI_API_KEY=your_key_here  # Optional, increases rate limit

# Currency conversion
EXCHANGE_RATE_API_KEY=your_key_here  # Optional, exchangerate-api.io
EXCHANGE_RATE_PROVIDER=exchangerate-api  # or "fixer", "openexchangerates"
```

---

## Consequences

### Positive

1. **Consistency**: Unified symbol format across all providers
2. **Flexibility**: Convert between any identifier type (ticker, CUSIP, ISIN)
3. **Multi-currency**: Support portfolios with mixed currencies
4. **Caching**: Fast lookups after first request (svc-infra cache)
5. **Free tier friendly**: 1,500 exchange rate requests/month sufficient for MVP
6. **Graceful degradation**: Falls back to provider-native symbols on API failure
7. **Type safety**: Full Pydantic models for all responses
8. **Provider-agnostic**: Works with banking, market, crypto, brokerage providers
9. **Historical data**: Support backtesting with historical exchange rates

### Negative

1. **External dependency**: Relies on third-party APIs (exchangerate-api.io, OpenFIGI)
2. **Rate limits**: Free tiers have monthly quotas (need monitoring)
3. **Latency**: First lookup requires external API call (cold cache)
4. **Maintenance**: Symbol mappings may need updates (M&A, ticker changes)
5. **API costs**: High-volume production may require paid tiers ($10-50/month)
6. **Complexity**: Adds another layer to provider integrations

### Neutral

1. **Caching strategy**: Long TTL for symbols (24h), short for rates (5m)
2. **Fallback behavior**: Return original symbol if resolution fails
3. **Batch operations**: Optimize for multiple symbol lookups
4. **Provider quirks**: Need mapping table for provider-specific formats

---

## Implementation Notes

### Module Structure

```
src/fin_infra/
  normalization/
    __init__.py           # easy_normalization() builder
    symbol_resolver.py    # SymbolResolver class
    currency_converter.py # CurrencyConverter class
    providers/
      __init__.py
      openfigi.py         # OpenFIGI API client
      exchangerate.py     # exchangerate-api.io client
      static_mappings.py  # Pre-cached common symbols
    models.py             # Pydantic models
```

### Static Mappings (Seed Data)

Pre-cache common symbols to reduce API calls:

```python
# normalization/providers/static_mappings.py
TICKER_TO_CUSIP = {
    "AAPL": "037833100",
    "TSLA": "88160R101",
    "GOOGL": "02079K305",
    "MSFT": "594918104",
    "AMZN": "023135106",
    # ... top 100 stocks
}

TICKER_TO_ISIN = {
    "AAPL": "US0378331005",
    "TSLA": "US88160R1014",
    "GOOGL": "US02079K3059",
    "MSFT": "US5949181045",
    "AMZN": "US0231351067",
    # ... top 100 stocks
}

PROVIDER_SYMBOL_MAP = {
    "yahoo": {
        "BTC-USD": "BTC",
        "ETH-USD": "ETH",
    },
    "coingecko": {
        "bitcoin": "BTC",
        "ethereum": "ETH",
    },
    "alpaca": {
        "BTCUSD": "BTC",
        "ETHUSD": "ETH",
    }
}
```

### Caching Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Ticker → CUSIP | 24 hours | CUSIPs rarely change |
| Ticker → ISIN | 24 hours | ISINs rarely change |
| Ticker → Metadata | 6 hours | Company name, exchange stable |
| Exchange rates (real-time) | 5 minutes | Rates change frequently |
| Exchange rates (historical) | 24 hours | Historical data immutable |
| Supported currencies | 24 hours | Currency list stable |

### Error Handling

```python
class SymbolNotFoundError(Exception):
    """Symbol could not be resolved."""
    pass

class CurrencyNotSupportedError(Exception):
    """Currency code not supported."""
    pass

class ExchangeRateAPIError(Exception):
    """External API unavailable."""
    pass

# Graceful fallback
try:
    ticker = await resolver.to_ticker(cusip)
except SymbolNotFoundError:
    ticker = cusip  # Use original identifier
    logger.warning(f"Could not resolve CUSIP {cusip}, using as-is")
```

---

## Example Integrations

### 1. Multi-Provider Portfolio Aggregation

```python
from fin_infra.banking import easy_banking
from fin_infra.brokerage import easy_brokerage
from fin_infra.normalization import easy_normalization

resolver, converter = easy_normalization()

# Get positions from brokerage
brokerage = easy_brokerage()
positions = await brokerage.positions()

# Normalize to USD (positions might be in various currencies)
total_value_usd = 0.0
for position in positions:
    # Convert position value to USD
    if position.currency != "USD":
        value_usd = await converter.convert(
            position.market_value,
            position.currency,
            "USD"
        )
    else:
        value_usd = position.market_value
    
    total_value_usd += value_usd
    
    # Resolve symbol to standard ticker
    ticker = await resolver.normalize(position.symbol, provider="alpaca")
    print(f"{ticker}: ${value_usd:,.2f}")

print(f"Total Portfolio Value: ${total_value_usd:,.2f} USD")
```

### 2. Symbol Lookup Service

```python
from fastapi import FastAPI
from fin_infra.normalization import easy_normalization

app = FastAPI()
resolver, converter = easy_normalization()

@app.get("/symbols/resolve/{identifier}")
async def resolve_symbol(identifier: str):
    """Resolve any identifier to ticker symbol."""
    return {
        "input": identifier,
        "ticker": await resolver.to_ticker(identifier),
        "cusip": await resolver.to_cusip(identifier),
        "isin": await resolver.to_isin(identifier),
        "metadata": await resolver.get_metadata(identifier)
    }

@app.get("/currencies/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
):
    """Convert amount between currencies."""
    rate = await converter.get_rate(from_currency, to_currency)
    converted = await converter.convert(amount, from_currency, to_currency)
    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "rate": rate,
        "converted": converted
    }
```

### 3. Historical Backtesting

```python
from fin_infra.normalization import easy_normalization
from fin_infra.markets import easy_market

resolver, converter = easy_normalization()
market = easy_market()

# Backtest portfolio value in EUR (2023)
portfolio = [
    {"ticker": "AAPL", "shares": 100, "date": "2023-01-01"},
    {"ticker": "TSLA", "shares": 50, "date": "2023-01-01"},
]

total_value_eur = 0.0
for holding in portfolio:
    # Get historical price (USD)
    quote = market.quote(holding["ticker"])  # Simplified
    value_usd = quote.price * holding["shares"]
    
    # Convert to EUR using historical rate
    value_eur = await converter.convert(
        value_usd,
        "USD",
        "EUR",
        date=holding["date"]  # Historical rate
    )
    total_value_eur += value_eur

print(f"Portfolio Value (Jan 1, 2023): €{total_value_eur:,.2f}")
```

---

## Future Enhancements

1. **More identifier types**: SEDOL, RIC, Bloomberg ticker
2. **Crypto exchanges**: Exchange-specific symbol resolution (Binance, Coinbase)
3. **OTC markets**: Pink sheets, OTC bulletin board symbols
4. **International markets**: LSE, TSE, HKEX symbol formats
5. **Real-time streaming**: WebSocket for live exchange rates
6. **Batch optimization**: Single API call for multiple symbols
7. **Symbol changes**: Track ticker changes over time (M&A, rebranding)
8. **Provider caching**: Cache per-provider normalized symbols
9. **Admin endpoints**: Manual symbol mapping overrides
10. **Metrics**: Track resolution success rate, API quota usage

---

## Related Documentation

- [svc-infra Cache Documentation](../../../../svc-infra/src/svc_infra/cache/)
- [svc-infra HTTP Client](../../../../svc-infra/src/svc_infra/http/)
- [Banking Provider Guide](../banking.md)
- [Market Data Guide](../market-data.md)
- [Brokerage Guide](../brokerage.md)
- [Caching & Rate Limits Guide](../caching-rate-limits-retries.md)

---

## References

- **OpenFIGI API**: https://www.openfigi.com/api
- **exchangerate-api.io**: https://www.exchangerate-api.com/docs/overview
- **SEC EDGAR**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **CUSIP Format**: https://www.cusip.com/identifiers.html
- **ISIN Format**: https://www.isin.org/isin/
