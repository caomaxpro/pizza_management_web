"""
Payment Serializers
DRF serializers for Payment and Refund models
"""
from rest_framework import serializers
from .model import Payment, Refund, PaymentPhase, PaymentMethod, PaymentStatus, RefundStatus


class PaymentPhaseSerializer(serializers.ModelSerializer):
    """Serializer for PaymentPhase model (audit trail)"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentPhase
        fields = [
            'id',
            'payment',
            'status',
            'status_display',
            'reason',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields


class RefundSerializer(serializers.ModelSerializer):
    """Full serializer for Refund model (read + admin writes)"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True, default=None)
    processed_by_email = serializers.CharField(source='processed_by.email', read_only=True, default=None)
    
    class Meta:
        model = Refund
        fields = [
            'id',
            'payment',
            'amount',
            'fee',
            'reason',
            'refund_id',
            'idempotency_key',
            'status',
            'status_display',
            'requested_by',
            'requested_by_email',
            'processed_by',
            'processed_by_email',
            'requested_from_ip',
            'risk_score',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = [
            'id', 'refund_id', 'idempotency_key',
            'requested_by', 'processed_by',
            'requested_from_ip', 'risk_score',
            'fee', 'status',
            'created_at', 'updated_at',
        ]


class RefundRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for customer refund requests.
    Accepts only payment, amount, and reason — everything else is set server-side.
    """
    # Optional client-supplied idempotency key (handled in mixin, not here)
    idempotency_key = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason', 'idempotency_key']

    def validate(self, attrs):
        payment = attrs.get('payment')
        amount = attrs.get('amount')

        if payment and payment.user != self.context['request'].user:
            raise serializers.ValidationError('You can only request refunds for your own payments.')

        if payment and amount and amount > payment.amount:
            raise serializers.ValidationError(
                f'Refund amount ({amount}) exceeds payment amount ({payment.amount}).'
            )

        # Total previously refunded
        if payment:
            already_refunded = sum(
                r.amount for r in payment.refunds.exclude(status=RefundStatus.REJECTED)
            )
            if amount and amount + already_refunded > payment.amount:
                raise serializers.ValidationError(
                    f'Total refunded ({already_refunded + amount}) would exceed payment amount ({payment.amount}).'
                )

        return attrs

    def create(self, validated_data):
        # Strip idempotency_key — handled by mixin
        validated_data.pop('idempotency_key', None)
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    phases = PaymentPhaseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'order',
            'method',
            'method_display',
            'status',
            'status_display',
            'amount',
            'transaction_id',
            'notes',
            'metadata',
            'refunds',
            'phases',
            'created_at',
            'updated_at',
            'completed_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'transaction_id']
    
    def create(self, validated_data):
        """Set user to current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for payment lists"""
    
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_id = serializers.CharField(source='order.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'method',
            'method_display',
            'status',
            'status_display',
            'amount',
            'created_at'
        ]
        read_only_fields = fields
