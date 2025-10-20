from __future__ import annotations

from typing import Iterable

import numpy as np
import numpy_financial as npf


def npv(rate: float, cashflows: Iterable[float]) -> float:
    """Net Present Value. rate = discount rate (e.g. 0.08 for 8%)."""
    arr = np.array(list(cashflows), dtype=float)
    return float(npf.npv(rate, arr))


def irr(cashflows: Iterable[float]) -> float:
    """Internal Rate of Return. Returns decimal (e.g. 0.123 = 12.3%)."""
    arr = np.array(list(cashflows), dtype=float)
    return float(npf.irr(arr))
