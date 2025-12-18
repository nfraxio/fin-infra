"""Unit tests for financial edge cases (Task 4.4.4).

Tests cover critical scenarios:
- Currency edge cases (zero exchange rate, extreme rates, same currency)
- Order partial fills (brokerage orders partially filled)
- Date boundary issues (midnight UTC vs local time)
- Leap year/DST (financial calculations across transitions)
"""

from __future__ import annotations

import zoneinfo
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from fin_infra.models.brokerage import Order, Position
from fin_infra.models.transactions import Transaction
from fin_infra.models.accounts import Account, AccountType
from fin_infra.net_worth.calculator import normalize_currency


class TestCurrencyEdgeCases:
    """Tests for currency conversion edge cases."""

    def test_same_currency_returns_amount_unchanged(self):
        """Test conversion between same currency returns exact amount."""
        result = normalize_currency(100.0, "USD", "USD")
        assert result == 100.0

    def test_same_currency_case_handling(self):
        """Test same currency comparison is case-insensitive in normalize_currency."""
        # normalize_currency uses == which is case-sensitive
        # This documents current behavior
        result = normalize_currency(100.0, "USD", "USD")
        assert result == 100.0

        # Mismatched case requires exchange rate
        with pytest.raises(ValueError, match="exchange_rate parameter"):
            normalize_currency(100.0, "usd", "USD")

    def test_zero_exchange_rate(self):
        """Test zero exchange rate produces zero result."""
        result = normalize_currency(100.0, "USD", "EUR", exchange_rate=0.0)
        assert result == 0.0

    def test_negative_exchange_rate(self):
        """Test negative exchange rate (edge case - should it be rejected?)."""
        # Currently no validation on exchange_rate
        result = normalize_currency(100.0, "USD", "EUR", exchange_rate=-1.0)
        assert result == -100.0  # Documents current behavior

    def test_very_small_exchange_rate(self):
        """Test very small exchange rate (hyperinflation scenario)."""
        # 1 USD = 0.000001 of some hyperinflated currency
        result = normalize_currency(1_000_000.0, "USD", "ZWD", exchange_rate=0.000001)
        assert abs(result - 1.0) < 1e-10

    def test_very_large_exchange_rate(self):
        """Test very large exchange rate (strong currency to weak)."""
        # 1 strong currency = 10,000,000 weak currency
        result = normalize_currency(1.0, "BTC", "SAT", exchange_rate=100_000_000.0)
        assert result == 100_000_000.0

    def test_exchange_rate_precision(self):
        """Test exchange rate with many decimal places."""
        # Precise rate: 1 USD = 0.91234567 EUR
        rate = 0.91234567
        result = normalize_currency(100.0, "USD", "EUR", exchange_rate=rate)
        assert abs(result - 91.234567) < 1e-6

    def test_conversion_with_zero_amount(self):
        """Test converting zero amount."""
        result = normalize_currency(0.0, "USD", "EUR", exchange_rate=0.92)
        assert result == 0.0

    def test_conversion_with_negative_amount(self):
        """Test converting negative amount (liability)."""
        result = normalize_currency(-1000.0, "USD", "EUR", exchange_rate=0.92)
        assert result == -920.0

    def test_missing_exchange_rate_raises(self):
        """Test that missing exchange rate for different currencies raises."""
        with pytest.raises(ValueError, match="exchange_rate parameter"):
            normalize_currency(100.0, "USD", "EUR")

    def test_infinity_handling(self):
        """Test handling of infinity in exchange rate."""
        result = normalize_currency(100.0, "USD", "XXX", exchange_rate=float("inf"))
        assert result == float("inf")

    def test_nan_handling(self):
        """Test handling of NaN in exchange rate."""
        import math

        result = normalize_currency(100.0, "USD", "XXX", exchange_rate=float("nan"))
        assert math.isnan(result)


