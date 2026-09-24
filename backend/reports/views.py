"""
reports/views.py
================
Read-only reporting endpoints. The app owns no models — it rolls up rows that
live in sales/ and inventory/.

Everything a report page needs comes back in one response, computed on the
server, so the figures on a chart, a headline tile and the product breakdown
can never disagree with each other the way three separate client-side
aggregations can.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdminOrInventoryManager
from fms.dates import day_range_filter
from sales.models import Sale

# A report spanning more days than this would render an unreadable axis and a
# needlessly large payload; the range is clamped and the response says so.
MAX_DAYS = 180

DEFAULT_WINDOW_DAYS = 7


def _parse_day(value, field):
    """Parses an ISO date query parameter, or raises a message for the caller."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be a date in YYYY-MM-DD format.")


def _money(value):
    """Two-decimal string, the same shape DRF gives a DecimalField."""
    return str(Decimal(value).quantize(Decimal("0.01")))


@api_view(["GET"])
@permission_classes([IsAdminOrInventoryManager])
def sales_report(request):
    """
    Sales report for a date range.

    Admin and manager both generate this; employees are refused by
    the permission class. Query parameters ``start_date`` and ``end_date``
    (YYYY-MM-DD) are both optional — with neither, the report covers the last
    seven days, matching the dashboard.
    """
    today = timezone.localdate()

    try:
        start = _parse_day(request.query_params.get("start_date"), "start_date")
        end = _parse_day(request.query_params.get("end_date"), "end_date")
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if start is None and end is None:
        start = today - timedelta(days=DEFAULT_WINDOW_DAYS - 1)
    if end is None:
        end = today
    if start is None:
        # Half-open range: fall back to the earliest sale on record, or the
        # end date itself when there are no sales at all.
        earliest = Sale.objects.order_by("sale_date").values_list(
            "sale_date", flat=True
        ).first()
        start = timezone.localtime(earliest).date() if earliest else end

    if start > end:
        return Response(
            {"detail": "start_date cannot be after end_date."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    truncated = False
    if (end - start).days + 1 > MAX_DAYS:
        end = start + timedelta(days=MAX_DAYS - 1)
        truncated = True

    sales = (
        Sale.objects.filter(**day_range_filter("sale_date", start, end))
        .prefetch_related("items__product")
        .order_by("sale_date")
    )

    # One dense bucket per day, so a day with no sales still reports a zero
    # rather than dropping out of the series and distorting the trend.
    buckets = {}
    cursor = start
    while cursor <= end:
        buckets[cursor] = {"revenue": Decimal("0"), "count": 0}
        cursor += timedelta(days=1)

    products = {}
    items_sold = 0
    revenue = Decimal("0")
    sales_count = 0

    for sale in sales:
        day = timezone.localtime(sale.sale_date).date()
        bucket = buckets.get(day)
        if bucket is None:  # pragma: no cover — the filter already bounds this
            continue

        bucket["revenue"] += sale.total_amount
        bucket["count"] += 1
        revenue += sale.total_amount
        sales_count += 1

        for item in sale.items.all():
            entry = products.setdefault(
                item.product_id,
                {
                    "product_id": item.product_id,
                    "product_name": item.product.product_name,
                    "sku": item.product.sku,
                    "quantity": 0,
                    "revenue": Decimal("0"),
                },
            )
            entry["quantity"] += item.quantity
            entry["revenue"] += item.subtotal
            items_sold += item.quantity

    days = [
        {
            "day": day.isoformat(),
            "revenue": _money(values["revenue"]),
            "count": values["count"],
        }
        for day, values in sorted(buckets.items())
    ]

    # The extremes look only at days that had a sale: over a long range most
    # empty days are days the factory was simply closed, and a minimum of zero
    # would say nothing.
    active = [
        (day, values) for day, values in sorted(buckets.items()) if values["count"]
    ]

    def _extreme(key, pick):
        if not active:
            return None
        day, values = pick(active, key=lambda entry: entry[1][key])
        return {
            "day": day.isoformat(),
            "count": values["count"],
            "revenue": _money(values["revenue"]),
        }

    day_count = len(days)

    return Response(
        {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "truncated": truncated,
            "totals": {
                "sales_count": sales_count,
                "revenue": _money(revenue),
                "items_sold": items_sold,
                "days": day_count,
                "selling_days": len(active),
                "average_daily_revenue": _money(
                    revenue / day_count if day_count else Decimal("0")
                ),
            },
            "busiest_day": _extreme("count", max),
            "quietest_day": _extreme("count", min),
            "best_revenue_day": _extreme("revenue", max),
            "days_series": days,
            "products": sorted(
                (
                    {**entry, "revenue": _money(entry["revenue"])}
                    for entry in products.values()
                ),
                key=lambda entry: entry["quantity"],
                reverse=True,
            ),
        }
    )
