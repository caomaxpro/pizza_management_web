from django.urls import path
from rest_framework.routers import SimpleRouter
from order_management.order.controllers import OrderViewSet

router = SimpleRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = router.urls
