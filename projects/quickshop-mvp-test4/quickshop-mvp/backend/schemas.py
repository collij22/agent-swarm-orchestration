from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

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
    refresh_token: str
    token_type: str = "bearer"

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: int
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    category: Category
    
    class Config:
        from_attributes = True

class ProductSimple(BaseModel):
    """Simplified product model for listings"""
    id: int
    name: str
    price: float
    image_url: Optional[str] = None
    stock_quantity: int
    
    class Config:
        from_attributes = True

# Cart schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItem(CartItemBase):
    id: int
    product: ProductSimple
    created_at: datetime
    
    class Config:
        from_attributes = True

class Cart(BaseModel):
    id: int
    items: List[CartItem] = []
    total_amount: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Order schemas
class OrderCreate(BaseModel):
    shipping_address: str

class OrderItem(BaseModel):
    id: int
    product_id: int
    product: ProductSimple
    quantity: int
    price_at_time: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    total_amount: float
    status: str
    shipping_address: str
    items: List[OrderItem] = []
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Payment schemas
class PaymentIntentCreate(BaseModel):
    amount: float
    currency: str = "usd"
    order_id: Optional[int] = None

class PaymentIntent(BaseModel):
    client_secret: str
    payment_intent_id: str

# Admin schemas
class AdminStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    recent_orders: List[Order] = []

# Search and filter schemas
class ProductFilter(BaseModel):
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search: Optional[str] = None
    in_stock: Optional[bool] = None