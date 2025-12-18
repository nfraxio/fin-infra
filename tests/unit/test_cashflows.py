"""Unit tests for cashflow calculations.

Tests cover:
- Basic functionality
- Edge cases (empty arrays, single values)
- Negative rates
- Division by zero scenarios
- IRR convergence failures
- Known values from financial textbooks
- pmt, fv, pv functions
"""

from __future__ import annotations

import math

import pytest

from fin_infra.cashflows import npv, irr, pmt, fv, pv
from fin_infra.cashflows.core import npv as core_npv, irr as core_irr


class TestNPVBasic:
    """Basic NPV functionality tests."""

    def test_npv_positive_cashflows(self):
        """Test NPV with typical investment cashflows."""
        cf = [-1000, 200, 300, 400, 500]
        result = npv(0.08, cf)
        assert isinstance(result, float)
        assert result > 0  # Positive NPV = good investment

    def test_npv_negative_result(self):
        """Test NPV that results in negative value (bad investment)."""
        cf = [-10000, 100, 100, 100]  # Very poor return
        result = npv(0.08, cf)
        assert result < 0  # Negative NPV = bad investment

    def test_npv_zero_rate(self):
        """Test NPV with zero discount rate (simple sum)."""
        cf = [-1000, 500, 500, 500]
        result = npv(0.0, cf)
        # At 0% discount, NPV = sum of cashflows
        assert abs(result - 500) < 0.01

    def test_npv_known_value(self):
        """Test NPV against known textbook value.

        Reference: Principles of Corporate Finance (Brealey, Myers)
        Project with initial investment $100, returns $110 next year at 10% rate.
        NPV = -100 + 110/1.10 = -100 + 100 = 0
        """
        cf = [-100, 110]
        result = npv(0.10, cf)
        assert abs(result) < 0.01  # Should be approximately 0


class TestNPVEdgeCases:
    """Edge case tests for NPV."""

    def test_npv_empty_array(self):
        """Test NPV with empty cashflow array."""
        result = npv(0.08, [])
        assert result == 0.0 or math.isnan(result)  # Empty = no value

    def test_npv_single_value(self):
        """Test NPV with single cashflow (initial investment only)."""
        cf = [-1000]
        result = npv(0.08, cf)
        assert result == -1000.0  # Just the initial investment

    def test_npv_all_zeros(self):
        """Test NPV with all zero cashflows."""
        cf = [0, 0, 0, 0]
        result = npv(0.08, cf)
        assert result == 0.0

    def test_npv_very_large_values(self):
        """Test NPV with very large cashflows."""
        cf = [-1e12, 2e11, 3e11, 4e11, 5e11]
        result = npv(0.08, cf)
        assert isinstance(result, float)
        assert not math.isnan(result)
        assert not math.isinf(result)

    def test_npv_generator_input(self):
        """Test NPV accepts generator/iterator input."""
        cf_gen = (x for x in [-1000, 200, 300, 400, 500])
        result = npv(0.08, cf_gen)
        assert isinstance(result, float)


class TestNPVNegativeRates:
    """Tests for NPV with negative discount rates."""

    def test_npv_negative_rate(self):
        """Test NPV with negative discount rate (deflation scenario)."""
        cf = [-1000, 200, 300, 400, 500]
        result = npv(-0.05, cf)
        assert isinstance(result, float)
        # Negative rate makes future values worth MORE
        positive_rate_npv = npv(0.05, cf)
        assert result > positive_rate_npv

    def test_npv_rate_minus_one(self):
        """Test NPV at exactly -100% rate (boundary condition)."""
        cf = [-1000, 500, 500]
        # At -100% rate, denominator becomes 0 for period > 0
        # This may result in inf/nan
        result = npv(-1.0, cf)
        # Just verify it handles without crashing
        assert isinstance(result, float)


class TestIRRBasic:
    """Basic IRR functionality tests."""

    def test_irr_positive_return(self):
        """Test IRR with profitable investment."""
        cf = [-1000, 200, 300, 400, 500]
        result = irr(cf)
        assert isinstance(result, float)
        assert -1.0 < result < 1.0  # Reasonable IRR range

    def test_irr_known_value(self):
        """Test IRR against known textbook value.

        Investment: -100 today, +110 next year
        IRR = 10% (i.e., 0.10)
        """
        cf = [-100, 110]
        result = irr(cf)
        assert abs(result - 0.10) < 0.001  # Should be 10%

    def test_irr_break_even(self):
        """Test IRR when exactly breaking even (NPV=0 at 0%)."""
        cf = [-1000, 500, 500]  # Sum = 0, so IRR = 0%
        result = irr(cf)
        assert abs(result - 0.0) < 0.001

    def test_irr_negative_return(self):
        """Test IRR for unprofitable investment."""
        cf = [-1000, 100, 100]  # Lose money
        result = irr(cf)
        assert result < 0  # Negative IRR = loss

    def test_irr_verify_with_npv(self):
        """Verify IRR by checking NPV at that rate equals zero."""
        cf = [-1000, 300, 400, 500, 200]
        r = irr(cf)
        npv_at_irr = npv(r, cf)
        assert abs(npv_at_irr) < 0.01  # NPV at IRR should be ~0


