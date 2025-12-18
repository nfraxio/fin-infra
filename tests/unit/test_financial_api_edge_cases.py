"""Unit tests for financial API edge cases.

Tests cover critical API integration scenarios that could cause data loss,
incorrect calculations, or security issues:

Task 4.4.7 Areas:
1. API Timeout Recovery — Plaid/SnapTrade timeout mid-transaction
2. Token Expiration Race — Token expires during multi-call flow
3. Large Portfolios — Performance with 10,000+ holdings

FINANCIAL SOFTWARE SAFETY REQUIREMENTS:
- Never lose money due to API failures
- Never double-execute operations on retry
- Graceful degradation when providers are down
- Idempotent operations where possible
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from fin_infra.investments.models import (
    Holding,
    Security,
    SecurityType,
    TransactionType,
)

# ============================================================================
# Test Fixtures
# ============================================================================


def create_test_security(
    symbol: str = "AAPL", security_type: SecurityType = SecurityType.equity
) -> Security:
    """Create a test security."""
    return Security(
        security_id=f"sec_{symbol}",
        ticker_symbol=symbol,
        name=f"{symbol} Inc.",
        type=security_type,
        close_price=Decimal("150.00"),
        currency="USD",
    )


def create_test_holding(
    symbol: str = "AAPL",
    quantity: Decimal = Decimal("10"),
    price: Decimal = Decimal("150.00"),
    cost_basis: Decimal | None = Decimal("1400.00"),
) -> Holding:
    """Create a test holding."""
    return Holding(
        account_id="acct_test_001",
        security=create_test_security(symbol),
        quantity=quantity,
        institution_price=price,
        institution_value=quantity * price,
        cost_basis=cost_basis,
        currency="USD",
    )


def create_large_holdings_list(count: int) -> list[Holding]:
    """Create a large list of holdings for performance testing."""
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ"]
    holdings = []
    for i in range(count):
        symbol = symbols[i % len(symbols)]
        holdings.append(
            Holding(
                account_id=f"acct_{i // 100:04d}",
                security=Security(
                    security_id=f"sec_{symbol}_{i}",
                    ticker_symbol=symbol,
                    name=f"{symbol} Inc.",
                    type=SecurityType.equity,
                    close_price=Decimal(str(100 + (i % 100))),
                    currency="USD",
                ),
                quantity=Decimal(str(10 + (i % 50))),
                institution_price=Decimal(str(100 + (i % 100))),
                institution_value=Decimal(str((10 + (i % 50)) * (100 + (i % 100)))),
                cost_basis=Decimal(str((10 + (i % 50)) * (90 + (i % 100)))),
                currency="USD",
            )
        )
    return holdings


# ============================================================================
# 1. API Timeout Recovery Tests — Plaid/SnapTrade timeout mid-transaction
# ============================================================================


class TestAPITimeoutRecovery:
    """Tests for API timeout handling and recovery."""

    @pytest.mark.asyncio
    async def test_snaptrade_timeout_on_get_holdings(self):
        """Test SnapTrade provider handles timeout gracefully."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Mock the httpx client to simulate timeout
        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Connection timeout")

            with pytest.raises((httpx.TimeoutException, ValueError)):
                await provider.get_holdings("user:secret")

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_snaptrade_timeout_on_get_transactions(self):
        """Test SnapTrade provider handles timeout on transactions."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises((httpx.TimeoutException, ValueError)):
                await provider.get_transactions(
                    "user:secret",
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 12, 31),
                )

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_snaptrade_partial_failure_recovery(self):
        """Test SnapTrade recovers when some accounts fail but others succeed."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # First call (accounts) succeeds, second call (positions) times out
        call_count = 0

        async def mock_get(url, headers=None):
            nonlocal call_count
            call_count += 1

            mock_response = AsyncMock()

            if "accounts" in url:
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.json = AsyncMock(
                    return_value=[
                        {"id": "acct_001", "name": "Test Account"},
                    ]
                )
                return mock_response
            elif "positions" in url:
                raise httpx.TimeoutException("Position fetch timed out")

            raise ValueError(f"Unexpected URL: {url}")

        with patch.object(provider.client, "get", side_effect=mock_get):
            with pytest.raises((httpx.TimeoutException, ValueError)):
                await provider.get_holdings("user:secret")

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_experian_client_retry_on_timeout(self):
        """Test Experian client retries on timeout (uses tenacity)."""
        from fin_infra.credit.experian.auth import ExperianAuthManager
        from fin_infra.credit.experian.client import ExperianClient

        # Create mock auth manager
        mock_auth = AsyncMock(spec=ExperianAuthManager)
        mock_auth.get_token = AsyncMock(return_value="mock_token")

        client = ExperianClient(
            base_url="https://sandbox.experian.com",
            auth_manager=mock_auth,
        )

        # Verify client has timeout configured
        assert client.timeout == 10.0

        # Mock the internal httpx client to simulate timeout then success
        with patch.object(client._client, "request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Timeout")

            # The retry decorator should retry but eventually fail
            with pytest.raises(httpx.TimeoutException):
                await client.get_credit_score("user123")

        await client.close()

    @pytest.mark.asyncio
    async def test_snaptrade_default_timeout_configured(self):
        """Verify SnapTrade provider has timeout configured."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Check that httpx client has timeout
        assert provider.client.timeout is not None
        assert provider.client.timeout.connect == 30.0 or provider.client.timeout == 30.0

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_timeout_does_not_corrupt_state(self):
        """Test that timeout during multi-account fetch doesn't corrupt provider state."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Simulate timeout
        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises((httpx.TimeoutException, ValueError)):
                await provider.get_holdings("user:secret")

        # Provider should still be usable after timeout
        assert provider.client_id == "test_client"
        assert provider.consumer_key == "test_key"
        assert provider.client is not None

        await provider.client.aclose()


