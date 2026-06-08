from django.contrib import admin
from .models import Order, Delivery
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'customer_name', 'status', 'total', 'created_at')

@admin.register(Delivery)
class DeliveryAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'order', 'status', 'created_at')