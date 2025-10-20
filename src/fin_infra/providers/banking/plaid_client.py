from __future__ import annotations

# Plaid SDK surface changes across versions; this class intentionally wraps
# creation and calls in a minimal way so internal changes don't leak out.
try:
    from plaid import Client as PlaidClientSDK  # legacy surface
except Exception:  # pragma: no cover - dynamic import guard
    PlaidClientSDK = None  # type: ignore

from ...settings import Settings
from ..base import BankingProvider


class PlaidBanking(BankingProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        if PlaidClientSDK is None:
            raise RuntimeError(
                "plaid-python client not available or import failed; check installed version"
            )
        self.client = PlaidClientSDK(
            client_id=self.settings.plaid_client_id,
            secret=self.settings.plaid_secret,
            environment=self.settings.plaid_env,
        )

    def create_link_token(self, user_id: str) -> str:
        resp = self.client.LinkToken.create(  # type: ignore[attr-defined]
            {
                "user": {"client_user_id": user_id},
                "client_name": "fin-infra",
                "products": ["auth", "transactions"],
                "country_codes": ["US"],
                "language": "en",
            }
        )
        return resp["link_token"]

    def exchange_public_token(self, public_token: str) -> dict:
        return self.client.Item.public_token.exchange(public_token)  # type: ignore[attr-defined]

    def accounts(self, access_token: str) -> list[dict]:
        return self.client.Accounts.get(access_token)["accounts"]  # type: ignore[attr-defined]
