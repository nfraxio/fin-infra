from __future__ import annotations

from alpaca_trade_api import REST

from ...settings import Settings
from ..base import BrokerageProvider


class AlpacaBrokerage(BrokerageProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.client = REST(
            self.settings.alpaca_api_key,
            self.settings.alpaca_api_secret,
            base_url=self.settings.alpaca_base_url,
            api_version="v2",
        )

    def submit_order(
        self, symbol: str, qty: float, side: str, type_: str, time_in_force: str
    ) -> dict:
        order = self.client.submit_order(
            symbol=symbol, qty=qty, side=side, type=type_, time_in_force=time_in_force
        )
        return getattr(order, "_raw", getattr(order, "_raw", {})) or order.__dict__

    def positions(self):
        for p in self.client.list_positions():
            yield getattr(p, "_raw", p.__dict__)
