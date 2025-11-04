# Cashflows & Financial Calculations

fin-infra provides production-ready financial calculation functions for cashflow analysis, present value calculations, and investment returns.

## Installation

The cashflows module is included in the core fin-infra package:

```bash
pip install fin-infra
```

## Quick Start

```python
from fin_infra.cashflows import npv, irr, xnpv, xirr, pmt, fv, pv

# Calculate Net Present Value
cashflows = [-1000, 200, 300, 400, 500]
discount_rate = 0.08
net_value = npv(discount_rate, cashflows)
print(f"NPV: ${net_value:.2f}")

# Calculate Internal Rate of Return
rate = irr(cashflows)
print(f"IRR: {rate:.2%}")
```

## Core Functions

### Net Present Value (NPV)
Calculate the present value of a series of cashflows:

```python
from fin_infra.cashflows import npv

# Initial investment followed by returns
cashflows = [-10000, 3000, 4000, 5000, 6000]
discount_rate = 0.10

net_value = npv(discount_rate, cashflows)
print(f"NPV: ${net_value:.2f}")
# NPV: $3396.88
```

### Internal Rate of Return (IRR)
Find the discount rate that makes NPV = 0:

```python
from fin_infra.cashflows import irr

cashflows = [-10000, 3000, 4000, 5000, 6000]
rate = irr(cashflows)
print(f"IRR: {rate:.2%}")
# IRR: 21.16%
```

### Extended NPV (XNPV)
Calculate NPV with irregular time periods:

```python
from datetime import date
from fin_infra.cashflows import xnpv

dates = [
    date(2024, 1, 1),
    date(2024, 3, 15),
    date(2024, 7, 20),
    date(2024, 12, 31),
]
cashflows = [-10000, 3000, 4000, 5000]
discount_rate = 0.10

net_value = xnpv(discount_rate, cashflows, dates)
print(f"XNPV: ${net_value:.2f}")
```

### Extended IRR (XIRR)
Calculate IRR with irregular time periods:

```python
from fin_infra.cashflows import xirr

dates = [
    date(2024, 1, 1),
    date(2024, 3, 15),
    date(2024, 7, 20),
    date(2024, 12, 31),
]
cashflows = [-10000, 3000, 4000, 5000]

rate = xirr(cashflows, dates)
print(f"XIRR: {rate:.2%}")
```

### Payment (PMT)
Calculate periodic payment for a loan:

```python
from fin_infra.cashflows import pmt

rate = 0.05 / 12  # 5% annual rate, monthly payments
nper = 30 * 12    # 30 years
pv = 200000       # Loan amount

monthly_payment = pmt(rate, nper, pv)
print(f"Monthly Payment: ${-monthly_payment:.2f}")
# Monthly Payment: $1,073.64
```

### Future Value (FV)
Calculate future value of an investment:

```python
from fin_infra.cashflows import fv

rate = 0.08 / 12  # 8% annual return, monthly compounding
nper = 10 * 12    # 10 years
pmt = -500        # Monthly contribution
pv = -10000       # Initial investment

future_value = fv(rate, nper, pmt, pv)
print(f"Future Value: ${future_value:.2f}")
# Future Value: $101,483.63
```

### Present Value (PV)
Calculate present value of future cashflows:

```python
from fin_infra.cashflows import pv

rate = 0.06 / 12  # 6% annual rate
nper = 20 * 12    # 20 years
pmt = 1000        # Monthly payment

present_value = pv(rate, nper, pmt)
print(f"Present Value: ${-present_value:.2f}")
# Present Value: $139,580.77
```

## Advanced Use Cases

