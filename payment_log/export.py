"""CSV and PDF export for invoice data."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

from .storage import Store


def export_csv(store: Store, path: str | Path) -> list[dict[str, Any]]:
    """Write all invoice rows to a CSV file and return the rows."""
    rows = store.all_rows()
    fieldnames = [
        "invoice_id",
        "client_name",
        "client_email",
        "amount",
        "due_date",
        "description",
        "paid",
        "outstanding",
        "status",
        "days_overdue",
    ]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return rows


def export_pdf(store: Store, path: str | Path) -> list[dict[str, Any]]:
    """Write a printable PDF summary of all invoices and return the rows."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    rows = store.all_rows()
    totals_rows, grand = store.totals_by_client()

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    sub_style = styles["Normal"]

    elements: list[Any] = []
    elements.append(Paragraph("Client Payment Summary", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Generated locally by payment-log (Asdale Dynamics, LLC). "
        "All figures computed on your machine; no data leaves your computer.",
        sub_style,
    ))
    elements.append(Spacer(1, 12))

    if rows:
        header = [
            "Invoice",
            "Client",
            "Amount",
            "Due",
            "Paid",
            "Outstanding",
            "Status",
        ]
        data = [header]
        for r in rows:
            data.append(
                [
                    r["invoice_id"],
                    r["client_name"],
                    f"${r['amount']:,.2f}",
                    r["due_date"],
                    f"${r['paid']:,.2f}",
                    f"${r['outstanding']:,.2f}",
                    r["status"],
                ]
            )
        table = Table(data, colWidths=[0.85 * inch, 1.7 * inch, 0.85 * inch, 0.8 * inch, 0.8 * inch, 0.95 * inch, 0.85 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f7")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c4d0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Client totals
    elements.append(Paragraph("Totals by Client", styles["Heading2"]))
    elements.append(Spacer(1, 6))
    cheader = ["Client", "Invoices", "Billed", "Paid", "Outstanding", "Overdue"]
    cdata = [cheader]
    for r in totals_rows:
        cdata.append(
            [
                r["client_name"],
                str(r["invoice_count"]),
                f"${r['billed']:,.2f}",
                f"${r['paid']:,.2f}",
                f"${r['outstanding']:,.2f}",
                str(r["overdue_count"]),
            ]
        )
    cdata.append(
        [
            grand["client_name"],
            str(grand["invoice_count"]),
            f"${grand['billed']:,.2f}",
            f"${grand['paid']:,.2f}",
            f"${grand['outstanding']:,.2f}",
            str(grand["overdue_count"]),
        ]
    )
    ctable = Table(
        cdata,
        colWidths=[2.2 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch, 1.0 * inch, 0.8 * inch],
    )
    ctable.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#eef2f7")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d7dee9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c4d0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(ctable)

    from reportlab.platypus import SimpleDocTemplate

    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                            title="Client Payment Summary",
                            author="Asdale Dynamics, LLC")
    doc.build(elements)
    return rows
