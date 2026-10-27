"""Tests for the JSON store (CRUD, persistence, payment recording)."""

from datetime import date

from payment_log.models import Client, Invoice, Payment
from payment_log.storage import Store


def _store(tmp_path):
    return Store(path=tmp_path / "payment_log.json")


def test_add_and_list_client(tmp_path):
    store = _store(tmp_path)
    client = Client(name="Acme Widgets", email="billing@acme.example", notes="net 15")
    store.add_client(client)
    assert store.get_client(client.id) is not None
    names = [c.name for c in store.list_clients()]
    assert names == ["Acme Widgets"]


def test_duplicate_client_rejected(tmp_path):
    store = _store(tmp_path)
    store.add_client(Client(name="Acme Widgets"))
    try:
        store.add_client(Client(name="Acme Widgets"))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for duplicate client")


def test_find_client_by_name(tmp_path):
    store = _store(tmp_path)
    store.add_client(Client(name="Acme Widgets"))
    assert store.find_client_by_name("acme widgets") is not None
    assert store.find_client_by_name("Nobody") is None


def test_add_invoice_requires_known_client(tmp_path):
    store = _store(tmp_path)
    inv = Invoice(client_id="nope", amount=50.0, due_date=date(2026, 11, 1))
    try:
        store.add_invoice(inv)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown client")


def test_record_payment_updates_invoice(tmp_path):
    store = _store(tmp_path)
    client = Client(name="Acme Widgets")
    store.add_client(client)
    inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 11, 1))
    store.add_invoice(inv)
    store.record_payment("inv-1", Payment(amount=30.0, date=date(2026, 10, 20)))
    got = store.get_invoice("inv-1")
    assert got is not None
    assert got.paid_total() == 30.0
    assert got.outstanding() == 70.0


def test_all_rows_contains_computed_fields(tmp_path):
    store = _store(tmp_path)
    client = Client(name="Acme Widgets", email="billing@acme.example")
    store.add_client(client)
    inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 11, 15), description="retainer")
    inv.add_payment(Payment(amount=40.0, date=date(2026, 11, 1)))
    store.add_invoice(inv)
    rows = store.all_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["invoice_id"] == "inv-1"
    assert row["client_name"] == "Acme Widgets"
    assert row["client_email"] == "billing@acme.example"
    assert row["amount"] == 100.0
    assert row["paid"] == 40.0
    assert row["outstanding"] == 60.0
    assert row["status"] == "open"
    assert row["days_overdue"] >= 0