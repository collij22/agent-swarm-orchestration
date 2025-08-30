from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    sku: str
    image_url: Optional[str] = None

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

    @validator('stock_quantity')
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError('Stock quantity must be non-negative')
        return v

class ProductCreate(ProductBase):
    category_ids: Optional[List[int]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    category_ids: Optional[List[int]] = None

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    categories: List[CategoryResponse] = []

    class Config:
        from_attributes = True

# Cart schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse
    subtotal: float

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
    item_count: int

# Order schemas
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    shipping_address: str

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    order_number: str
    status: str
    total_amount: float
    payment_status: str
    created_at: datetime
    updated_at: Optional[datetime]
    order_items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

# Payment schemas
class PaymentIntentCreate(BaseModel):
    amount: float
    currency: str = "usd"
    order_id: Optional[int] = None

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str

# Admin schemas
class AdminStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    recent_orders: List[OrderResponse]

# Search and filter schemas
class ProductSearch(BaseModel):
    query: Optional[str] = None
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: bool = False
    limit: int = 20
    offset: int = 0