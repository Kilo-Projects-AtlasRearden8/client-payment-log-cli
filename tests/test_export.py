"""Tests for CSV and PDF export."""

import csv
import os
from datetime import date

from payment_log.models import Client, Invoice, Payment
from payment_log.storage import Store
from payment_log.export import export_csv, export_pdf


def _store(tmp_path):
    store = Store(path=tmp_path / "payment_log.json")
    client = Client(name="Acme Widgets", email="billing@acme.example")
    store.add_client(client)
    inv = Invoice(client_id=client.id, amount=1000.0, due_date=date(2026, 11, 15), description="retainer")
    inv.add_payment(Payment(amount=400.0, date=date(2026, 11, 1), method="check"))
    store.add_invoice(inv)
    return store


def test_export_csv_writes_header_and_rows(tmp_path):
    store = _store(tmp_path)
    out = tmp_path / "payments.csv"
    rows = export_csv(store, out)
    assert len(rows) == 1
    assert os.path.exists(out)
    with open(out, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        data = list(reader)
    assert len(data) == 1
    assert data[0]["client_name"] == "Acme Widgets"
    assert data[0]["amount"] == "1000.0"
    assert data[0]["paid"] == "400.0"
    assert data[0]["outstanding"] == "600.0"


def test_export_pdf_creates_file(tmp_path):
    store = _store(tmp_path)
    out = tmp_path / "payments.pdf"
    rows = export_pdf(store, out)
    assert len(rows) == 1
    assert os.path.exists(out)
    assert out.stat().st_size > 0