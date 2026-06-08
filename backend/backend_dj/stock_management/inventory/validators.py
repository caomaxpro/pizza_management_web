# inventory/validators.py
from pydantic import BaseModel, field_validator, model_validator, ValidationInfo
from typing import List, Literal, Optional
from django.core.exceptions import ValidationError

from .model import Inventory


class InventoryValidator(BaseModel):
    """Pydantic validator for Inventory data"""
    
    name: str
    description: Optional[str] = None
    unit: str
    current_stock: float = 0
    min_threshold: float = 0
    max_threshold: Optional[float] = None
    is_active: bool = True
    
    model_config = {'extra': 'allow'}  # Allow extra fields (like from context)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, value, info: ValidationInfo):
        """Validate inventory name"""
        if not value or len(value.strip()) == 0:
            raise ValueError("Name cannot be empty")
        
        if len(value) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        
        # Check for duplicates (case-insensitive), excluding the current instance if updating
        query = Inventory.objects.filter(name__iexact=value.strip())
        
        # If validating an update, exclude the current instance
        if info.context and 'exclude_id' in info.context:
            query = query.exclude(id=info.context['exclude_id'])
        
        if query.exists():
            raise ValueError(f"Item '{value}' already exists")
        
        return value.strip()
    
    @field_validator('current_stock', 'min_threshold', 'max_threshold')
    @classmethod
    def validate_positive(cls, value):
        """Validate all stock values are non-negative"""
        if value is not None and value < 0:
            raise ValueError("Stock values cannot be negative")
        return value
    
    @model_validator(mode='after')
    def validate_thresholds(self):
        """Validate threshold relationships"""
        if self.max_threshold and self.min_threshold > self.max_threshold:
            raise ValueError("min_threshold cannot be > max_threshold")
        
        if self.current_stock > self.max_threshold if self.max_threshold else False:
            raise ValueError(f"current_stock ({self.current_stock}) exceeds max_threshold ({self.max_threshold})")
        
        return self


class InventoryFilterValidator(BaseModel):
    """
    Validator for filtering/searching inventory items.
    
    Allows:
    - is_active: boolean filter
    - search: text search in name/description
    - ordering: order by field
    - min_stock: filter items with stock >= min_stock
    - max_stock: filter items with stock <= max_stock
    """
    
    is_active: Optional[bool] = None
    search: Optional[str] = None
    ordering: Optional[str] = "-created_at"
    min_stock: Optional[float] = None
    max_stock: Optional[float] = None

    @field_validator('search')
    @classmethod
    def validate_search(cls, value):
        """Search string max length"""
        if value and len(value) > 100:
            raise ValueError("Search query too long (max 100 chars)")
        return value
    
    @field_validator('ordering')
    @classmethod
    def validate_ordering(cls, value):
        """Validate ordering field"""
        allowed = ['name', '-name', 'created_at', '-created_at', 'current_stock', '-current_stock']
        if value not in allowed:
            raise ValueError(f"Invalid ordering. Allowed: {allowed}")
        return value
    
    @field_validator('min_stock', 'max_stock')
    @classmethod
    def validate_stock_values(cls, value):
        """Validate stock values are non-negative"""
        if value is not None and value < 0:
            raise ValueError("Stock values cannot be negative")
        return value


class BulkLogEntryValidator(BaseModel):
    """Validator for a single InventoryLog entry in a bulk create request."""
    inventory_id: int
    quantity_change: float
    reason_type: Literal['receipt', 'stock_take']
    reason_detail: Optional[str] = None

    @field_validator('quantity_change')
    @classmethod
    def validate_nonzero(cls, v):
        if v == 0:
            raise ValueError("quantity_change cannot be zero")
        return v


class BulkLogCreateValidator(BaseModel):
    """Validator for the full bulk log create payload."""
    entries: List[BulkLogEntryValidator]

    @model_validator(mode='after')
    def validate_nonempty(self):
        if not self.entries:
            raise ValueError("At least one log entry is required")
        return self


def validate_inventory_data(data: dict, exclude_id: Optional[int] = None) -> dict:
    """Validate inventory data using Pydantic
    
    Args:
        data: Inventory data to validate
        exclude_id: ID of the current instance (for updates) to exclude from duplicate check
    """
    try:
        context = {'exclude_id': exclude_id} if exclude_id else {}
        validated = InventoryValidator.model_validate(data, context=context)
        return validated.model_dump()
    except ValueError as e:
        raise ValidationError(str(e))


def validate_inventory_filter(query_params: dict) -> dict:
    """
    Validate and parse filter/search query parameters.
    
    Args:
        query_params: dict from request.query_params
        
    Returns:
        Validated filter dict
    """
    try:
        # Convert string booleans to actual booleans
        is_active = query_params.get('is_active')
        
        # Handle list values (from QueryDict) or string values
        if isinstance(is_active, list):
            is_active = is_active[0] if is_active else None
        
        if is_active:
            is_active = str(is_active).lower() in ('true', '1', 'yes')
        
        # Handle search parameter (same list handling)
        search = query_params.get('search')
        if isinstance(search, list):
            search = search[0] if search else None
        
        # Handle min_stock and max_stock (also handle lists)
        min_stock = query_params.get('min_stock')
        if isinstance(min_stock, list):
            min_stock = min_stock[0] if min_stock else None
        
        max_stock = query_params.get('max_stock')
        if isinstance(max_stock, list):
            max_stock = max_stock[0] if max_stock else None
        
        data = {
            'is_active': is_active if is_active is not None else None,
            'search': search,
            'ordering': query_params.get('ordering', '-created_at'),
            'min_stock': float(min_stock) if min_stock else None,
            'max_stock': float(max_stock) if max_stock else None,
        }
        
        validated = InventoryFilterValidator(**data)
        return {k: v for k, v in validated.model_dump().items() if v is not None}
    except ValueError as e:
        raise ValidationError(str(e))


def validate_stock_adjustment(inventory_id: int, quantity: float, reason: str = "") -> dict:
    """Validate stock adjustment parameters"""
    class StockAdjustmentValidator(BaseModel):
        inventory_id: int
        quantity: float
        reason: str = ""
        
        @field_validator('inventory_id')
        @classmethod
        def validate_inventory_exists(cls, value):
            if not Inventory.objects.filter(id=value).exists():
                raise ValueError(f"Inventory {value} not found")
            return value
        
        @field_validator('quantity')
        @classmethod
        def validate_quantity(cls, value):
            if value == 0:
                raise ValueError("Quantity cannot be zero")
            return value
        
        @field_validator('reason')
        @classmethod
        def validate_reason(cls, value):
            if len(value) > 255:
                raise ValueError("Reason cannot exceed 255 characters")
            return value
    
    try:
        validated = StockAdjustmentValidator(
            inventory_id=inventory_id,
            quantity=quantity,
            reason=reason
        )
        return validated.model_dump()
    except ValueError as e:
        raise ValidationError(str(e))