"""
fms/dates.py
============
Filtering datetime columns by local calendar day.

Django's ``__date`` lookup converts each stored UTC value to the local time
zone inside MySQL with CONVERT_TZ(), which needs MySQL's time-zone tables.
Those are not loaded on a default install, so the lookup silently matches
nothing. Instead, each local day is turned into an exact [start, next start)
range in Python and compared against the raw column, which works everywhere
and can use an index.
"""

from datetime import date, datetime, time, timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError


def day_start(day):
    """Midnight at the start of ``day`` in the current (local) time zone."""
    return timezone.make_aware(datetime.combine(day, time.min))


def day_range_filter(field, start=None, end=None):
    """
    Filter kwargs for ``field`` falling on local days ``start``..``end``
    (both inclusive, either may be None).
    """
    lookups = {}
    if start is not None:
        lookups[f"{field}__gte"] = day_start(start)
    if end is not None:
        lookups[f"{field}__lt"] = day_start(end + timedelta(days=1))
    return lookups


def parse_day_param(params, name):
    """Reads an optional YYYY-MM-DD query parameter; 400 if it is malformed."""
    value = params.get(name)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({name: f"{name} must be a date in YYYY-MM-DD format."})
