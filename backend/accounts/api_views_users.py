from rest_framework import filters, viewsets

from .models import User
from .permissions import IsAdmin
from .serializers import UserManagementSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-only user account management (create/update role & active status,
    reset password, deactivate). Full record editing otherwise stays in
    Django Admin per the project spec.
    """

    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name", "email"]
