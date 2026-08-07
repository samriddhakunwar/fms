from django.contrib.auth import authenticate, login

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import LoginSerializer


_login_responses = {
    200: openapi.Response(
        description="Login successful",
        examples={
            "application/json": {
                "message": "Login successful",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "role": "ADMIN",
                },
            }
        },
    ),
    400: openapi.Response(
        description="Validation error — missing or blank fields",
        examples={
            "application/json": {
                "username": ["This field is required."],
                "password": ["This field is required."],
            }
        },
    ),
    401: openapi.Response(
        description="Invalid credentials",
        examples={
            "application/json": {
                "message": "Invalid username or password",
            }
        },
    ),
}


@swagger_auto_schema(
    method="post",
    operation_summary="Login",
    operation_description=(
        "Authenticate a user with username and password.\n\n"
        "On success the server creates a Django session (cookie) and returns "
        "basic user info. The session can then be used with other "
        "session-protected endpoints.\n\n"
        "Roles: `ADMIN` | `INVENTORY_MANAGER` | `EMPLOYEE`"
    ),
    request_body=LoginSerializer,
    responses=_login_responses,
    tags=["Authentication"],
)
@api_view(["POST"])
def api_login(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"message": "Invalid username or password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request, user)

    return Response(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
        },
        status=status.HTTP_200_OK,
    )
