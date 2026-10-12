"""
The sales report's rows, shared by the on-screen preview and the PDF / Excel
downloads.

The report is built once by build_report(); the JSON preview and both
file formats render that same dict, so what is downloaded is always exactly
what was shown for the same date range.
"""

from datetime import date
from decimal import Decimal
from io import BytesIO

from django.utils import timezone

from fms.dates import day_range_filter
from sales.models import SaleItem

COMPANY_NAME = "Factory Management System"


def _local_day(value):
    return timezone.localtime(value).date()


def _sales(start, end):
    items = (
        SaleItem.objects.filter(**day_range_filter("sale__sale_date", start, end))
        .select_related("sale", "product")
        .order_by("sale__sale_date", "sale_id", "id")
    )
    rows = [
        [
            _local_day(item.sale.sale_date),
            item.sale.invoice_number,
            item.sale.sold_to,
            item.product.product_name,
            item.product.sku,
            item.quantity,
            item.unit_price,
            item.subtotal,
        ]
        for item in items
    ]
    return {
        "title": "Sales Report",
        "columns": [
            ("Sale Date", "date"),
            ("Invoice", "text"),
            ("Customer", "text"),
            ("Product", "text"),
            ("SKU", "text"),
            ("Quantity", "int"),
            ("Unit Price", "money"),
            ("Subtotal", "money"),
        ],
        "rows": rows,
        "summary": [
            ("Invoices", len({row[1] for row in rows}), "int"),
            ("Items sold", sum(row[5] for row in rows), "int"),
            ("Total revenue", sum((row[7] for row in rows), Decimal("0")), "money"),
        ],
        "note": "One row per invoice line, by sale date.",
    }


def build_report(start, end):
    report = _sales(start, end)
    report.update(
        start_date=start,
        end_date=end,
        generated_at=timezone.localtime(),
    )
    return report


def filename(report, extension):
    title = report["title"].replace(" ", "_")
    return f"{title}_{report['start_date']}_to_{report['end_date']}.{extension}"


def _text(value, kind):
    if value is None or value == "":
        return "—"
    if kind == "money":
        return f"Rs {value:,.2f}"
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    if isinstance(value, date):
        return value.isoformat()
    return value


def as_json(report):
    return {
        "title": report["title"],
        "start_date": report["start_date"].isoformat(),
        "end_date": report["end_date"].isoformat(),
        "generated_at": report["generated_at"].isoformat(),
        "note": report["note"],
        "columns": [{"label": label, "type": kind} for label, kind in report["columns"]],
        "rows": [[_json_value(value) for value in row] for row in report["rows"]],
        "summary": [
            {"label": label, "value": _json_value(value), "type": kind}
            for label, value, kind in report["summary"]
        ],
    }


def as_xlsx(report):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    formats = {"money": '"Rs" #,##0.00', "date": "yyyy-mm-dd", "int": "#,##0"}
    bold = Font(bold=True)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = report["title"][:31]
    sheet.append([f"{COMPANY_NAME} — {report['title']}"])
    sheet["A1"].font = Font(bold=True, size=14)
    sheet.append([f"Period: {report['start_date']} to {report['end_date']}"])
    sheet.append([f"Generated: {report['generated_at']:%Y-%m-%d %H:%M}"])
    sheet.append([report["note"]])
    sheet.append([])

    for label, value, kind in report["summary"]:
        sheet.append([label, value])
        sheet.cell(sheet.max_row, 1).font = bold
        sheet.cell(sheet.max_row, 2).number_format = formats[kind]
    sheet.append([])

    sheet.append([label for label, _ in report["columns"]])
    header_row = sheet.max_row
    for cell in sheet[header_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="343A40")
    if not report["rows"]:
        sheet.append(["No records found for the selected date range."])
    for row in report["rows"]:
        sheet.append(row)
        for cell, (_, kind) in zip(sheet[sheet.max_row], report["columns"]):
            if kind in formats:
                cell.number_format = formats[kind]
    sheet.freeze_panes = sheet.cell(header_row + 1, 1)

    for index, (label, _) in enumerate(report["columns"], start=1):
        widest = max([len(label)] + [len(_text(r[index - 1], "")) for r in report["rows"]])
        sheet.column_dimensions[get_column_letter(index)].width = min(widest + 4, 45)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def as_pdf(report):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"].clone("cell", fontSize=8, leading=10)
    header_fill = colors.HexColor("#343A40")
    grid = colors.HexColor("#DEE2E6")

    def page_number(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin, 10 * mm, f"Page {doc.page}"
        )
        canvas.drawString(doc.leftMargin, 10 * mm, f"{COMPANY_NAME} — {report['title']}")

    story = [
        Paragraph(COMPANY_NAME, styles["Title"]),
        Paragraph(report["title"], styles["Heading2"]),
        Paragraph(
            f"Period: <b>{report['start_date']}</b> to <b>{report['end_date']}</b>"
            f" &nbsp;·&nbsp; Generated: {report['generated_at']:%Y-%m-%d %H:%M}",
            styles["Normal"],
        ),
        Paragraph(report["note"], styles["Italic"]),
        Spacer(1, 6 * mm),
    ]

    summary = Table(
        [[label, _text(value, kind)] for label, value, kind in report["summary"]],
        hAlign="LEFT",
    )
    summary.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, grid),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]
        )
    )
    story += [summary, Spacer(1, 6 * mm)]

    if report["rows"]:
        numeric = [i for i, (_, kind) in enumerate(report["columns"]) if kind in ("money", "int")]
        data = [[label for label, _ in report["columns"]]] + [
            [
                Paragraph(_text(value, kind), cell_style) if kind == "text" else _text(value, kind)
                for value, (_, kind) in zip(row, report["columns"])
            ]
            for row in report["rows"]
        ]
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), header_fill),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, grid),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
                ]
                + [("ALIGN", (i, 0), (i, -1), "RIGHT") for i in numeric]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No records found for the selected date range.", styles["Normal"]))

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        title=f"{report['title']} {report['start_date']} to {report['end_date']}",
        author=COMPANY_NAME,
        bottomMargin=18 * mm,
    ).build(story, onFirstPage=page_number, onLaterPages=page_number)
    return buffer.getvalue()
