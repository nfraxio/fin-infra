"""Unit tests for financial edge cases.

Tests cover critical scenarios that could cause money loss or incorrect calculations:
- Decimal precision in money calculations
- Negative balance handling
- Fractional shares
- Edge case amounts (zero, very small, very large)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fin_infra.models.accounts import Account, AccountType
from fin_infra.models.transactions import Transaction


class TestDecimalPrecision:
    """Tests for Decimal precision in financial models."""

    def test_classic_float_precision_bug(self):
        """Verify the classic $0.01 + $0.02 != $0.03 is handled correctly.

        In floating point: 0.01 + 0.02 = 0.030000000000000002
        With Decimal: 0.01 + 0.02 = 0.03 exactly
        """
        t1 = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("0.01"),
        )
        t2 = Transaction(
            id="t2",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("0.02"),
        )

        total = t1.amount + t2.amount
        assert total == Decimal("0.03")
        assert str(total) == "0.03"  # No floating point garbage

    def test_account_balance_decimal_precision(self):
        """Test account balances maintain Decimal precision."""
        account = Account(
            id="acc1",
            name="Checking",
            type=AccountType.checking,
            balance_available=Decimal("1000.01"),
            balance_current=Decimal("1000.02"),
        )

        # Verify exact values preserved
        assert account.balance_available == Decimal("1000.01")
        assert account.balance_current == Decimal("1000.02")

        # Verify arithmetic works correctly
        difference = account.balance_current - account.balance_available
        assert difference == Decimal("0.01")

    def test_float_to_decimal_coercion(self):
        """Test that float inputs are safely coerced to Decimal."""
        # Transaction amount coercion
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=100.50,  # float input
        )
        assert isinstance(t.amount, Decimal)
        assert t.amount == Decimal("100.5")

        # Account balance coercion
        acc = Account(
            id="acc1",
            name="Test",
            type=AccountType.checking,
            balance_available=500.25,  # float input
            balance_current=500.25,
        )
        assert isinstance(acc.balance_available, Decimal)
        assert acc.balance_available == Decimal("500.25")

    def test_many_small_amounts_sum_correctly(self):
        """Test that summing many small amounts doesn't accumulate errors."""
        amounts = [Decimal("0.01") for _ in range(100)]
        total = sum(amounts)
        assert total == Decimal("1.00")

        # Float precision issues are demonstrated with slightly different values
        # 0.1 + 0.2 != 0.3 in floats (classic example)
        float_result = 0.1 + 0.2
        assert float_result != 0.3  # Float precision issue!

        # Decimal handles this correctly
        decimal_result = Decimal("0.1") + Decimal("0.2")
        assert decimal_result == Decimal("0.3")

    def test_currency_conversion_precision(self):
        """Test precision is maintained in currency-like calculations."""
        # Exchange rate with many decimal places
        rate = Decimal("0.000032")  # e.g., some crypto rate
        amount = Decimal("1000000.00")

        converted = amount * rate
        assert converted == Decimal("32.000000")

        # Reverse should give back original
        reverse = converted / rate
        assert reverse == amount

    def test_percentage_calculations(self):
        """Test percentage calculations maintain precision."""
        principal = Decimal("10000.00")
        rate = Decimal("0.0525")  # 5.25%

        interest = principal * rate
        assert interest == Decimal("525.0000")

        # Monthly rate calculation
        monthly_rate = rate / 12
        monthly_interest = principal * monthly_rate
        # Should be exactly $43.75
        assert monthly_interest == Decimal("43.75")

    def test_very_large_amounts(self):
        """Test handling of very large financial amounts (billions)."""
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("999999999999.99"),  # ~$1 trillion
        )
        assert t.amount == Decimal("999999999999.99")

        # Arithmetic should still be precise
        doubled = t.amount * 2
        assert doubled == Decimal("1999999999999.98")

    def test_very_small_amounts(self):
        """Test handling of very small amounts (sub-cent for crypto)."""
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("0.00000001"),  # 1 satoshi
        )
        assert t.amount == Decimal("0.00000001")

        # Sum many tiny amounts
        total = t.amount * 100000000
        assert total == Decimal("1.00000000")


class TestNegativeBalances:
    """Tests for negative balance handling."""

    def test_negative_balance_creation(self):
        """Test accounts can have negative balances (overdraft, credit)."""
        # Overdraft checking account
        overdraft = Account(
            id="acc1",
            name="Checking",
            type=AccountType.checking,
            balance_available=Decimal("-150.00"),
            balance_current=Decimal("-150.00"),
        )
        assert overdraft.balance_available == Decimal("-150.00")
        assert overdraft.balance_current < 0

    def test_credit_card_negative_balance(self):
        """Test credit card with balance owed (negative available)."""
        credit = Account(
            id="cc1",
            name="Credit Card",
            type=AccountType.credit,
            balance_available=Decimal("-2500.00"),  # Amount owed
            balance_current=Decimal("-2500.00"),
        )
        assert credit.balance_available == Decimal("-2500.00")

    def test_negative_transaction_amounts(self):
        """Test transactions with negative amounts (refunds, credits)."""
        refund = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("-50.00"),  # Refund
            description="Refund",
        )
        assert refund.amount == Decimal("-50.00")

    def test_balance_arithmetic_with_negatives(self):
        """Test arithmetic operations with negative balances."""
        balance = Decimal("-100.00")
        deposit = Decimal("250.00")

        new_balance = balance + deposit
        assert new_balance == Decimal("150.00")

        # Withdraw more than available
        withdrawal = Decimal("-200.00")
        final = new_balance + withdrawal
        assert final == Decimal("-50.00")

    def test_net_worth_with_negative_accounts(self):
        """Test calculating net worth with mix of positive/negative accounts."""
        checking = Account(
            id="chk",
            name="Checking",
            type=AccountType.checking,
            balance_current=Decimal("5000.00"),
        )
        savings = Account(
            id="sav",
            name="Savings",
            type=AccountType.savings,
            balance_current=Decimal("10000.00"),
        )
        credit_card = Account(
            id="cc",
            name="Credit Card",
            type=AccountType.credit,
            balance_current=Decimal("-2500.00"),
        )
        loan = Account(
            id="loan",
            name="Car Loan",
            type=AccountType.loan,
            balance_current=Decimal("-15000.00"),
        )

        accounts = [checking, savings, credit_card, loan]
        net_worth = sum(acc.balance_current or Decimal("0") for acc in accounts)

        # 5000 + 10000 - 2500 - 15000 = -2500
        assert net_worth == Decimal("-2500.00")


