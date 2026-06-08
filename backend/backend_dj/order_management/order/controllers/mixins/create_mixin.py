from typing import TYPE_CHECKING, Any, cast
from rest_framework import status
from rest_framework.response import Response
from order_management.order.model import Order
from order_management.order.serializers import OrderSerializer
from order_management.order.validators import validate_order_data
from user_management.models import User
from helper.auth_decorators import jwt_authentication, rate_limit

if TYPE_CHECKING:
    from rest_framework.serializers import Serializer


class CreateMixin:
    """Mixin for CREATE operations: create"""
    
    @jwt_authentication
    @rate_limit(limit=20, window=3600, prefix='order_create', scope='user')
    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """POST /orders/ - Create new order (any authenticated user, rate-limited to 20/hour per user)"""
        print("[Order Create]: Running")
        try:
            # Set the order user to the current authenticated user
            user = cast(User, request.user)  # type: ignore
            data = dict(request.data)  # type: ignore
            data['user'] = user.id  # Force user ownership
            
            # Validate order data
            validate_order_data(data)  # type: ignore[arg-type]
            
            serializer = self.get_serializer(data=data)  # type: ignore[attr-defined]
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            
            print(f"✓ Order {order.id} created")  # type: ignore[attr-defined]
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            print(f"❌ Validation Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
