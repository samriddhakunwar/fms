"""
fms/exceptions.py
=================
Project-wide DRF exception handling.

Several models use ``on_delete=models.PROTECT`` to preserve audit trails
(a sold product, an employee with payslips, a user who recorded sales).
Django raises ``ProtectedError`` for those deletes, which DRF does not
know about — it escapes as an unhandled 500 and the UI can only say
"Something went wrong on the server."

This handler turns it into a 409 with a ``detail`` message the frontend
already knows how to display.
"""

from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def _describe_protected(exc):
    """Human-readable summary of the records blocking the delete."""
    objects = list(exc.protected_objects)
    model = objects[0]._meta.verbose_name_plural if objects else "related records"
    return f"{len(objects)} {model}" if objects else str(model)


def fms_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, ProtectedError):
        return Response(
            {
                "detail": (
                    "This record cannot be deleted because it is referenced by "
                    f"{_describe_protected(exc)}. Remove or reassign them first."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    return None
