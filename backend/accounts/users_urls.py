from rest_framework.routers import SimpleRouter

from .api_views_users import AdminAccountViewSet, ManagerAccountViewSet, UserViewSet

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")
router.register("admins", AdminAccountViewSet, basename="admin-account")
router.register("managers", ManagerAccountViewSet, basename="manager-account")

urlpatterns = router.urls