### Loan Amortization Schedule
```python
from fin_infra.cashflows import pmt, ipmt, ppmt
import pandas as pd

def amortization_schedule(principal, annual_rate, years):
    monthly_rate = annual_rate / 12
    nper = years * 12
    
    monthly_pmt = -pmt(monthly_rate, nper, principal)
    
    schedule = []
    balance = principal
    
    for month in range(1, nper + 1):
        interest = ipmt(monthly_rate, month, nper, principal)
        principal_pmt = ppmt(monthly_rate, month, nper, principal)
        balance -= principal_pmt
        
        schedule.append({
            'Month': month,
            'Payment': monthly_pmt,
            'Principal': principal_pmt,
            'Interest': -interest,
            'Balance': balance
        })
    
    return pd.DataFrame(schedule)

# Create amortization schedule
schedule = amortization_schedule(200000, 0.05, 30)
print(schedule.head())
```

### Investment Portfolio Analysis
```python
from fin_infra.cashflows import xnpv, xirr
from datetime import date, timedelta

class Portfolio:
    def __init__(self):
        self.transactions = []
    
    def add_contribution(self, amount, date):
        self.transactions.append((-amount, date))
    
    def add_withdrawal(self, amount, date):
        self.transactions.append((amount, date))
    
    def calculate_returns(self, current_value, as_of_date):
        cashflows = [cf for cf, _ in self.transactions]
        dates = [dt for _, dt in self.transactions]
        
        # Add current value as final cashflow
        cashflows.append(current_value)
        dates.append(as_of_date)
        
        # Calculate returns
        irr_value = xirr(cashflows, dates)
        return irr_value

# Example usage
portfolio = Portfolio()
portfolio.add_contribution(10000, date(2023, 1, 1))
portfolio.add_contribution(5000, date(2023, 6, 1))
portfolio.add_contribution(5000, date(2024, 1, 1))

returns = portfolio.calculate_returns(
    current_value=25000,
    as_of_date=date(2024, 12, 31)
)
print(f"Portfolio IRR: {returns:.2%}")
```

### Retirement Planning
```python
from fin_infra.cashflows import fv, pv

def retirement_calculator(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    monthly_contribution: float,
    annual_return: float,
    retirement_spending: float,
    years_in_retirement: int = 30
):
    # Years until retirement
    years_to_retirement = retirement_age - current_age
    
    # Calculate savings at retirement
    savings_at_retirement = fv(
        rate=annual_return / 12,
        nper=years_to_retirement * 12,
        pmt=-monthly_contribution,
        pv=-current_savings
    )
    
    # Calculate required savings for retirement spending
    required_savings = pv(
        rate=annual_return / 12,
        nper=years_in_retirement * 12,
        pmt=retirement_spending
    )
    
    shortfall = required_savings + savings_at_retirement
    
    return {
        'savings_at_retirement': savings_at_retirement,
        'required_savings': -required_savings,
        'shortfall': shortfall,
        'on_track': shortfall <= 0
    }

result = retirement_calculator(
    current_age=30,
    retirement_age=65,
    current_savings=50000,
    monthly_contribution=1000,
    annual_return=0.07,
    retirement_spending=5000
)

print(f"Savings at retirement: ${result['savings_at_retirement']:,.2f}")
print(f"Required savings: ${result['required_savings']:,.2f}")
print(f"On track: {result['on_track']}")
```

## Testing

```python
import pytest
from fin_infra.cashflows import npv, irr

def test_npv():
    cashflows = [-1000, 300, 300, 300, 300]
    discount_rate = 0.10
    
    result = npv(discount_rate, cashflows)
    assert abs(result - (-48.68)) < 1.0

def test_irr():
    cashflows = [-1000, 300, 300, 300, 300]
    
    result = irr(cashflows)
    assert abs(result - 0.0779) < 0.01  # ~7.79%
```

## Best Practices

1. **Consistent Sign Convention**: Negative for outflows, positive for inflows
2. **Annualized Returns**: Always specify if returns are annual, monthly, etc.
3. **Time Value**: Use XNPV/XIRR for irregular periods
4. **Rounding**: Round financial values appropriately (usually 2 decimals)
5. **Validation**: Validate input cashflows before calculations
6. **Error Handling**: Handle cases where IRR cannot converge

## Next Steps

- [Market Data Integration](market-data.md)
- [Banking Integration](banking.md)
- [Brokerage Integration](brokerage.md)
