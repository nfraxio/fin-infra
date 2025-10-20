from __future__ import annotations

from ..base import BankingProvider


class TellerBanking(BankingProvider):
    """Skeleton client for Teller; implement real calls when API keys available.

    Teller offers a free developer tier; this is a surface definition.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def create_link_token(self, user_id: str) -> str:  # pragma: no cover - placeholder
        return ""

    def exchange_public_token(self, public_token: str) -> dict:  # pragma: no cover - placeholder
        return {}

    def accounts(self, access_token: str) -> list[dict]:  # pragma: no cover - placeholder
        return []
