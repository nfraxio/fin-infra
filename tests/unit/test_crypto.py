"""Unit tests for crypto data module - easy_crypto and add_crypto_data."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timezone

from fin_infra.crypto import easy_crypto, add_crypto_data
from fin_infra.models import Quote, Candle


class TestEasyCrypto:
    """Test easy_crypto() builder function."""
    
    def test_default_provider_coingecko(self):
        """Should default to CoinGecko provider."""
        crypto = easy_crypto()
        assert crypto is not None
        # CoinGecko is the only supported provider currently
        from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
        assert isinstance(crypto, CoinGeckoCryptoData)
    
    def test_explicit_coingecko_provider(self):
        """Should create CoinGecko provider when explicitly specified."""
        crypto = easy_crypto(provider="coingecko")
        from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
        assert isinstance(crypto, CoinGeckoCryptoData)
    
    def test_invalid_provider_raises_error(self):
        """Should raise ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unknown crypto data provider: invalid"):
            easy_crypto(provider="invalid")
    
    def test_case_insensitive_provider_name(self):
        """Provider name should be case insensitive."""
        crypto = easy_crypto(provider="COINGECKO")
        from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
        assert isinstance(crypto, CoinGeckoCryptoData)


class TestAddCryptoData:
    """Test add_crypto_data() FastAPI integration helper."""
    
    def test_add_crypto_data_mounts_routes(self):
        """Should mount crypto data routes to FastAPI app."""
        from fastapi import FastAPI
        
        app = FastAPI()
        crypto = add_crypto_data(app, prefix="/crypto")
        
        # Check provider stored on app state
        assert hasattr(app.state, "crypto_provider")
        assert app.state.crypto_provider is crypto
        
        # Check routes are mounted
        route_paths = [route.path for route in app.routes]
        assert "/crypto/ticker/{symbol}" in route_paths
        assert "/crypto/ohlcv/{symbol}" in route_paths
    
    def test_add_crypto_data_with_custom_prefix(self):
        """Should mount routes with custom prefix."""
        from fastapi import FastAPI
        
        app = FastAPI()
        add_crypto_data(app, prefix="/api/v1/crypto")
        
        route_paths = [route.path for route in app.routes]
        assert "/api/v1/crypto/ticker/{symbol}" in route_paths
        assert "/api/v1/crypto/ohlcv/{symbol}" in route_paths
    
    def test_add_crypto_data_with_provider_string(self):
        """Should accept provider as string."""
        from fastapi import FastAPI
        
        app = FastAPI()
        crypto = add_crypto_data(app, provider="coingecko")
        
        from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
        assert isinstance(crypto, CoinGeckoCryptoData)
    
    def test_add_crypto_data_with_provider_instance(self):
        """Should accept provider as instance."""
        from fastapi import FastAPI
        from fin_infra.providers.market.coingecko import CoinGeckoCryptoData
        
        app = FastAPI()
        provider_instance = CoinGeckoCryptoData()
        crypto = add_crypto_data(app, provider=provider_instance)
        
        assert crypto is provider_instance
        assert app.state.crypto_provider is provider_instance


class TestCryptoRoutes:
    """Test crypto data API routes."""
    
    @pytest.fixture
    def app_with_crypto(self):
        """Create FastAPI app with crypto data routes."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        add_crypto_data(app, prefix="/crypto")
        return TestClient(app)
    
    @patch("fin_infra.providers.market.coingecko.httpx.get")
    def test_get_ticker_endpoint(self, mock_get, app_with_crypto):
        """Should fetch ticker via API endpoint."""
        # Mock CoinGecko API response
        mock_response = Mock()
        mock_response.json.return_value = {"bitcoin": {"usdt": 45000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Symbol path should be simple string, the provider handles the slash in ticker() method
        response = app_with_crypto.get("/crypto/ticker/BTC-USDT")
        
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "price" in data
        assert "as_of" in data
    
    @patch("fin_infra.providers.market.coingecko.httpx.get")
    def test_get_ohlcv_endpoint(self, mock_get, app_with_crypto):
        """Should fetch OHLCV via API endpoint."""
        # Mock CoinGecko API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "prices": [
                [1704067200000, 45000.0],
                [1704153600000, 46000.0],
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Symbol path should be simple string, the provider handles the slash in ohlcv() method
        response = app_with_crypto.get("/crypto/ohlcv/BTC-USDT?timeframe=1d&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "timeframe" in data
        assert "candles" in data
        assert data["timeframe"] == "1d"
        assert len(data["candles"]) == 2
        
        # Check candle structure
        candle = data["candles"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle
    
    def test_ticker_endpoint_error_handling(self, app_with_crypto):
        """Should handle errors gracefully."""
        with patch("fin_infra.providers.market.coingecko.httpx.get") as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            response = app_with_crypto.get("/crypto/ticker/INVALID")
            
            assert response.status_code == 400
            assert "Error fetching ticker" in response.json()["detail"]
