"""
Payment Services
Business logic for payment processing
"""
from django.utils import timezone
from .model import Payment, Refund, PaymentStatus
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment operations"""
    
    @staticmethod
    def create_payment(order, amount, method, **kwargs):
        """
        Create a new payment record
        
        Args:
            order: Order instance
            amount: Payment amount
            method: Payment method
            **kwargs: Additional fields
        
        Returns:
            Payment instance
        """
        payment = Payment.objects.create(
            user=order.user,
            order=order,
            amount=amount,
            method=method,
            **kwargs
        )
        logger.info(f"Payment created: {payment.id} for order {order.id}")
        return payment
    
    @staticmethod
    def complete_payment(payment, transaction_id=None):
        """
        Mark payment as completed
        
        Args:
            payment: Payment instance
            transaction_id: External transaction ID
        
        Returns:
            Updated Payment instance
        """
        payment.completed_at = timezone.now()
        if transaction_id:
            payment.transaction_id = transaction_id
        payment.save(update_fields=['transaction_id', 'updated_at', 'completed_at'])
        
        # Track phase transition
        metadata = {}
        if transaction_id:
            metadata['transaction_id'] = transaction_id
        payment.add_phase(
            status=PaymentStatus.COMPLETED,
            reason="Payment gateway approved and processed",
            metadata=metadata
        )
        
        logger.info(f"Payment completed: {payment.id}")
        return payment
    
    @staticmethod
    def fail_payment(payment, reason=None):
        """
        Mark payment as failed
        
        Args:
            payment: Payment instance
            reason: Failure reason
        
        Returns:
            Updated Payment instance
        """
        if reason:
            payment.notes = reason
        payment.save(update_fields=['notes', 'updated_at'])
        
        # Track phase transition
        payment.add_phase(
            status=PaymentStatus.FAILED,
            reason=reason or "Payment gateway rejected",
            metadata={"failure_reason": reason} if reason else {}
        )
        
        logger.warning(f"Payment failed: {payment.id}")
        return payment
    
    @staticmethod
    def refund_payment(payment, amount, reason):
        """
        Create a refund for a payment
        
        Args:
            payment: Payment instance
            amount: Refund amount
            reason: Refund reason
        
        Returns:
            Refund instance
        """
        if amount > payment.amount:
            raise ValueError(f"Refund amount ({amount}) exceeds payment amount ({payment.amount})")
        
        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason
        )
        logger.info(f"Refund created: {refund.id} for payment {payment.id}")
        return refund
    
    @staticmethod
    def complete_refund(refund, refund_id=None):
        """
        Mark refund as completed
        
        Args:
            refund: Refund instance
            refund_id: External refund ID
        
        Returns:
            Updated Refund instance
        """
        refund.status = PaymentStatus.COMPLETED
        refund.completed_at = timezone.now()
        if refund_id:
            refund.refund_id = refund_id
        refund.save()
        
        # Mark parent payment as refunded if all remaining amount is refunded
        payment = refund.payment
        total_refunded = sum(r.amount for r in payment.refunds.filter(status=PaymentStatus.COMPLETED))
        if total_refunded >= payment.amount:
            payment.add_phase(
                status=PaymentStatus.REFUNDED,
                reason="All refunds processed and payment fully refunded",
                metadata={"total_refunded": str(total_refunded), "refund_id": refund.id}
            )
        
        logger.info(f"Refund completed: {refund.id}")
        return refund


class PaymentValidator:
    """Validator for payment operations"""
    
    @staticmethod
    def validate_payment_amount(payment, order):
        """Validate payment amount matches order total"""
        if payment.amount != order.total_price:
            logger.warning(f"Payment amount mismatch - Payment: {payment.amount}, Order: {order.total_price}")
            return False
        return True
    
    @staticmethod
    def validate_refund_amount(payment, amount):
        """Validate refund amount"""
        total_refunded = sum(r.amount for r in payment.refunds.all())
        if amount + total_refunded > payment.amount:
            return False
        return True
