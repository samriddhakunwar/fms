from rest_framework.routers import SimpleRouter

from .api_views_users import UserViewSet

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls
