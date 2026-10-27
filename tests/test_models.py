"""Tests for the Invoice and Payment data models."""

from datetime import date

from payment_log.models import Invoice, Payment


def test_invoice_paid_total_starts_at_zero():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 11, 1))
    assert inv.paid_total() == 0.0


def test_invoice_outstanding_equals_amount_when_unpaid():
    inv = Invoice(client_id="c1", amount=250.0, due_date=date(2026, 11, 1))
    assert inv.outstanding() == 250.0


def test_invoice_outstanding_after_partial_payment():
    inv = Invoice(client_id="c1", amount=1000.0, due_date=date(2026, 11, 1))
    inv.add_payment(Payment(amount=400.0, date=date(2026, 10, 20)))
    inv.add_payment(Payment(amount=350.0, date=date(2026, 10, 25)))
    assert inv.paid_total() == 750.0
    assert inv.outstanding() == 250.0


def test_invoice_outstanding_never_negative():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 11, 1))
    inv.add_payment(Payment(amount=150.0, date=date(2026, 10, 20)))
    assert inv.paid_total() == 150.0
    assert inv.outstanding() == 0.0
    assert inv.is_paid() is True


def test_invoice_is_paid_when_fully_paid():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 11, 1))
    inv.add_payment(Payment(amount=100.0, date=date(2026, 10, 20)))
    assert inv.is_paid() is True


def test_invoice_not_overdue_when_paid_even_if_past_due():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 1, 1))
    inv.add_payment(Payment(amount=100.0, date=date(2026, 10, 20)))
    assert inv.is_overdue(as_of=date(2026, 12, 1)) is False


def test_invoice_overdue_after_due_date():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 10, 1))
    assert inv.is_overdue(as_of=date(2026, 10, 5)) is True
    assert inv.is_overdue(as_of=date(2026, 10, 1)) is False
    assert inv.is_overdue(as_of=date(2026, 9, 30)) is False


def test_days_overdue_counts_days_past_due():
    inv = Invoice(client_id="c1", amount=100.0, due_date=date(2026, 10, 1))
    assert inv.days_overdue(as_of=date(2026, 10, 1)) == 0
    assert inv.days_overdue(as_of=date(2026, 10, 5)) == 4
    assert inv.days_overdue(as_of=date(2026, 9, 30)) == 0
    assert inv.days_overdue() >= 0  # today-based, never negative


def test_payment_amount_and_date():
    pay = Payment(amount=250.0, date=date(2026, 11, 3), method="check")
    assert pay.amount == 250.0
    assert pay.date == date(2026, 11, 3)
    assert pay.method == "check"
