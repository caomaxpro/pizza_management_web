"""Create Mixin for Payment operations"""
import hashlib
import logging
from typing import Any, Dict, cast
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from helper.auth_decorators import jwt_authentication, role_required
from payment_management.throttles import is_ip_blacklisted
from payment_management.decorators import captcha_required
from payment_management.model import Refund, RefundStatus

logger = logging.getLogger(__name__)


class CreateMixin:
    """Mixin for create operations"""
    
    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        """Get serializer instance - should be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_serializer()")
    
    def get_success_headers(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Get headers for successful creation - should be implemented in ViewSet"""
        return {}
    
    def perform_create(self, serializer: Any) -> None:
        """Handle create operation"""
        serializer.save()
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create payment record (admin/manager only — usually done by system/gateway)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @jwt_authentication
    @captcha_required
    def request_refund(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Customer endpoint to request a refund.

        Defense layers (in order):
        1. JWT authentication (decorator above).
        2. IP blacklist check  — blacklisted IPs forced to pending review.
        3. IP rate limit       — 5 requests / IP / hour (configurable).
        4. Adaptive CAPTCHA    — required when IP nears rate limit.
        5. Idempotency key     — prevents duplicate submissions.
        6. Risk scoring        — combines abuse flags; high-risk → pending.
        7. Rule engine         — dispatched to Celery for auto-approve/gateway call.
        """
        # IP, rate info, logging, CAPTCHA — all handled by @captcha_required.
        ip: str = request._refund_ip   # type: ignore[attr-defined]
        rate: dict = request._refund_rate  # type: ignore[attr-defined]
        data = cast(dict, request.data)

        # ── Blacklist check ────────────────────────────────────────────────
        blacklisted = is_ip_blacklisted(ip)

        # ── Idempotency ────────────────────────────────────────────────────
        raw_key = data.get('idempotency_key')
        if not raw_key:
            # Auto-generate from user + payment_id + amount for convenience
            payment_id = data.get('payment')
            amount = data.get('amount', '')
            raw_key = f"{request.user.pk}:{payment_id}:{amount}"
        idempotency_key = hashlib.sha256(str(raw_key).encode()).hexdigest()[:64]

        existing = Refund.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            from payment_management.serializers import RefundSerializer
            return Response(
                RefundSerializer(existing).data,
                status=status.HTTP_200_OK,
            )

        # ── Risk scoring ───────────────────────────────────────────────────────
        risk_score = 0
        if blacklisted:
            risk_score += 50
        if rate['abuse']:
            risk_score += 30
        if rate['count'] > 1:
            risk_score += min(rate['count'] * 5, 20)

        # High risk → force manual review regardless of auto rules
        force_pending = risk_score >= 50

        # ── Create Refund record ───────────────────────────────────────────────
        from payment_management.serializers import RefundRequestSerializer
        serializer = RefundRequestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        refund_status = RefundStatus.PENDING if force_pending else RefundStatus.REQUESTED
        refund = cast(Refund, serializer.save(
            requested_by=request.user,
            requested_from_ip=ip,
            risk_score=risk_score,
            idempotency_key=idempotency_key,
            status=refund_status,
        ))

        # ── Dispatch to Celery rule engine (only for non-forced-pending) ───────
        if not force_pending:
            try:
                from payment_management.tasks import process_refund
                process_refund.delay(refund.id)  # type: ignore[union-attr]
            except Exception as exc:
                logger.error(f"Failed to dispatch process_refund task for refund {refund.id}: {exc}")
                # Fallback: mark as pending so admin can review
                refund.status = RefundStatus.PENDING
                refund.save(update_fields=['status'])

        from payment_management.serializers import RefundSerializer
        return Response(
            {
                'refund': RefundSerializer(refund).data,
                'message': (
                    'Your refund request has been submitted and is under review.'
                    if refund.status == RefundStatus.PENDING
                    else 'Refund request received. Processing will begin shortly.'
                ),
            },
            status=status.HTTP_201_CREATED,
        )

