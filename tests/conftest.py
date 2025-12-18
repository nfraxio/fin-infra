"""
Root conftest.py for fin-infra tests.

This file provides:
1. Common pytest markers for test categorization
2. Shared fixtures used across multiple test modules
3. Mock svc-infra dependencies (auth, database)
4. Common financial data fixtures

Fixtures are organized by category:
- Auth/Session mocks (svc-infra dependencies)
- FastAPI app/client fixtures
- Financial data fixtures (accounts, transactions, holdings)
- Store clearing helpers
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        path = str(item.fspath)
        norm = path.replace("\\", "/")

        # Mark integration tests
        if "/tests/integration/" in norm:
            item.add_marker(pytest.mark.integration)

        # Mark acceptance tests
        if "/tests/acceptance/" in norm:
            item.add_marker(pytest.mark.acceptance)

        # Mark by module name
        if "banking" in norm:
            item.add_marker(pytest.mark.banking)
        if "brokerage" in norm or "investments" in norm:
            item.add_marker(pytest.mark.brokerage)
        if "credit" in norm:
            item.add_marker(pytest.mark.credit)
        if "market" in norm:
            item.add_marker(pytest.mark.market)
        if "goals" in norm:
            item.add_marker(pytest.mark.goals)
        if "budgets" in norm:
            item.add_marker(pytest.mark.budgets)
        if "tax" in norm:
            item.add_marker(pytest.mark.tax)


def pytest_configure(config):
    """Register custom markers."""
    for name, desc in [
        ("integration", "Integration tests requiring full app setup"),
        ("acceptance", "Acceptance tests against real or mock providers"),
        ("banking", "Banking integration tests"),
        ("brokerage", "Brokerage/investments tests"),
        ("credit", "Credit score/report tests"),
        ("market", "Market data tests"),
        ("goals", "Financial goals tests"),
        ("budgets", "Budget management tests"),
        ("tax", "Tax calculation tests"),
        ("slow", "Slow-running tests"),
    ]:
        config.addinivalue_line("markers", f"{name}: {desc}")


# =============================================================================
# MOCK SVC-INFRA CLASSES
# =============================================================================


class MockUser:
    """Mock user object for testing.

    Mimics the user object from svc-infra auth system.
    """

    def __init__(
        self,
        id: str = "test_user",
        email: str = "test@example.com",
        is_active: bool = True,
    ):
        self.id = id
        self.email = email
        self.is_active = is_active


class MockDatabaseSession:
    """Mock database session for testing.

    Provides a minimal interface compatible with svc-infra's get_session.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    async def execute(self, *_, **__):
        class _Res:
            def scalars(self):
                return self

            def all(self):
                return []

            def scalar_one_or_none(self):
                return None

        return _Res()

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    async def get(self, model, pk):
        return MockUser()


# =============================================================================
# SVC-INFRA MOCK FIXTURES
# =============================================================================


@pytest.fixture
def mock_user() -> MockUser:
    """Create a mock user for testing."""
    return MockUser()


@pytest.fixture
def mock_session() -> MockDatabaseSession:
    """Create a mock database session."""
    return MockDatabaseSession()


def setup_svc_infra_mocks(app: FastAPI, user: MockUser | None = None):
    """Set up svc-infra dependency mocks for a FastAPI app.

    This overrides get_session and _current_principal dependencies
    so that fin-infra endpoints can run without a real svc-infra setup.

    Args:
        app: FastAPI application
        user: Optional MockUser (created if not provided)

    Returns:
        The MockUser being used

    Example:
        @pytest.fixture
        def app():
            app = FastAPI()
            add_budgets(app)
            setup_svc_infra_mocks(app)
            return app
    """
    from svc_infra.api.fastapi.db.sql.session import get_session
    from svc_infra.api.fastapi.auth.security import _current_principal, Principal

    if user is None:
        user = MockUser()

    session = MockDatabaseSession()

    async def _mock_session():
        return session

    async def mock_principal(request=None, session=None, jwt_or_cookie=None, ak=None):
        return Principal(user=user, scopes=["read", "write"], via="test")

    app.dependency_overrides[get_session] = _mock_session
    app.dependency_overrides[_current_principal] = mock_principal

    return user


# =============================================================================
# FASTAPI FIXTURES
# =============================================================================


