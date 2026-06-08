"""
Payment Celery tasks — refund rule engine & auto-processing.

Rule engine (auto-approve conditions, all must pass):
    1. Payment is COMPLETED.
    2. Order age <= AUTO_REFUND_MAX_AGE_MINUTES (default 10 min).
    3. Refund amount <= AUTO_REFUND_MAX_AMOUNT (default 500_000 VND / configurable).
    4. No other approved/processing refund for the same payment.
    5. Refund risk_score < AUTO_REFUND_MAX_RISK (default 20).

If all pass  → mark PROCESSING, call gateway (stub), mark PROCESSED.
Otherwise   → mark PENDING (admin review queue).

Config (settings.py):
    AUTO_REFUND_MAX_AGE_MINUTES = 10
    AUTO_REFUND_MAX_AMOUNT = 500000
    AUTO_REFUND_MAX_RISK = 20
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task

from .model import Refund, RefundStatus

logger = logging.getLogger(__name__)

_MAX_AGE = getattr(settings, 'AUTO_REFUND_MAX_AGE_MINUTES', 10)
_MAX_AMOUNT = getattr(settings, 'AUTO_REFUND_MAX_AMOUNT', 500_000)
_MAX_RISK = getattr(settings, 'AUTO_REFUND_MAX_RISK', 20)


def _can_auto_approve(refund: Refund) -> tuple[bool, str]:
    """
    Run rule checks. Returns (can_approve: bool, reason: str).
    """
    payment = refund.payment

    # Rule 1: payment must be completed
    from .model import PaymentStatus
    if payment.status != PaymentStatus.COMPLETED:
        return False, f'Payment status is {payment.status}, not completed'

    # Rule 2: order age
    age = timezone.now() - payment.created_at
    if age > timedelta(minutes=_MAX_AGE):
        return False, f'Payment too old ({age.seconds // 60} min, limit {_MAX_AGE} min)'

    # Rule 3: amount cap
    if refund.amount > _MAX_AMOUNT:
        return False, f'Amount {refund.amount} exceeds auto-approve cap {_MAX_AMOUNT}'

    # Rule 4: no duplicate active refund for same payment
    duplicate = Refund.objects.filter(
        payment=payment,
        status__in=[RefundStatus.PROCESSING, RefundStatus.PROCESSED],
    ).exclude(pk=refund.pk).exists()
    if duplicate:
        return False, 'Another refund for this payment is already processing/processed'

    # Rule 5: risk score
    if refund.risk_score >= _MAX_RISK:
        return False, f'Risk score {refund.risk_score} too high (limit {_MAX_RISK})'

    return True, 'All rules passed'


def _call_gateway(refund: Refund) -> str:
    """
    Stub for payment gateway call.
    Replace with actual gateway SDK call (e.g., Stripe, VNPay, MoMo).
    Returns a gateway refund transaction ID.
    """
    # TODO: integrate with real gateway
    # Example (Stripe):
    #   import stripe
    #   result = stripe.Refund.create(
    #       payment_intent=refund.payment.transaction_id,
    #       amount=int(refund.amount * 100),
    #       idempotency_key=refund.idempotency_key,
    #   )
    #   return result.id
    logger.info(f"[STUB] Gateway refund called for refund {refund.id}, amount {refund.amount}")
    return f'STUB_REFUND_{refund.id}'


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_refund(self, refund_id: int) -> dict:
    """
    Celery task: evaluate refund request and auto-process if rules pass.

    Returns a dict summary (useful for testing / monitoring).
    """
    try:
        refund = Refund.objects.select_related('payment').get(pk=refund_id)
    except Refund.DoesNotExist:
        logger.error(f"process_refund: Refund {refund_id} not found")
        return {'ok': False, 'reason': 'not_found'}

    # Only process requests in REQUESTED status
    if refund.status != RefundStatus.REQUESTED:
        logger.info(f"process_refund: Refund {refund_id} already in status {refund.status}, skipping")
        return {'ok': True, 'reason': 'already_handled', 'status': refund.status}

    can_approve, reason = _can_auto_approve(refund)

    if not can_approve:
        logger.info(f"process_refund: Refund {refund_id} → PENDING ({reason})")
        refund.status = RefundStatus.PENDING
        refund.save(update_fields=['status', 'updated_at'])
        return {'ok': True, 'reason': reason, 'status': RefundStatus.PENDING}

    # Auto-approve path
    try:
        refund.status = RefundStatus.PROCESSING
        refund.save(update_fields=['status', 'updated_at'])

        gateway_id = _call_gateway(refund)

        refund.refund_id = gateway_id
        refund.status = RefundStatus.PROCESSED
        refund.completed_at = timezone.now()
        refund.save(update_fields=['refund_id', 'status', 'completed_at', 'updated_at'])

        logger.info(f"process_refund: Refund {refund_id} PROCESSED (gateway_id={gateway_id})")
        return {'ok': True, 'reason': 'auto_approved', 'status': RefundStatus.PROCESSED, 'gateway_id': gateway_id}

    except Exception as exc:
        logger.error(f"process_refund: Gateway error for refund {refund_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            refund.status = RefundStatus.PENDING
            refund.save(update_fields=['status', 'updated_at'])
            return {'ok': False, 'reason': 'gateway_error_max_retries', 'status': RefundStatus.PENDING}
