"""DEPRECATED: Use fin_infra.providers instead.

This module is deprecated and will be removed in a future version.
All ABCs have been consolidated into fin_infra.providers.base.

Migration:
    # Old (deprecated)
    from fin_infra.clients import BankingClient, MarketDataClient

    # New
    from fin_infra.providers.base import BankingProvider, MarketDataProvider
"""

import warnings

from .base import BankingClient, CreditClient, MarketDataClient

warnings.warn(
    "fin_infra.clients is deprecated. Use fin_infra.providers instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["BankingClient", "MarketDataClient", "CreditClient"]
