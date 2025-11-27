# Brokerage Integration

fin-infra provides unified interfaces for connecting to brokerage accounts for automated trading, portfolio management, and position tracking. The brokerage integration supports **paper trading** (sandbox) and **live trading** with built-in safety mechanisms.

## ⚠️ Important Disclaimers

**TRADING INVOLVES SUBSTANTIAL RISK**: This software is provided for educational and development purposes. Real trading involves risk of loss. Paper trading results DO NOT guarantee real trading success.

**PAPER TRADING FIRST**: Always test with paper trading before using live mode. fin-infra defaults to paper trading mode for safety.

**NOT FINANCIAL ADVICE**: This library does not provide investment advice. You are responsible for all trading decisions and their consequences.

**REGULATORY COMPLIANCE**: Ensure your trading application complies with all applicable regulations (SEC, FINRA, etc.) in your jurisdiction.

## Supported Providers

### Current
- **Alpaca** (✅ Implemented)
  - Commission-free trading API
  - Full paper trading environment
  - Real-time market data
  - Order management (market, limit, stop, stop-limit)
  - Position tracking
  - Portfolio history

### Coming Soon
- **Interactive Brokers**: Institutional-grade API (research pending)
- **TD Ameritrade**: thinkorswim API (research pending)

## Quick Setup

### Zero-Config (Paper Trading)
```python
from fin_infra.brokerage import easy_brokerage

# Defaults to paper trading mode (safe for testing)
# Reads ALPACA_PAPER_API_KEY and ALPACA_PAPER_SECRET_KEY from environment
brokerage = easy_brokerage()

# Verify it's in paper mode
print(f"Mode: {brokerage.mode}")  # Output: "paper"
```

### Explicit Configuration
```python
from fin_infra.brokerage import easy_brokerage

# Paper trading (explicit)
brokerage = easy_brokerage(
    provider="alpaca",
    mode="paper",
    api_key="YOUR_PAPER_API_KEY",
    api_secret="YOUR_PAPER_SECRET_KEY"
)

# Live trading (requires explicit mode="live")
# ⚠️ WARNING: This uses real money!
brokerage = easy_brokerage(
    provider="alpaca",
    mode="live",  # Must explicitly set to "live"
    api_key="YOUR_LIVE_API_KEY",
    api_secret="YOUR_LIVE_SECRET_KEY"
)
```

### Environment Variables
```bash
# Paper trading credentials (default)
export ALPACA_PAPER_API_KEY="your_paper_api_key"
export ALPACA_PAPER_SECRET_KEY="your_paper_secret_key"

# Live trading credentials (opt-in)
export ALPACA_LIVE_API_KEY="your_live_api_key"
export ALPACA_LIVE_SECRET_KEY="your_live_secret_key"
```