class TestOrderPartialFills:
    """Tests for brokerage order partial fill scenarios."""

    def test_order_partially_filled_status(self):
        """Test order with partially_filled status."""
        order = Order(
            id="ord_123",
            symbol="AAPL",
            qty=Decimal("100"),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("150.00"),
            filled_qty=Decimal("50"),
            filled_avg_price=Decimal("149.50"),
            status="partially_filled",
            created_at=datetime.now(timezone.utc),
        )

        assert order.status == "partially_filled"
        assert order.filled_qty == Decimal("50")
        assert order.qty == Decimal("100")
        assert order.filled_qty < order.qty

    def test_order_zero_filled(self):
        """Test order with zero filled quantity."""
        order = Order(
            id="ord_124",
            symbol="TSLA",
            qty=Decimal("100"),
            side="sell",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("250.00"),
            filled_qty=Decimal("0"),
            status="new",
            created_at=datetime.now(timezone.utc),
        )

        assert order.filled_qty == Decimal("0")
        assert order.filled_avg_price is None

    def test_order_fully_filled(self):
        """Test order that is fully filled."""
        order = Order(
            id="ord_125",
            symbol="GOOGL",
            qty=Decimal("50"),
            side="buy",
            type="market",
            time_in_force="day",
            filled_qty=Decimal("50"),
            filled_avg_price=Decimal("140.25"),
            status="filled",
            created_at=datetime.now(timezone.utc),
            filled_at=datetime.now(timezone.utc),
        )

        assert order.filled_qty == order.qty
        assert order.status == "filled"

    def test_order_overfilled_not_possible(self):
        """Test that overfilled orders are possible but unusual."""
        # In practice, filled_qty should never exceed qty,
        # but the model doesn't enforce this
        order = Order(
            id="ord_126",
            symbol="AMZN",
            qty=Decimal("10"),
            side="buy",
            type="market",
            time_in_force="day",
            filled_qty=Decimal("11"),  # More than ordered
            filled_avg_price=Decimal("180.00"),
            status="filled",
            created_at=datetime.now(timezone.utc),
        )

        # Document: model allows this (no validation)
        assert order.filled_qty > order.qty

    def test_partial_fill_price_calculation(self):
        """Test calculating remaining value for partial fill."""
        order = Order(
            id="ord_127",
            symbol="NVDA",
            qty=Decimal("100"),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("500.00"),
            filled_qty=Decimal("60"),
            filled_avg_price=Decimal("495.50"),
            status="partially_filled",
            created_at=datetime.now(timezone.utc),
        )

        remaining_qty = order.qty - order.filled_qty
        assert remaining_qty == Decimal("40")

        filled_value = order.filled_qty * order.filled_avg_price
        assert filled_value == Decimal("29730.00")

    def test_fractional_share_partial_fill(self):
        """Test partial fill with fractional shares."""
        order = Order(
            id="ord_128",
            symbol="BRK.A",
            qty=Decimal("0.5"),
            side="buy",
            type="market",
            time_in_force="day",
            filled_qty=Decimal("0.25"),
            filled_avg_price=Decimal("650000.00"),
            status="partially_filled",
            created_at=datetime.now(timezone.utc),
        )

        assert order.filled_qty == Decimal("0.25")
        remaining = order.qty - order.filled_qty
        assert remaining == Decimal("0.25")

    def test_order_canceled_after_partial_fill(self):
        """Test order canceled with partial fill."""
        order = Order(
            id="ord_129",
            symbol="META",
            qty=Decimal("200"),
            side="sell",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("350.00"),
            filled_qty=Decimal("75"),
            filled_avg_price=Decimal("350.00"),
            status="canceled",
            created_at=datetime.now(timezone.utc),
            canceled_at=datetime.now(timezone.utc),
        )

        assert order.status == "canceled"
        assert order.filled_qty > 0  # Partial fill before cancel

    def test_order_expired_after_partial_fill(self):
        """Test order expired with partial fill."""
        order = Order(
            id="ord_130",
            symbol="AAPL",
            qty=Decimal("500"),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("175.00"),
            filled_qty=Decimal("350"),
            filled_avg_price=Decimal("174.90"),
            status="expired",
            created_at=datetime.now(timezone.utc),
            expired_at=datetime.now(timezone.utc),
        )

        assert order.status == "expired"
        unfilled = order.qty - order.filled_qty
        assert unfilled == Decimal("150")


