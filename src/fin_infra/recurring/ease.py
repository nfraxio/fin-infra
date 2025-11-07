"""
Easy builder for recurring transaction detection.

Provides one-call setup with sensible defaults.
"""

from __future__ import annotations

from .detector import RecurringDetector


def easy_recurring_detection(
    min_occurrences: int = 3,
    amount_tolerance: float = 0.02,
    date_tolerance_days: int = 7,
    **config,
) -> RecurringDetector:
    """
    One-call setup for recurring transaction detection.

    Provides sensible defaults for pattern detection with configurable sensitivity.

    Args:
        min_occurrences: Minimum number of transactions to detect pattern (default: 3)
                        Set to 2 for annual subscriptions with limited history
        amount_tolerance: Amount variance tolerance for fixed patterns (default: 0.02 = 2%)
                         Higher values (0.05 = 5%) are more lenient
                         Lower values (0.01 = 1%) are more strict
        date_tolerance_days: Date clustering tolerance in days (default: 7)
                           Used for grouping transactions with slight date variation
        **config: Additional configuration options (reserved for future use)

    Returns:
        Configured RecurringDetector ready for pattern detection

    Raises:
        ValueError: If parameters are out of valid range

    Examples:
        >>> # Default configuration (balanced)
        >>> detector = easy_recurring_detection()
        >>> patterns = detector.detect_patterns(transactions)

        >>> # Strict detection (fewer false positives)
        >>> detector = easy_recurring_detection(
        ...     min_occurrences=4,
        ...     amount_tolerance=0.01,
        ...     date_tolerance_days=3
        ... )

        >>> # Lenient detection (more patterns detected)
        >>> detector = easy_recurring_detection(
        ...     min_occurrences=2,
        ...     amount_tolerance=0.05,
        ...     date_tolerance_days=10
        ... )

        >>> # Annual subscriptions only (2 occurrences sufficient)
        >>> detector = easy_recurring_detection(min_occurrences=2)
    """
    # Validate parameters
    if min_occurrences < 2:
        raise ValueError(
            f"min_occurrences must be >= 2 (got {min_occurrences}). "
            "Minimum 2 transactions required to detect pattern."
        )

    if not 0.0 <= amount_tolerance <= 1.0:
        raise ValueError(
            f"amount_tolerance must be between 0.0 and 1.0 (got {amount_tolerance}). "
            "Typical values: 0.01 (strict) to 0.05 (lenient)."
        )

    if date_tolerance_days < 0:
        raise ValueError(
            f"date_tolerance_days must be >= 0 (got {date_tolerance_days}). "
            "Typical values: 3 (strict) to 14 (lenient)."
        )

    # Validate config keys (reserved for future use)
    valid_config_keys = set()  # Will expand in V2
    invalid_keys = set(config.keys()) - valid_config_keys
    if invalid_keys:
        raise ValueError(
            f"Invalid configuration keys: {invalid_keys}. "
            f"Valid keys: {valid_config_keys or 'none (reserved for future use)'}"
        )

    # Create detector with validated parameters
    detector = RecurringDetector(
        min_occurrences=min_occurrences,
        amount_tolerance=amount_tolerance,
        date_tolerance_days=date_tolerance_days,
    )

    return detector
