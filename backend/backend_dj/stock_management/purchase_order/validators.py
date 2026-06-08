# purchase_order/validators.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date
from django.core.exceptions import ValidationError

from stock_management.models import PurchaseOrder, Provider, Inventory


class PurchaseOrderValidator(BaseModel):
    """Pydantic validator for PurchaseOrder creation/update"""
    
    order_number: str
    provider_id: int
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    
    @field_validator('order_number')
    @classmethod
    def validate_order_number(cls, value):
        """Validate PO number format"""
        if not value:
            raise ValueError("Order number cannot be empty")
        
        if not value.startswith('PO-'):
            raise ValueError("Order number must start with 'PO-'")
        
        if len(value) > 100:
            raise ValueError("Order number cannot exceed 100 characters")
        
        return value
    
    @field_validator('provider_id')
    @classmethod
    def validate_provider(cls, value):
        """Validate provider exists and is active"""
        try:
            provider = Provider.objects.get(id=value)
            if not provider.is_active:
                raise ValueError(f"Provider '{provider.name}' is inactive")
            return value
        except Provider.DoesNotExist:
            raise ValueError(f"Provider with ID {value} not found")
    
    @field_validator('expected_delivery_date')
    @classmethod
    def validate_delivery_date(cls, value):
        """Validate delivery date is in future"""
        if value and value < date.today():
            raise ValueError("Expected delivery date cannot be in the past")
        return value
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, value):
        """Validate notes length"""
        if value and len(value) > 1000:
            raise ValueError("Notes cannot exceed 1000 characters")
        return value


class PurchaseOrderItemValidator(BaseModel):
    """Pydantic validator for PurchaseOrderItem"""
    
    inventory_id: int
    quantity: float
    actual_unit_price: Optional[float] = None
    
    @field_validator('inventory_id')
    @classmethod
    def validate_inventory(cls, value):
        """Validate inventory exists"""
        try:
            inventory = Inventory.objects.get(id=value)
            if not inventory.is_active:
                raise ValueError(f"Inventory '{inventory.name}' is inactive")
            return value
        except Inventory.DoesNotExist:
            raise ValueError(f"Inventory with ID {value} not found")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, value):
        """Validate quantity > 0"""
        if value <= 0:
            raise ValueError("Quantity must be greater than 0")
        return value
    
    @field_validator('actual_unit_price')
    @classmethod
    def validate_unit_price(cls, value):
        """Validate unit price is positive"""
        if value is not None and value < 0:
            raise ValueError("Unit price cannot be negative")
        return value


class PurchaseOrderFilterValidator(BaseModel):
    """Validator for filtering purchase orders"""
    
    status: Optional[str] = None
    provider_id: Optional[int] = None
    search: Optional[str] = None
    ordering: Optional[str] = "-order_date"
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, value):
        """Validate status is valid choice"""
        valid_statuses = ['pending', 'received', 'cancelled']
        if value and value not in valid_statuses:
            raise ValueError(f"Invalid status. Allowed: {valid_statuses}")
        return value
    
    @field_validator('provider_id')
    @classmethod
    def validate_provider_exists(cls, value):
        """Validate provider exists"""
        if value:
            try:
                Provider.objects.get(id=value)
                return value
            except Provider.DoesNotExist:
                raise ValueError(f"Provider with ID {value} not found")
        return value
    
    @field_validator('search')
    @classmethod
    def validate_search(cls, value):
        """Validate search string length"""
        if value and len(value) > 100:
            raise ValueError("Search query too long (max 100 chars)")
        return value
    
    @field_validator('ordering')
    @classmethod
    def validate_ordering(cls, value):
        """Validate ordering field"""
        allowed = [
            'order_number', '-order_number',
            'order_date', '-order_date',
            'status', '-status',
            'total_cost', '-total_cost'
        ]
        if value not in allowed:
            raise ValueError(f"Invalid ordering. Allowed: {allowed}")
        return value


def validate_purchase_order_data(data: dict) -> dict:
    """Validate purchase order data using Pydantic"""
    try:
        validated = PurchaseOrderValidator(**data)
        return validated.model_dump()
    except ValueError as e:
        raise ValidationError(str(e))


def validate_purchase_order_item_data(data: dict) -> dict:
    """Validate purchase order item data"""
    try:
        validated = PurchaseOrderItemValidator(**data)
        return validated.model_dump()
    except ValueError as e:
        raise ValidationError(str(e))


def validate_purchase_order_filter(query_params: dict) -> dict:
    """Validate and parse filter query parameters"""
    try:
        data = {
            'status': query_params.get('status'),
            'provider_id': int(query_params['provider_id']) if 'provider_id' in query_params and query_params['provider_id'] else None,
            'search': query_params.get('search'),
            'ordering': query_params.get('ordering', '-order_date'),
        }
        
        validated = PurchaseOrderFilterValidator(**data)
        return {k: v for k, v in validated.model_dump().items() if v is not None}
    except ValueError as e:
        raise ValidationError(str(e))