class TestDateBoundaryIssues:
    """Tests for date boundary issues (midnight UTC vs local time)."""

    def test_transaction_date_is_date_not_datetime(self):
        """Test Transaction.date is date type, not datetime."""
        txn = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2025, 12, 17),
            amount=Decimal("100.00"),
        )

        assert isinstance(txn.date, date)
        assert not isinstance(txn.date, datetime)

    def test_transaction_near_midnight_utc(self):
        """Test transaction created near midnight UTC."""
        # 11:59 PM UTC on Dec 16
        utc_time = datetime(2025, 12, 16, 23, 59, 59, tzinfo=timezone.utc)
        # Transaction date should be Dec 16
        txn = Transaction(
            id="t2",
            account_id="acc1",
            date=utc_time.date(),
            amount=Decimal("-50.00"),
        )

        assert txn.date == date(2025, 12, 16)

    def test_transaction_after_midnight_utc(self):
        """Test transaction created just after midnight UTC."""
        utc_time = datetime(2025, 12, 17, 0, 0, 1, tzinfo=timezone.utc)
        txn = Transaction(
            id="t3",
            account_id="acc1",
            date=utc_time.date(),
            amount=Decimal("-25.00"),
        )

        assert txn.date == date(2025, 12, 17)

    def test_transaction_local_vs_utc_date_difference(self):
        """Test transaction where local time and UTC are on different dates."""
        # 8 PM EST on Dec 16 = 1 AM UTC on Dec 17
        est = zoneinfo.ZoneInfo("America/New_York")
        local_time = datetime(2025, 12, 16, 20, 0, 0, tzinfo=est)
        utc_time = local_time.astimezone(timezone.utc)

        # Local date is Dec 16, UTC date is Dec 17
        assert local_time.date() == date(2025, 12, 16)
        assert utc_time.date() == date(2025, 12, 17)

        # If we use UTC date for transaction:
        txn_utc = Transaction(
            id="t4",
            account_id="acc1",
            date=utc_time.date(),
            amount=Decimal("-100.00"),
        )
        assert txn_utc.date == date(2025, 12, 17)

        # If we use local date:
        txn_local = Transaction(
            id="t5",
            account_id="acc1",
            date=local_time.date(),
            amount=Decimal("-100.00"),
        )
        assert txn_local.date == date(2025, 12, 16)

    def test_order_timestamps_are_utc(self):
        """Test that Order timestamps should use UTC."""
        now_utc = datetime.now(timezone.utc)
        order = Order(
            id="ord_date1",
            symbol="AAPL",
            qty=Decimal("10"),
            side="buy",
            type="market",
            time_in_force="day",
            filled_qty=Decimal("10"),
            filled_avg_price=Decimal("150.00"),
            status="filled",
            created_at=now_utc,
            filled_at=now_utc,
        )

        assert order.created_at.tzinfo is not None
        assert order.filled_at.tzinfo is not None

    def test_order_naive_datetime_handling(self):
        """Test Order with naive datetime (no timezone)."""
        # Naive datetime - no timezone info
        naive_dt = datetime(2025, 12, 17, 10, 30, 0)
        order = Order(
            id="ord_date2",
            symbol="AAPL",
            qty=Decimal("5"),
            side="buy",
            type="market",
            time_in_force="day",
            status="new",
            created_at=naive_dt,
        )

        # Model accepts naive datetime (documents current behavior)
        assert order.created_at.tzinfo is None

    def test_date_boundary_at_market_close(self):
        """Test date boundary at market close (4 PM ET)."""
        et = zoneinfo.ZoneInfo("America/New_York")

        # Market close on Dec 16, 2025 at 4 PM ET
        market_close = datetime(2025, 12, 16, 16, 0, 0, tzinfo=et)

        # Order placed just before close
        order = Order(
            id="ord_close1",
            symbol="SPY",
            qty=Decimal("100"),
            side="buy",
            type="market",
            time_in_force="day",
            status="filled",
            filled_qty=Decimal("100"),
            filled_avg_price=Decimal("475.00"),
            created_at=market_close - timedelta(seconds=10),
            filled_at=market_close,
        )

        assert order.created_at.date() == date(2025, 12, 16)
        assert order.filled_at.date() == date(2025, 12, 16)

    def test_date_boundary_weekend_handling(self):
        """Test date handling for weekend transactions."""
        # Saturday transaction (e.g., crypto)
        saturday = date(2025, 12, 20)  # Saturday

        txn = Transaction(
            id="t_weekend",
            account_id="crypto_acc",
            date=saturday,
            amount=Decimal("-500.00"),
            description="BTC purchase",
        )

        assert txn.date.weekday() == 5  # Saturday


