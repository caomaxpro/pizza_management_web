from order_management.order.model import Order


class OrderService:
    """
    Service class for order-related operations.
    """
    
    @staticmethod
    def get_user_orders(user_id: int):
        """Get all orders for a specific user."""
        return Order.objects.filter(user_id=user_id)
    
    @staticmethod
    def get_pending_orders():
        """Get all pending orders."""
        return Order.objects.filter(status='pending')
    
    @staticmethod
    def get_orders_by_status(status: str):
        """Get orders by status."""
        return Order.objects.filter(status=status)
