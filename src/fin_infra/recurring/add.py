"""
FastAPI integration for recurring transaction detection.

Provides REST API endpoints for pattern detection, subscription tracking, and predictions.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .ease import easy_recurring_detection
from .models import (
    BillPrediction,
    DetectionRequest,
    DetectionResponse,
    RecurringPattern,
    SubscriptionStats,
)

if TYPE_CHECKING:
    from fastapi import FastAPI


def add_recurring_detection(
    app: FastAPI,
    prefix: str = "/recurring",
    min_occurrences: int = 3,
    amount_tolerance: float = 0.02,
    date_tolerance_days: int = 7,
    include_in_schema: bool = True,
) -> "RecurringDetector":
    """
    Add recurring transaction detection endpoints to FastAPI app.

    Mounts 3 endpoints:
    - POST /recurring/detect - Detect patterns in transaction list
    - GET /recurring/subscriptions - List detected subscriptions (cached)
    - GET /recurring/predictions - Predict next bills

    Args:
        app: FastAPI application instance
        prefix: URL prefix for endpoints (default: "/recurring")
        min_occurrences: Minimum transactions to detect pattern (default: 3)
        amount_tolerance: Amount variance tolerance (default: 0.02 = 2%)
        date_tolerance_days: Date clustering tolerance (default: 7 days)
        include_in_schema: Include endpoints in OpenAPI schema (default: True)

    Returns:
        Configured RecurringDetector instance (stored in app.state)

    Examples:
        >>> from fastapi import FastAPI
        >>> from fin_infra.recurring import add_recurring_detection
        >>>
        >>> app = FastAPI(title="My Finance API")
        >>> detector = add_recurring_detection(app)
        >>>
        >>> # Available endpoints:
        >>> # POST /recurring/detect
        >>> # GET /recurring/subscriptions
        >>> # GET /recurring/predictions
    """
    # Create detector
    detector = easy_recurring_detection(
        min_occurrences=min_occurrences,
        amount_tolerance=amount_tolerance,
        date_tolerance_days=date_tolerance_days,
    )

    # Store in app state for access in routes
    app.state.recurring_detector = detector

    # Try to import svc-infra dual routers (fallback to APIRouter if not available)
    try:
        from svc_infra.api.fastapi.dual.protected import user_router

        router = user_router(prefix=prefix, tags=["Recurring Detection"])
    except ImportError:
        from fastapi import APIRouter

        router = APIRouter(prefix=prefix, tags=["Recurring Detection"])

    # Route 1: Detect patterns
    @router.post("/detect", response_model=DetectionResponse)
    async def detect_recurring_patterns(request: DetectionRequest):
        """
        Detect recurring patterns in transaction history.

        Analyzes transaction history for recurring subscriptions and bills using
        3-layer hybrid detection (fixed → variable → irregular).

        **Example Request:**
        ```json
        {
          "days": 365,
          "min_confidence": 0.7,
          "include_predictions": true
        }
        ```

        **Returns:**
        - List of detected recurring patterns with confidence scores
        - Optional predictions for next charges
        - Processing time in milliseconds
        """
        start_time = time.time()

        # TODO: Get transactions from database (user-specific)
        # For now, return empty result with structure
        # In production: transactions = get_user_transactions(user.id, days=request.days)

        transactions = []  # Placeholder

        # Detect patterns
        patterns = detector.detect_patterns(transactions)

        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= request.min_confidence]

        # Generate predictions if requested
        predictions = None
        if request.include_predictions:
            predictions = _generate_predictions(patterns)

        processing_time = (time.time() - start_time) * 1000

        return DetectionResponse(
            patterns=patterns,
            count=len(patterns),
            predictions=predictions,
            processing_time_ms=processing_time,
        )

    # Route 2: Get subscriptions (cached)
    @router.get("/subscriptions", response_model=list[RecurringPattern])
    async def get_subscriptions(
        min_confidence: float = 0.7,
        days: int = 365,
    ):
        """
        Get detected subscriptions (cached results).

        Returns cached recurring patterns detected from user's transaction history.

        **Query Parameters:**
        - `min_confidence`: Minimum confidence threshold (0.0-1.0, default: 0.7)
        - `days`: Days of history to analyze (default: 365)

        **Returns:**
        List of recurring patterns sorted by confidence (descending)
        """
        # TODO: Check cache first (svc-infra.cache)
        # cache_key = f"subscriptions:{user_id}:{days}:{min_confidence}"
        # cached = get_from_cache(cache_key)
        # if cached:
        #     return cached

        # Detect patterns (same as /detect endpoint)
        transactions = []  # Placeholder
        patterns = detector.detect_patterns(transactions)
        patterns = [p for p in patterns if p.confidence >= min_confidence]

        # TODO: Cache results (24h TTL)
        # set_cache(cache_key, patterns, ttl=86400)

        return patterns

    # Route 3: Get predictions
    @router.get("/predictions", response_model=list[BillPrediction])
    async def get_bill_predictions(
        days_ahead: int = 30,
        min_confidence: float = 0.7,
    ):
        """
        Predict upcoming bills and subscriptions.

        Predicts future charges based on detected recurring patterns.

        **Query Parameters:**
        - `days_ahead`: Days to predict ahead (default: 30)
        - `min_confidence`: Minimum confidence threshold (default: 0.7)

        **Returns:**
        List of predicted charges with expected dates and amounts
        """
        # Get detected patterns
        transactions = []  # Placeholder
        patterns = detector.detect_patterns(transactions)
        patterns = [p for p in patterns if p.confidence >= min_confidence]

        # Generate predictions for next N days
        predictions = _generate_predictions(patterns, days_ahead=days_ahead)

        return predictions

    # Route 4: Get statistics
    @router.get("/stats", response_model=SubscriptionStats)
    async def get_subscription_stats():
        """
        Get subscription statistics.

        Returns aggregate statistics about detected recurring transactions:
        - Total subscriptions count
        - Estimated monthly total
        - Breakdown by pattern type and cadence
        - Top merchants by amount
        """
        # Get all detected patterns
        transactions = []  # Placeholder
        patterns = detector.detect_patterns(transactions)

        # Calculate stats
        stats = _calculate_stats(patterns)

        return stats

    # Mount router
    app.include_router(router, include_in_schema=include_in_schema)

    # Register scoped docs (if svc-infra available)
    try:
        from svc_infra.api.fastapi.docs.scoped import add_prefixed_docs

        add_prefixed_docs(
            app,
            prefix=prefix,
            title="Recurring Detection",
            auto_exclude_from_root=True,
            visible_envs=None,
        )
    except ImportError:
        pass  # svc-infra not available, skip scoped docs

    return detector


def _generate_predictions(
    patterns: list[RecurringPattern],
    days_ahead: int = 30,
) -> list[BillPrediction]:
    """
    Generate bill predictions from patterns.

    Args:
        patterns: Detected recurring patterns
        days_ahead: Days to predict ahead

    Returns:
        List of BillPrediction objects
    """
    predictions = []
    cutoff_date = datetime.now() + timedelta(days=days_ahead)

    for pattern in patterns:
        # Only predict if next_expected_date is within cutoff
        if pattern.next_expected_date <= cutoff_date:
            prediction = BillPrediction(
                merchant_name=pattern.merchant_name,
                expected_date=pattern.next_expected_date,
                expected_amount=pattern.amount,
                expected_range=pattern.amount_range,
                confidence=pattern.confidence,
                cadence=pattern.cadence,
            )
            predictions.append(prediction)

    # Sort by expected date
    return sorted(predictions, key=lambda x: x.expected_date)


def _calculate_stats(patterns: list[RecurringPattern]) -> SubscriptionStats:
    """
    Calculate subscription statistics.

    Args:
        patterns: Detected recurring patterns

    Returns:
        SubscriptionStats object
    """
    from collections import Counter

    if not patterns:
        return SubscriptionStats(
            total_subscriptions=0,
            monthly_total=0.0,
            by_pattern_type={},
            by_cadence={},
            top_merchants=[],
            confidence_distribution={},
        )

    # Count by pattern type
    by_pattern_type = dict(Counter(p.pattern_type.value for p in patterns))

    # Count by cadence
    by_cadence = dict(Counter(p.cadence.value for p in patterns))

    # Calculate monthly total (estimate)
    monthly_total = 0.0
    for pattern in patterns:
        if pattern.amount:
            # Convert to monthly equivalent
            if pattern.cadence.value == "monthly":
                monthly_total += pattern.amount
            elif pattern.cadence.value == "biweekly":
                monthly_total += pattern.amount * 2
            elif pattern.cadence.value == "quarterly":
                monthly_total += pattern.amount / 3
            elif pattern.cadence.value == "annual":
                monthly_total += pattern.amount / 12

    # Top merchants by amount
    merchants_with_amount = [
        (p.merchant_name, p.amount) for p in patterns if p.amount is not None
    ]
    top_merchants = sorted(merchants_with_amount, key=lambda x: x[1], reverse=True)[:5]

    # Confidence distribution
    confidence_dist = {
        "high (0.85-1.0)": sum(1 for p in patterns if p.confidence >= 0.85),
        "medium (0.70-0.84)": sum(
            1 for p in patterns if 0.70 <= p.confidence < 0.85
        ),
        "low (0.60-0.69)": sum(1 for p in patterns if 0.60 <= p.confidence < 0.70),
    }

    return SubscriptionStats(
        total_subscriptions=len(patterns),
        monthly_total=monthly_total,
        by_pattern_type=by_pattern_type,
        by_cadence=by_cadence,
        top_merchants=top_merchants,
        confidence_distribution=confidence_dist,
    )
