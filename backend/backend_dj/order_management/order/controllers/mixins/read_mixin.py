from typing import TYPE_CHECKING, Any, cast
from rest_framework import status
from rest_framework.response import Response
from order_management.order.model import Order
from order_management.order.orderitem_model import OrderItem
from order_management.order.serializers import OrderSerializer
from user_management.models import User
from helper.auth_decorators import jwt_authentication
from django.db.models import Count, Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

if TYPE_CHECKING:
    from rest_framework.serializers import Serializer


class ReadMixin:
    """Mixin for READ operations: list, retrieve"""
    
    @jwt_authentication
    def list(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """GET /orders/ - List all orders (authenticated users see own, staff see all)"""
        print("[Order List]: Running")
        try:
            user = cast(User, request.user)  # type: ignore
            # Admin users see all orders, regular users see only their own
            if user.is_staff or user.is_superuser:
                queryset = self.get_queryset()  # type: ignore[attr-defined]
            else:
                queryset = self.get_queryset().filter(user=user)  # type: ignore[attr-defined]
            serializer = self.get_serializer(queryset, many=True)  # type: ignore[attr-defined]
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @jwt_authentication
    def retrieve(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """GET /orders/{id}/ - Get order details (own order or staff)"""
        print("[Order Retrieve]: Running")
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
                    {'error': 'You do not have permission to view this order'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(order)  # type: ignore[attr-defined]
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def orders_report(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """GET /orders/report/orders/ - Orders report (admin only — auth handled by viewset action)"""
        print("[Orders Report]: Running")
        try:
            # Get query parameters for filtering
            days_param = request.query_params.get('days', None)  # type: ignore
            status_filter = request.query_params.get('status', None)  # type: ignore
            
            # Apply date filtering if specified
            queryset = Order.objects.all()
            if days_param:
                cutoff_date = timezone.now() - timedelta(days=int(days_param))
                queryset = queryset.filter(created_at__gte=cutoff_date)
            
            # Apply status filtering if specified
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # Calculate statistics
            total_orders = queryset.count()
            status_breakdown = queryset.values('status').annotate(count=Count('id')).order_by('status')
            avg_order_value = queryset.aggregate(avg=Coalesce(Sum('total_price'), 0, output_field=DecimalField()))['avg']
            
            # Count by date (last 30 days)
            orders_by_date = queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).extra(select={'date': 'DATE(created_at)'}).values('date').annotate(count=Count('id')).order_by('date')
            
            report_data = {
                'total_orders': total_orders,
                'status_breakdown': list(status_breakdown),
                'average_order_value': float(avg_order_value) if avg_order_value else 0,
                'orders_last_30_days': list(orders_by_date),
                'report_date': timezone.now().isoformat(),
            }
            
            if days_param:
                report_data['filter_days'] = int(days_param)
            if status_filter:
                report_data['filter_status'] = status_filter
            
            return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Exception in orders_report: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def items_report(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """GET /orders/report/items/ - Order items report (admin only — auth handled by viewset action)"""
        print("[Items Report]: Running")
        try:
            # Get query parameters for filtering
            days_param = request.query_params.get('days', None)  # type: ignore
            limit = int(request.query_params.get('limit', 10))  # type: ignore
            
            # Apply date filtering if specified
            queryset = OrderItem.objects.all()
            if days_param:
                cutoff_date = timezone.now() - timedelta(days=int(days_param))
                queryset = queryset.filter(order__created_at__gte=cutoff_date)
            
            # Top ordered items by quantity
            top_items = queryset.values('customizations').annotate(
                total_quantity=Sum('quantity'),
                times_ordered=Count('id'),
                total_revenue=Sum('subtotal'),
                avg_unit_price=Coalesce(Sum('unit_price') / Count('id'), 0, output_field=DecimalField())
            ).order_by('-total_quantity')[:limit]
            
            # Parse item names from customizations
            items_list = []
            for item in top_items:
                customizations = item.get('customizations') or {}
                item_name = customizations.get('item_name', 'Unknown Item')
                items_list.append({
                    'item_name': item_name,
                    'total_quantity': item['total_quantity'] or 0,
                    'times_ordered': item['times_ordered'] or 0,
                    'total_revenue': float(item['total_revenue'] or 0),
                    'avg_unit_price': float(item['avg_unit_price'] or 0),
                })
            
            # Total statistics
            total_items_ordered = queryset.aggregate(total=Sum('quantity'))['total'] or 0
            total_items_count = queryset.count()
            
            report_data = {
                'top_items': items_list,
                'total_items_ordered': total_items_ordered,
                'total_unique_items_ordered': total_items_count,
                'report_date': timezone.now().isoformat(),
            }
            
            if days_param:
                report_data['filter_days'] = int(days_param)
            report_data['limit'] = limit
            
            return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Exception in items_report: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def revenue_report(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """GET /orders/report/revenue/ - Revenue report (admin only — auth handled by viewset action)"""
        print("[Revenue Report]: Running")
        try:
            # Get query parameters for filtering
            days_param = request.query_params.get('days', 30)  # type: ignore
            
            # Apply date filtering
            queryset = Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=int(days_param))
            )
            
            # Overall revenue statistics
            total_revenue = queryset.aggregate(
                total=Coalesce(Sum('total_price'), 0, output_field=DecimalField())
            )['total'] or 0
            
            total_cancellation_fees = queryset.aggregate(
                total=Coalesce(Sum('cancellation_fee'), 0, output_field=DecimalField())
            )['total'] or 0
            
            net_revenue = total_revenue - total_cancellation_fees
            
            # Revenue by order status
            revenue_by_status = queryset.values('status').annotate(
                total=Coalesce(Sum('total_price'), 0, output_field=DecimalField()),
                count=Count('id'),
                avg=Coalesce(Sum('total_price') / Count('id'), 0, output_field=DecimalField())
            ).order_by('-total')
            
            # Daily revenue (last 30 days or specified period)
            daily_revenue = queryset.extra(
                select={'date': 'DATE(created_at)'}
            ).values('date').annotate(
                total=Coalesce(Sum('total_price'), 0, output_field=DecimalField()),
                count=Count('id')
            ).order_by('date')
            
            # Cancelled orders with refund/fee info
            cancelled_orders = Order.objects.filter(
                status='cancelled',
                created_at__gte=timezone.now() - timedelta(days=int(days_param))
            ).aggregate(
                count=Count('id'),
                total_cancellation_fees=Coalesce(Sum('cancellation_fee'), 0, output_field=DecimalField()),
                total_order_value=Coalesce(Sum('total_price'), 0, output_field=DecimalField())
            )
            
            report_data = {
                'period_days': int(days_param),
                'total_revenue': float(total_revenue),
                'total_cancellation_fees': float(total_cancellation_fees),
                'net_revenue': float(net_revenue),
                'total_orders': queryset.count(),
                'average_order_value': float(total_revenue / queryset.count()) if queryset.count() > 0 else 0,
                'revenue_by_status': [
                    {
                        'status': item['status'],
                        'total': float(item['total']),
                        'count': item['count'],
                        'average': float(item['avg']),
                    }
                    for item in revenue_by_status
                ],
                'daily_revenue': [
                    {
                        'date': str(item['date']),
                        'total': float(item['total']),
                        'order_count': item['count'],
                    }
                    for item in daily_revenue
                ],
                'cancelled_orders': {
                    'count': cancelled_orders['count'] or 0,
                    'total_order_value': float(cancelled_orders['total_order_value'] or 0),
                    'total_cancellation_fees': float(cancelled_orders['total_cancellation_fees'] or 0),
                },
                'report_date': timezone.now().isoformat(),
            }
            
            return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Exception in revenue_report: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
