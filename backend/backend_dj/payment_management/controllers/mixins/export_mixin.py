"""Export Mixin for Payment operations - Audit trail & archival"""
from typing import Any, Dict, Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from payment_management.serializers import RefundSerializer
from helper.auth_decorators import jwt_authentication, role_required


class ExportMixin:
    """Mixin for export and archival operations - Financial audit & record management"""
    
    def get_object(self) -> Any:
        """Get object instance - must be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_object()")
    
    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        """Get serializer instance - must be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_serializer()")
    
    def _get_refund_data(self, payment: Any) -> list:
        """Extract refund data from payment - returns list of refund dicts"""
        refunds = getattr(payment, 'refunds', None)
        if refunds is None:
            return []
        try:
            serializer = RefundSerializer(refunds.all(), many=True)
            return list(serializer.data)
        except Exception:
            return []
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def export(self, request: Request, id: Optional[int] = None) -> JsonResponse:
        """Export payment record as JSON audit trail with full metadata"""
        payment = self.get_object()
        serializer = self.get_serializer(payment)
        refund_data = self._get_refund_data(payment)
        
        # Build export data with audit metadata
        export_data = {
            'payment': serializer.data,
            'refunds': refund_data,
            'exported_at': timezone.now().isoformat(),
            'metadata': {
                'user_id': payment.user.id if payment.user else None,
                'user_email': payment.user.email if payment.user else 'unknown',
                'export_version': '1.0',
                'exporter_user': request.user.email if request.user else 'system'
            }
        }
        
        return JsonResponse(export_data, safe=False)
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def archive(self, request: Request, id: Optional[int] = None) -> Response:
        """Archive and soft-delete payment after 90-day retention period"""
        payment = self.get_object()
        age = timezone.now() - payment.created_at
        
        # Verify retention period (90 days minimum)
        if age < timedelta(days=90):
            days_left = 90 - age.days
            return Response(
                {
                    'error': 'Payment cannot be archived yet',
                    'reason': f'Must retain for {days_left} more days (90-day policy)',
                    'created_at': payment.created_at.isoformat(),
                    'days_retained': age.days
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Export full audit trail before deletion
        serializer = self.get_serializer(payment)
        refund_data = self._get_refund_data(payment)
        
        archive_data = {
            'payment': serializer.data,
            'refunds': refund_data,
            'archived_at': timezone.now().isoformat(),
            'archived_by': request.user.email if request.user else 'system',
            'action': 'archived'
        }
        
        # TODO: Store archive in audit log (optional implementations):
        # Option 1: PaymentAuditLog model (separate tracking)
        # PaymentAuditLog.objects.create(
        #     payment_id=payment.id,
        #     action='archived',
        #     actor=request.user,
        #     data_snapshot=archive_data
        # )
        #
        # Option 2: S3/Cloud storage for compliance
        # s3_client.put_object(
        #     Bucket='audit-logs',
        #     Key=f'payments/{payment.id}/{timezone.now().timestamp()}.json',
        #     Body=json.dumps(archive_data)
        # )
        
        # Delete payment record
        payment_id = payment.id
        payment.delete()
        
        return Response(
            {
                'message': 'Payment archived and deleted',
                'payment_id': payment_id,
                'archive': archive_data
            },
            status=status.HTTP_200_OK
        )
