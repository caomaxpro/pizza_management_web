from django.test import TestCase
from django.contrib.auth.models import User
from order_management.order.model import Order


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
    
    def test_create_order(self):
        order = Order.objects.create(
            user=self.user,
            order_number='ORD-001',
            delivery_address='123 Main St',
            total_price=25.99
        )
        self.assertEqual(order.order_number, 'ORD-001')
        self.assertEqual(order.status, 'pending')
