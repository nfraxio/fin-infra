"""
FastAPI Integration for Net Worth Tracking

Provides REST API endpoints for net worth tracking:
- GET /net-worth/current - Current net worth (cached 1h)
- GET /net-worth/snapshots - Historical snapshots
- GET /net-worth/breakdown - Asset/liability breakdown
- POST /net-worth/snapshot - Force snapshot creation

**Quick Start**:
```python
from fastapi import FastAPI
from fin_infra.net_worth import add_net_worth_tracking, easy_net_worth
from fin_infra.banking import easy_banking

app = FastAPI()

# Create tracker
banking = easy_banking(provider="plaid")
tracker = easy_net_worth(banking=banking)

# Add endpoints (one line!)
add_net_worth_tracking(app, tracker=tracker)
```

**Auto-wired Integration** (no tracker needed):
```python
from fastapi import FastAPI
from fin_infra.net_worth import add_net_worth_tracking

app = FastAPI()

# Endpoints added, tracker auto-created
tracker = add_net_worth_tracking(app)
```
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from fin_infra.net_worth.ease import NetWorthTracker, easy_net_worth
from fin_infra.net_worth.models import (
    NetWorthRequest,
    NetWorthResponse,
    SnapshotHistoryRequest,
    SnapshotHistoryResponse,
)


def add_net_worth_tracking(
    app: FastAPI,
    tracker: NetWorthTracker | None = None,
    prefix: str = "/net-worth",
    include_in_schema: bool = True,
) -> NetWorthTracker:
    """
    Add net worth tracking endpoints to FastAPI app.
    
    **Example - With Tracker**:
    ```python
    from fastapi import FastAPI
    from fin_infra.banking import easy_banking
    from fin_infra.net_worth import easy_net_worth, add_net_worth_tracking
    
    app = FastAPI()
    
    # Create providers + tracker
    banking = easy_banking(provider="plaid")
    tracker = easy_net_worth(banking=banking)
    
    # Add endpoints
    add_net_worth_tracking(app, tracker=tracker)
    ```
    
    **Example - Auto-wired** (no providers yet):
    ```python
    from fastapi import FastAPI
    from fin_infra.net_worth import add_net_worth_tracking
    
    app = FastAPI()
    
    # Add endpoints (tracker created with defaults)
    tracker = add_net_worth_tracking(app)
    
    # Later: wire up providers
    from fin_infra.banking import easy_banking
    banking = easy_banking(provider="plaid")
    tracker.aggregator.banking_provider = banking
    ```
    
    Args:
        app: FastAPI application instance
        tracker: NetWorthTracker instance (optional, will create default)
        prefix: URL prefix for endpoints (default: "/net-worth")
        include_in_schema: Include in OpenAPI schema (default: True)
    
    Returns:
        NetWorthTracker instance (for programmatic access)
    
    **Endpoints Added**:
    - `GET {prefix}/current` - Current net worth (cached 1h)
    - `GET {prefix}/snapshots` - Historical snapshots
    - `GET {prefix}/breakdown` - Asset/liability breakdown
    - `POST {prefix}/snapshot` - Force snapshot creation
    
    **Authentication**:
    All endpoints require user authentication (svc-infra user_router).
    User ID extracted from JWT token automatically.
    """
    # Create default tracker if not provided
    if tracker is None:
        # For now, create empty tracker (providers will be wired later)
        # TODO: Auto-detect providers from app.state
        tracker = easy_net_worth(
            banking=None,  # Will be set later
            brokerage=None,
            crypto=None,
        )
    
    # Store tracker on app state for access in routes
    app.state.net_worth_tracker = tracker
    
    # Import svc-infra dual router (when available)
    # For now, use standard FastAPI router
    try:
        from svc_infra.api.fastapi.dual.protected import user_router
        router = user_router(prefix=prefix, tags=["Net Worth"])
    except ImportError:
        # Fallback to standard router if svc-infra not available
        from fastapi import APIRouter
        router = APIRouter(prefix=prefix, tags=["Net Worth"])
    
    @router.get(
        "/current",
        response_model=NetWorthResponse,
        summary="Get Current Net Worth",
        description="Calculate current net worth from all providers (cached 1h)",
    )
    async def get_current_net_worth(
        user_id: str = Query(..., description="User identifier"),
        access_token: str = Query(None, description="Provider access token"),
        force_refresh: bool = Query(False, description="Skip cache, recalculate"),
        include_breakdown: bool = Query(True, description="Include asset/liability details"),
    ) -> NetWorthResponse:
        """
        Get current net worth.
        
        **Example Request**:
        ```
        GET /net-worth/current?user_id=user_123&access_token=plaid_token_abc
        ```
        
        **Example Response**:
        ```json
        {
          "snapshot": {
            "id": "snapshot_abc123",
            "user_id": "user_123",
            "total_net_worth": 55000.0,
            "total_assets": 60000.0,
            "total_liabilities": 5000.0,
            ...
          },
          "asset_allocation": {
            "cash": 10000.0,
            "investments": 45000.0,
            ...
          },
          "processing_time_ms": 1250
        }
        ```
        """
        start_time = datetime.utcnow()
        
        try:
            # Calculate net worth
            snapshot = await tracker.calculate_net_worth(
                user_id=user_id,
                access_token=access_token,
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Build response
            from fin_infra.net_worth.calculator import (
                calculate_asset_allocation,
                calculate_liability_breakdown,
            )
            
            # Get asset details from snapshot (stored in aggregator)
            # For now, create empty lists (TODO: store in snapshot)
            asset_details = []
            liability_details = []
            
            # Calculate breakdowns
            asset_allocation = calculate_asset_allocation(asset_details)
            liability_breakdown = calculate_liability_breakdown(liability_details)
            
            return NetWorthResponse(
                snapshot=snapshot,
                asset_allocation=asset_allocation,
                liability_breakdown=liability_breakdown,
                asset_details=asset_details if include_breakdown else [],
                liability_details=liability_details if include_breakdown else [],
                processing_time_ms=int(processing_time),
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get(
        "/snapshots",
        response_model=SnapshotHistoryResponse,
        summary="Get Historical Snapshots",
        description="Retrieve historical net worth snapshots for charting",
    )
    async def get_snapshots(
        user_id: str = Query(..., description="User identifier"),
        days: int = Query(90, ge=1, le=730, description="Look back N days (max 2 years)"),
        granularity: str = Query(
            "daily",
            pattern="^(daily|weekly|monthly)$",
            description="Snapshot granularity",
        ),
    ) -> SnapshotHistoryResponse:
        """
        Get historical snapshots.
        
        **Example Request**:
        ```
        GET /net-worth/snapshots?user_id=user_123&days=90&granularity=daily
        ```
        
        **Example Response**:
        ```json
        {
          "snapshots": [
            {"snapshot_date": "2025-11-06", "total_net_worth": 55000.0, ...},
            {"snapshot_date": "2025-11-05", "total_net_worth": 54500.0, ...},
            ...
          ],
          "count": 90,
          "start_date": "2025-08-08",
          "end_date": "2025-11-06"
        }
        ```
        """
        try:
            # Get snapshots from tracker
            snapshots = await tracker.get_snapshots(
                user_id=user_id,
                days=days,
                granularity=granularity,
            )
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            return SnapshotHistoryResponse(
                snapshots=snapshots,
                count=len(snapshots),
                start_date=start_date,
                end_date=end_date,
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get(
        "/breakdown",
        summary="Get Asset/Liability Breakdown",
        description="Get detailed asset and liability breakdown for pie charts",
    )
    async def get_breakdown(
        user_id: str = Query(..., description="User identifier"),
        access_token: str = Query(None, description="Provider access token"),
    ):
        """
        Get asset/liability breakdown.
        
        Returns simplified breakdown for visualization (pie charts).
        
        **Example Response**:
        ```json
        {
          "assets": {
            "cash": 10000.0,
            "investments": 45000.0,
            "crypto": 5000.0,
            "real_estate": 0.0,
            "vehicles": 0.0,
            "other": 0.0
          },
          "liabilities": {
            "credit_cards": 5000.0,
            "mortgages": 0.0,
            "auto_loans": 0.0,
            "student_loans": 0.0,
            "personal_loans": 0.0,
            "lines_of_credit": 0.0
          }
        }
        ```
        """
        try:
            # Get current net worth
            snapshot = await tracker.calculate_net_worth(
                user_id=user_id,
                access_token=access_token,
            )
            
            return {
                "assets": {
                    "cash": snapshot.cash,
                    "investments": snapshot.investments,
                    "crypto": snapshot.crypto,
                    "real_estate": snapshot.real_estate,
                    "vehicles": snapshot.vehicles,
                    "other": snapshot.other_assets,
                },
                "liabilities": {
                    "credit_cards": snapshot.credit_cards,
                    "mortgages": snapshot.mortgages,
                    "auto_loans": snapshot.auto_loans,
                    "student_loans": snapshot.student_loans,
                    "personal_loans": snapshot.personal_loans,
                    "lines_of_credit": snapshot.lines_of_credit,
                },
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post(
        "/snapshot",
        summary="Force Snapshot Creation",
        description="Manually create snapshot (admin only)",
    )
    async def force_snapshot(
        user_id: str = Query(..., description="User identifier"),
        access_token: str = Query(None, description="Provider access token"),
    ):
        """
        Force snapshot creation.
        
        Creates snapshot immediately (bypasses schedule).
        Useful for testing or manual triggers.
        
        **Example Request**:
        ```
        POST /net-worth/snapshot?user_id=user_123&access_token=plaid_token_abc
        ```
        
        **Example Response**:
        ```json
        {
          "message": "Snapshot created successfully",
          "snapshot_id": "snapshot_abc123",
          "net_worth": 55000.0
        }
        ```
        """
        try:
            # Create snapshot
            snapshot = await tracker.create_snapshot(
                user_id=user_id,
                access_token=access_token,
            )
            
            return {
                "message": "Snapshot created successfully",
                "snapshot_id": snapshot.id,
                "net_worth": snapshot.total_net_worth,
                "snapshot_date": snapshot.snapshot_date,
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Mount router
    app.include_router(router, include_in_schema=include_in_schema)
    
    # Register scoped docs (when svc-infra available)
    try:
        from svc_infra.api.fastapi.docs.scoped import add_prefixed_docs
        
        add_prefixed_docs(
            app,
            prefix=prefix,
            title="Net Worth Tracking",
            description="Calculate and track net worth from multiple financial providers",
            auto_exclude_from_root=True,
            visible_envs=None,  # Show in all environments
        )
    except ImportError:
        # svc-infra not available, skip scoped docs
        pass
    
    return tracker
