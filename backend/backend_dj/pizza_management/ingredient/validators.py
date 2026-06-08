from typing import Optional

from pydantic import BaseModel, Field, field_validator


class IngredientCreateRequest(BaseModel):
    """Pydantic model for Ingredient creation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    
    type: str = Field(...)
    sub_type: Optional[str] = Field(None, max_length=50)
    
    image_url: Optional[str] = Field(None, max_length=500)
    piece_image_url: Optional[str] = Field(None, max_length=500)
    
    is_active: bool = True

    # Parse form-data strings to correct types
    @field_validator('price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if isinstance(v, str):
            return float(v)
        return v

    @field_validator('is_active', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return v

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = ["dough", "sauce", "cheese", "topping", "extra"]
        if v not in allowed:
            raise ValueError(f"Invalid type. Must be one of {allowed}")
        return v

    @field_validator('sub_type')
    @classmethod
    def validate_sub_type(cls, v, info):
        if v and info.data.get('type') != 'topping':
            raise ValueError("sub_type is only allowed for topping type.")
        return v


class IngredientUpdateRequest(BaseModel):
    """Pydantic model for Ingredient update"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    image_url: Optional[str] = None
    piece_image_url: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return float(v)
        return v
    
    @field_validator('original_price', mode='before')
    @classmethod
    def parse_original_price(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return float(v)
        return v

    @field_validator('is_active', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return v

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is None:
            return v
        allowed = ["dough", "sauce", "cheese", "topping", "extra"]
        if v not in allowed:
            raise ValueError(f"Invalid type. Must be one of {allowed}")
        return v


class IngredientFilterRequest(BaseModel):
    """Pydantic model for Ingredient filtering"""
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("is_active", mode="before")
    @classmethod
    def parse_bool(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return v