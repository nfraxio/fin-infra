from __future__ import annotations

# Plaid SDK surface changes across versions; this class intentionally wraps
# creation and calls in a minimal way so internal changes don't leak out.
try:
    from plaid import Client as PlaidClientSDK  # legacy surface
except Exception:  # pragma: no cover - dynamic import guard
    PlaidClientSDK = None  # type: ignore

from ...settings import Settings
from ..base import BankingProvider


class PlaidClient(BankingProvider):
    def __init__(
        self,
        settings: Settings | None = None,
        client_id: str | None = None,
        secret: str | None = None,
        environment: str | None = None,
    ) -> None:
        """Initialize Plaid client with either Settings object or individual parameters.
        
        Args:
            settings: Settings object (legacy pattern)
            client_id: Plaid client ID (preferred - from env or passed directly)
            secret: Plaid secret (preferred - from env or passed directly)
            environment: Plaid environment - sandbox, development, or production
        """
        if PlaidClientSDK is None:
            raise RuntimeError(
                "plaid-python client not available or import failed; check installed version"
            )
        
        # Support both patterns: Settings object or individual params
        if settings is not None:
            # Legacy pattern with Settings object
            client_id = client_id or settings.plaid_client_id
            secret = secret or settings.plaid_secret
            environment = environment or settings.plaid_env
        
        # Individual params take precedence
        self.client = PlaidClientSDK(
            client_id=client_id,
            secret=secret,
            environment=environment,
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

    def transactions(
        self, access_token: str, *, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict]:
        """Fetch transactions for an access token within optional date range."""
        options = {}
        if start_date:
            options["start_date"] = start_date
        if end_date:
            options["end_date"] = end_date
        resp = self.client.Transactions.get(access_token, **options)  # type: ignore[attr-defined]
        return resp.get("transactions", [])

    def balances(self, access_token: str, account_id: str | None = None) -> dict:
        """Fetch current balances for all accounts or specific account."""
        resp = self.client.Accounts.balance.get(access_token)  # type: ignore[attr-defined]
        accounts = resp.get("accounts", [])
        
        if account_id:
            # Filter to specific account
            for account in accounts:
                if account.get("account_id") == account_id:
                    return {"balances": [account.get("balances", {})]}
            return {"balances": []}
        
        # Return all balances
        return {"balances": [acc.get("balances", {}) for acc in accounts]}

    def identity(self, access_token: str) -> dict:
        """Fetch identity/account holder information."""
        return self.client.Identity.get(access_token)  # type: ignore[attr-defined]