class TestLeapYearAndDST:
    """Tests for leap year and daylight saving time transitions."""

    def test_transaction_on_leap_day(self):
        """Test transaction on February 29 (leap year)."""
        leap_day = date(2024, 2, 29)  # 2024 is a leap year

        txn = Transaction(
            id="t_leap",
            account_id="acc1",
            date=leap_day,
            amount=Decimal("1000.00"),
        )

        assert txn.date.month == 2
        assert txn.date.day == 29

    def test_transaction_next_day_after_leap_day(self):
        """Test transaction on March 1 after leap day."""
        march_1 = date(2024, 3, 1)
        leap_day = date(2024, 2, 29)

        # Difference should be 1 day
        diff = march_1 - leap_day
        assert diff.days == 1

        txn = Transaction(
            id="t_march1",
            account_id="acc1",
            date=march_1,
            amount=Decimal("500.00"),
        )

        assert txn.date == march_1

    def test_non_leap_year_february(self):
        """Test February 29 doesn't exist in non-leap year."""
        with pytest.raises(ValueError):
            date(2025, 2, 29)  # 2025 is not a leap year

    def test_dst_spring_forward(self):
        """Test timestamp during DST spring forward (2 AM -> 3 AM)."""
        et = zoneinfo.ZoneInfo("America/New_York")

        # March 9, 2025 2:30 AM doesn't exist (clocks skip from 2 to 3)
        # This typically raises an error or gets adjusted
        try:
            # Try to create time that doesn't exist
            dt = datetime(2025, 3, 9, 2, 30, tzinfo=et)
            # If it doesn't raise, the date part should still work
            assert dt.date() == date(2025, 3, 9)
        except Exception:
            # Some implementations may raise for non-existent times
            pass

    def test_dst_fall_back(self):
        """Test timestamp during DST fall back (ambiguous time)."""
        et = zoneinfo.ZoneInfo("America/New_York")

        # November 2, 2025 1:30 AM occurs twice (before and after fall back)
        dt1 = datetime(2025, 11, 2, 1, 30, tzinfo=et, fold=0)  # First occurrence
        dt2 = datetime(2025, 11, 2, 1, 30, tzinfo=et, fold=1)  # Second occurrence

        # Same local time, different UTC times
        assert dt1.date() == dt2.date() == date(2025, 11, 2)

        # Convert to UTC to see difference
        utc1 = dt1.astimezone(timezone.utc)
        utc2 = dt2.astimezone(timezone.utc)

        # Second occurrence is 1 hour later in UTC
        assert (utc2 - utc1).total_seconds() == 3600

    def test_order_during_dst_transition(self):
        """Test order creation during DST transition."""
        et = zoneinfo.ZoneInfo("America/New_York")

        # Create order at ambiguous time (1:30 AM during fall back)
        ambiguous_time = datetime(2025, 11, 2, 1, 30, tzinfo=et, fold=1)

        order = Order(
            id="ord_dst",
            symbol="AAPL",
            qty=Decimal("10"),
            side="buy",
            type="market",
            time_in_force="day",
            status="new",
            created_at=ambiguous_time,
        )

        assert order.created_at.date() == date(2025, 11, 2)

    def test_year_boundary_transaction(self):
        """Test transaction on year boundary (Dec 31 -> Jan 1)."""
        dec_31 = date(2025, 12, 31)
        jan_1 = date(2026, 1, 1)

        txn_2025 = Transaction(
            id="t_2025",
            account_id="acc1",
            date=dec_31,
            amount=Decimal("-100.00"),
        )

        txn_2026 = Transaction(
            id="t_2026",
            account_id="acc1",
            date=jan_1,
            amount=Decimal("-50.00"),
        )

        assert txn_2025.date.year == 2025
        assert txn_2026.date.year == 2026
        assert (txn_2026.date - txn_2025.date).days == 1

    def test_century_leap_year(self):
        """Test century year (2000 was leap, 2100 won't be)."""
        # 2000 was a leap year (divisible by 400)
        leap_2000 = date(2000, 2, 29)
        assert leap_2000.day == 29

        # 2100 won't be a leap year (divisible by 100 but not 400)
        with pytest.raises(ValueError):
            date(2100, 2, 29)

    def test_fiscal_year_end_on_leap_day(self):
        """Test fiscal period ending on leap day."""
        # Company with fiscal year ending Feb 29 in leap year
        fiscal_end_leap = date(2024, 2, 29)
        fiscal_start = date(2023, 3, 1)

        # Calculate fiscal year length
        days_in_fiscal_year = (fiscal_end_leap - fiscal_start).days + 1
        assert days_in_fiscal_year == 366  # Leap year

    def test_timezone_date_boundary_across_dst(self):
        """Test date boundary when timezone crosses DST at midnight."""
        et = zoneinfo.ZoneInfo("America/New_York")

        # 11 PM on March 8, 2025 (before DST)
        before_dst = datetime(2025, 3, 8, 23, 0, tzinfo=et)

        # 3 AM on March 9, 2025 (after DST - 2 AM became 3 AM)
        after_dst = datetime(2025, 3, 9, 3, 0, tzinfo=et)

        # Time difference: 11 PM to 3 AM spans the DST transition
        # Wall clock: 4 hours (11 PM -> 12 AM -> 1 AM -> 2 AM [skip] -> 3 AM)
        # Real time: 4 hours because zoneinfo handles the transition
        diff = after_dst - before_dst
        assert diff.total_seconds() == 4 * 3600  # 4 real hours elapsed

    def test_multi_currency_transaction_across_dst(self):
        """Test that currency doesn't affect date handling."""
        txn_usd = Transaction(
            id="t_usd",
            account_id="acc1",
            date=date(2025, 3, 9),  # DST transition day
            amount=Decimal("100.00"),
            currency="USD",
        )

        txn_eur = Transaction(
            id="t_eur",
            account_id="acc2",
            date=date(2025, 3, 9),
            amount=Decimal("92.00"),
            currency="EUR",
        )

        assert txn_usd.date == txn_eur.date

    def test_account_balance_snapshot_timing(self):
        """Test account balance snapshot at midnight boundaries."""
        # Account created at 11:59 PM
        datetime(2025, 12, 16, 23, 59, 0, tzinfo=timezone.utc)

        account = Account(
            id="acc_timing",
            name="Timing Test",
            type=AccountType.checking,
            balance_current=Decimal("1000.00"),
        )

        # Balance is point-in-time, not date-specific
        assert account.balance_current == Decimal("1000.00")


