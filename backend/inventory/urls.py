from rest_framework.routers import SimpleRouter

from .views import ProductViewSet, StockMovementViewSet

router = SimpleRouter()
router.register("products", ProductViewSet, basename="product")
router.register("stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls
