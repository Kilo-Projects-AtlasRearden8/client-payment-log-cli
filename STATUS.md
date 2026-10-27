# STATUS.md

## What was built

**payment-log** — an installable, local-first Python CLI for freelancers and small businesses to log client payments, track overdue invoices, and export CSV or PDF summaries. Built by Asdale Dynamics, LLC as a small-business/author tool. All data and computation runs on the machine: no network calls, no accounts, no API keys, no telemetry, and no personal data ever leaves the computer.

Features:

- **`add-client`** — create a client record with name, email, and notes
- **`add-invoice`** — log a new invoice for a client with amount, due date, and description
- **`record-payment`** — record a payment against an invoice with date, method, and notes
- **`list-invoices`** — list all invoices with billed, paid, outstanding amounts and status (open/overdue/paid)
- **`overdue`** — list overdue invoices with days overdue, filtered to unpaid invoices past their due date
- **`totals`** — show billed, paid, and outstanding totals per client, plus a grand total row; supports `--client` filter
- **`export-csv`** — export all invoices to CSV with full detail rows (invoice_id, client, amount, due, paid, outstanding, status, days_overdue)
- **`export-pdf`** — export a printable PDF summary with invoice table and client totals table

Data stored locally in `~/.payment_log/payment_log.json` (single JSON file). Move it, back it up, or delete it — nothing phones home.

## Layout

```
payment_log/          package (models, storage, export, CLI)
tests/                pytest suite (25 tests covering models, storage, totals, date math, export, CLI)
pyproject.toml        packaging + entry point (payment-log)
LICENSE               MIT, Copyright (c) 2026 Asdale Dynamics, LLC
README.md             usage guide and plain-English overview
STATUS.md             this file
```

## How to run

```bash
pip install .                   # or: pip install -e . for development
payment-log --help
payment-log add-client "Acme Widgets" --email billing@acme.example
payment-log add-invoice "Acme Widgets" 1250.00 --due 2026-11-15 --description "retainer"
payment-log record-payment inv-1 500.00 --date 2026-11-01 --method check
payment-log list-invoices
payment-log overdue
payment-log totals
payment-log totals --client "Acme Widgets"
payment-log export-csv payments.csv
payment-log export-pdf payments.pdf
python -m payment_log            # module entry also works
pytest                           # run the test suite
```

## Verification results

- `python3 -m pytest -v` → **25 passed** (unit tests for every module: models, storage, totals, date math, export, CLI; end-to-end CLI tests via the argument parser, including error paths)
- Console script `payment-log` verified installed via `pip install -e .`; exercised all 8 commands (`add-client`, `add-invoice`, `record-payment`, `list-invoices`, `overdue`, `totals`, `export-csv`, `export-pdf`) plus `--version`, `--help`, and module entry `python -m payment_log`
- Error paths verified: unknown client/invoice returns exit code 2 with a readable message on stderr; duplicate client rejected
- Data persistence verified: store survives process restarts via JSON file at `~/.payment_log/payment_log.json`
- CSV export verified: headers and rows correct, includes all computed fields
- PDF export verified: generates valid PDF with invoice table and client totals table using reportlab

Example run:
```
$ payment-log add-client "Acme Widgets" --email billing@acme.example
client added: Acme Widgets (id: Acme Widgets)

$ payment-log add-invoice "Acme Widgets" 1250.00 --due 2026-11-15 --description "October retainer"
invoice inv-1 for Acme Widgets: $1,250.00 due 2026-11-15

$ payment-log record-payment inv-1 500.00 --date 2026-11-01 --method check
recorded $500.00 on 2026-11-01 for invoice inv-1 (Acme Widgets); outstanding: $750.00

$ payment-log list-invoices
id     client        amount     due         paid     outstanding  status  days overdue
-----  ------------  ---------  ----------  -------  -----------  ------  ------------
inv-1  Acme Widgets  $1,250.00  2026-11-15  $500.00  $750.00      open    0

$ payment-log overdue
no overdue invoices.

$ payment-log totals
client        invoices  billed     paid     outstanding  overdue
------------  --------  ---------  -------  -----------  -------
Acme Widgets  1         $1,250.00  $500.00  $750.00      0

grand total: $1,250.00 billed, $500.00 paid, $750.00 outstanding across 1 invoice(s)
```

## Known gaps

- No invoice editing or deletion (only append-only add/record)
- No multi-currency support (all amounts in USD implicitly)
- No recurring invoice templates or scheduled invoices
- No tax calculation or line-item detail on invoices
- PDF export uses reportlab (extra dependency); could be made optional or use pure-stdlib fallback
- No automatic backup or versioning of the data file
- No configuration file (data directory is hardcoded to `~/.payment_log/`)
- The `days overdue` column shows 0 for non-overdue invoices rather than a dash/blank
- No import functionality (e.g., from CSV or other bookkeeping tools)
- No balance-forward or statement generation for a date range