class TestFractionalShares:
    """Tests for fractional share quantities."""

    def test_very_small_share_quantity(self):
        """Test holdings with very small fractional quantities."""
        # This would typically be in a Holdings model
        quantity = Decimal("0.00001")
        price = Decimal("150.00")

        value = quantity * price
        assert value == Decimal("0.00150")

    def test_fractional_share_purchase(self):
        """Test fractional share purchase calculation."""
        investment = Decimal("100.00")
        share_price = Decimal("350.75")

        shares_purchased = investment / share_price
        # Should be ~0.2851...
        assert shares_purchased > Decimal("0.28")
        assert shares_purchased < Decimal("0.29")

        # Verify we can calculate back
        value = shares_purchased * share_price
        # Due to Decimal precision, this should be very close to $100
        assert abs(value - investment) < Decimal("0.01")

    def test_fractional_dividend_calculation(self):
        """Test dividend calculation on fractional shares."""
        shares = Decimal("0.12345")
        dividend_per_share = Decimal("0.50")

        dividend = shares * dividend_per_share
        assert dividend == Decimal("0.061725")

    def test_crypto_fractional_amounts(self):
        """Test cryptocurrency with many decimal places."""
        btc_quantity = Decimal("0.00123456")
        btc_price = Decimal("45000.00")

        value = btc_quantity * btc_price
        assert value == Decimal("55.55520000")


class TestZeroAmounts:
    """Tests for zero amount edge cases."""

    def test_zero_balance_account(self):
        """Test account with zero balance."""
        account = Account(
            id="acc1",
            name="Empty Account",
            type=AccountType.checking,
            balance_available=Decimal("0"),
            balance_current=Decimal("0.00"),
        )
        assert account.balance_available == Decimal("0")
        assert account.balance_current == Decimal("0.00")

    def test_zero_amount_transaction(self):
        """Test transaction with zero amount (fee waiver, etc.)."""
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("0.00"),
            description="Fee waived",
        )
        assert t.amount == Decimal("0.00")

    def test_none_balances(self):
        """Test accounts with None balances (unknown/pending)."""
        account = Account(
            id="acc1",
            name="Pending Account",
            type=AccountType.checking,
            balance_available=None,
            balance_current=None,
        )
        assert account.balance_available is None
        assert account.balance_current is None

    def test_sum_with_none_balances(self):
        """Test summing balances when some are None."""
        accounts = [
            Account(id="1", name="A", type=AccountType.checking, balance_current=Decimal("100")),
            Account(id="2", name="B", type=AccountType.checking, balance_current=None),
            Account(id="3", name="C", type=AccountType.checking, balance_current=Decimal("200")),
        ]

        total = sum(acc.balance_current for acc in accounts if acc.balance_current is not None)
        assert total == Decimal("300")


class TestAccountTypeEdgeCases:
    """Tests for account type edge cases."""

    def test_all_account_types(self):
        """Test all account types can be created."""
        for acc_type in AccountType:
            account = Account(
                id=f"acc_{acc_type.value}",
                name=f"Test {acc_type.value}",
                type=acc_type,
            )
            assert account.type == acc_type

    def test_account_type_from_string(self):
        """Test account type can be created from string."""
        account = Account(
            id="acc1",
            name="Test",
            type="checking",  # String, not enum
        )
        assert account.type == AccountType.checking


class TestTransactionEdgeCases:
    """Tests for transaction edge cases."""

    def test_transaction_date_types(self):
        """Test transaction with different date inputs."""
        # Standard date
        t1 = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 15),
            amount=Decimal("100"),
        )
        assert t1.date == date(2024, 1, 15)

    def test_leap_year_transaction(self):
        """Test transaction on leap year date."""
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 2, 29),  # 2024 is a leap year
            amount=Decimal("100"),
        )
        assert t.date.day == 29
        assert t.date.month == 2

    def test_year_boundary_transaction(self):
        """Test transaction on year boundary."""
        t_last = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2023, 12, 31),
            amount=Decimal("100"),
        )
        t_first = Transaction(
            id="t2",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("100"),
        )

        # Verify dates are sequential
        assert (t_first.date - t_last.date).days == 1

    def test_optional_fields_none(self):
        """Test transaction with all optional fields as None."""
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("100"),
            description=None,
            category=None,
        )
        assert t.description is None
        assert t.category is None

    def test_very_long_description(self):
        """Test transaction with very long description."""
        long_desc = "A" * 10000
        t = Transaction(
            id="t1",
            account_id="acc1",
            date=date(2024, 1, 1),
            amount=Decimal("100"),
            description=long_desc,
        )
        assert len(t.description) == 10000
