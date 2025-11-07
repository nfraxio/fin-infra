"""
Easy Net Worth Tracker Builder

One-line builder for net worth tracking with sensible defaults.

**Quick Start**:
```python
from fin_infra.net_worth import easy_net_worth
from fin_infra.banking import easy_banking
from fin_infra.brokerage import easy_brokerage

# Create providers
banking = easy_banking(provider="plaid")
brokerage = easy_brokerage(provider="alpaca")

# Create tracker (one line!)
tracker = easy_net_worth(
    banking=banking,
    brokerage=brokerage
)

# Calculate net worth
snapshot = await tracker.calculate_net_worth(
    user_id="user_123",
    access_token="plaid_token_abc"
)

print(f"Net Worth: ${snapshot.total_net_worth:,.2f}")
```

**FastAPI Integration**:
```python
from fastapi import FastAPI
from fin_infra.net_worth import add_net_worth_tracking

app = FastAPI()

# Add net worth endpoints (one line!)
tracker = add_net_worth_tracking(app)
```
"""

from typing import Any

from fin_infra.net_worth.aggregator import NetWorthAggregator


class NetWorthTracker:
    """
    High-level net worth tracking interface.
    
    Provides simple methods for calculating net worth,
    creating snapshots, and retrieving history.
    
    **Example**:
    ```python
    tracker = NetWorthTracker(aggregator)
    
    # Calculate current net worth
    snapshot = await tracker.calculate_net_worth("user_123")
    
    # Create snapshot in database
    await tracker.create_snapshot("user_123")
    
    # Get historical snapshots
    history = await tracker.get_snapshots("user_123", days=90)
    ```
    """
    
    def __init__(self, aggregator: NetWorthAggregator):
        """
        Initialize tracker with aggregator.
        
        Args:
            aggregator: NetWorthAggregator instance
        """
        self.aggregator = aggregator
    
    async def calculate_net_worth(
        self,
        user_id: str,
        access_token: str | None = None,
    ):
        """
        Calculate current net worth (real-time).
        
        Args:
            user_id: User identifier
            access_token: Provider access token
        
        Returns:
            NetWorthSnapshot
        """
        return await self.aggregator.aggregate_net_worth(
            user_id=user_id,
            access_token=access_token,
        )
    
    async def create_snapshot(
        self,
        user_id: str,
        access_token: str | None = None,
    ):
        """
        Create and store snapshot in database.
        
        Args:
            user_id: User identifier
            access_token: Provider access token
        
        Returns:
            NetWorthSnapshot (with change tracking)
        """
        # Calculate current net worth
        snapshot = await self.calculate_net_worth(user_id, access_token)
        
        # TODO: Implement database storage with svc-infra.db
        # - Fetch previous snapshot
        # - Calculate change
        # - Store new snapshot
        # - Check for significant change
        # - Emit webhook event if significant
        
        return snapshot
    
    async def get_snapshots(
        self,
        user_id: str,
        days: int = 90,
        granularity: str = "daily",
    ):
        """
        Retrieve historical snapshots.
        
        Args:
            user_id: User identifier
            days: Look back N days
            granularity: Snapshot granularity (daily, weekly, monthly)
        
        Returns:
            List of NetWorthSnapshot
        """
        # TODO: Implement database retrieval with svc-infra.db
        # - Query snapshots table
        # - Filter by date range
        # - Apply granularity (aggregate if needed)
        
        return []


def easy_net_worth(
    banking: Any = None,
    brokerage: Any = None,
    crypto: Any = None,
    market: Any = None,
    base_currency: str = "USD",
    snapshot_schedule: str = "daily",
    change_threshold_percent: float = 5.0,
    change_threshold_amount: float = 10000.0,
    **config,
) -> NetWorthTracker:
    """
    Create net worth tracker with sensible defaults (one-liner).
    
    **Example - Minimal**:
    ```python
    from fin_infra.banking import easy_banking
    from fin_infra.net_worth import easy_net_worth
    
    banking = easy_banking(provider="plaid")
    tracker = easy_net_worth(banking=banking)
    ```
    
    **Example - Multi-Provider**:
    ```python
    from fin_infra.banking import easy_banking
    from fin_infra.brokerage import easy_brokerage
    from fin_infra.crypto import easy_crypto
    from fin_infra.net_worth import easy_net_worth
    
    banking = easy_banking(provider="plaid")
    brokerage = easy_brokerage(provider="alpaca")
    crypto = easy_crypto(provider="ccxt")
    
    tracker = easy_net_worth(
        banking=banking,
        brokerage=brokerage,
        crypto=crypto,
        base_currency="USD",
        change_threshold_percent=5.0,  # 5% change triggers alert
        change_threshold_amount=10000.0  # $10k change triggers alert
    )
    ```
    
    **Example - Custom Config**:
    ```python
    tracker = easy_net_worth(
        banking=banking,
        snapshot_schedule="weekly",  # Weekly instead of daily
        change_threshold_percent=10.0,  # 10% change threshold
        change_threshold_amount=50000.0  # $50k change threshold
    )
    ```
    
    Args:
        banking: Banking provider instance (Plaid/Teller)
        brokerage: Brokerage provider instance (Alpaca)
        crypto: Crypto provider instance (CCXT)
        market: Market data provider instance (Alpha Vantage)
        base_currency: Base currency for normalization (default: "USD")
        snapshot_schedule: Snapshot frequency (default: "daily")
                          Options: "daily", "weekly", "monthly", "manual"
        change_threshold_percent: Percentage change threshold for alerts (default: 5.0%)
        change_threshold_amount: Absolute change threshold for alerts (default: $10,000)
        **config: Additional configuration (future use)
    
    Returns:
        NetWorthTracker instance ready to use
    
    Raises:
        ValueError: If no providers specified
    
    **Configuration Options**:
    - `snapshot_schedule`: How often to create snapshots
      - "daily": Create snapshot at midnight UTC (default)
      - "weekly": Create snapshot every Sunday at midnight
      - "monthly": Create snapshot on 1st of each month
      - "manual": Only create snapshots on demand
    
    - `change_threshold_percent`: Percentage change to trigger "significant change" alert
      - Default: 5.0 (5%)
      - Example: If net worth is $100k, alert on ±$5k change
    
    - `change_threshold_amount`: Absolute change to trigger alert
      - Default: 10000.0 ($10k)
      - Example: Alert on any ±$10k change regardless of percentage
    
    **Note**: Change is significant if EITHER threshold is exceeded (OR logic)
    """
    # Validate at least one provider
    if not any([banking, brokerage, crypto]):
        raise ValueError(
            "At least one provider required. "
            "Pass banking=easy_banking(...), brokerage=easy_brokerage(...), "
            "or crypto=easy_crypto(...)"
        )
    
    # Create aggregator
    aggregator = NetWorthAggregator(
        banking_provider=banking,
        brokerage_provider=brokerage,
        crypto_provider=crypto,
        market_provider=market,
        base_currency=base_currency,
    )
    
    # Create tracker
    tracker = NetWorthTracker(aggregator)
    
    # Store config for later use (jobs, webhooks)
    tracker.snapshot_schedule = snapshot_schedule
    tracker.change_threshold_percent = change_threshold_percent
    tracker.change_threshold_amount = change_threshold_amount
    tracker.config = config
    
    return tracker
