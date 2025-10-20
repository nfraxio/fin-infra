from __future__ import annotations

import abc
from typing import Iterable, Sequence

from ..models import Account, Quote, Transaction


class BankingClient(abc.ABC):
    """Abstract client for banking providers (e.g., Plaid).

    Implementations should handle authentication and retries internally and
    return normalized models.
    """

    @abc.abstractmethod
    async def get_accounts(self, user_id: str) -> Sequence[Account]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_transactions(
        self, account_id: str, *, start: str | None = None, end: str | None = None
    ) -> Iterable[Transaction]:
        raise NotImplementedError


class MarketDataClient(abc.ABC):
    @abc.abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError


class CreditClient(abc.ABC):
    @abc.abstractmethod
    async def get_score(self, user_id: str) -> int | None:
        raise NotImplementedError