class TestIRREdgeCases:
    """Edge case tests for IRR."""

    def test_irr_empty_array(self):
        """Test IRR with empty cashflow array."""
        result = irr([])
        # Should return nan (no solution)
        assert math.isnan(result)

    def test_irr_single_value(self):
        """Test IRR with single cashflow."""
        result = irr([-1000])
        # No solution for single cashflow
        assert math.isnan(result)

    def test_irr_all_positive(self):
        """Test IRR when all cashflows are positive (no initial investment)."""
        cf = [100, 200, 300]
        result = irr(cf)
        # No sign change = no IRR solution
        assert math.isnan(result)

    def test_irr_all_negative(self):
        """Test IRR when all cashflows are negative."""
        cf = [-100, -200, -300]
        result = irr(cf)
        # No sign change = no IRR solution
        assert math.isnan(result)

    def test_irr_all_zeros(self):
        """Test IRR with all zero cashflows."""
        cf = [0, 0, 0, 0]
        result = irr(cf)
        # Indeterminate case
        assert math.isnan(result)


class TestIRRConvergence:
    """Tests for IRR convergence edge cases."""

    def test_irr_multiple_sign_changes(self):
        """Test IRR with multiple sign changes (may have multiple roots).

        Cashflows: -100, +230, -132
        This has two IRR solutions: 10% and 20%
        """
        cf = [-100, 230, -132]
        result = irr(cf)
        # numpy-financial returns one solution (typically the first found)
        assert isinstance(result, float)
        # Verify it's a valid IRR (NPV ≈ 0)
        if not math.isnan(result):
            npv_at_irr = npv(result, cf)
            assert abs(npv_at_irr) < 0.5  # Reasonable tolerance

    def test_irr_very_high_return(self):
        """Test IRR with extremely high return."""
        cf = [-1, 1000]  # 99900% return
        result = irr(cf)
        assert result > 100  # Very high IRR

    def test_irr_very_low_return(self):
        """Test IRR with extremely poor return."""
        cf = [-1000, 1]  # Nearly total loss
        result = irr(cf)
        assert result < -0.9  # Very negative IRR

    def test_irr_long_cashflow_series(self):
        """Test IRR with many periods."""
        # 100 periods of small positive cashflows after initial investment
        cf = [-10000] + [200] * 100
        result = irr(cf)
        assert isinstance(result, float)
        assert not math.isnan(result)


class TestPMT:
    """Tests for payment calculation function."""

    def test_pmt_basic_loan(self):
        """Test basic loan payment calculation."""
        # $100,000 loan, 5% annual rate, 30 years
        monthly_rate = 0.05 / 12
        months = 30 * 12
        payment = pmt(monthly_rate, months, 100000)
        # Payment should be negative (outflow) and around $537
        assert payment < 0
        assert abs(payment) > 500
        assert abs(payment) < 600

    def test_pmt_known_value(self):
        """Test PMT against known textbook value.

        $200,000 mortgage at 6% for 30 years = $1,199.10/month
        """
        monthly_rate = 0.06 / 12
        months = 30 * 12
        payment = pmt(monthly_rate, months, 200000)
        assert abs(abs(payment) - 1199.10) < 1.0  # Within $1

    def test_pmt_zero_rate(self):
        """Test PMT with zero interest rate."""
        payment = pmt(0.0, 12, 1200)
        # At 0% interest, payment = principal / periods
        assert abs(payment) == pytest.approx(100.0, rel=0.01)

    def test_pmt_with_future_value(self):
        """Test PMT with non-zero future value (balloon payment)."""
        payment = pmt(0.05 / 12, 60, 20000, fv=5000)
        assert isinstance(payment, float)
        assert payment < 0  # Still an outflow


class TestFV:
    """Tests for future value calculation function."""

    def test_fv_basic_savings(self):
        """Test basic savings growth."""
        # Save $500/month at 7% annual for 10 years
        monthly_rate = 0.07 / 12
        months = 10 * 12
        future = fv(monthly_rate, months, -500)
        # Should accumulate to ~$87,000
        assert future > 80000
        assert future < 95000

    def test_fv_lump_sum(self):
        """Test future value of lump sum investment."""
        # $10,000 at 5% for 10 years
        future = fv(0.05, 10, 0, -10000)
        # FV = 10000 * (1.05)^10 = ~$16,289
        assert abs(future - 16288.95) < 1.0

    def test_fv_zero_rate(self):
        """Test FV with zero growth rate."""
        future = fv(0.0, 12, -100)
        # At 0%, FV = sum of payments
        assert abs(future - 1200) < 0.01


class TestPV:
    """Tests for present value calculation function."""

    def test_pv_basic(self):
        """Test basic present value calculation."""
        # What's the present value of $100/month for 5 years at 8%?
        monthly_rate = 0.08 / 12
        months = 5 * 12
        present = pv(monthly_rate, months, -100)
        # Should be around $4,900
        assert present > 4800
        assert present < 5000

    def test_pv_lump_sum(self):
        """Test present value of future lump sum."""
        # What's $10,000 in 10 years worth today at 5%?
        present = pv(0.05, 10, 0, -10000)
        # PV = 10000 / (1.05)^10 = ~$6,139
        assert abs(present - 6139.13) < 1.0

    def test_pv_fv_inverse(self):
        """Test that PV and FV are inverses for lump sum."""
        rate = 0.05
        periods = 10
        initial = -1000  # Initial investment

        # Calculate future value of lump sum
        future = fv(rate, periods, 0, initial)
        # Present value of that future amount should equal initial
        present = pv(rate, periods, 0, future)
        assert abs(present - initial) < 0.01


class TestCoreModuleDirect:
    """Tests for core module direct imports."""

    def test_core_npv_same_as_package(self):
        """Verify core.npv matches package npv."""
        cf = [-1000, 200, 300, 400]
        assert core_npv(0.08, cf) == npv(0.08, cf)

    def test_core_irr_same_as_package(self):
        """Verify core.irr matches package irr."""
        cf = [-1000, 200, 300, 400, 500]
        assert core_irr(cf) == irr(cf)
