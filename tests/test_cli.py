"""End-to-end CLI tests via the argument parser."""

from datetime import date

from payment_log.cli import main


def test_add_client_and_list_invoices(tmp_path, monkeypatch):
    import payment_log.storage as storage
    storage.DATA_FILE = tmp_path / "payment_log.json"
    storage.DATA_DIR = tmp_path

    rc = main(["add-client", "Acme Widgets", "--email", "b@a.example", "--notes", "net 15"])
    assert rc == 0

    rc = main(["add-invoice", "Acme Widgets", "1250.00", "--due", "2026-11-15", "--description", "retainer"])
    assert rc == 0

    rc = main(["record-payment", "inv-1", "500.00", "--date", "2026-11-01", "--method", "check"])
    assert rc == 0

    rc = main(["list-invoices"])
    assert rc == 0


def test_overdue_and_totals(tmp_path, monkeypatch):
    import payment_log.storage as storage
    storage.DATA_FILE = tmp_path / "payment_log.json"
    storage.DATA_DIR = tmp_path

    from payment_log.models import Client, Invoice
    from payment_log.storage import Store
    store = Store()
    client = Client(name="Acme Widgets")
    store.add_client(client)
    inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 10, 1))
    store.add_invoice(inv)

    rc = main(["overdue"])
    assert rc == 0

    rc = main(["totals"])
    assert rc == 0

    rc = main(["totals", "--client", "Acme Widgets"])
    assert rc == 0


def test_export_csv_and_pdf(tmp_path, monkeypatch):
    import payment_log.storage as storage
    storage.DATA_FILE = tmp_path / "payment_log.json"
    storage.DATA_DIR = tmp_path

    from payment_log.models import Client, Invoice
    from payment_log.storage import Store
    store = Store()
    client = Client(name="Acme Widgets")
    store.add_client(client)
    inv = Invoice(client_id=client.id, amount=100.0, due_date=date(2026, 11, 1))
    store.add_invoice(inv)

    rc = main(["export-csv", str(tmp_path / "out.csv")])
    assert rc == 0
    assert (tmp_path / "out.csv").exists()

    rc = main(["export-pdf", str(tmp_path / "out.pdf")])
    assert rc == 0
    assert (tmp_path / "out.pdf").exists()


def test_unknown_client_errors(tmp_path, monkeypatch):
    import payment_log.storage as storage
    storage.DATA_FILE = tmp_path / "payment_log.json"
    storage.DATA_DIR = tmp_path

    rc = main(["add-invoice", "Nobody", "50.00", "--due", "2026-11-01"])
    assert rc == 2