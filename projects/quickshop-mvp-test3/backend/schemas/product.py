from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: str
    stock_quantity: int = 0
    image_url: Optional[str] = None
    is_featured: bool = False
    category_id: Optional[int] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: str
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    is_featured: bool
    in_stock: bool
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Simplified product schema for faster responses
class ProductSimple(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: Optional[str] = None
    in_stock: bool

    class Config:
        from_attributes = True