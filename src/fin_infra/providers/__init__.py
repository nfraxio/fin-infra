"""
Financial data providers.

This module provides access to various financial data providers through
a unified interface. Use the registry for dynamic provider loading.
"""

from .base import (
    BankingProvider,
    BrokerageProvider,
    CreditProvider,
    CryptoDataProvider,
    IdentityProvider,
    MarketDataProvider,
    TaxProvider,
)
from .registry import (
    ProviderNotFoundError,
    ProviderRegistry,
    list_providers,
    resolve,
)

__all__ = [
    # Provider interfaces
    "BankingProvider",
    "BrokerageProvider",
    "CreditProvider",
    "CryptoDataProvider",
    "IdentityProvider",
    "MarketDataProvider",
    "TaxProvider",
    # Registry
    "ProviderRegistry",
    "ProviderNotFoundError",
    "resolve",
    "list_providers",
]
