from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import LoginSerializer, UserSerializer


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


@swagger_auto_schema(
    method="post",
    operation_summary="Logout",
    operation_description="Ends the current session.",
    responses={200: openapi.Response(description="Logged out")},
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_logout(request):
    logout(request)
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_summary="Current session",
    operation_description=(
        "Returns the currently authenticated user, or 401 if there is no "
        "active session. Used by the frontend to restore auth state on "
        "page load."
    ),
    responses={
        200: UserSerializer,
        401: openapi.Response(
            description="Not authenticated",
            examples={"application/json": {"message": "Not authenticated"}},
        ),
    },
    tags=["Authentication"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_current_user(request):
    if not request.user.is_authenticated:
        return Response(
            {"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_summary="CSRF cookie",
    operation_description=(
        "Sets the csrftoken cookie. Call once before the first unsafe "
        "(POST/PUT/PATCH/DELETE) request so the client can read the token "
        "and send it back as the X-CSRFToken header."
    ),
    responses={200: openapi.Response(description="Cookie set")},
    tags=["Authentication"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_csrf(request):
    return Response({"csrfToken": get_token(request)}, status=status.HTTP_200_OK)
