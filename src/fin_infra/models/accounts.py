from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AccountType(str, Enum):
    checking = "checking"
    savings = "savings"
    credit = "credit"
    investment = "investment"
    loan = "loan"
    other = "other"


class Account(BaseModel):
    id: str
    name: str
    type: AccountType
    mask: Optional[str] = None
    currency: str = "USD"
    institution: Optional[str] = None
    balance_available: Optional[float] = None
    balance_current: Optional[float] = None
