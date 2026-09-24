from datetime import date, datetime, time, timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError


def day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def day_range_filter(field, start=None, end=None):
    lookups = {}
    if start is not None:
        lookups[f"{field}__gte"] = day_start(start)
    if end is not None:
        lookups[f"{field}__lt"] = day_start(end + timedelta(days=1))
    return lookups


def parse_day_param(params, name):
    value = params.get(name)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({name: f"{name} must be a date in YYYY-MM-DD format."})
