"""Easy builder for analytics engine.

Provides simple setup with sensible defaults.
"""

from __future__ import annotations


def easy_analytics(**config):
    """Create configured analytics engine with sensible defaults.
    
    This is the simplest way to get started with analytics. The function
    returns a ready-to-use AnalyticsEngine instance with all dependencies
    configured.
    
    Args:
        **config: Optional configuration overrides
            - cache_ttl: Cache TTL in seconds (default: 3600 = 1 hour)
            - default_period_days: Default analysis period (default: 30)
            - savings_definition: "gross", "net", or "discretionary" (default: "net")
            - benchmark_symbol: Default benchmark ticker (default: "SPY")
    
    Returns:
        Configured AnalyticsEngine instance ready to use
    
    Raises:
        ValueError: If invalid configuration provided
    
    Example:
        >>> from fin_infra.analytics import easy_analytics
        >>> 
        >>> # Zero config
        >>> analytics = easy_analytics()
        >>> 
        >>> # Custom config
        >>> analytics = easy_analytics(
        ...     cache_ttl=7200,
        ...     savings_definition="gross",
        ...     benchmark_symbol="VTI"
        ... )
    """
    # TODO: Implement in Task 8
    # Will create and configure AnalyticsEngine with:
    # - Cache configuration (svc-infra cache)
    # - Dependencies (banking, brokerage, categorization, recurring, net_worth)
    # - Sensible defaults (30-day periods, net savings, SPY benchmark)
    raise NotImplementedError("easy_analytics() will be implemented in Task 8")
