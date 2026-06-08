"""
Payment Admin
Django admin configuration for payment models
"""
from django.contrib import admin
from .model import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model"""
    list_display = ['id', 'user', 'order', 'amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['user__email', 'transaction_id', 'order__id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'order')
        }),
        ('Payment Details', {
            'fields': ('method', 'amount', 'status')
        }),
        ('Transaction', {
            'fields': ('transaction_id', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin for Refund model"""
    list_display = ['id', 'payment', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__id', 'refund_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Reference', {
            'fields': ('payment',)
        }),
        ('Refund Details', {
            'fields': ('amount', 'status', 'reason')
        }),
        ('Transaction', {
            'fields': ('refund_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
