from typing import cast, Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from order_management.order.model import Order
from user_management.models import User
from helper.auth_decorators import jwt_authentication, role_required


class DeleteMixin:
    """Mixin for DELETE operations: destroy, delete_many, delete_all"""
    
    @jwt_authentication
    def destroy(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """DELETE /orders/{id}/ - Cancel order (own order or admin, cancelation fee rules apply)"""
        print("[Order Destroy]: Running")
        try:
            from decimal import Decimal
            user = cast(User, request.user)  # type: ignore
            order_id = kwargs.get('pk')  # type: ignore[misc]
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Check permission: user owns order or is admin
            if order.user.id != user.id and not (user.is_staff or user.is_superuser):
                return Response(
                    {'error': 'You do not have permission to delete this order'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Plan C: Allow free cancellation for pending/confirmed, fee for preparing, deny for ready/delivered
            cancellation_fee = Decimal('0.00')
            
            if order.status == 'delivered':
                return Response(
                    {"error": "Cannot cancel delivered orders"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if order.status == 'ready':
                return Response(
                    {"error": "Cannot cancel orders ready for pickup"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if order.status == 'preparing':
                # Calculate 20% cancellation fee for preparing orders
                cancellation_fee = (order.total_price * Decimal('0.20')).quantize(Decimal('0.01'))
                order.cancellation_fee = cancellation_fee
                order.cancellation_reason = 'User cancelled while preparing (20% fee applied)'
            
            order_data = {
                "id": order.id,  # type: ignore[attr-defined]
                "order_number": order.order_number,
                "status": order.status,
                "original_price": float(order.total_price),
                "cancellation_fee": float(cancellation_fee),
                "refund_amount": float(order.total_price - cancellation_fee)
            }
            order.delete()
            
            msg = f"Order {order_data['id']} cancelled"
            if cancellation_fee > 0:
                msg += f" with {cancellation_fee} cancellation fee"
            print(f"✓ {msg}")
            
            return Response({"message": msg, "order": order_data}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'], permission_classes=[])  # type: ignore[misc]
    @jwt_authentication
    def delete_many(self, request):  # type: ignore[no-untyped-def]
        """DELETE /orders/delete-many/ - Cancel multiple orders (own pending/confirmed, admins can cancel any non-delivered)"""
        print("[Order Delete Many]: Running")
        try:
            user = cast(User, request.user)  # type: ignore
            data = cast(dict[str, Any], dict(request.data))
            ids = data.get('ids')
            
            if not ids:
                return Response({"error": "ids parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(ids, list) or len(ids) == 0:
                return Response({"error": "ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get orders based on user role
            if user.is_staff or user.is_superuser:
                # Admins can delete all non-delivered orders
                orders = Order.objects.filter(id__in=ids)
            else:
                # Regular users can only delete their own pending/confirmed orders
                orders = Order.objects.filter(
                    id__in=ids,
                    user=user,
                    status__in=['pending', 'confirmed']
                )
            
            deleted_count = 0
            skipped_count = 0
            skipped_orders = []
            
            for order in Order.objects.filter(id__in=ids):
                # Check if order should be skipped
                skip_reason = None
                
                # Check deletion permissions based on user role
                if not (user.is_staff or user.is_superuser):
                    if order.user.id != user.id:
                        skip_reason = "You do not own this order"
                    elif order.status == 'ready':
                        skip_reason = "Cannot cancel ready orders (ready for pickup)"
                    elif order.status == 'delivered':
                        skip_reason = "Cannot cancel delivered orders"
                    elif order.status not in ['pending', 'confirmed', 'preparing']:
                        skip_reason = f"Cannot cancel orders in {order.status} status"
                else:
                    # Admins: cannot delete ready/delivered orders
                    if order.status == 'delivered':
                        skip_reason = "Delivered orders cannot be deleted"
                    elif order.status == 'ready':
                        skip_reason = "Ready orders cannot be deleted"
                
                if skip_reason:
                    skipped_count += 1
                    skipped_orders.append({
                        "id": order.id,  # type: ignore[attr-defined]
                        "order_number": order.order_number,
                        "status": order.status,
                        "reason": skip_reason
                    })
                else:
                    # Plan C: Apply 20% cancellation fee for preparing orders
                    from decimal import Decimal
                    if order.status == 'preparing':
                        cancellation_fee = (order.total_price * Decimal('0.20')).quantize(Decimal('0.01'))
                        order.cancellation_fee = cancellation_fee
                        order.cancellation_reason = 'User cancelled while preparing (20% fee applied)'
                    
                    order.delete()
                    deleted_count += 1
            
            print(f"✓ Deleted {deleted_count} orders, skipped {skipped_count}")
            return Response({
                "message": f"{deleted_count} orders deleted, {skipped_count} skipped",
                "deleted_count": deleted_count,
                "skipped_count": skipped_count,
                "skipped_orders": skipped_orders
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'], permission_classes=[])  # type: ignore[misc]
    @jwt_authentication
    @role_required(["admin"])
    def delete_all(self, request):  # type: ignore[no-untyped-def]
        """DELETE /orders/delete-all/ - Cancel all non-delivered/non-ready orders (admin only)"""
        print("[Order Delete All]: Running")
        try:
            from decimal import Decimal
            # Get all non-delivered and non-ready orders
            orders = Order.objects.exclude(status__in=['delivered', 'ready'])
            deleted_count = 0
            fee_count = 0
            total_fees = Decimal('0.00')
            
            for order in orders:
                # Plan C: Apply 20% fee for preparing orders
                if order.status == 'preparing':
                    cancellation_fee = (order.total_price * Decimal('0.20')).quantize(Decimal('0.01'))
                    order.cancellation_fee = cancellation_fee
                    order.cancellation_reason = 'Admin cancelled (20% fee applied)'
                    total_fees += cancellation_fee
                    fee_count += 1
                
                order.delete()
                deleted_count += 1
            
            # Get preserved orders count to report
            ready_orders = Order.objects.filter(status='ready').count()
            delivered_orders = Order.objects.filter(status='delivered').count()
            
            print(f"✓ Deleted {deleted_count} orders ({fee_count} with cancellation fees)")
            return Response({
                "message": f"{deleted_count} orders deleted ({deleted_count - fee_count} free + {fee_count} with 20% fees)",
                "deleted_count": deleted_count,
                "free_cancellation_count": deleted_count - fee_count,
                "fee_cancellation_count": fee_count,
                "total_cancellation_fees": float(total_fees),
                "preserved_ready_orders": ready_orders,
                "preserved_delivered_orders": delivered_orders
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
