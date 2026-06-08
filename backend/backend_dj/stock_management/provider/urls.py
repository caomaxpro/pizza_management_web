# provider/urls.py
from django.urls import path

from .controllers import ProviderViewSet

# List and Create
provider_list = ProviderViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

# Retrieve, Update, Partial Update, Delete
provider_detail = ProviderViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

# Bulk Update operations
provider_update_many = ProviderViewSet.as_view({
    'patch': 'update_many',
})

provider_update_all = ProviderViewSet.as_view({
    'patch': 'update_all',
})

# Bulk Delete operations
provider_delete_all = ProviderViewSet.as_view({
    'delete': 'delete_all',
})

provider_delete_many = ProviderViewSet.as_view({
    'delete': 'delete_many',
})

urlpatterns = [
    # Bulk operations MUST come before detail routes
    path('provider/update-many/', provider_update_many, name='provider-update-many'),
    path('provider/update-all/', provider_update_all, name='provider-update-all'),
    path('provider/delete-many/', provider_delete_many, name='provider-delete-many'),
    path('provider/delete-all/', provider_delete_all, name='provider-delete-all'),
    
    # Provider CRUD
    path('provider/', provider_list, name='provider-list'),
    path('provider/<int:pk>/', provider_detail, name='provider-detail'),
]
