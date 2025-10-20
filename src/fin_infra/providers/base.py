from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Any, Sequence
from datetime import datetime

from ..models import Quote, Candle


class MarketDataProvider(ABC):
    @abstractmethod
    def quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    def history(self, symbol: str, *, period: str = "1mo", interval: str = "1d") -> Sequence[Candle]: ...


class CryptoDataProvider(ABC):
    @abstractmethod
    def ticker(self, symbol_pair: str) -> Quote: ...

    @abstractmethod
    def ohlcv(self, symbol_pair: str, timeframe: str = "1d", limit: int = 100) -> Sequence[Candle]: ...


class BankingProvider(ABC):
    @abstractmethod
    def create_link_token(self, user_id: str) -> str: ...

    @abstractmethod
    def exchange_public_token(self, public_token: str) -> dict: ...

    @abstractmethod
    def accounts(self, access_token: str) -> list[dict]: ...


class BrokerageProvider(ABC):
    @abstractmethod
    def submit_order(
        self, symbol: str, qty: float, side: str, type_: str, time_in_force: str
    ) -> dict: ...

    @abstractmethod
    def positions(self) -> Iterable[dict]: ...


class IdentityProvider(ABC):
    @abstractmethod
    def create_verification_session(self, **kwargs) -> dict: ...

    @abstractmethod
    def get_verification_session(self, session_id: str) -> dict: ...


class CreditProvider(ABC):
    @abstractmethod
    def get_credit_score(self, user_id: str, **kwargs) -> dict | None: ...
