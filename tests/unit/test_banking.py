"""Tests for banking provider integration."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
import httpx

from fin_infra.banking import easy_banking
from fin_infra.providers.banking.teller_client import TellerClient
from fin_infra.providers.base import BankingProvider


class TestEasyBanking:
    """Test easy_banking() builder function."""

    def test_easy_banking_default_teller(self):
        """Test that easy_banking() defaults to Teller provider."""
        with patch.dict(
            "os.environ",
            {
                "TELLER_CERTIFICATE_PATH": "./cert.pem",
                "TELLER_PRIVATE_KEY_PATH": "./key.pem",
                "TELLER_ENVIRONMENT": "sandbox",
            },
        ), patch("ssl.create_default_context"), patch("httpx.Client"):
            banking = easy_banking()
            assert isinstance(banking, BankingProvider)
            assert isinstance(banking, TellerClient)
            assert banking.cert_path == "./cert.pem"
            assert banking.key_path == "./key.pem"
            assert banking.environment == "sandbox"

    def test_easy_banking_explicit_provider(self):
        """Test easy_banking() with explicit provider name."""
        with patch.dict(
            "os.environ",
            {
                "TELLER_CERTIFICATE_PATH": "./cert.pem",
                "TELLER_PRIVATE_KEY_PATH": "./key.pem",
            },
        ), patch("ssl.create_default_context"), patch("httpx.Client"):
            banking = easy_banking(provider="teller")
            assert isinstance(banking, TellerClient)

    def test_easy_banking_config_override(self):
        """Test easy_banking() with configuration override."""
        # Clear any cached providers first
        from fin_infra.providers.registry import _registry
        _registry._cache.clear()
        
        with patch("ssl.create_default_context"), patch("httpx.Client"):
            banking = easy_banking(
                provider="teller",
                cert_path="./override_cert.pem",
                key_path="./override_key.pem",
                environment="production",
            )
            assert isinstance(banking, TellerClient)
            assert banking.cert_path == "./override_cert.pem"
            assert banking.key_path == "./override_key.pem"
            assert banking.environment == "production"

    def test_easy_banking_missing_env_uses_defaults(self):
        """Test easy_banking() uses defaults when env vars missing."""
        # Clear any cached providers first
        from fin_infra.providers.registry import _registry
        _registry._cache.clear()
        
        with patch.dict("os.environ", {}, clear=True):
            banking = easy_banking()
            assert isinstance(banking, TellerClient)
            # Should use None cert paths for sandbox (test mode)
            assert banking.cert_path is None
            assert banking.key_path is None
            assert banking.environment == "sandbox"


class TestTellerClient:
    """Test Teller banking provider implementation."""

    def test_init_with_defaults(self):
        """Test TellerClient initialization with defaults."""
        teller = TellerClient()
        assert teller.cert_path is None
        assert teller.key_path is None
        assert teller.environment == "sandbox"
        assert teller.base_url == "https://api.sandbox.teller.io"
        assert teller.timeout == 30.0

    def test_init_with_custom_config(self):
        """Test TellerClient initialization with custom configuration."""
        with patch("ssl.create_default_context"), patch("httpx.Client"):
            teller = TellerClient(
                cert_path="./cert.pem",
                key_path="./key.pem",
                environment="production",
                timeout=60.0,
            )
            assert teller.cert_path == "./cert.pem"
            assert teller.key_path == "./key.pem"
            assert teller.environment == "production"
            assert teller.base_url == "https://api.teller.io"
            assert teller.timeout == 60.0

    def test_init_production_requires_certificates(self):
        """Test TellerClient requires certificates in production."""
        with pytest.raises(ValueError, match="cert_path and key_path are required"):
            TellerClient(environment="production")

    def test_create_link_token(self):
        """Test create_link_token makes correct API call."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {"enrollment_id": "test_enrollment_123"}
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "request", return_value=mock_response) as mock_request:
            result = teller.create_link_token(user_id="user123")
        
        assert result == "test_enrollment_123"
        mock_request.assert_called_once_with(
            "POST",
            "/enrollments",
            json={
                "user_id": "user123",
                "products": ["accounts", "transactions", "balances", "identity"],
            },
        )

    def test_exchange_public_token(self):
        """Test exchange_public_token returns access token."""
        teller = TellerClient()
        result = teller.exchange_public_token("public_token_123")
        
        assert result == {
            "access_token": "public_token_123",
            "item_id": None,
        }

    def test_accounts(self):
        """Test accounts fetches account list."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "acc_123",
                "name": "Checking",
                "type": "checking",
                "mask": "1234",
                "currency": "USD",
            }
        ]
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "get", return_value=mock_response) as mock_get:
            result = teller.accounts(access_token="token_123")
        
        assert len(result) == 1
        assert result[0]["id"] == "acc_123"
        mock_get.assert_called_once_with(
            "/accounts",
            auth=("token_123", ""),
        )

    def test_transactions(self):
        """Test transactions fetches transaction list."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": "txn_123",
                "account_id": "acc_123",
                "amount": -50.00,
                "date": "2025-01-01",
            }
        ]
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "get", return_value=mock_response) as mock_get:
            result = teller.transactions(
                access_token="token_123",
                start_date="2025-01-01",
                end_date="2025-01-31",
            )
        
        assert len(result) == 1
        assert result[0]["id"] == "txn_123"
        mock_get.assert_called_once_with(
            "/transactions",
            auth=("token_123", ""),
            params={"from_date": "2025-01-01", "to_date": "2025-01-31"},
        )

    def test_balances_all_accounts(self):
        """Test balances fetches all account balances."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "accounts": [{"id": "acc_123", "balance": 1000.00}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "get", return_value=mock_response) as mock_get:
            result = teller.balances(access_token="token_123")
        
        assert "accounts" in result
        mock_get.assert_called_once_with(
            "/accounts/balances",
            auth=("token_123", ""),
        )

    def test_balances_specific_account(self):
        """Test balances fetches specific account balance."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "balance_available": 1000.00,
            "balance_current": 1050.00,
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "get", return_value=mock_response) as mock_get:
            result = teller.balances(access_token="token_123", account_id="acc_123")
        
        assert result["balance_available"] == 1000.00
        mock_get.assert_called_once_with(
            "/accounts/acc_123/balances",
            auth=("token_123", ""),
        )

    def test_identity(self):
        """Test identity fetches account holder information."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "John Doe",
            "email": "john@example.com",
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(teller.client, "get", return_value=mock_response) as mock_get:
            result = teller.identity(access_token="token_123")
        
        assert result["name"] == "John Doe"
        mock_get.assert_called_once_with(
            "/identity",
            auth=("token_123", ""),
        )

    def test_request_error_handling(self):
        """Test _request handles HTTP errors."""
        teller = TellerClient()
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=Mock(),
            response=Mock(),
        )
        
        with patch.object(teller.client, "request", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                teller._request("GET", "/test")
