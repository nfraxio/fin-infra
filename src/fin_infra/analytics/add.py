"""FastAPI integration for analytics module.

Provides add_analytics() helper to mount analytics endpoints.
MUST use svc-infra dual routers (user_router) - NEVER generic APIRouter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def add_analytics(app: FastAPI, prefix: str = "/analytics", provider=None):
    """Add analytics endpoints to FastAPI application.
    
    Mounts analytics endpoints and registers scoped documentation on the landing page.
    Uses svc-infra user_router for authenticated endpoints (MANDATORY).
    
    Args:
        app: FastAPI application instance
        prefix: URL prefix for analytics endpoints (default: "/analytics")
        provider: Optional pre-configured AnalyticsEngine instance
    
    Returns:
        AnalyticsEngine instance (either provided or newly created)
    
    Raises:
        ValueError: If invalid configuration provided
    
    Example:
        >>> from svc_infra.api.fastapi.ease import easy_service_app
        >>> from fin_infra.analytics import add_analytics
        >>> 
        >>> app = easy_service_app(name="FinanceAPI")
        >>> analytics = add_analytics(app)
        >>> 
        >>> # Access at /analytics/cash-flow, /analytics/savings-rate, etc.
        >>> # Visit /docs to see "Analytics" card on landing page
    
    Endpoints mounted:
        - GET /analytics/cash-flow?user_id=...&start_date=...&end_date=...
        - GET /analytics/savings-rate?user_id=...&period=monthly
        - GET /analytics/spending-insights?user_id=...&period=30d
        - GET /analytics/portfolio?user_id=...&accounts=...
        - GET /analytics/performance?user_id=...&benchmark=SPY&period=1y
        - POST /analytics/forecast-net-worth (body: user_id, years, assumptions)
    
    API Compliance:
        - Uses svc-infra user_router (authenticated endpoints)
        - Calls add_prefixed_docs() for landing page card
        - Stores provider on app.state.analytics_provider
        - Returns provider for programmatic access
    """
    # TODO: Implement in Task 9
    # Will:
    # 1. Create or use provided analytics engine (via easy_analytics)
    # 2. Import user_router from svc-infra (MANDATORY)
    # 3. Create router with prefix and tags
    # 4. Define all endpoint handlers
    # 5. Apply svc-infra cache decorators (1h TTL)
    # 6. Mount router with include_in_schema=True
    # 7. Call add_prefixed_docs() for landing page card (CRITICAL)
    # 8. Store on app.state.analytics_provider
    # 9. Return analytics instance
    raise NotImplementedError("add_analytics() will be implemented in Task 9")
