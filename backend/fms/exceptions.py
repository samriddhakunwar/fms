from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def fms_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None or not isinstance(exc, ProtectedError):
        return response

    objects = list(exc.protected_objects)
    what = f"{len(objects)} {objects[0]._meta.verbose_name_plural}" if objects else "related records"
    return Response(
        {
            "detail": (
                f"This record cannot be deleted because it is referenced by {what}. "
                "Remove or reassign them first."
            )
        },
        status=status.HTTP_409_CONFLICT,
    )
