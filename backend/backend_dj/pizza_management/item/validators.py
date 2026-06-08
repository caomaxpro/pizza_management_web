from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union

class ItemCreateRequest(BaseModel):
    """Pydantic model for Item creation
    
    Note: Stock management fields (lead_time_days, safety_stock_days, stock_quantity)
    are validated here but NOT persisted on the Item model. They are reserved for
    future integration with the inventory management module. Currently, these fields
    are filtered out during Item creation in the create_mixin and are not applied.
    """
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    
    # classification & media
    type: Optional[str] = Field(None, max_length=50)
    sub_type: Optional[str] = Field(None, max_length=50)  # Add this
    image_url: Optional[str] = Field(None, max_length=500)
    
    # relationships (Ingredient IDs)
    dough: Optional[int] = Field(None, ge=1)
    sauce: Optional[int] = Field(None, ge=1)
    cheese: Optional[int] = Field(None, ge=1)
    toppings: Optional[List[int]] = None
    extras: Optional[List[int]] = None
    
    # metadata
    is_active: bool = True
    reorder_level: Optional[int] = Field(None, ge=0)
    lead_time_days: int = Field(default=3, ge=1)
    safety_stock_days: int = Field(default=2, ge=1)
    stock_quantity: int = Field(default=0, ge=0)

    # Validators
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = ["pizza", "drink", "salad", "sides", "other"]
        if v and v not in allowed:
            raise ValueError(f"Invalid type. Must be one of {allowed}")
        return v

    @field_validator('toppings', 'extras', mode='before')
    @classmethod
    def validate_id_lists(cls, v, info):
        if v and not all(isinstance(x, int) and x > 0 for x in v):
            raise ValueError("All IDs must be positive integers")
        return v

    @field_validator('sub_type')
    @classmethod
    def validate_sub_type(cls, v):
        if v is None:
            return v
        allowed = ["veggie", "meat", "cheese"]
        if v not in allowed:
            raise ValueError(f"Invalid sub_type. Must be one of {allowed}")
        return v

    @field_validator('is_active', mode='before')
    @classmethod
    def parse_is_active_create(cls, v):
        """Accept string/list values from FormData: '1'/'0'/'true'/'false'"""
        if isinstance(v, bool):
            return v
        if isinstance(v, list):
            v = v[0] if v else False
        if isinstance(v, str):
            return v.lower() in ('1', 'true', 'yes')
        return bool(v)


class ItemUpdateRequest(BaseModel):
    """Pydantic model for Item update (all fields optional)
    
    Note: Stock management fields (lead_time_days, safety_stock_days, stock_quantity)
    are validated here but NOT persisted on the Item model. They are reserved for
    future integration with the inventory management module. Currently, these fields
    are filtered out during Item updates in the update_mixin and are not applied.
    """
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    
    # classification & media
    type: Optional[str] = None
    sub_type: Optional[str] = None  # Add this
    image_url: Optional[str] = None
    
    # relationships (Ingredient IDs)
    dough: Optional[int] = Field(None, ge=1)
    sauce: Optional[int] = Field(None, ge=1)
    cheese: Optional[int] = Field(None, ge=1)
    toppings: Optional[List[int]] = None
    extras: Optional[List[int]] = None
    
    # metadata
    is_active: Optional[bool] = None
    reorder_level: Optional[int] = None

    @field_validator('is_active', mode='before')
    @classmethod
    def parse_is_active_update(cls, v):
        """Accept string/list values from FormData: '1'/'0'/'true'/'false'"""
        if v is None or isinstance(v, bool):
            return v
        if isinstance(v, list):
            v = v[0] if v else None
        if v is None:
            return None
        if isinstance(v, str):
            return v.lower() in ('1', 'true', 'yes')
        return bool(v)
    lead_time_days: Optional[int] = None
    safety_stock_days: Optional[int] = None
    stock_quantity: Optional[int] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is None:
            return v
        allowed = ["pizza", "drink", "salad", "sides", "other"]
        if v not in allowed:
            raise ValueError(f"Invalid type. Must be one of {allowed}")
        return v


class ItemFilterRequest(BaseModel):
    """Pydantic model for Item filtering query params"""
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Union[str, bool, None] = None  # Accept str, bool, or None

    @field_validator("is_active", mode="before")
    @classmethod
    def parse_bool(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v) if v is not None else None