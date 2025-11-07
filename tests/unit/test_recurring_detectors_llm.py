"""
Unit tests for recurring/detectors_llm.py (Layer 4 - LLM variable amount detection).

Tests variable recurring pattern detection with mocked CoreLLM responses.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fin_infra.recurring.detectors_llm import (
    VariableDetectorLLM,
    VariableRecurringPattern,
    VARIABLE_DETECTION_SYSTEM_PROMPT,
    VARIABLE_DETECTION_USER_PROMPT,
)


class TestVariableRecurringPattern:
    """Test VariableRecurringPattern Pydantic model."""

    def test_valid_model_recurring(self):
        """Test valid VariableRecurringPattern for recurring pattern."""
        result = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$45-$55",
            reasoning="Seasonal winter heating variation",
            confidence=0.88,
        )

        assert result.is_recurring is True
        assert result.cadence == "monthly"
        assert result.expected_range == "$45-$55"
        assert result.reasoning == "Seasonal winter heating variation"
        assert result.confidence == 0.88

    def test_valid_model_not_recurring(self):
        """Test valid VariableRecurringPattern for non-recurring pattern."""
        result = VariableRecurringPattern(
            is_recurring=False,
            cadence=None,
            expected_range=None,
            reasoning="Too much variance, no seasonal pattern",
            confidence=0.75,
        )

        assert result.is_recurring is False
        assert result.cadence is None
        assert result.expected_range is None
        assert "variance" in result.reasoning
        assert result.confidence == 0.75

    def test_confidence_validation(self):
        """Test confidence must be between 0.0 and 1.0."""
        # Valid confidence
        VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$50",
            reasoning="test",
            confidence=0.8,
        )

        # Invalid confidence (too high)
        with pytest.raises(ValueError):
            VariableRecurringPattern(
                is_recurring=True,
                cadence="monthly",
                expected_range="$50",
                reasoning="test",
                confidence=1.5,
            )


class TestVariableDetectorLLM:
    """Test VariableDetectorLLM with mocked CoreLLM."""

    @pytest.fixture
    def mock_llm(self):
        """Mock CoreLLM for testing."""
        with patch("fin_infra.recurring.detectors_llm.CoreLLM") as mock:
            yield mock

    @pytest.fixture
    def detector(self, mock_llm):
        """Create VariableDetectorLLM with mocked dependencies."""
        return VariableDetectorLLM(
            provider="google",
            model_name="gemini-2.0-flash-exp",
            max_cost_per_day=0.10,
            max_cost_per_month=2.00,
        )

    @pytest.mark.asyncio
    async def test_detect_seasonal_utility_bills(self, detector, mock_llm):
        """Test detection of seasonal utility bills ($45-$55 monthly)."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$45-$55",
            reasoning="Seasonal winter heating variation causes 20% fluctuation",
            confidence=0.88,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Transaction pattern
        transactions = [
            {"merchant": "City Electric", "amount": 45.50, "date": "2024-01-15"},
            {"merchant": "City Electric", "amount": 52.30, "date": "2024-02-15"},
            {"merchant": "City Electric", "amount": 48.75, "date": "2024-03-15"},
            {"merchant": "City Electric", "amount": 54.20, "date": "2024-04-15"},
        ]

        # Detect pattern
        result = await detector.detect("City Electric", transactions)

        # Verify result
        assert result.is_recurring is True
        assert result.cadence == "monthly"
        assert "$45-$55" in result.expected_range
        assert "seasonal" in result.reasoning.lower() or "winter" in result.reasoning.lower()
        assert result.confidence >= 0.85

        # Verify LLM was called with correct parameters
        detector.llm.achat.assert_called_once()
        call_args = detector.llm.achat.call_args
        assert call_args.kwargs["provider"] == "google"
        assert call_args.kwargs["model"] == "gemini-2.0-flash-exp"
        assert call_args.kwargs["output_schema"] == VariableRecurringPattern
        assert call_args.kwargs["temperature"] == 0.0

        # Verify prompt contains system and user messages
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == VARIABLE_DETECTION_SYSTEM_PROMPT
        assert messages[1]["role"] == "user"
        assert "City Electric" in messages[1]["content"]
        assert "$45" in messages[1]["content"] or "$52" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_detect_phone_overage_spikes(self, detector, mock_llm):
        """Test detection of phone bills with occasional overage spikes."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$50-$55 (occasional $75-$80 spikes)",
            reasoning="Regular monthly bill with occasional overage charge spikes",
            confidence=0.86,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Transaction pattern with spike
        transactions = [
            {"merchant": "T-Mobile", "amount": 50.00, "date": "2024-01-15"},
            {"merchant": "T-Mobile", "amount": 78.50, "date": "2024-02-15"},  # Spike
            {"merchant": "T-Mobile", "amount": 50.00, "date": "2024-03-15"},
            {"merchant": "T-Mobile", "amount": 50.00, "date": "2024-04-15"},
        ]

        # Detect pattern
        result = await detector.detect("T-Mobile", transactions)

        # Verify result
        assert result.is_recurring is True
        assert "spike" in result.reasoning.lower() or "overage" in result.reasoning.lower()
        assert result.confidence >= 0.80

    @pytest.mark.asyncio
    async def test_detect_random_variance_not_recurring(self, detector, mock_llm):
        """Test detection rejects random variance as not recurring."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=False,
            cadence=None,
            expected_range=None,
            reasoning="Too much variance with no seasonal or usage-based pattern",
            confidence=0.82,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Random transaction pattern
        transactions = [
            {"merchant": "Random Store", "amount": 25.00, "date": "2024-01-15"},
            {"merchant": "Random Store", "amount": 150.00, "date": "2024-02-15"},
            {"merchant": "Random Store", "amount": 40.00, "date": "2024-03-15"},
            {"merchant": "Random Store", "amount": 200.00, "date": "2024-04-15"},
        ]

        # Detect pattern
        result = await detector.detect("Random Store", transactions)

        # Verify result
        assert result.is_recurring is False
        assert result.cadence is None
        assert result.expected_range is None
        assert "variance" in result.reasoning.lower() or "random" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_detect_winter_heating_seasonal_pattern(self, detector, mock_llm):
        """Test detection of winter heating bills that double in cold months."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$45-$120 (seasonal)",
            reasoning="Winter heating season doubles bill from summer baseline",
            confidence=0.90,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Seasonal pattern (winter spike)
        transactions = [
            {"merchant": "Gas Company", "amount": 45.00, "date": "2024-06-15"},  # Summer
            {"merchant": "Gas Company", "amount": 120.00, "date": "2024-12-15"},  # Winter
            {"merchant": "Gas Company", "amount": 115.00, "date": "2024-01-15"},  # Winter
            {"merchant": "Gas Company", "amount": 50.00, "date": "2024-03-15"},  # Spring
        ]

        # Detect pattern
        result = await detector.detect("Gas Company", transactions)

        # Verify result
        assert result.is_recurring is True
        assert "seasonal" in result.reasoning.lower() or "winter" in result.reasoning.lower()
        assert result.confidence >= 0.85

    @pytest.mark.asyncio
    async def test_detect_gym_membership_with_annual_fee_waiver(self, detector, mock_llm):
        """Test detection of gym membership with one month waived annual fee."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$40 (occasional $0 for annual fee waiver)",
            reasoning="Regular membership with annual fee waived one month per year",
            confidence=0.87,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Pattern with one $0 month
        transactions = [
            {"merchant": "Gym Membership", "amount": 40.00, "date": "2024-01-15"},
            {"merchant": "Gym Membership", "amount": 40.00, "date": "2024-02-15"},
            {"merchant": "Gym Membership", "amount": 0.00, "date": "2024-03-15"},  # Waived
            {"merchant": "Gym Membership", "amount": 40.00, "date": "2024-04-15"},
        ]

        # Detect pattern
        result = await detector.detect("Gym Membership", transactions)

        # Verify result
        assert result.is_recurring is True
        assert "annual" in result.reasoning.lower() or "waiv" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_budget_tracking(self, detector, mock_llm):
        """Test budget tracking increments after LLM calls."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$50",
            reasoning="test",
            confidence=0.85,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Initial budget
        assert detector._daily_cost == 0.0
        assert detector._monthly_cost == 0.0

        # Call detect
        transactions = [{"merchant": "Test", "amount": 50.00, "date": "2024-01-15"}]
        await detector.detect("Test", transactions)

        # Verify budget increased
        assert detector._daily_cost == 0.0001  # Google Gemini cost per detection
        assert detector._monthly_cost == 0.0001

        # Call again
        await detector.detect("Test2", transactions)

        # Verify budget doubled
        assert detector._daily_cost == 0.0002
        assert detector._monthly_cost == 0.0002

    @pytest.mark.asyncio
    async def test_budget_exceeded_returns_not_recurring(self, detector, mock_llm):
        """Test that exceeding budget returns is_recurring=false without LLM call."""
        # Set budget exceeded flag
        detector._budget_exceeded = True

        # Try to detect
        transactions = [{"merchant": "Test", "amount": 50.00, "date": "2024-01-15"}]
        result = await detector.detect("Test", transactions)

        # Verify LLM was NOT called
        detector.llm.achat.assert_not_called()

        # Verify fallback result
        assert result.is_recurring is False
        assert result.confidence == 0.5
        assert "budget exceeded" in result.reasoning.lower() or "unavailable" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_budget_exceeded_when_daily_limit_hit(self, detector, mock_llm):
        """Test budget exceeded flag set when daily limit is hit."""
        # Set daily cost near limit
        detector._daily_cost = 0.09  # Just below $0.10 limit
        detector.max_cost_per_day = 0.10

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$50",
            reasoning="test",
            confidence=0.85,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Make request that pushes over limit
        transactions = [{"merchant": "Test", "amount": 50.00, "date": "2024-01-15"}]
        await detector.detect("Test", transactions)

        # Verify budget exceeded flag is set
        assert detector._budget_exceeded is True
        assert detector._daily_cost > detector.max_cost_per_day

    @pytest.mark.asyncio
    async def test_llm_error_returns_low_confidence(self, detector, mock_llm):
        """Test that LLM errors return is_recurring=false with low confidence."""
        # Mock LLM error
        detector.llm.achat = AsyncMock(side_effect=Exception("LLM timeout"))

        # Try to detect
        transactions = [{"merchant": "Test", "amount": 50.00, "date": "2024-01-15"}]
        result = await detector.detect("Test", transactions)

        # Verify fallback result
        assert result.is_recurring is False
        assert result.confidence == 0.3  # Lower confidence for errors
        assert "error" in result.reasoning.lower() or "unavailable" in result.reasoning.lower()

    def test_reset_daily_budget(self, detector):
        """Test daily budget reset."""
        # Set some costs
        detector._daily_cost = 0.05
        detector._budget_exceeded = True

        # Reset daily budget
        detector.reset_daily_budget()

        # Verify reset
        assert detector._daily_cost == 0.0
        assert detector._budget_exceeded is False

        # Monthly cost should NOT be reset
        detector._monthly_cost = 1.0
        detector.reset_daily_budget()
        assert detector._monthly_cost == 1.0

    def test_reset_monthly_budget(self, detector):
        """Test monthly budget reset."""
        # Set some costs
        detector._monthly_cost = 1.5
        detector._budget_exceeded = True

        # Reset monthly budget
        detector.reset_monthly_budget()

        # Verify reset
        assert detector._monthly_cost == 0.0
        assert detector._budget_exceeded is False

    def test_get_budget_status(self, detector):
        """Test budget status reporting."""
        # Set some costs
        detector._daily_cost = 0.05
        detector._monthly_cost = 1.0
        detector.max_cost_per_day = 0.10
        detector.max_cost_per_month = 2.00

        # Get status
        status = detector.get_budget_status()

        # Verify status
        assert status["daily_cost"] == 0.05
        assert status["daily_limit"] == 0.10
        assert status["daily_remaining"] == 0.05
        assert status["monthly_cost"] == 1.0
        assert status["monthly_limit"] == 2.00
        assert status["monthly_remaining"] == 1.0
        assert status["exceeded"] is False

    @pytest.mark.asyncio
    async def test_empty_transactions_raises_error(self, detector):
        """Test that empty transactions list raises ValueError."""
        with pytest.raises(ValueError, match="transactions cannot be empty"):
            await detector.detect("Test", [])

    @pytest.mark.asyncio
    async def test_user_prompt_formatting(self, detector, mock_llm):
        """Test that user prompt is formatted correctly with transaction data."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.structured = VariableRecurringPattern(
            is_recurring=True,
            cadence="monthly",
            expected_range="$50",
            reasoning="test",
            confidence=0.85,
        )
        detector.llm.achat = AsyncMock(return_value=mock_response)

        # Transactions
        transactions = [
            {"merchant": "Test Merchant", "amount": 50.00, "date": "2024-01-15"},
            {"merchant": "Test Merchant", "amount": 55.00, "date": "2024-02-15"},
        ]

        # Detect
        await detector.detect("Test Merchant", transactions)

        # Verify user prompt
        call_args = detector.llm.achat.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        
        # Should contain merchant name
        assert "Test Merchant" in user_message
        
        # Should contain transaction amounts
        assert "$50" in user_message or "50.00" in user_message
        assert "$55" in user_message or "55.00" in user_message
        
        # Should contain dates
        assert "2024-01-15" in user_message or "Jan" in user_message
        assert "2024-02-15" in user_message or "Feb" in user_message
