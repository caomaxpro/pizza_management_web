"""
Django management command to seed dummy order and payment data for testing.

Usage:
    python manage.py seed_dummy_data           # seed 100 orders
    python manage.py seed_dummy_data --count 50
    python manage.py seed_dummy_data --clear   # clear existing seed data first
    python manage.py seed_dummy_data --clear --count 100
"""
import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

SEED_EMAIL_SUFFIX = "@seed.test"

ORDER_STATUSES = [
    ("delivered", 40),
    ("cancelled", 15),
    ("pending", 15),
    ("confirmed", 10),
    ("preparing", 10),
    ("ready", 10),
]

PAYMENT_METHODS = [
    ("cash", 30),
    ("credit_card", 25),
    ("debit_card", 20),
    ("paypal", 15),
    ("bank_transfer", 10),
]

ITEMS_DATA = [
    ("Margherita Pizza", 14.99, "pizza"),
    ("Pepperoni Pizza", 16.99, "pizza"),
    ("BBQ Chicken Pizza", 18.99, "pizza"),
    ("Veggie Supreme", 14.99, "pizza"),
    ("Four Cheese Pizza", 17.99, "pizza"),
    ("Caesar Salad", 9.99, "salad"),
    ("Garden Salad", 7.99, "salad"),
    ("Coca Cola", 2.99, "drink"),
    ("Sprite", 2.99, "drink"),
    ("Garlic Bread", 4.99, "sides"),
]

CUSTOMER_NAMES = [
    ("customer1", "Nguyen Van A"),
    ("customer2", "Tran Thi B"),
    ("customer3", "Le Van C"),
]

DELIVERY_ADDRESSES = [
    "123 Nguyen Hue, District 1, Ho Chi Minh City",
    "456 Le Loi, District 3, Ho Chi Minh City",
    "789 Tran Hung Dao, District 5, Ho Chi Minh City",
    "321 Pham Ngu Lao, District 1, Ho Chi Minh City",
    "654 Vo Van Tan, District 3, Ho Chi Minh City",
    "987 Nguyen Thi Minh Khai, District 1, Ho Chi Minh City",
    "111 Dien Bien Phu, Binh Thanh District, Ho Chi Minh City",
    "222 Hoang Dieu, District 4, Ho Chi Minh City",
]


def _weighted_choice(weighted_list):
    """Pick a value from [(value, weight), ...] weighted randomly."""
    total = sum(w for _, w in weighted_list)
    r = random.randint(1, total)
    cumulative = 0
    for value, weight in weighted_list:
        cumulative += weight
        if r <= cumulative:
            return value
    return weighted_list[-1][0]


