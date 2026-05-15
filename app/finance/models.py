from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal
from uuid import uuid4

TransactionKind = Literal["income", "expense"]
FinanceEntryKind = Literal["variable", "recurring", "installments"]
BillRecurrence = Literal["none", "monthly", "weekly", "yearly"]


def new_finance_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utc_timestamp(now: datetime | None = None) -> str:
    moment = now or datetime.utcnow()
    return moment.replace(microsecond=0).isoformat() + "Z"


@dataclass(frozen=True)
class Transaction:
    id: str
    title: str
    amount: float
    type: TransactionKind
    category: str
    account: str
    date: str
    notes: str
    finance_type: FinanceEntryKind
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Bill:
    id: str
    title: str
    amount: float
    due_date: str
    paid: bool
    recurrence: BillRecurrence
    account: str
    category: str
    notes: str
    created_at: str
    paid_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Installment:
    id: str
    title: str
    total_amount: float
    installment_amount: float
    current_installment: int
    total_installments: int
    due_day: int
    account: str
    category: str
    notes: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Goal:
    id: str
    title: str
    target_amount: float
    current_amount: float
    deadline: str
    notes: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
