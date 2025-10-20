from __future__ import annotations

from ..base import IdentityProvider


class StripeIdentity(IdentityProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def create_verification_session(self, **kwargs) -> dict:  # pragma: no cover - placeholder
        return {"id": "vs_123", **kwargs}

    def get_verification_session(self, session_id: str) -> dict:  # pragma: no cover - placeholder
        return {"id": session_id, "status": "processing"}
