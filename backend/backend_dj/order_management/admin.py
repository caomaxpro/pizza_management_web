from django.contrib import admin
from order_management.order.model import Order
from order_management.order.orderitem_model import OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem - allows editing items within Order admin"""
    model = OrderItem
    extra = 0
    fields = ('item', 'quantity', 'unit_price', 'subtotal', 'customizations', 'notes')
    readonly_fields = ('subtotal', 'created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model"""
    list_display = ('order_number', 'user', 'status', 'total_price', 'order_date', 'delivery_date')
    list_filter = ('status', 'order_date', 'delivery_date')
    search_fields = ('order_number', 'user__email', 'user__username')
    readonly_fields = ('order_date', 'created_at', 'updated_at', 'order_number')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'order_date', 'delivery_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model"""
    list_display = ('order', 'item', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('created_at', 'order__status')
    search_fields = ('order__order_number', 'item__name')
    readonly_fields = ('subtotal', 'created_at', 'updated_at')
