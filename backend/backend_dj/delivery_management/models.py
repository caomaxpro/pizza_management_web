from django.utils import timezone

from django.db import models
from simple_history.models import HistoricalRecords

from pizza_management.models import Item

# Create your models here.

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("preparing", "Preparing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    ORDER_TYPE_CHOICES = [("delivery", "Delivery"), ("pickup", "Pickup")]
    PAYMENT_METHOD_CHOICES = [("card", "Card"), ("cash", "Cash"), ("online", "Online")]
    PAYMENT_STATUS_CHOICES = [("pending", "Pending"), ("paid", "Paid"), ("collected", "Collected"), ("refunded", "Refunded")]

    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_phone = models.CharField(max_length=30, null=True, blank=True)
    user = models.ForeignKey('user_management.User', null=True, blank=True, on_delete=models.SET_NULL)
    total = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default="delivery")
    pickup_shop = models.ForeignKey("Shop", null=True, blank=True, on_delete=models.SET_NULL, related_name="pickup_orders")
    shipping_address = models.ForeignKey('user_management.Address', null=True, blank=True, on_delete=models.SET_NULL, related_name="shipping_orders")
    shipping_snapshot = models.JSONField(null=True, blank=True)
    delivery_fee = models.FloatField(default=0.0)
    tip = models.FloatField(default=0.0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    is_prepaid = models.BooleanField(default=False)
    scheduled_time = models.DateTimeField(null=True, blank=True)         # scheduled delivery/pickup
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    delivery_instructions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    items = models.ManyToManyField(Item, through="OrderItem", related_name="orders")

    history = HistoricalRecords()

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name or 'Guest'}"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)  # the menu item (could be a pizza, drink, etc.)
    qty = models.IntegerField(default=1)
    unit_price = models.FloatField()  # snapshot of price at order time

    # Snapshot of chosen ingredients/customization at order time.
    # Example structure:
    # {
    #   "dough": {"id": 12, "name":"Thin", "price": 1.0},
    #   "sauce": {...},
    #   "cheese": {...},
    #   "toppings": [{"id":3,"name":"Pepperoni","qty":2}, ...],
    #   "extras": [...]
    # }
    customization = models.JSONField(null=True, blank=True)

    class Meta:
        # keep flexibility — don't enforce unique_together for composite items
        pass


class Shop(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    phone = models.CharField(max_length=30, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    default_preparation_time_minutes = models.IntegerField(default=15)
    opening_hours = models.TextField(null=True, blank=True)  # or JSON
    created_at = models.DateTimeField(default=timezone.now)


DELIVERY_STATUS = [
    ("requested","Requested"),
    ("assigned","Assigned"),
    ("accepted","Accepted"),
    ("arrived_shop","Arrived at shop"),
    ("waiting_for_order","Waiting for order"),
    ("order_placed","Order placed"),
    ("collected","Collected"),
    ("on_way","On the way"),
    ("delivered","Delivered"),
    ("failed","Failed"),
    ("cancelled","Cancelled"),
]


class Delivery(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=DELIVERY_STATUS, default="requested")
    accepted_at = models.DateTimeField(null=True, blank=True) # out for delivery
    arrived_at = models.DateTimeField(null=True, blank=True) 
    collected_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True) # delivered at
    otp = models.CharField(max_length=8, null=True, blank=True)
    payment_collected = models.FloatField(null=True, blank=True)
    proof_photo = models.CharField(max_length=500, null=True, blank=True)  # url/path
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now) # order confirmed
    
    history = HistoricalRecords()
