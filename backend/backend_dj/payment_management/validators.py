"""
Payment Validators
Validation rules for payment operations
"""
from rest_framework import serializers
from .model import Payment, PaymentStatus


def validate_payment_status(status):
    """Validate payment status is valid"""
    valid_statuses = [choice[0] for choice in PaymentStatus.choices]
    if status not in valid_statuses:
        raise serializers.ValidationError(f"Invalid status: {status}")
    return status


def validate_payment_method(method):
    """Validate payment method is valid"""
    from .model import PaymentMethod
    valid_methods = [choice[0] for choice in PaymentMethod.choices]
    if method not in valid_methods:
        raise serializers.ValidationError(f"Invalid payment method: {method}")
    return method
