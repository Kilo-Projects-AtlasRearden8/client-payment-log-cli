"""Data models for client payments, invoices, and payments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Client:
    """A client who receives invoices and makes payments."""

    name: str
    email: str = ""
    notes: str = ""
    id: str | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = self.name


@dataclass
class Payment:
    """A payment recorded against an invoice."""

    amount: float
    date: date
    method: str = ""
    notes: str = ""
    id: str | None = None


@dataclass
class Invoice:
    """An invoice billed to a client, with tracked payments."""

    client_id: str
    amount: float
    due_date: date
    description: str = ""
    id: str | None = None
    payments: list[Payment] = field(default_factory=list)

    def paid_total(self) -> float:
        """Sum of all payments recorded against this invoice."""
        return sum(p.amount for p in self.payments)

    def outstanding(self) -> float:
        """Amount still owed on this invoice (never negative)."""
        return max(0.0, self.amount - self.paid_total())

    def is_paid(self) -> bool:
        return self.paid_total() >= self.amount

    def is_overdue(self, as_of: date | None = None) -> bool:
        if self.is_paid():
            return False
        today = as_of if as_of is not None else date.today()
        return today > self.due_date

    def days_overdue(self, as_of: date | None = None) -> int:
        """Number of days past due. Zero when not overdue."""
        if self.is_paid():
            return 0
        today = as_of if as_of is not None else date.today()
        delta = (today - self.due_date).days
        return delta if delta > 0 else 0

    def add_payment(self, payment: Payment) -> None:
        self.payments.append(payment)
