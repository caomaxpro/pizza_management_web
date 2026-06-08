"""
Payment Model
Manages payment transactions and payment methods
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class PaymentMethod(models.TextChoices):
    """Available payment methods"""
    CREDIT_CARD = 'credit_card', 'Credit Card'
    DEBIT_CARD = 'debit_card', 'Debit Card'
    PAYPAL = 'paypal', 'PayPal'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    CASH = 'cash', 'Cash'


class PaymentStatus(models.TextChoices):
    """Payment status tracking"""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'


class RefundStatus(models.TextChoices):
    """Refund lifecycle status"""
    REQUESTED = 'requested', 'Requested'       # customer submitted request
    PENDING = 'pending', 'Pending'              # flagged for manual review
    PROCESSING = 'processing', 'Processing'    # auto rule passed, calling gateway
    PROCESSED = 'processed', 'Processed'       # gateway confirmed
    REJECTED = 'rejected', 'Rejected'          # rejected by rule or admin


class Payment(models.Model):
    """Payment model for tracking transactions"""
    
    # Primary key
    id = models.BigAutoField(primary_key=True)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    order = models.OneToOneField(
        'order_management.Order',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Payment Details
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CREDIT_CARD
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Transaction Info
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def get_method_display(self) -> str:
    #     """Get display name for payment method"""
        result = dict(PaymentMethod.choices).get(self.method)
        return str(result) if result else "Unknown"
    
    def get_status_display(self) -> str:
        """Get display name for payment status"""
        result = dict(PaymentStatus.choices).get(self.status)
        return str(result) if result else "Unknown"
    
    def __str__(self) -> str:
        return f"Payment {self.id} - {self.get_status_display()} ({self.amount})"
    
    def add_phase(self, status: str, reason: str = "", metadata: dict = None) -> 'PaymentPhase':
        """
        Log a payment phase transition.
        
        Args:
            status: The new payment status
            reason: Human-readable reason for this transition
            metadata: Additional context (e.g., error_code, gateway_response)
            
        Returns:
            PaymentPhase instance created
        """
        if metadata is None:
            metadata = {}
        
        phase = PaymentPhase.objects.create(
            payment=self,
            status=status,
            reason=reason,
            metadata=metadata
        )
        
        # Update parent Payment status to match the latest phase
        self.status = status
        self.save(update_fields=['status', 'updated_at'])
        
        return phase


class PaymentPhase(models.Model):
    """
    Payment state machine tracking.
    Records each status transition with timestamp and reason.
    Enables audit trail and debugging of payment processing issues.
    """
    
    # Relations
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='phases'
    )
    
    # Status at this phase
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices
    )
    
    # Transition context
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text='Why this status change occurred (e.g., "Payment gateway approval", "Customer cancelled")'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context like error codes, gateway responses, or retry info'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Payment Phase'
        verbose_name_plural = 'Payment Phases'
        indexes = [
            models.Index(fields=['payment', 'created_at']),
        ]
    
    def get_status_display(self) -> str:
        """Get display name for payment status"""
        result = dict(PaymentStatus.choices).get(self.status)
        return str(result) if result else "Unknown"
    
    def __str__(self) -> str:
        return f"PaymentPhase {self.payment_id} → {self.status} @ {self.created_at}"


class Refund(models.Model):
    """Refund model for tracking refund transactions"""
    
    # Primary key
    id = models.BigAutoField(primary_key=True)
    
    # Relations
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_refunds'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )

    # Refund Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Cancellation fee deducted from refund'
    )
    reason = models.TextField()
    refund_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text='Client-supplied key to prevent duplicate submissions'
    )

    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.REQUESTED
    )

    # Anti-abuse metadata
    requested_from_ip = models.GenericIPAddressField(null=True, blank=True)
    risk_score = models.SmallIntegerField(
        default=0,
        help_text='0 = clean, higher = more suspicious'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
    
    def get_status_display(self) -> str:
        """Get display name for refund status"""
        result = dict(RefundStatus.choices).get(self.status)
        return str(result) if result else "Unknown"
    
    def __str__(self) -> str:
        return f"Refund {self.id} - {self.get_status_display()} ({self.amount})"


class IPLog(models.Model):
    """Track refund requests per IP for rate-limiting and abuse detection"""
    ip_address = models.GenericIPAddressField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    endpoint = models.CharField(max_length=64, default='request_refund')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'IP Log'
        verbose_name_plural = 'IP Logs'

    def __str__(self) -> str:
        return f"IPLog {self.ip_address} @ {self.created_at}"


class IPBlacklist(models.Model):
    """Persistent IP blacklist for repeated abuse"""
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    reason = models.TextField(blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # NULL = permanent; set a date to auto-expire
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'IP Blacklist'
        verbose_name_plural = 'IP Blacklist'

    def __str__(self) -> str:
        return f"Blacklist {self.ip_address}"