class Command(BaseCommand):
    help = "Seed dummy order and payment data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of orders to create (default: 100)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="Spread orders over this many past days (default: 60)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seed data before seeding",
        )

    def handle(self, *args, **options):
        count = options["count"]
        days = options["days"]
        do_clear = options["clear"]

        if do_clear:
            self._clear_seed_data()

        users = self._get_or_create_users()
        items = self._get_or_create_items()

        self.stdout.write(f"Seeding {count} orders spread over last {days} days...")

        orders_created = 0
        payments_created = 0
        refunds_created = 0

        for i in range(count):
            order = self._create_order(users, items, days)
            payment = self._create_payment(order)
            orders_created += 1
            payments_created += 1

            # Create refund for some cancelled/refunded payments
            if payment.status in ("refunded",) or (
                payment.status == "failed" and random.random() < 0.3
            ):
                self._create_refund(payment)
                refunds_created += 1

            if (i + 1) % 20 == 0:
                self.stdout.write(f"  Created {i + 1}/{count} orders...")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created: {orders_created} orders, "
            f"{payments_created} payments, {refunds_created} refunds."
        ))

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _clear_seed_data(self):
        """Delete orders/payments for seed users."""
        from order_management.order.model import Order
        from payment_management.model import Payment

        seed_users = User.objects.filter(
            email__endswith=SEED_EMAIL_SUFFIX
        )
        deleted_orders, _ = Order.objects.filter(user__in=seed_users).delete()
        self.stdout.write(
            self.style.WARNING(f"Cleared {deleted_orders} orders from seed users.")
        )

    def _get_or_create_users(self):
        users = []
        for username, full_name in CUSTOMER_NAMES:
            email = f"{username}{SEED_EMAIL_SUFFIX}"
            first, *rest = full_name.split()
            last = " ".join(rest)
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": f"{username}_seed",
                    "first_name": first,
                    "last_name": last,
                    "role": "customer",
                    "is_active": True,
                },
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
                self.stdout.write(f"  Created user: {email}")
            users.append(user)
        return users

    def _get_or_create_items(self):
        from pizza_management.item.model import Item

        existing = list(Item.objects.filter(is_active=True)[:20])
        if existing:
            self.stdout.write(f"  Using {len(existing)} existing items.")
            return existing

        # Create minimal items without ingredient FKs
        created_items = []
        for name, price, item_type in ITEMS_DATA:
            item, created = Item.objects.get_or_create(
                name=name,
                defaults={
                    "price": float(price),
                    "type": item_type,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  Created item: {name}")
            created_items.append(item)
        return created_items

    def _create_order(self, users, items, days):
        from order_management.order.model import Order
        from order_management.order.orderitem_model import OrderItem

        user = random.choice(users)
        status = _weighted_choice(ORDER_STATUSES)

        # Random date in the past `days` days
        days_ago = random.randint(0, days)
        hours_ago = random.randint(0, 23)
        order_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)

        delivery_date = None
        if status == "delivered":
            delivery_date = order_date + timedelta(hours=random.randint(1, 3))

        # Build order items
        num_items = random.randint(1, 4)
        chosen_items = random.choices(items, k=num_items)

        cancellation_fee = Decimal("0.00")
        cancellation_reason = None
        if status == "cancelled":
            cancellation_reason = random.choice([
                "Customer changed mind",
                "Duplicate order",
                "Long wait time",
                "Address error",
            ])

        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Calculate total
        subtotals = []
        item_data = []
        for item in chosen_items:
            qty = random.randint(1, 3)
            unit_price = Decimal(str(round(item.price, 0)))
            subtotal = unit_price * qty
            subtotals.append(subtotal)
            item_data.append((item, qty, unit_price, subtotal))

        delivery_fee = Decimal(str(random.choice([2.50, 3.00, 3.50, 4.00, 4.50, 5.50])))
        total_price = sum(subtotals) + delivery_fee

        if status == "cancelled" and random.random() < 0.5:
            cancellation_fee = (total_price * Decimal("0.20")).quantize(Decimal("1"))

        order = Order(
            user=user,
            order_number=order_number,
            status=status,
            total_price=total_price,
            delivery_address=random.choice(DELIVERY_ADDRESSES),
            notes=None,
            cancellation_fee=cancellation_fee,
            cancellation_reason=cancellation_reason,
            delivery_date=delivery_date,
        )
        order.save()

        # Backdate order_date and created_at using update()
        Order.objects.filter(pk=order.pk).update(
            order_date=order_date,
            created_at=order_date,
            updated_at=order_date,
        )
        order.refresh_from_db()

        # Create order items
        for item, qty, unit_price, subtotal in item_data:
            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal,
            )

        return order

    def _create_payment(self, order):
        from payment_management.model import Payment, PaymentMethod, PaymentStatus

        method = _weighted_choice(PAYMENT_METHODS)

        # Determine payment status based on order status
        status_map = {
            "delivered": "completed",
            "confirmed": "completed",
            "ready": "completed",
            "preparing": "processing",
            "pending": random.choice(["pending", "processing"]),
            "cancelled": random.choice(["failed", "refunded"]),
        }
        pay_status = status_map.get(order.status, "pending")

        completed_at = None
        if pay_status == "completed":
            completed_at = order.updated_at + timedelta(minutes=random.randint(1, 10))

        transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"

        payment = Payment(
            user=order.user,
            order=order,
            method=method,
            status=pay_status,
            amount=order.total_price,
            transaction_id=transaction_id,
            completed_at=completed_at,
        )
        payment.save()

        # Backdate created_at to match order
        Payment.objects.filter(pk=payment.pk).update(
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        payment.refresh_from_db()
        return payment

    def _create_refund(self, payment):
        from payment_management.model import Refund, RefundStatus

        refund_amount = payment.amount * Decimal("0.8")  # 80% after 20% fee
        fee = payment.amount * Decimal("0.2")

        status_choices = ["processed", "processing", "pending", "requested"]
        refund_status = random.choice(status_choices)

        completed_at = None
        if refund_status == "processed":
            completed_at = payment.created_at + timedelta(days=random.randint(1, 5))

        Refund.objects.create(
            payment=payment,
            requested_by=payment.user,
            amount=refund_amount.quantize(Decimal("1")),
            fee=fee.quantize(Decimal("1")),
            reason=random.choice([
                "Order cancelled by customer",
                "Item unavailable",
                "Delivery issue",
                "Duplicate payment",
            ]),
            refund_id=f"REF-{uuid.uuid4().hex[:12].upper()}",
            idempotency_key=uuid.uuid4().hex,
            status=refund_status,
            risk_score=random.randint(0, 20),
            completed_at=completed_at,
        )
