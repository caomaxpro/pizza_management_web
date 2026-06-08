"""Read Mixin for Payment operations"""
from typing import Any, List
from decimal import Decimal
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from helper.auth_decorators import jwt_authentication, role_required


class ReadMixin:
    """Mixin for read operations"""
    
    def get_object(self) -> Any:
        """Get object instance - should be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_object()")
    
    def get_queryset(self) -> Any:
        """Get base queryset - should be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_queryset()")
    
    def filter_queryset(self, queryset: Any) -> Any:
        """Filter queryset - should be implemented in ViewSet"""
        return queryset
    
    def paginate_queryset(self, queryset: Any) -> Any:
        """Paginate queryset - should be implemented in ViewSet"""
        return None
    
    def get_paginated_response(self, data: List[Any]) -> Response:
        """Return paginated response - should be implemented in ViewSet"""
        return Response(data)
    
    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        """Get serializer instance - should be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_serializer()")
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """List all records with pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve single record"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def report(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """GET /payments/report/?days=30 — Payment analytics report (admin only)."""
        from payment_management.model import Payment, Refund

        try:
            period_days = int(request.query_params.get("days", 30))
        except (ValueError, TypeError):
            period_days = 30

        since = timezone.now() - timedelta(days=period_days)

        # ── Payment method breakdown ───────────────────────────────────────
        METHOD_LABELS = {
            "credit_card": "Credit Card",
            "debit_card": "Debit Card",
            "paypal": "PayPal",
            "bank_transfer": "Bank Transfer",
            "cash": "Cash",
        }

        method_qs = (
            Payment.objects.filter(created_at__gte=since)
            .values("method")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-count")
        )
        payment_method_breakdown = [
            {
                "method": row["method"],
                "label": METHOD_LABELS.get(row["method"], row["method"]),
                "count": row["count"],
                "total": float(row["total"] or 0),
            }
            for row in method_qs
        ]

        # ── Payment status breakdown ───────────────────────────────────────
        status_qs = (
            Payment.objects.filter(created_at__gte=since)
            .values("status")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-count")
        )
        payment_status_breakdown = [
            {
                "status": row["status"],
                "count": row["count"],
                "total": float(row["total"] or 0),
            }
            for row in status_qs
        ]

        total_payments = Payment.objects.filter(created_at__gte=since).count()

        # ── Refund stats ───────────────────────────────────────────────────
        refund_qs = Refund.objects.filter(created_at__gte=since)
        refund_by_status = (
            refund_qs.values("status")
            .annotate(count=Count("id"), total=Sum("amount"))
        )
        refund_status_counts: dict = {
            row["status"]: {"count": row["count"], "total": float(row["total"] or 0)}
            for row in refund_by_status
        }

        total_refund_amount = refund_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

        refund_stats = {
            "total_refunds": refund_qs.count(),
            "total_amount": float(total_refund_amount),
            "requested_count": refund_status_counts.get("requested", {}).get("count", 0),
            "pending_count": refund_status_counts.get("pending", {}).get("count", 0),
            "processing_count": refund_status_counts.get("processing", {}).get("count", 0),
            "processed_count": refund_status_counts.get("processed", {}).get("count", 0),
            "rejected_count": refund_status_counts.get("rejected", {}).get("count", 0),
        }

        return Response({
            "period_days": period_days,
            "total_payments": total_payments,
            "payment_method_breakdown": payment_method_breakdown,
            "payment_status_breakdown": payment_status_breakdown,
            "refund_stats": refund_stats,
            "report_date": timezone.now().isoformat(),
        })
