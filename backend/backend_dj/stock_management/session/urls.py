from django.urls import path
from stock_management.session.views import StockTakeSessionViewSet

session_list = StockTakeSessionViewSet.as_view({'get': 'list'})
session_active = StockTakeSessionViewSet.as_view({'get': 'active'})
session_start = StockTakeSessionViewSet.as_view({'post': 'start'})
session_detail = StockTakeSessionViewSet.as_view({'get': 'retrieve'})
session_assign = StockTakeSessionViewSet.as_view({'post': 'assign'})
session_close = StockTakeSessionViewSet.as_view({'post': 'close'})
session_takeover = StockTakeSessionViewSet.as_view({'post': 'takeover'})

urlpatterns = [
    # Custom actions before detail routes
    path('stock-take/active/', session_active, name='stock-take-active'),
    path('stock-take/start/', session_start, name='stock-take-start'),

    # Detail actions
    path('stock-take/<int:pk>/assign/', session_assign, name='stock-take-assign'),
    path('stock-take/<int:pk>/close/', session_close, name='stock-take-close'),
    path('stock-take/<int:pk>/takeover/', session_takeover, name='stock-take-takeover'),

    # Collection / detail
    path('stock-take/', session_list, name='stock-take-list'),
    path('stock-take/<int:pk>/', session_detail, name='stock-take-detail'),
]
