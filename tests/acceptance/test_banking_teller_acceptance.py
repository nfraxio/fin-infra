import os
import pytest

from fin_infra.providers.banking.teller_client import TellerClient


pytestmark = [pytest.mark.acceptance]


def _teller_certs_available():
    """Check if Teller certificates exist."""
    cert_path = os.getenv("TELLER_CERTIFICATE_PATH")
    key_path = os.getenv("TELLER_PRIVATE_KEY_PATH")
    return cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path)


@pytest.mark.skipif(
    not _teller_certs_available(),
    reason="No Teller certificates configured or files not found (set TELLER_CERTIFICATE_PATH and TELLER_PRIVATE_KEY_PATH)",
)
def test_teller_accounts_smoke():
    """Smoke test for Teller banking provider with real certificates."""
    cert_path = os.getenv("TELLER_CERTIFICATE_PATH")
    key_path = os.getenv("TELLER_PRIVATE_KEY_PATH")
    environment = os.getenv("TELLER_ENVIRONMENT", "sandbox")

    teller = TellerClient(cert_path=cert_path, key_path=key_path, environment=environment)

    # Verify all required methods exist
    assert hasattr(teller, "create_link_token")
    assert hasattr(teller, "exchange_public_token")
    assert hasattr(teller, "accounts")
    assert hasattr(teller, "transactions")
    assert hasattr(teller, "balances")
    assert hasattr(teller, "identity")

    # Verify client is properly initialized
    assert teller.cert_path == cert_path
    assert teller.key_path == key_path
    assert teller.environment == environment
    assert teller.base_url == "https://api.sandbox.teller.io"
