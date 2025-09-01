from pydantic import BaseModel
from typing import List
from datetime import datetime
from decimal import Decimal
from .product import ProductResponse

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    product: ProductResponse
    created_at: datetime

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_amount: Decimal
    total_items: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True