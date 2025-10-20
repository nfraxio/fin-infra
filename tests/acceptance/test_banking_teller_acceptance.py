import os
import pytest

from fin_infra.providers.banking.teller_client import TellerBanking


pytestmark = [pytest.mark.acceptance]


@pytest.mark.skipif(not os.getenv("TELLER_API_KEY"), reason="No Teller key configured")
def test_teller_accounts_smoke():
    tb = TellerBanking(api_key=os.getenv("TELLER_API_KEY"))
    # Placeholder until real implementation: just ensure method exists
    assert hasattr(tb, "accounts")
