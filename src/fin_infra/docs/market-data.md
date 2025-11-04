# Market Data Integration

fin-infra provides unified access to equity and cryptocurrency market data through multiple providers, with fallback support and consistent data models.

## Supported Providers

### Equity Markets
- **Alpha Vantage**: Free tier with rate limits
- **Yahoo Finance**: Via yahooquery
- **IEX Cloud**: Coming soon
- **Polygon.io**: Coming soon

### Cryptocurrency Markets
- **CoinGecko**: Free API with rate limits
- **CCXT**: Multi-exchange support (Binance, Coinbase, Kraken, etc.)
- **CoinMarketCap**: Coming soon

## Quick Setup

### Equity Market Data
```python
from fin_infra.markets import easy_market

# Auto-configured with default provider
market = easy_market()  # Uses Alpha Vantage by default

# Or specify provider
market = easy_market(provider="yahoo")
```

### Crypto Market Data
```python
from fin_infra.markets import easy_crypto

# Auto-configured with default provider
crypto = easy_crypto()  # Uses CoinGecko by default

# Or specify exchange via CCXT
crypto = easy_crypto(provider="ccxt", exchange="binance")
```

## Equity Market Operations

### 1. Get Real-Time Quote
```python
from fin_infra.models.quotes import Quote

quote = market.quote("AAPL")

print(f"Symbol: {quote.symbol}")
print(f"Price: ${quote.price}")
print(f"Change: {quote.change} ({quote.change_percent}%)")
print(f"Volume: {quote.volume}")
print(f"Market Cap: ${quote.market_cap}")
print(f"52-Week High: ${quote.high_52week}")
print(f"52-Week Low: ${quote.low_52week}")
```

### 2. Get Multiple Quotes
```python
quotes = market.quotes(["AAPL", "GOOGL", "MSFT", "TSLA"])

for quote in quotes:
    print(f"{quote.symbol}: ${quote.price}")
```

### 3. Historical Data
```python
from datetime import date, timedelta

# Get 1 month of daily data
historical = market.historical(
    symbol="AAPL",
    start_date=date.today() - timedelta(days=30),
    end_date=date.today(),
    interval="1d"  # 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
)

for candle in historical:
    print(f"{candle.timestamp}: O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}")
```

### 4. Search Symbols
```python
results = market.search("apple")

for result in results:
    print(f"{result.symbol}: {result.name}")
    print(f"Exchange: {result.exchange}")
    print(f"Type: {result.asset_type}")
```

### 5. Company Information
```python
company = market.company_info("AAPL")

print(f"Name: {company.name}")
print(f"Description: {company.description}")
print(f"Industry: {company.industry}")
print(f"Sector: {company.sector}")
print(f"Website: {company.website}")
print(f"CEO: {company.ceo}")
```

## Cryptocurrency Operations

### 1. Get Crypto Price
```python
ticker = crypto.ticker("BTC/USDT")

print(f"Symbol: {ticker.symbol}")
print(f"Price: ${ticker.last}")
print(f"Bid: ${ticker.bid}")
print(f"Ask: ${ticker.ask}")
print(f"24h Volume: {ticker.volume}")
print(f"24h Change: {ticker.change_24h}%")
```

### 2. Get Multiple Tickers
```python
tickers = crypto.tickers(["BTC/USDT", "ETH/USDT", "SOL/USDT"])

for ticker in tickers:
    print(f"{ticker.symbol}: ${ticker.last}")
```

### 3. OHLCV Candles
```python
candles = crypto.candles(
    symbol="BTC/USDT",
    timeframe="1h",  # 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
    limit=100
)

for candle in candles:
    print(f"{candle.timestamp}: ${candle.close}")
```

### 4. Order Book
```python
orderbook = crypto.orderbook("BTC/USDT", limit=10)

print("Bids:")
for price, volume in orderbook.bids[:5]:
    print(f"  ${price} x {volume}")

print("Asks:")
for price, volume in orderbook.asks[:5]:
    print(f"  ${price} x {volume}")
```

### 5. Market List
```python
markets = crypto.list_markets()

for market in markets:
    print(f"{market.symbol}: {market.base}/{market.quote}")
```

## Data Models

### Quote
```python
from fin_infra.models.quotes import Quote

class Quote:
    symbol: str
    price: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int
    market_cap: Decimal | None
    high_52week: Decimal | None
    low_52week: Decimal | None
    pe_ratio: Decimal | None
    dividend_yield: Decimal | None
```

### Candle (OHLCV)
```python
from fin_infra.models.candle import Candle

class Candle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
```

## Rate Limiting & Caching

```python
from fin_infra.markets import easy_market
from fin_infra.cache import init_cache

# Initialize cache
init_cache(url="redis://localhost:6379", prefix="fininfra", version="v1")

# Market data calls are automatically cached
market = easy_market()

# First call hits API
quote1 = market.quote("AAPL")  # API call

# Second call within TTL returns cached data
quote2 = market.quote("AAPL")  # Cache hit
```

## Provider Fallback

```python
from fin_infra.markets import MarketDataAggregator

# Configure multiple providers with fallback
aggregator = MarketDataAggregator(
    providers=[
        ("alphavantage", {"api_key": "xxx"}),
        ("yahoo", {}),
        ("iex", {"api_key": "yyy"})
    ]
)

# Automatically falls back to next provider on error
quote = aggregator.quote("AAPL")
```

## Error Handling

```python
from fin_infra.markets.exceptions import (
    MarketDataError,
    SymbolNotFoundError,
    RateLimitError,
    ProviderError
)

try:
    quote = market.quote("INVALID_SYMBOL")
except SymbolNotFoundError:
    print("Symbol not found")
except RateLimitError:
    print("Rate limit exceeded, implement backoff")
except ProviderError as e:
    print(f"Provider error: {e.message}")
```

## Streaming Real-Time Data

```python
from fin_infra.markets import easy_market_stream

# WebSocket streaming (for supported providers)
async with easy_market_stream() as stream:
    await stream.subscribe(["AAPL", "GOOGL", "TSLA"])
    
    async for quote in stream:
        print(f"{quote.symbol}: ${quote.price}")
```

## Best Practices

1. **Caching**: Always enable caching for market data to reduce API calls
2. **Rate Limiting**: Respect provider rate limits, implement exponential backoff
3. **Fallback Providers**: Configure multiple providers for reliability
4. **Symbol Normalization**: Normalize symbols before querying (e.g., "AAPL" not "aapl")
5. **Time Zones**: Always work with timezone-aware datetimes
6. **Data Validation**: Validate data ranges and handle missing data gracefully

## Testing

```python
import pytest
from fin_infra.markets import easy_market

def test_get_quote():
    market = easy_market()
    quote = market.quote("AAPL")
    
    assert quote.symbol == "AAPL"
    assert quote.price > 0
    assert quote.volume > 0

@pytest.mark.acceptance
def test_real_market_data():
    market = easy_market()
    quote = market.quote("AAPL")
    
    # Test against real API
    assert quote is not None
```

## Next Steps

- [Banking Integration](banking.md)
- [Brokerage Integration](brokerage.md)
- [Cashflows & Financial Calculations](cashflows.md)
