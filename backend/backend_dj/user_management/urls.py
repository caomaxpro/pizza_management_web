"""
User Management URLs
URL configuration for user endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers import UserViewSet, AddressViewSet, AuthViewSet, WorkScheduleViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'schedules', WorkScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]
