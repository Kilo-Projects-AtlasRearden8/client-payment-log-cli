# payment-log

Local-first CLI for freelancers and small businesses: log client payments,
track overdue invoices, and export CSV or PDF summaries. Everything computes
on your machine: no accounts, no network calls, no API keys, no telemetry,
and no personal data ever leaves your computer.

Built by [Asdale Dynamics, LLC](https://dylanasdale.github.io) — beginner
friendly AI education, books, and practical small-business tools, in plain
English, step by step, never condescending. Dylan Asdale is a registered
nurse turned AI author and founder of Asdale Dynamics, LLC (Indiana, formed
October 2026). His book *The Massive AI Manual* and hub site
dylanasdale.github.io explain AI "like a friend would."

This is a bookkeeping helper, not accounting software or tax advice. Reconcile
its figures against your bank records and your accountant before filing.

## Install

Requires Python 3.9+.

```bash
pip install .
```

For development:

```bash
pip install -e .
pip install pytest
```

## Quick start

```bash
# Add a client
payment-log add-client "Acme Widgets" --email billing@acme.example --notes "Net 15 terms"

# Log an invoice
payment-log add-invoice "Acme Widgets" --amount 1250.00 --due 2026-11-15 --description "October retainer"

# Record a partial payment
payment-log record-payment <invoice-id> --amount 500.00 --date 2026-11-01 --method check

# See every invoice with payment totals and status
payment-log list-invoices

# See only overdue invoices, with days overdue
payment-log overdue

# Totals per client (billed / paid / outstanding) plus a grand total
payment-log totals
payment-log totals --client "Acme Widgets"

# Export everything to CSV or PDF
payment-log export-csv payments.csv
payment-log export-pdf payments.pdf
```

Run `payment-log <command> --help` for every option.

## Commands

| Command       | What it does                                              |
| ------------- | --------------------------------------------------------- |
| `add-client`  | Create a client record (name, email, notes)               |
| `add-invoice` | Log a new invoice for a client with amount and due date   |
| `record-payment` | Record a payment against an invoice (date, method, notes) |
| `list-invoices` | List invoices with paid/outstanding amounts and status   |
| `overdue`     | List overdue invoices with days overdue                   |
| `totals`      | Billed, paid, and outstanding per client, plus grand total |
| `export-csv`  | Export all invoices to CSV                                |
| `export-pdf`  | Export all invoices to a printable PDF summary            |

## Data, stored locally

Your client list, invoices, and payments live in one JSON file at
`~/.payment_log/payment_log.json`. Move it, back it up, or delete it —
nothing phones home and nothing is stored in the cloud.

## Testing

```bash
pytest
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.
