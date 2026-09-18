from rest_framework.routers import SimpleRouter

from .views import SalaryPaymentViewSet

router = SimpleRouter()
router.register("salary-payments", SalaryPaymentViewSet, basename="salarypayment")

urlpatterns = router.urls