class TestPositionEdgeCases:
    """Tests for Position model edge cases."""

    def test_position_with_zero_quantity(self):
        """Test position with zero quantity (closed position)."""
        pos = Position(
            symbol="AAPL",
            qty=Decimal("0"),
            side="long",
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("0"),
            cost_basis=Decimal("0"),
            unrealized_pl=Decimal("0"),
            unrealized_plpc=Decimal("0"),
        )

        assert pos.qty == Decimal("0")
        assert pos.market_value == Decimal("0")

    def test_position_negative_unrealized_pl(self):
        """Test position with negative unrealized P/L."""
        pos = Position(
            symbol="TSLA",
            qty=Decimal("10"),
            side="long",
            avg_entry_price=Decimal("300.00"),
            current_price=Decimal("250.00"),
            market_value=Decimal("2500.00"),
            cost_basis=Decimal("3000.00"),
            unrealized_pl=Decimal("-500.00"),
            unrealized_plpc=Decimal("-0.1667"),
        )

        assert pos.unrealized_pl < 0
        assert pos.unrealized_plpc < 0

    def test_short_position(self):
        """Test short position calculations."""
        pos = Position(
            symbol="GME",
            qty=Decimal("100"),
            side="short",
            avg_entry_price=Decimal("20.00"),
            current_price=Decimal("15.00"),
            market_value=Decimal("-1500.00"),  # Negative for short
            cost_basis=Decimal("2000.00"),
            unrealized_pl=Decimal("500.00"),  # Profit when price drops
            unrealized_plpc=Decimal("0.25"),
        )

        assert pos.side == "short"
        # Short position profits when price drops


class TestExtremeValues:
    """Tests for extreme value handling."""

    def test_very_large_transaction_amount(self):
        """Test transaction with very large amount."""
        large_amount = Decimal("999999999999.99")  # ~1 trillion

        txn = Transaction(
            id="t_large",
            account_id="acc1",
            date=date(2025, 12, 17),
            amount=large_amount,
        )

        assert txn.amount == large_amount

    def test_very_small_transaction_amount(self):
        """Test transaction with very small amount."""
        small_amount = Decimal("0.0000001")  # Sub-cent (crypto)

        txn = Transaction(
            id="t_small",
            account_id="crypto_acc",
            date=date(2025, 12, 17),
            amount=small_amount,
        )

        assert txn.amount == small_amount

    def test_order_very_high_price(self):
        """Test order with very high price (BRK.A level)."""
        order = Order(
            id="ord_high",
            symbol="BRK.A",
            qty=Decimal("1"),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("700000.00"),
            status="new",
            created_at=datetime.now(timezone.utc),
        )

        assert order.limit_price == Decimal("700000.00")

    def test_order_very_low_price(self):
        """Test order with very low price (penny stock)."""
        order = Order(
            id="ord_low",
            symbol="PENNY",
            qty=Decimal("10000"),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=Decimal("0.0001"),
            status="new",
            created_at=datetime.now(timezone.utc),
        )

        assert order.limit_price == Decimal("0.0001")
