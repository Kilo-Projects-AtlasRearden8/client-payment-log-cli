"""Tests for totals aggregation and date math (overdue logic)."""

from datetime import date

from payment_log.models import Invoice, Payment
from payment_log.storage import Store


def _store(tmp_path):
    return Store(path=tmp_path / "payment_log.json")


def _client(store, name):
    from payment_log.models import Client
    client = Client(name=name)
    store.add_client(client)
    return client


def test_totals_empty_store(tmp_path):
    store = _store(tmp_path)
    rows, grand = store.totals_by_client()
    assert rows == []
    assert grand["billed"] == 0.0
    assert grand["paid"] == 0.0
    assert grand["outstanding"] == 0.0


def test_totals_single_unpaid_invoice(tmp_path):
    store = _store(tmp_path)
    client = _client(store, "Acme Widgets")
    inv = Invoice(client_id=client.id, amount=1000.0, due_date=date(2026, 11, 15))
    store.add_invoice(inv)
    rows, grand = store.totals_by_client()
    assert len(rows) == 1
    assert rows[0]["client_name"] == "Acme Widgets"
    assert rows[0]["billed"] == 1000.0
    assert rows[0]["paid"] == 0.0
    assert rows[0]["outstanding"] == 1000.0
    assert grand["billed"] == 1000.0
    assert grand["outstanding"] == 1000.0


def test_totals_multiple_clients_and_payments(tmp_path):
    store = _store(tmp_path)
    acme = _client(store, "Acme Widgets")
    globex = _client(store, "Globex Corp")

    inv1 = Invoice(client_id=acme.id, amount=1000.0, due_date=date(2026, 11, 15))
    inv1.add_payment(Payment(amount=400.0, date=date(2026, 11, 1)))
    store.add_invoice(inv1)

    inv2 = Invoice(client_id=acme.id, amount=500.0, due_date=date(2026, 12, 1))
    store.add_invoice(inv2)

    inv3 = Invoice(client_id=globex.id, amount=2000.0, due_date=date(2026, 10, 1))
    inv3.add_payment(Payment(amount=2000.0, date=date(2026, 10, 5)))
    store.add_invoice(inv3)

    rows, grand = store.totals_by_client()
    by_name = {r["client_name"]: r for r in rows}
    assert by_name["Acme Widgets"]["billed"] == 1500.0
    assert by_name["Acme Widgets"]["paid"] == 400.0
    assert by_name["Acme Widgets"]["outstanding"] == 1100.0
    assert by_name["Globex Corp"]["billed"] == 2000.0
    assert by_name["Globex Corp"]["paid"] == 2000.0
    assert by_name["Globex Corp"]["outstanding"] == 0.0
    assert grand["billed"] == 3500.0
    assert grand["paid"] == 2400.0
    assert grand["outstanding"] == 1100.0


def test_overdue_date_math(tmp_path):
    store = _store(tmp_path)
    client = _client(store, "Acme Widgets")
    overdue_inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 10, 1))
    open_inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 12, 1))
    paid_inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 9, 1))
    paid_inv.add_payment(Payment(amount=100.0, date=date(2026, 9, 10)))
    store.add_invoice(overdue_inv)
    store.add_invoice(open_inv)
    store.add_invoice(paid_inv)

    today = date(2026, 10, 5)
    assert overdue_inv.is_overdue(as_of=today) is True
    assert overdue_inv.days_overdue(as_of=today) == 4
    assert open_inv.is_overdue(as_of=today) is False
    assert paid_inv.is_overdue(as_of=today) is False
    assert paid_inv.days_overdue(as_of=today) == 0

    overdue_rows = [i for i in store.list_invoices() if not i.is_paid() and i.is_overdue(as_of=today)]
    assert len(overdue_rows) == 1
    assert overdue_rows[0].id == overdue_inv.id