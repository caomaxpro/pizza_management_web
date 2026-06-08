from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from order_management.order.model import Order
from order_management.order.serializers import OrderSerializer
from order_management.order.controllers.mixins import CreateMixin, ReadMixin, UpdateMixin, DeleteMixin
from helper.auth_decorators import jwt_authentication, role_required


class OrderViewSet(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    
    Endpoints:
    - GET /api/orders/ - List all orders
    - POST /api/orders/ - Create new order
    - GET /api/orders/{id}/ - Get order details
    - PUT /api/orders/{id}/ - Update order
    - PATCH /api/orders/{id}/ - Partial update order
    - DELETE /api/orders/{id}/ - Delete order
    - PATCH /api/orders/update-many/ - Update multiple orders
    - PATCH /api/orders/update-all/ - Update all pending orders
    - DELETE /api/orders/delete-many/ - Delete multiple orders
    - DELETE /api/orders/delete-all/ - Delete all non-delivered orders
    
    Report Endpoints (Admin Only):
    - GET /api/orders/report/orders/ - Orders report (status breakdown, order count, etc.)
    - GET /api/orders/report/items/ - Items report (top items ordered, frequency, revenue)
    - GET /api/orders/report/revenue/ - Revenue report (total revenue, breakdown by status, daily)
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[])
    @jwt_authentication
    def user_orders(self, request):
        """GET /orders/user-orders/ — All orders for the current authenticated user."""
        user_orders = Order.objects.filter(user=request.user)
        serializer = self.get_serializer(user_orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager", "staff"])
    def pending_orders(self, request):
        """GET /orders/pending-orders/ — All pending orders (staff/admin only)."""
        pending = Order.objects.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='report/orders', permission_classes=[])
    @jwt_authentication
    @role_required(["admin"])
    def orders_report(self, request):
        """GET /orders/report/orders/ — Orders report (admin only)."""
        return ReadMixin.orders_report(self, request)

    @action(detail=False, methods=['get'], url_path='report/items', permission_classes=[])
    @jwt_authentication
    @role_required(["admin"])
    def items_report(self, request):
        """GET /orders/report/items/ — Items report (admin only)."""
        return ReadMixin.items_report(self, request)

    @action(detail=False, methods=['get'], url_path='report/revenue', permission_classes=[])
    @jwt_authentication
    @role_required(["admin"])
    def revenue_report(self, request):
        """GET /orders/report/revenue/ — Revenue report (admin only)."""
        return ReadMixin.revenue_report(self, request)
