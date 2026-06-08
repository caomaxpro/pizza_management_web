"""
Payment ViewSets
REST API endpoints for payment operations
"""
from typing import Any
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.request import Request
from django.http import JsonResponse

from .mixins import CreateMixin, ReadMixin, ExportMixin
from ..model import Payment, Refund
from ..serializers import PaymentSerializer, PaymentListSerializer, RefundSerializer
from ..services import PaymentService
from helper.auth_decorators import jwt_authentication, role_required


class IsOwnerOrStaff(BasePermission):
    """Permission to check if user is owner or staff"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user owns the object or is staff"""
        return obj.user == request.user or request.user.is_staff


class UserFilterBackend(filters.BaseFilterBackend):
    """Filter queryset by current user"""
    
    def filter_queryset(self, request, queryset, view):
        """Filter by user"""
        if request.user.is_staff:
            return queryset
        return queryset.filter(user=request.user)


class UserPaymentFilterBackend(filters.BaseFilterBackend):
    """Filter refunds by current user's payments"""
    
    def filter_queryset(self, request, queryset, view):
        """Filter by payment user"""
        if request.user.is_staff:
            return queryset
        return queryset.filter(payment__user=request.user)


class PaymentViewSet(CreateMixin, ReadMixin, ExportMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for Payment operations - Read-only financial records with export & archival"""
    
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [UserFilterBackend]
    lookup_field = 'id'
    
    def get_serializer_class(self) -> Any:
        """Use different serializer for list view"""
        if self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer

    @action(detail=False, methods=['get'], url_path='report', permission_classes=[])
    @jwt_authentication
    @role_required(["admin"])
    def report(self, request: Request) -> Response:
        """GET /payments/report/?days=30 — Payment analytics report (admin only)."""
        return ReadMixin.report(self, request)

    @action(detail=True, methods=['post'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def complete(self, request: Request, id: int | None = None) -> Response:
        """Mark payment as completed"""
        payment = self.get_object()
        transaction_id = getattr(request.data, 'get', lambda x: None)('transaction_id')
        payment = PaymentService.complete_payment(payment, transaction_id)
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def fail(self, request: Request, id: int | None = None) -> Response:
        """Mark payment as failed"""
        payment = self.get_object()
        reason = getattr(request.data, 'get', lambda x: None)('reason')
        payment = PaymentService.fail_payment(payment, reason)
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[])
    def refund(self, request: Request, id: int | None = None) -> Response:
        """Create a refund for payment — admin/manager only (execute refund via gateway)"""
        payment = self.get_object()
        amount = getattr(request.data, 'get', lambda x: None)('amount')
        reason = getattr(request.data, 'get', lambda x: None)('reason')
        
        if not amount or not reason:
            return Response(
                {'error': 'amount and reason are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refund = PaymentService.refund_payment(payment, float(amount), reason)
            serializer = RefundSerializer(refund)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[])
    def request_refund(self, request: Request, id: int | None = None) -> Response:
        """
        Customer endpoint: submit a refund request.
        Applies IP logging, rate limit, adaptive CAPTCHA, idempotency, and risk scoring.
        Auto-processes via Celery rule engine; high-risk cases go to admin review queue.
        """
        return super().request_refund(request)
    
    @action(detail=True, methods=['get'])
    def export(self, request: Request, id: int | None = None) -> JsonResponse:
        """Export payment record as JSON audit trail"""
        return super().export(request, id)
    
    @action(detail=True, methods=['post'])
    def archive(self, request: Request, id: int | None = None) -> Response:
        """Archive and delete payment after 90 days"""
        return super().archive(request, id)


class RefundViewSet(CreateMixin, ReadMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for Refund operations - Financial audit records"""
    
    queryset = Refund.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [UserPaymentFilterBackend]
    lookup_field = 'id'
    
    def get_serializer_class(self) -> Any:
        """Return refund serializer"""
        return RefundSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request: Request, id: int | None = None) -> Response:
        """Mark refund as completed"""
        refund = self.get_object()
        refund_id = getattr(request.data, 'get', lambda x: None)('refund_id')
        refund = PaymentService.complete_refund(refund, refund_id)
        serializer = self.get_serializer(refund)
        return Response(serializer.data)