@pytest.fixture
def base_app() -> FastAPI:
    """Create a base FastAPI app with svc-infra mocks.

    This fixture provides a minimal FastAPI app with mocked dependencies.
    Add your endpoints on top of this.
    """
    app = FastAPI(title="Test API")
    setup_svc_infra_mocks(app)
    return app


@pytest.fixture
def test_client(base_app) -> TestClient:
    """Create a test client for the base app."""
    return TestClient(base_app)


# =============================================================================
# STORE CLEARING HELPERS
# =============================================================================


@pytest.fixture(autouse=False)
def clear_goals_stores():
    """Clear goals and funding stores before/after each test.

    Use with autouse=True in test modules that need clean state.
    """
    from fin_infra.goals.management import clear_goals_store
    from fin_infra.goals.funding import clear_funding_store

    clear_goals_store()
    clear_funding_store()
    yield
    clear_goals_store()
    clear_funding_store()


# =============================================================================
# FINANCIAL DATA FIXTURES
# =============================================================================


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Provide sample bank account data for testing."""
    return {
        "account_id": "acc_123",
        "name": "Test Checking",
        "type": "depository",
        "subtype": "checking",
        "balance_available": Decimal("1500.00"),
        "balance_current": Decimal("1500.00"),
        "currency": "USD",
        "institution_id": "ins_1",
        "institution_name": "Test Bank",
    }


@pytest.fixture
def sample_accounts() -> List[Dict[str, Any]]:
    """Provide multiple sample accounts for testing."""
    return [
        {
            "account_id": "acc_checking",
            "name": "Checking",
            "type": "depository",
            "subtype": "checking",
            "balance_available": Decimal("5000.00"),
            "balance_current": Decimal("5000.00"),
            "currency": "USD",
        },
        {
            "account_id": "acc_savings",
            "name": "Savings",
            "type": "depository",
            "subtype": "savings",
            "balance_available": Decimal("10000.00"),
            "balance_current": Decimal("10000.00"),
            "currency": "USD",
        },
        {
            "account_id": "acc_credit",
            "name": "Credit Card",
            "type": "credit",
            "subtype": "credit card",
            "balance_available": Decimal("3000.00"),
            "balance_current": Decimal("-500.00"),
            "currency": "USD",
        },
    ]


@pytest.fixture
def sample_transaction_data() -> Dict[str, Any]:
    """Provide sample transaction data for testing."""
    return {
        "transaction_id": "txn_123",
        "account_id": "acc_123",
        "amount": Decimal("42.50"),
        "date": datetime.now(timezone.utc),
        "name": "Coffee Shop",
        "merchant_name": "Starbucks",
        "category": ["Food and Drink", "Coffee"],
        "pending": False,
    }


@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    """Provide multiple sample transactions for testing."""
    now = datetime.now(timezone.utc)
    return [
        {
            "transaction_id": "txn_1",
            "account_id": "acc_123",
            "amount": Decimal("50.00"),
            "date": now - timedelta(days=1),
            "name": "Grocery Store",
            "category": ["Shops", "Supermarkets"],
            "pending": False,
        },
        {
            "transaction_id": "txn_2",
            "account_id": "acc_123",
            "amount": Decimal("12.99"),
            "date": now - timedelta(days=2),
            "name": "Netflix",
            "category": ["Service", "Subscription"],
            "pending": False,
        },
        {
            "transaction_id": "txn_3",
            "account_id": "acc_123",
            "amount": Decimal("2500.00"),
            "date": now - timedelta(days=5),
            "name": "Payroll",
            "category": ["Transfer", "Payroll"],
            "pending": False,
        },
    ]


@pytest.fixture
def sample_holding_data() -> Dict[str, Any]:
    """Provide sample investment holding data for testing."""
    return {
        "holding_id": "hold_123",
        "account_id": "acc_brokerage",
        "symbol": "AAPL",
        "quantity": Decimal("10.0"),
        "cost_basis": Decimal("150.00"),
        "current_price": Decimal("175.00"),
        "market_value": Decimal("1750.00"),
        "currency": "USD",
    }


@pytest.fixture
def sample_holdings() -> List[Dict[str, Any]]:
    """Provide multiple sample holdings for testing."""
    return [
        {
            "holding_id": "hold_aapl",
            "symbol": "AAPL",
            "quantity": Decimal("10.0"),
            "cost_basis": Decimal("150.00"),
            "current_price": Decimal("175.00"),
            "market_value": Decimal("1750.00"),
        },
        {
            "holding_id": "hold_googl",
            "symbol": "GOOGL",
            "quantity": Decimal("5.0"),
            "cost_basis": Decimal("120.00"),
            "current_price": Decimal("140.00"),
            "market_value": Decimal("700.00"),
        },
        {
            "holding_id": "hold_vti",
            "symbol": "VTI",
            "quantity": Decimal("20.0"),
            "cost_basis": Decimal("200.00"),
            "current_price": Decimal("220.00"),
            "market_value": Decimal("4400.00"),
        },
    ]


@pytest.fixture
def sample_quote_data() -> Dict[str, Any]:
    """Provide sample market quote data for testing."""
    return {
        "symbol": "AAPL",
        "price": Decimal("175.50"),
        "change": Decimal("2.30"),
        "change_percent": Decimal("1.33"),
        "volume": 45_000_000,
        "timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_goal_data() -> Dict[str, Any]:
    """Provide sample financial goal data for testing."""
    return {
        "name": "Emergency Fund",
        "target_amount": Decimal("10000.00"),
        "current_amount": Decimal("2500.00"),
        "deadline": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "category": "savings",
        "priority": "high",
    }


@pytest.fixture
def sample_budget_data() -> Dict[str, Any]:
    """Provide sample budget data for testing."""
    return {
        "name": "Monthly Food Budget",
        "category": "Food and Drink",
        "amount": Decimal("500.00"),
        "period": "monthly",
        "start_date": datetime.now(timezone.utc).replace(day=1).isoformat(),
    }


@pytest.fixture
def sample_credit_report_data() -> Dict[str, Any]:
    """Provide sample credit report data for testing."""
    return {
        "score": 750,
        "score_type": "FICO",
        "report_date": datetime.now(timezone.utc).isoformat(),
        "accounts_count": 5,
        "credit_utilization": Decimal("0.25"),
        "payment_history": "good",
    }


# =============================================================================
# CASHFLOW FIXTURES
# =============================================================================


@pytest.fixture
def sample_cashflows() -> List[float]:
    """Provide sample cashflows for NPV/IRR testing."""
    return [-1000.0, 200.0, 300.0, 400.0, 500.0]


@pytest.fixture
def sample_cashflows_with_dates() -> List[tuple]:
    """Provide sample cashflows with dates for XNPV/XIRR testing."""
    base_date = datetime.now(timezone.utc)
    return [
        (base_date, -1000.0),
        (base_date + timedelta(days=365), 200.0),
        (base_date + timedelta(days=730), 300.0),
        (base_date + timedelta(days=1095), 400.0),
        (base_date + timedelta(days=1460), 500.0),
    ]


# =============================================================================
# MOCK PROVIDER FIXTURES
# =============================================================================


@pytest.fixture
def mock_banking_provider():
    """Create a mock banking provider for testing."""
    provider = Mock()
    provider.get_accounts = AsyncMock(return_value=[])
    provider.get_transactions = AsyncMock(return_value=[])
    provider.get_balance = AsyncMock(return_value=None)
    provider.refresh = AsyncMock()
    return provider


@pytest.fixture
def mock_market_provider():
    """Create a mock market data provider for testing."""
    provider = Mock()
    provider.quote = Mock(return_value=None)
    provider.quotes = Mock(return_value=[])
    provider.historical = Mock(return_value=[])
    return provider


@pytest.fixture
def mock_brokerage_provider():
    """Create a mock brokerage provider for testing."""
    provider = Mock()
    provider.get_accounts = AsyncMock(return_value=[])
    provider.get_holdings = AsyncMock(return_value=[])
    provider.get_orders = AsyncMock(return_value=[])
    provider.submit_order = AsyncMock()
    return provider


# =============================================================================
# DATE HELPERS
# =============================================================================


@pytest.fixture
def sample_deadline() -> str:
    """Sample deadline 2 years from now."""
    return (datetime.now(timezone.utc) + timedelta(days=730)).isoformat()


@pytest.fixture
def today() -> datetime:
    """Return today's date at midnight UTC."""
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
