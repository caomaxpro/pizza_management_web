from django.urls import path, include

urlpatterns = [
    path('items/', include('pizza_management.item.urls')),
    path('ingredients/', include('pizza_management.ingredient.urls')),
]