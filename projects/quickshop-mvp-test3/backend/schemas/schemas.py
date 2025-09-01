"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    stock_quantity: int = 0
    image_url: Optional[str] = None

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductSimple(BaseModel):
    """Simplified product model for quick responses"""
    id: int
    name: str
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# Cart Schemas
class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class CartItem(BaseModel):
    product: ProductSimple
    quantity: int

class Cart(BaseModel):
    id: int
    items: List[CartItem] = []
    total: float = 0.0

# Order Schemas
class OrderCreate(BaseModel):
    shipping_address: str
    payment_method_id: Optional[str] = None  # Stripe payment method ID

class OrderItem(BaseModel):
    product: ProductSimple
    quantity: int
    price: float

class Order(BaseModel):
    id: int
    total_amount: float
    status: str
    shipping_address: Optional[str] = None
    created_at: datetime
    order_items: List[OrderItem] = []

    class Config:
        from_attributes = True

# Response Schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# Pagination Schema
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    per_page: int
    pages: int