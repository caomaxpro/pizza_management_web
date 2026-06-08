from django.contrib import admin
from stock_management.models import Inventory, InventoryLog, Provider, PurchaseOrder, PurchaseOrderItem, PurchaseOrderReceipt

# Register your models here.
admin.site.register(Inventory)
admin.site.register(InventoryLog)
admin.site.register(Provider)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
admin.site.register(PurchaseOrderReceipt)