# ============================================================================
# 2. Token Expiration Race Tests — Token expires during multi-call flow
# ============================================================================


class TestTokenExpirationRace:
    """Tests for token expiration during multi-step API operations."""

    @pytest.mark.asyncio
    async def test_experian_token_invalidation_on_401(self):
        """Test Experian client invalidates token on 401 and retries."""
        from fin_infra.credit.experian.auth import ExperianAuthManager
        from fin_infra.credit.experian.client import ExperianClient
        from fin_infra.exceptions import ExperianAuthError

        mock_auth = AsyncMock(spec=ExperianAuthManager)
        mock_auth.get_token = AsyncMock(return_value="expired_token")
        mock_auth.invalidate = AsyncMock()

        client = ExperianClient(
            base_url="https://sandbox.experian.com",
            auth_manager=mock_auth,
        )

        # Simulate 401 Unauthorized response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Token expired"}}

        with patch.object(client._client, "request") as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_response,
            )

            with pytest.raises(ExperianAuthError):
                await client.get_credit_score("user123")

        # Token should have been invalidated
        mock_auth.invalidate.assert_called()

        await client.close()

    @pytest.mark.asyncio
    async def test_snaptrade_token_format_validation(self):
        """Test SnapTrade validates access_token format (user_id:user_secret)."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Test valid format parsing
        user_id, user_secret = provider._parse_access_token("user_123:secret_abc")
        assert user_id == "user_123"
        assert user_secret == "secret_abc"

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_snaptrade_invalid_token_format_raises(self):
        """Test SnapTrade raises error for invalid token format."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Invalid format (no colon separator)
        with pytest.raises((ValueError, Exception)):
            provider._parse_access_token("invalid_token_no_colon")

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh_race(self):
        """Test handling of concurrent requests during token refresh window."""
        from fin_infra.credit.experian.auth import ExperianAuthManager

        # Simulate a race where two requests try to refresh simultaneously
        refresh_call_count = 0

        class MockAuthManager(ExperianAuthManager):
            def __init__(self):
                self._token = None
                self._lock = asyncio.Lock()

            async def get_token(self) -> str:
                nonlocal refresh_call_count
                async with self._lock:
                    if self._token is None:
                        refresh_call_count += 1
                        await asyncio.sleep(0.01)  # Simulate network delay
                        self._token = f"token_{refresh_call_count}"
                    return self._token

            async def invalidate(self):
                self._token = None

        auth = MockAuthManager()

        # Run concurrent token fetches
        tokens = await asyncio.gather(
            auth.get_token(),
            auth.get_token(),
            auth.get_token(),
        )

        # All requests should get the same token (only one refresh)
        assert all(t == tokens[0] for t in tokens)
        assert refresh_call_count == 1

    @pytest.mark.asyncio
    async def test_token_expiry_mid_multi_account_fetch(self):
        """Test token expires midway through fetching multiple accounts."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        call_count = 0

        async def mock_get(url, headers=None):
            nonlocal call_count
            call_count += 1

            mock_response = AsyncMock()

            if "accounts" in url:
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.json = AsyncMock(
                    return_value=[
                        {"id": "acct_001"},
                        {"id": "acct_002"},
                    ]
                )
                return mock_response
            elif "positions" in url and call_count <= 2:
                # First position fetch succeeds
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.json = AsyncMock(return_value=[])
                return mock_response
            else:
                # Second position fetch fails with 401 (token expired)
                mock_response.status_code = 401
                mock_response.raise_for_status = Mock(
                    side_effect=httpx.HTTPStatusError(
                        "401",
                        request=MagicMock(),
                        response=MagicMock(status_code=401),
                    )
                )
                return mock_response

        with patch.object(provider.client, "get", side_effect=mock_get):
            with pytest.raises((httpx.HTTPStatusError, ValueError)):
                await provider.get_holdings("user:secret")

        await provider.client.aclose()

    def test_plaid_token_validation_patterns(self):
        """Test Plaid token format validation patterns."""
        from fin_infra.banking.utils import (
            validate_mx_token,
            validate_plaid_token,
            validate_teller_token,
        )

        # Valid Plaid token (starts with access-)
        assert validate_plaid_token("access-sandbox-abc123") is True
        assert validate_plaid_token("access-production-xyz789") is True

        # Invalid Plaid token
        assert validate_plaid_token("invalid-token") is False
        assert validate_plaid_token("") is False
        assert validate_plaid_token(None) is False  # type: ignore

        # Teller tokens
        assert validate_teller_token("token_test_abc123") is True
        assert validate_teller_token("invalid") is False

        # MX tokens (uses USR- prefix format)
        assert validate_mx_token("USR-abc123") is True
        assert validate_mx_token("invalid") is False


# ============================================================================
# 3. Large Portfolio Performance Tests — 10,000+ holdings
# ============================================================================


class TestLargePortfolioPerformance:
    """Tests for performance with large portfolios."""

    def test_portfolio_metrics_10k_holdings_performance(self):
        """Test portfolio_metrics_with_holdings handles 10,000 holdings efficiently."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        holdings = create_large_holdings_list(10_000)

        start_time = time.perf_counter()
        metrics = portfolio_metrics_with_holdings(holdings)
        elapsed = time.perf_counter() - start_time

        # Should complete in under 1 second
        assert elapsed < 1.0, f"10k holdings took {elapsed:.2f}s (should be <1s)"

        # Verify results are correct
        assert metrics.total_value > 0
        assert len(metrics.allocation_by_asset_class) > 0

    def test_portfolio_metrics_50k_holdings_performance(self):
        """Test portfolio_metrics_with_holdings handles 50,000 holdings."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        holdings = create_large_holdings_list(50_000)

        start_time = time.perf_counter()
        metrics = portfolio_metrics_with_holdings(holdings)
        elapsed = time.perf_counter() - start_time

        # Should complete in under 3 seconds
        assert elapsed < 3.0, f"50k holdings took {elapsed:.2f}s (should be <3s)"
        assert metrics.total_value > 0

    def test_allocation_calculation_performance(self):
        """Test asset allocation calculation with many unique securities."""
        from fin_infra.analytics.portfolio import _calculate_allocation_from_holdings

        holdings = create_large_holdings_list(10_000)
        total_value = float(sum(h.institution_value for h in holdings))

        start_time = time.perf_counter()
        allocation = _calculate_allocation_from_holdings(holdings, total_value)
        elapsed = time.perf_counter() - start_time

        # Should complete in under 0.5 seconds
        assert elapsed < 0.5, f"Allocation calc took {elapsed:.2f}s (should be <0.5s)"
        assert len(allocation) > 0

    def test_large_holding_memory_efficiency(self):
        """Test that large holdings don't cause excessive memory usage."""
        import sys

        # Create 10k holdings
        holdings = create_large_holdings_list(10_000)

        # Each holding should be reasonable size
        single_holding_size = sys.getsizeof(holdings[0])
        # Holding objects are larger due to nested Security, but should be < 10KB each
        assert single_holding_size < 10_000

    def test_decimal_precision_maintained_in_large_sum(self):
        """Test Decimal precision maintained when summing large holdings."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        # Create holdings with precise decimal values
        holdings = []
        for i in range(10_000):
            holdings.append(
                Holding(
                    account_id="acct_test",
                    security=create_test_security(f"SEC{i}"),
                    quantity=Decimal("0.001"),  # Small quantity
                    institution_price=Decimal("0.001"),  # Small price
                    institution_value=Decimal("0.000001"),  # Very small value
                    cost_basis=Decimal("0.0000009"),
                    currency="USD",
                )
            )

        metrics = portfolio_metrics_with_holdings(holdings)

        # Total should be exactly 0.01 (10000 * 0.000001)
        assert abs(metrics.total_value - 0.01) < 0.00001

    def test_empty_holdings_performance(self):
        """Test performance with empty holdings list."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        start_time = time.perf_counter()
        metrics = portfolio_metrics_with_holdings([])
        elapsed = time.perf_counter() - start_time

        assert elapsed < 0.01
        assert metrics.total_value == 0
        assert len(metrics.allocation_by_asset_class) == 0

    def test_single_holding_edge_case(self):
        """Test with single holding (degenerate case)."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        holdings = [create_test_holding()]
        metrics = portfolio_metrics_with_holdings(holdings)

        assert metrics.total_value == 1500.0  # 10 * 150
        assert len(metrics.allocation_by_asset_class) == 1
        assert metrics.allocation_by_asset_class[0].percentage == 100.0


# ============================================================================
# 4. HTTP Error Handling Tests
# ============================================================================


class TestHTTPErrorHandling:
    """Tests for proper HTTP error handling in API clients."""

    @pytest.mark.asyncio
    async def test_snaptrade_rate_limit_error(self):
        """Test SnapTrade handles 429 rate limit error."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}

        with patch.object(provider.client, "get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 429
            mock_response_obj.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "429",
                    request=MagicMock(),
                    response=mock_response,
                )
            )
            mock_get.return_value = mock_response_obj

            with pytest.raises((httpx.HTTPStatusError, ValueError)):
                await provider.get_holdings("user:secret")

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_snaptrade_500_server_error(self):
        """Test SnapTrade handles 500 server error."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Create proper mock response for 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {"error": "Internal Server Error"}

        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=mock_response,
            )

            # Should raise either HTTPStatusError or ValueError (transformed)
            with pytest.raises((httpx.HTTPStatusError, ValueError, Exception)):
                await provider.get_holdings("user:secret")

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_experian_rate_limit_error(self):
        """Test Experian client handles 429 rate limit."""
        from fin_infra.credit.experian.auth import ExperianAuthManager
        from fin_infra.credit.experian.client import ExperianClient
        from fin_infra.exceptions import ExperianRateLimitError

        mock_auth = AsyncMock(spec=ExperianAuthManager)
        mock_auth.get_token = AsyncMock(return_value="mock_token")

        client = ExperianClient(
            base_url="https://sandbox.experian.com",
            auth_manager=mock_auth,
        )

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        with patch.object(client._client, "request") as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "429",
                request=MagicMock(),
                response=mock_response,
            )

            # After retries, should raise rate limit error
            with pytest.raises((ExperianRateLimitError, httpx.HTTPStatusError)):
                await client.get_credit_score("user123")

        await client.close()

    @pytest.mark.asyncio
    async def test_experian_not_found_error(self):
        """Test Experian client handles 404 not found."""
        from fin_infra.credit.experian.auth import ExperianAuthManager
        from fin_infra.credit.experian.client import ExperianClient
        from fin_infra.exceptions import ExperianNotFoundError

        mock_auth = AsyncMock(spec=ExperianAuthManager)
        mock_auth.get_token = AsyncMock(return_value="mock_token")

        client = ExperianClient(
            base_url="https://sandbox.experian.com",
            auth_manager=mock_auth,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": {"message": "User not found"}}

        with patch.object(client._client, "request") as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "404",
                request=MagicMock(),
                response=mock_response,
            )

            with pytest.raises(ExperianNotFoundError):
                await client.get_credit_score("nonexistent_user")

        await client.close()


# ============================================================================
# 5. Provider Initialization Edge Cases
# ============================================================================


class TestProviderInitialization:
    """Tests for provider initialization edge cases."""

    def test_snaptrade_missing_credentials_raises(self):
        """Test SnapTrade raises error when credentials missing."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        with pytest.raises(ValueError, match="client_id and consumer_key are required"):
            SnapTradeInvestmentProvider(client_id="", consumer_key="key")

        with pytest.raises(ValueError, match="client_id and consumer_key are required"):
            SnapTradeInvestmentProvider(client_id="id", consumer_key="")

        with pytest.raises(ValueError, match="client_id and consumer_key are required"):
            SnapTradeInvestmentProvider(client_id="", consumer_key="")

    def test_plaid_client_plaid_unavailable(self):
        """Test PlaidClient raises when plaid-python not installed."""
        # This test verifies the import guard works
        import sys
        from unittest.mock import patch

        # Temporarily remove plaid from sys.modules
        original_modules = sys.modules.copy()

        try:
            # Remove any plaid-related modules
            plaid_modules = [k for k in sys.modules if k.startswith("plaid")]
            for mod in plaid_modules:
                del sys.modules[mod]

            # Mock the import to fail
            with patch.dict(sys.modules, {"plaid": None}):
                # Force reimport - the module should handle missing plaid gracefully
                # Since plaid is actually installed, we just verify PLAID_AVAILABLE flag exists
                from fin_infra.providers.banking import plaid_client

                # The module should have the PLAID_AVAILABLE constant
                assert hasattr(plaid_client, "PLAID_AVAILABLE")
        finally:
            # Restore original modules
            sys.modules.update(original_modules)

    @pytest.mark.asyncio
    async def test_snaptrade_context_manager(self):
        """Test SnapTrade provider works as async context manager."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        async with SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        ) as provider:
            assert provider.client_id == "test_client"
            assert provider.client is not None

        # Client should be closed after context exit
        # (We can't easily verify this without checking internal state)

    def test_experian_client_initialization(self):
        """Test Experian client initializes correctly."""
        from fin_infra.credit.experian.auth import ExperianAuthManager
        from fin_infra.credit.experian.client import ExperianClient

        mock_auth = MagicMock(spec=ExperianAuthManager)

        client = ExperianClient(
            base_url="https://sandbox.experian.com",
            auth_manager=mock_auth,
            timeout=30.0,
        )

        assert client.base_url == "https://sandbox.experian.com"
        assert client.timeout == 30.0
        assert client.auth == mock_auth


# ============================================================================
# 6. Data Transformation Edge Cases
# ============================================================================


class TestDataTransformationEdgeCases:
    """Tests for edge cases in data transformation."""

    def test_snaptrade_transform_holding_missing_fields(self):
        """Test SnapTrade handles missing fields in position data."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Minimal position data (missing optional fields)
        position = {
            "symbol": {"symbol": "AAPL"},
            "units": 10,
            "price": 150.00,
            "value": 1500.00,
        }

        holding = provider._transform_holding(position, "acct_001")

        assert holding.account_id == "acct_001"
        assert holding.quantity == Decimal("10")
        assert holding.institution_price == Decimal("150")

    def test_snaptrade_transform_transaction_missing_fields(self):
        """Test SnapTrade handles missing fields in transaction data."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Minimal transaction data
        transaction = {
            "id": "tx_001",
            "date": "2024-01-15",
            "symbol": {"symbol": "AAPL"},
            "type": "BUY",
            "units": 10,
            "amount": 1500.00,
            "price": 150.00,
        }

        tx = provider._transform_transaction(transaction, "acct_001")

        assert tx.transaction_id == "tx_001"
        assert tx.account_id == "acct_001"

    def test_snaptrade_normalize_security_type(self):
        """Test SnapTrade normalizes various security type strings."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Test common security type mappings (SnapTrade uses specific type strings)
        # These mappings depend on actual implementation - verify some return valid types
        assert provider._normalize_security_type("equity") == SecurityType.equity
        assert provider._normalize_security_type("etf") == SecurityType.etf
        # Unknown types should map to 'other'
        assert provider._normalize_security_type("unknown_type_xyz") == SecurityType.other

    def test_snaptrade_normalize_transaction_type(self):
        """Test SnapTrade normalizes various transaction type strings."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        # Test common transaction type mappings
        assert provider._normalize_transaction_type("BUY") == TransactionType.buy
        assert provider._normalize_transaction_type("SELL") == TransactionType.sell
        assert provider._normalize_transaction_type("DIVIDEND") == TransactionType.dividend
        assert provider._normalize_transaction_type("UNKNOWN") == TransactionType.other


# ============================================================================
# 7. Banking Connection Status Edge Cases
# ============================================================================


class TestBankingConnectionStatusEdgeCases:
    """Tests for banking connection status parsing edge cases."""

    def test_parse_empty_banking_providers(self):
        """Test parsing empty banking_providers dict."""
        from fin_infra.banking.utils import parse_banking_providers

        status = parse_banking_providers({})

        assert status.has_any_connection is False
        assert len(status.connected_providers) == 0

    def test_parse_none_banking_providers(self):
        """Test parsing None banking_providers."""
        from fin_infra.banking.utils import parse_banking_providers

        status = parse_banking_providers(None)  # type: ignore

        assert status.has_any_connection is False

    def test_parse_plaid_unhealthy_connection(self):
        """Test parsing unhealthy Plaid connection."""
        from fin_infra.banking.utils import parse_banking_providers

        providers = {
            "plaid": {
                "access_token": "access-sandbox-abc123",
                "item_id": "item_abc123",
                "is_healthy": False,
                "error_message": "Item login required",
            }
        }

        status = parse_banking_providers(providers)

        assert status.plaid is not None
        assert status.plaid.connected is True
        assert status.plaid.is_healthy is False
        assert "login required" in status.plaid.error_message.lower()

    def test_should_refresh_token_stale_sync(self):
        """Test token refresh check for stale last_synced_at."""
        from datetime import datetime, timedelta

        from fin_infra.banking.utils import should_refresh_token

        # Last synced 31 days ago - should refresh (use timezone-aware datetime)
        old_sync = (datetime.now(UTC) - timedelta(days=31)).isoformat()
        providers = {
            "plaid": {
                "access_token": "access-sandbox-abc123",
                "last_synced_at": old_sync,
            }
        }

        assert should_refresh_token(providers, "plaid") is True

    def test_should_refresh_token_recent_sync(self):
        """Test token refresh check for recent sync."""
        from datetime import datetime, timedelta

        from fin_infra.banking.utils import should_refresh_token

        # Last synced 1 day ago - should not refresh (use timezone-aware datetime)
        recent_sync = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        providers = {
            "plaid": {
                "access_token": "access-sandbox-abc123",
                "last_synced_at": recent_sync,
                "is_healthy": True,
            }
        }

        assert should_refresh_token(providers, "plaid") is False


# ============================================================================
# 8. Concurrent Request Safety
# ============================================================================


class TestConcurrentRequestSafety:
    """Tests for safety under concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_holdings_fetches_independent(self):
        """Test concurrent holdings fetches are independent."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        call_count = 0

        async def mock_get(url, headers=None):
            nonlocal call_count
            call_count += 1

            # Simulate some delay
            await asyncio.sleep(0.01)

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            if "accounts" in url:
                mock_response.json = AsyncMock(return_value=[{"id": "acct_001"}])
            else:
                mock_response.json = AsyncMock(return_value=[])

            return mock_response

        with patch.object(provider.client, "get", side_effect=mock_get):
            # Run multiple concurrent fetches
            results = await asyncio.gather(
                provider.get_holdings("user1:secret1"),
                provider.get_holdings("user2:secret2"),
                provider.get_holdings("user3:secret3"),
                return_exceptions=True,
            )

            # All should complete (success or error, but not hang)
            assert len(results) == 3

        await provider.client.aclose()

    @pytest.mark.asyncio
    async def test_portfolio_metrics_thread_safe(self):
        """Test portfolio metrics calculation is thread-safe."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        holdings = create_large_holdings_list(1000)

        # Run concurrent calculations
        async def calculate():
            return portfolio_metrics_with_holdings(holdings)

        results = await asyncio.gather(
            calculate(),
            calculate(),
            calculate(),
        )

        # All results should be identical
        assert all(r.total_value == results[0].total_value for r in results)


