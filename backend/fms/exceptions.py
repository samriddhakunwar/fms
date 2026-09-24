from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def _describe_protected(exc):
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
