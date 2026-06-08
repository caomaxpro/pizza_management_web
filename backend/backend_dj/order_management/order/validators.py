from django.core.exceptions import ValidationError


def validate_order_data(data: dict) -> None:
    """
    Validate order data.
    
    Args:
        data: Dictionary containing order fields
        
    Raises:
        ValidationError: If validation fails
    """
    if not data.get('order_number'):
        raise ValidationError('Order number is required')
    
    if not data.get('delivery_address'):
        raise ValidationError('Delivery address is required')
    
    total_price = data.get('total_price')
    if total_price is not None and total_price < 0:
        raise ValidationError('Total price cannot be negative')
