from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    account_id: str
    date: date
    amount: float
    currency: str = "USD"
    description: Optional[str] = None
    category: Optional[str] = None
