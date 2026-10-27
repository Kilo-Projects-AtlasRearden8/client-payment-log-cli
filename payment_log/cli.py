"""Command-line interface for payment-log."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Sequence

from .export import export_csv, export_pdf
from .models import Client, Invoice, Payment
from .storage import Store

PROGRAM = "payment-log"
VERSION = "0.1.0"


def money(value: float) -> str:
    return f"${value:,.2f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "Log client payments, track overdue invoices, and export CSV or "
            "PDF summaries. All data stays on your machine."
        ),
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-client", help="create a client record")
    p.add_argument("name", help="client name")
    p.add_argument("--email", default="", help="client email address")
    p.add_argument("--notes", default="", help="notes about the client")
    p.set_defaults(func=cmd_add_client)

    p = sub.add_parser("add-invoice", help="log a new invoice for a client")
    p.add_argument("client", help="client name")
    p.add_argument("amount", type=float, help="invoice amount")
    p.add_argument("--due", required=True, help="due date (YYYY-MM-DD)")
    p.add_argument("--description", default="", help="invoice description")
    p.set_defaults(func=cmd_add_invoice)

    p = sub.add_parser("record-payment", help="record a payment against an invoice")
    p.add_argument("invoice", help="invoice id")
    p.add_argument("amount", type=float, help="payment amount")
    p.add_argument("--date", default=None, help="payment date (YYYY-MM-DD; defaults to today)")
    p.add_argument("--method", default="", help="payment method (check, transfer, etc.)")
    p.add_argument("--notes", default="", help="payment notes")
    p.set_defaults(func=cmd_record_payment)

    p = sub.add_parser("list-invoices", help="list invoices with totals and status")
    p.add_argument("--client", default=None, help="filter to this client name")
    p.set_defaults(func=cmd_list_invoices)

    p = sub.add_parser("overdue", help="list overdue invoices with days overdue")
    p.set_defaults(func=cmd_overdue)

    p = sub.add_parser("totals", help="billed / paid / outstanding per client")
    p.add_argument("--client", default=None, help="show only this client")
    p.set_defaults(func=cmd_totals)

    p = sub.add_parser("export-csv", help="export all invoices to CSV")
    p.add_argument("path", help="output CSV path")
    p.set_defaults(func=cmd_export_csv)

    p = sub.add_parser("export-pdf", help="export all invoices to a PDF summary")
    p.add_argument("path", help="output PDF path")
    p.set_defaults(func=cmd_export_pdf)

    return parser


def _parse_date(value: str, what: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid {what} date: {value!r} (use YYYY-MM-DD)")


def cmd_add_client(args) -> None:
    store = Store()
    if store.client_exists(args.name):
        raise ValueError(f"client already exists: {args.name}")
    client = Client(name=args.name, email=args.email, notes=args.notes)
    store.add_client(client)
    print(f"client added: {client.name} (id: {client.id})")


def cmd_add_invoice(args) -> None:
    store = Store()
    client = store.find_client_by_name(args.client)
    if client is None:
        raise ValueError(f"unknown client: {args.client}")
    due = _parse_date(args.due, "due")
    invoice = Invoice(
        client_id=client.id,
        amount=args.amount,
        due_date=due,
        description=args.description,
    )
    store.add_invoice(invoice)
    print(
        f"invoice {invoice.id} for {client.name}: {money(args.amount)} due {due.isoformat()}"
    )


def cmd_record_payment(args) -> None:
    store = Store()
    inv = store.get_invoice(args.invoice)
    if inv is None:
        raise ValueError(f"unknown invoice: {args.invoice}")
    pay_date = _parse_date(args.date, "payment") if args.date else date.today()
    payment = Payment(amount=args.amount, date=pay_date, method=args.method, notes=args.notes)
    store.record_payment(args.invoice, payment)
    client = store.get_client(inv.client_id)
    print(
        f"recorded {money(args.amount)} on {pay_date.isoformat()} for invoice {args.invoice} "
        f"({client.name if client else inv.client_id}); outstanding: {money(inv.outstanding() - args.amount)}"
    )


def _format_row(store: Store, inv_id: str) -> list[str] | None:
    inv = store.get_invoice(inv_id)
    if inv is None:
        return None
    client = store.get_client(inv.client_id)
    return [
        inv.id,
        client.name if client else inv.client_id,
        money(inv.amount),
        inv.due_date.isoformat(),
        money(inv.paid_total()),
        money(inv.outstanding()),
        "paid" if inv.is_paid() else ("overdue" if inv.is_overdue() else "open"),
        str(inv.days_overdue()),
    ]


def cmd_list_invoices(args) -> None:
    store = Store()
    rows: list[list[str]] = []
    for inv in store.list_invoices():
        if args.client is not None:
            client = store.get_client(inv.client_id)
            if client is None or client.name.lower() != args.client.lower():
                continue
        row = _format_row(store, inv.id)
        if row:
            rows.append(row)
    if not rows:
        print("no invoices found.")
        return
    headers = ["id", "client", "amount", "due", "paid", "outstanding", "status", "days overdue"]
    _print_table(headers, rows)


def cmd_overdue(args) -> None:
    store = Store()
    today = date.today()
    rows: list[list[str]] = []
    for inv in store.list_invoices():
        if inv.is_paid():
            continue
        if today > inv.due_date:
            row = _format_row(store, inv.id)
            if row:
                rows.append(row)
    if not rows:
        print("no overdue invoices.")
        return
    headers = ["id", "client", "amount", "due", "paid", "outstanding", "status", "days overdue"]
    print(f"overdue as of {today.isoformat()}:")
    _print_table(headers, rows)


def cmd_totals(args) -> None:
    store = Store()
    totals_rows, grand = store.totals_by_client()
    rows: list[list[str]] = []
    for r in totals_rows:
        if args.client is not None and r["client_name"].lower() != args.client.lower():
            continue
        rows.append(
            [
                r["client_name"],
                str(r["invoice_count"]),
                money(r["billed"]),
                money(r["paid"]),
                money(r["outstanding"]),
                str(r["overdue_count"]),
            ]
        )
    if not rows:
        print("no invoices found.")
        return
    headers = ["client", "invoices", "billed", "paid", "outstanding", "overdue"]
    _print_table(headers, rows)
    print()
    print(
        f"grand total: {money(grand['billed'])} billed, {money(grand['paid'])} paid, "
        f"{money(grand['outstanding'])} outstanding across {grand['invoice_count']} invoice(s)"
    )


def cmd_export_csv(args) -> None:
    store = Store()
    rows = export_csv(store, args.path)
    print(f"exported {len(rows)} invoice(s) to {args.path}")


def cmd_export_pdf(args) -> None:
    store = Store()
    rows = export_pdf(store, args.path)
    print(f"exported {len(rows)} invoice(s) to {args.path}")


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
