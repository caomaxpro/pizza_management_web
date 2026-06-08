"""
URL configuration for backend_dj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.health_check import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("user_management.urls")),
    path("api/pizza/", include("pizza_management.urls")),
    path("api/", include("order_management.urls")),
    path("api/", include("stock_management.inventory.urls")),
    path("api/", include("stock_management.provider.urls")),
    path("api/", include("stock_management.purchase_order.urls")),
    path("api/", include("stock_management.session.urls")),
    path("api/", include("payment_management.urls")),
]

# Serve media files and assets in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Also serve assets folder for images
    urlpatterns += static('/assets/', document_root=settings.BASE_DIR / 'assets')