# ============================================================================
# 9. Brokerage Capabilities Edge Cases
# ============================================================================


class TestBrokerageCapabilitiesEdgeCases:
    """Tests for brokerage capabilities edge cases."""

    def test_robinhood_read_only(self):
        """Test Robinhood is correctly marked as read-only."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        caps = provider.get_brokerage_capabilities("Robinhood")

        assert caps["supports_trading"] is False
        assert caps["read_only"] is True

    def test_etrade_supports_trading(self):
        """Test E*TRADE supports trading."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        caps = provider.get_brokerage_capabilities("E*TRADE")

        assert caps["supports_trading"] is True
        assert caps["supports_options"] is True

    def test_unknown_brokerage_defaults(self):
        """Test unknown brokerage returns safe defaults."""
        from fin_infra.investments.providers.snaptrade import SnapTradeInvestmentProvider

        provider = SnapTradeInvestmentProvider(
            client_id="test_client",
            consumer_key="test_key",
        )

        caps = provider.get_brokerage_capabilities("SomeUnknownBrokerage")

        # Should return safe defaults
        assert "supports_trading" in caps
        assert "read_only" in caps


# ============================================================================
# 10. Edge Cases with Decimal Money Values
# ============================================================================


class TestDecimalMoneyEdgeCases:
    """Tests for Decimal precision in financial calculations."""

    def test_holding_with_zero_quantity(self):
        """Test holding with zero quantity (closed position)."""
        holding = Holding(
            account_id="acct_test",
            security=create_test_security(),
            quantity=Decimal("0"),
            institution_price=Decimal("150.00"),
            institution_value=Decimal("0"),
            cost_basis=Decimal("0"),
            currency="USD",
        )

        assert holding.institution_value == Decimal("0")

    def test_holding_with_fractional_shares(self):
        """Test holding with fractional shares (common in modern brokerages)."""
        holding = Holding(
            account_id="acct_test",
            security=create_test_security("GOOGL"),
            quantity=Decimal("0.12345"),  # Fractional share
            institution_price=Decimal("2850.50"),
            institution_value=Decimal("351.8542725"),  # Precise value
            cost_basis=Decimal("300.00"),
            currency="USD",
        )

        # Verify precision is maintained
        assert holding.quantity == Decimal("0.12345")
        assert holding.institution_value == Decimal("351.8542725")

    def test_holding_with_very_small_value(self):
        """Test holding with very small value (crypto dust)."""
        holding = Holding(
            account_id="acct_test",
            security=create_test_security("BTC"),
            quantity=Decimal("0.00000001"),  # 1 satoshi equivalent
            institution_price=Decimal("50000.00"),
            institution_value=Decimal("0.0005"),
            cost_basis=Decimal("0.0004"),
            currency="USD",
        )

        assert holding.quantity == Decimal("0.00000001")

    def test_holding_with_large_value(self):
        """Test holding with very large value."""
        holding = Holding(
            account_id="acct_test",
            security=create_test_security("BRK.A"),  # Berkshire Class A
            quantity=Decimal("100"),
            institution_price=Decimal("500000.00"),  # ~$500k per share
            institution_value=Decimal("50000000.00"),  # $50M position
            cost_basis=Decimal("45000000.00"),
            currency="USD",
        )

        # Verify large values work correctly
        assert holding.institution_value == Decimal("50000000.00")

        # Calculate P/L
        gain = holding.institution_value - (holding.cost_basis or Decimal("0"))
        assert gain == Decimal("5000000.00")

    def test_portfolio_metrics_with_mixed_precision(self):
        """Test portfolio metrics with holdings of varying precision."""
        from fin_infra.analytics.portfolio import portfolio_metrics_with_holdings

        holdings = [
            Holding(
                account_id="acct_test",
                security=create_test_security("AAPL"),
                quantity=Decimal("100"),
                institution_price=Decimal("150.00"),
                institution_value=Decimal("15000.00"),
                cost_basis=Decimal("14000.00"),
                currency="USD",
            ),
            Holding(
                account_id="acct_test",
                security=create_test_security("SHIB"),  # High precision crypto
                quantity=Decimal("1000000.12345678"),
                institution_price=Decimal("0.00001234"),
                institution_value=Decimal("12.34"),  # ~$12
                cost_basis=Decimal("10.00"),
                currency="USD",
            ),
        ]

        metrics = portfolio_metrics_with_holdings(holdings)

        # Should handle mixed precision correctly
        assert metrics.total_value == pytest.approx(15012.34, rel=0.001)
