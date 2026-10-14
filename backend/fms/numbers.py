import uuid


def unique_number(model, field, prefix):
    """A random <prefix>-XXXXXXXXXX not yet used in model.field."""
    for _ in range(5):
        candidate = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
        if not model.objects.filter(**{field: candidate}).exists():
            return candidate
    raise RuntimeError(f"Could not generate a unique {field.replace('_', ' ')}.")
