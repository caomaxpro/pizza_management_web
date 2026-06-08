from typing import cast, Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError as DRFValidationError
from order_management.order.model import Order
from order_management.order.serializers import OrderSerializer
from order_management.order.validators import validate_order_data
from user_management.models import User
from helper.auth_decorators import jwt_authentication, role_required


class UpdateMixin:
    """Mixin for UPDATE operations: update, update_many, update_all"""
    
    @jwt_authentication
    def update(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """PUT/PATCH /orders/{id}/ - Update specific order (own order or admin)"""
        print("[Order Update]: Running")
        try:
            user = cast(User, request.user)  # type: ignore
            order_id = kwargs.get('pk')
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Check permission: user owns order or is admin
            if order.user.id != user.id and not (user.is_staff or user.is_superuser):
                return Response(
                    {'error': 'You do not have permission to update this order'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(order, data=request.data, partial=True)  # type: ignore[attr-defined]
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            
            print(f"✓ Order {order.id} updated")  # type: ignore[attr-defined]
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        
        except DRFValidationError as e:
            print(f"❌ Validation Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'], permission_classes=[])  # type: ignore[misc]
    @jwt_authentication
    @role_required(["admin"])
    def update_many(self, request):  # type: ignore[no-untyped-def]
        """PATCH /orders/update-many/ - Update multiple orders by ID list (admin only)"""
        print("[Order Update Many]: Running")
        try:
            data = cast(dict[str, Any], dict(request.data))
            ids = data.get('ids')
            
            if not ids:
                return Response({"error": "ids parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(ids, list) or len(ids) == 0:
                return Response({"error": "ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract update data
            update_data = {k: v for k, v in data.items() if k != 'ids'}
            
            orders = Order.objects.filter(id__in=ids)
            updated_count = 0
            updated_orders = []
            
            for order in orders:
                serializer = self.get_serializer(order, data=update_data, partial=True)  # type: ignore[attr-defined]
                if serializer.is_valid():
                    order = serializer.save()
                    updated_count += 1
                    updated_orders.append(OrderSerializer(order).data)
            
            print(f"✓ Updated {updated_count} orders")
            return Response({
                "message": f"{updated_count} orders updated",
                "updated_count": updated_count,
                "updated_orders": updated_orders
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'], permission_classes=[])  # type: ignore[misc]
    @jwt_authentication
    @role_required(["admin"])
    def update_all(self, request):  # type: ignore[no-untyped-def]
        """PATCH /orders/update-all/ - Update all pending orders (admin only)"""
        print("[Order Update All]: Running")
        try:
            data = cast(dict[str, Any], dict(request.data))
            
            # Only update pending orders
            orders = Order.objects.filter(status='pending')
            updated_count = 0
            updated_orders = []
            
            for order in orders:
                serializer = self.get_serializer(order, data=data, partial=True)  # type: ignore[attr-defined]
                if serializer.is_valid():
                    order = serializer.save()
                    updated_count += 1
                    updated_orders.append(OrderSerializer(order).data)
            
            print(f"✓ Updated {updated_count} pending orders")
            return Response({
                "message": f"{updated_count} pending orders updated",
                "updated_count": updated_count,
                "updated_orders": updated_orders
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
