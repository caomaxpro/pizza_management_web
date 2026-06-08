from django.urls import path

def get_patterns():
    """Defer import để tránh circular dependency"""
    from pizza_management.ingredient.controllers.viewset import IngredientViewSet
    
    return [
        # Ingredients
        path('', IngredientViewSet.as_view({'get': 'list', 'post': 'create'}), name='ingredient-list'),
        path('create/', IngredientViewSet.as_view({'post': 'create'}), name='ingredient-create'),
        path('get-all-items/', IngredientViewSet.as_view({'get': 'get_all_items'}), name='ingredient-get-all'),
        path('get-paginated-items/', IngredientViewSet.as_view({'get': 'get_paginated_items'}), name='ingredient-get-paginated'),
        path('get-many-items/', IngredientViewSet.as_view({'get': 'get_many_items'}), name='ingredient-get-many'),
        path('filter-ingredients/', IngredientViewSet.as_view({'get': 'filter_ingredients'}), name='ingredient-filter'),
        path('update-many/', IngredientViewSet.as_view({'patch': 'update_many'}), name='ingredient-update-many'),
        path('update-all/', IngredientViewSet.as_view({'patch': 'update_all'}), name='ingredient-update-all'),
        path('adjust-prices/', IngredientViewSet.as_view({'patch': 'adjust_prices'}), name='ingredient-adjust-prices'),
        path('rollback-prices/', IngredientViewSet.as_view({'patch': 'rollback_prices'}), name='ingredient-rollback-prices'),
        path('bulk_delete/', IngredientViewSet.as_view({'post': 'bulk_delete'}), name='ingredient-bulk-delete'),
        path('delete-many/', IngredientViewSet.as_view({'post': 'delete_many'}), name='ingredient-delete-many'),
        path('delete-all/', IngredientViewSet.as_view({'post': 'delete_all'}), name='ingredient-delete-all'),
        path('import-json/', IngredientViewSet.as_view({'post': 'import_json'}), name='ingredient-import'),
        path('import-cancel/<str:import_id>/', IngredientViewSet.as_view({'post': 'cancel_import'}), name='ingredient-cancel-import'),
        path('<int:pk>/', IngredientViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='ingredient-detail'),
        path('<int:pk>/get-item/', IngredientViewSet.as_view({'get': 'get_item'}), name='ingredient-get-item'),
    ]

urlpatterns = get_patterns()