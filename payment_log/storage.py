"""JSON-backed local storage for clients, invoices, and payments."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import Client, Invoice, Payment

DATA_DIR = Path.home() / ".payment_log"
DATA_FILE = DATA_DIR / "payment_log.json"


def _serialize_date(d) -> str:
    return d.isoformat()


def _deserialize_date(value: str):
    from datetime import date

    return date.fromisoformat(value)


def _client_to_dict(client: Client) -> dict[str, Any]:
    return {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "notes": client.notes,
    }


def _client_from_dict(data: dict[str, Any]) -> Client:
    return Client(
        id=data.get("id") or data["name"],
        name=data["name"],
        email=data.get("email", ""),
        notes=data.get("notes", ""),
    )


def _payment_to_dict(payment: Payment) -> dict[str, Any]:
    return {
        "id": payment.id,
        "amount": payment.amount,
        "date": _serialize_date(payment.date),
        "method": payment.method,
        "notes": payment.notes,
    }


def _payment_from_dict(data: dict[str, Any]) -> Payment:
    return Payment(
        id=data.get("id"),
        amount=data["amount"],
        date=_deserialize_date(data["date"]),
        method=data.get("method", ""),
        notes=data.get("notes", ""),
    )


def _invoice_to_dict(invoice: Invoice) -> dict[str, Any]:
    return {
        "id": invoice.id,
        "client_id": invoice.client_id,
        "amount": invoice.amount,
        "due_date": _serialize_date(invoice.due_date),
        "description": invoice.description,
        "payments": [_payment_to_dict(p) for p in invoice.payments],
    }


def _invoice_from_dict(data: dict[str, Any]) -> Invoice:
    inv = Invoice(
        id=data.get("id"),
        client_id=data["client_id"],
        amount=data["amount"],
        due_date=_deserialize_date(data["due_date"]),
        description=data.get("description", ""),
    )
    for pdata in data.get("payments", []):
        inv.add_payment(_payment_from_dict(pdata))
    return inv


def _load_raw() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {"clients": [], "invoices": []}
    try:
        with DATA_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"clients": [], "invoices": []}
    data.setdefault("clients", [])
    data.setdefault("invoices", [])
    return data


def _save_raw(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    os.replace(tmp, DATA_FILE)


class Store:
    """Thread-unsafe local store backed by a single JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DATA_FILE
        self._clients: dict[str, Client] = {}
        self._invoices: dict[str, Invoice] = {}
        self._next_client_id = 1
        self._next_invoice_id = 1
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            self._save()
            return
        for cdata in data.get("clients", []):
            client = _client_from_dict(cdata)
            self._clients[client.id] = client
            self._next_client_id = max(self._next_client_id, _id_num(client.id) + 1)
        for idata in data.get("invoices", []):
            inv = _invoice_from_dict(idata)
            self._invoices[inv.id] = inv
            self._next_invoice_id = max(self._next_invoice_id, _id_num(inv.id) + 1)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "clients": [_client_to_dict(c) for c in self._clients.values()],
            "invoices": [_invoice_to_dict(i) for i in self._invoices.values()],
        }
        tmp = self.path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        os.replace(tmp, self.path)

    # -- clients -----------------------------------------------------
    def add_client(self, client: Client) -> Client:
        if client.id in self._clients:
            raise ValueError(f"client already exists: {client.id}")
        self._clients[client.id] = client
        self._save()
        return client

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)

    def list_clients(self) -> list[Client]:
        return sorted(self._clients.values(), key=lambda c: c.name.lower())

    def client_exists(self, name: str) -> bool:
        return any(c.name.lower() == name.lower() for c in self._clients.values())

    def find_client_by_name(self, name: str) -> Client | None:
        for c in self._clients.values():
            if c.name.lower() == name.lower():
                return c
        return None

    # -- invoices ----------------------------------------------------
    def add_invoice(self, invoice: Invoice) -> Invoice:
        if invoice.id is None:
            invoice.id = f"inv-{self._next_invoice_id}"
            self._next_invoice_id += 1
        if invoice.id in self._invoices:
            raise ValueError(f"invoice already exists: {invoice.id}")
        if invoice.client_id not in self._clients:
            raise ValueError(f"unknown client: {invoice.client_id}")
        self._invoices[invoice.id] = invoice
        self._save()
        return invoice

    def get_invoice(self, invoice_id: str) -> Invoice | None:
        return self._invoices.get(invoice_id)

    def list_invoices(self) -> list[Invoice]:
        return sorted(
            self._invoices.values(),
            key=lambda i: (i.due_date, i.id),
        )

    def invoices_for_client(self, client_id: str) -> list[Invoice]:
        return sorted(
            [i for i in self._invoices.values() if i.client_id == client_id],
            key=lambda i: (i.due_date, i.id),
        )

    def record_payment(self, invoice_id: str, payment: Payment) -> Invoice:
        inv = self.get_invoice(invoice_id)
        if inv is None:
            raise ValueError(f"unknown invoice: {invoice_id}")
        if payment.id is None:
            payment.id = f"pay-{len(inv.payments) + 1}"
        inv.add_payment(payment)
        self._invoices[invoice_id] = inv
        self._save()
        return inv

    # -- aggregates --------------------------------------------------
    def all_rows(self) -> list[dict[str, Any]]:
        """One row per invoice with client name and computed totals."""
        rows: list[dict[str, Any]] = []
        for inv in self.list_invoices():
            client = self._clients.get(inv.client_id)
            rows.append(
                {
                    "invoice_id": inv.id,
                    "client_name": client.name if client else inv.client_id,
                    "client_email": client.email if client else "",
                    "amount": inv.amount,
                    "due_date": inv.due_date.isoformat(),
                    "description": inv.description,
                    "paid": inv.paid_total(),
                    "outstanding": inv.outstanding(),
                    "status": "paid" if inv.is_paid() else ("overdue" if inv.is_overdue() else "open"),
                    "days_overdue": inv.days_overdue(),
                }
            )
        return rows

    def totals_by_client(self) -> list[dict[str, Any]]:
        """Billed / paid / outstanding per client, plus grand total row."""
        client_map: dict[str, dict[str, Any]] = {}
        for inv in self.list_invoices():
            entry = client_map.setdefault(
                inv.client_id,
                {
                    "client_id": inv.client_id,
                    "client_name": self._clients[inv.client_id].name
                    if inv.client_id in self._clients
                    else inv.client_id,
                    "billed": 0.0,
                    "paid": 0.0,
                    "outstanding": 0.0,
                    "invoice_count": 0,
                    "overdue_count": 0,
                },
            )
            entry["billed"] += inv.amount
            entry["paid"] += inv.paid_total()
            entry["outstanding"] += inv.outstanding()
            entry["invoice_count"] += 1
            if inv.is_overdue():
                entry["overdue_count"] += 1
        rows = sorted(client_map.values(), key=lambda r: r["client_name"].lower())
        grand = {
            "client_id": "__grand__",
            "client_name": "TOTAL",
            "billed": sum(r["billed"] for r in rows),
            "paid": sum(r["paid"] for r in rows),
            "outstanding": sum(r["outstanding"] for r in rows),
            "invoice_count": sum(r["invoice_count"] for r in rows),
            "overdue_count": sum(r["overdue_count"] for r in rows),
        }
        return rows, grand


def _id_num(value: str) -> int:
    """Pull the trailing integer from an id like 'inv-42'."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0
