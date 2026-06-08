# provider/validators.py
from pydantic import BaseModel, field_validator
from typing import Optional
from django.core.exceptions import ValidationError

from stock_management.models import Provider


class ProviderValidator(BaseModel):
    """Pydantic validator for Provider creation/update"""
    
    name: str
    category: str = 'other'
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        """Validate provider name"""
        if not value or len(value.strip()) == 0:
            raise ValueError("Provider name cannot be empty")
        
        if len(value) > 255:
            raise ValueError("Provider name cannot exceed 255 characters")
        
        # Check for duplicates (case-insensitive)
        if Provider.objects.filter(name__iexact=value.strip()).exists():
            raise ValueError(f"Provider '{value}' already exists")
        
        return value.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        """Validate category is valid choice"""
        valid_categories = ['fresh', 'canned', 'bottled', 'dairy', 'equipment', 'other']
        if value not in valid_categories:
            raise ValueError(f"Invalid category. Allowed: {valid_categories}")
        return value
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value):
        """Validate phone number length"""
        if value and len(value) > 20:
            raise ValueError("Phone number cannot exceed 20 characters")
        return value
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, value):
        """Validate email format"""
        if value and len(value) > 254:
            raise ValueError("Email address too long")
        return value
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, value):
        """Validate address length"""
        if value and len(value) > 1000:
            raise ValueError("Address cannot exceed 1000 characters")
        return value


class ProviderFilterValidator(BaseModel):
    """Validator for filtering/searching providers"""
    
    category: Optional[str] = None
    search: Optional[str] = None
    is_active: Optional[bool] = None
    ordering: Optional[str] = "name"
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        """Validate category is valid choice"""
        valid_categories = ['fresh', 'canned', 'bottled', 'dairy', 'equipment', 'other']
        if value and value not in valid_categories:
            raise ValueError(f"Invalid category. Allowed: {valid_categories}")
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
        allowed = ['name', '-name', 'created_at', '-created_at', 'category', '-category']
        if value not in allowed:
            raise ValueError(f"Invalid ordering. Allowed: {allowed}")
        return value


def validate_provider_data(data: dict) -> dict:
    """Validate provider data using Pydantic"""
    try:
        validated = ProviderValidator(**data)
        return validated.model_dump()
    except ValueError as e:
        raise ValidationError(str(e))


def validate_provider_filter(query_params: dict) -> dict:
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
        if is_active:
            is_active = is_active.lower() in ('true', '1', 'yes')
        
        data = {
            'category': query_params.get('category'),
            'search': query_params.get('search'),
            'is_active': is_active if is_active is not None else None,
            'ordering': query_params.get('ordering', 'name'),
        }
        
        validated = ProviderFilterValidator(**data)
        return {k: v for k, v in validated.model_dump().items() if v is not None}
    except ValueError as e:
        raise ValidationError(str(e))
