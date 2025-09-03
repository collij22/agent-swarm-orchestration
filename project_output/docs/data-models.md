# QuickShop MVP Data Models

## Overview
This document defines the data models used throughout the QuickShop MVP application, including SQLAlchemy ORM models for database operations and Pydantic schemas for API validation and serialization.

## SQLAlchemy Models (Database Layer)

### Base Model
```python
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### User Model
```python
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
```

### Category Model
```python
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Category(BaseModel):
    __tablename__ = "categories"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id")
    products = relationship("Product", back_populates="category")
```

### Product Model
```python
from sqlalchemy import Column, String, Text, DECIMAL, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Product(BaseModel):
    __tablename__ = "products"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
```

### CartItem Model
```python
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class CartItem(BaseModel):
    __tablename__ = "cart_items"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    
    # Constraints
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)
```

### Order Model
```python
from sqlalchemy import Column, String, DECIMAL, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

class Order(BaseModel):
    __tablename__ = "orders"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    shipping_address = Column(Text, nullable=False)
    billing_address = Column(Text, nullable=False)
    payment_status = Column(String(50), nullable=False, default="pending", index=True)
    payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
```

### OrderItem Model
```python
from sqlalchemy import Column, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship

class OrderItem(BaseModel):
    __tablename__ = "order_items"
    
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
```

## Pydantic Schemas (API Layer)

### Base Schemas
```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime
```

### User Schemas
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

class UserResponse(UserBase, TimestampMixin):
    id: int
    is_active: bool
    is_admin: bool

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### Category Schemas
```python
from pydantic import BaseModel, Field
from typing import Optional

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase, TimestampMixin):
    id: int
    is_active: bool
    product_count: Optional[int] = None
```

### Product Schemas
```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Optional

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    category_id: int
    sku: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(..., ge=0)
    image_url: Optional[str] = Field(None, max_length=500)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category_id: Optional[int] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class ProductResponse(ProductBase, TimestampMixin):
    id: int
    is_active: bool
    category: CategoryResponse

class ProductListResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: Optional[str]
    stock_quantity: int
    category: CategoryResponse
```

### Cart Schemas
```python
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel, TimestampMixin):
    id: int
    product: ProductListResponse
    quantity: int
    subtotal: Decimal

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: Decimal
```

### Order Schemas
```python
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class OrderBase(BaseModel):
    shipping_address: str = Field(..., min_length=1)
    billing_address: str = Field(..., min_length=1)
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderItemResponse(BaseModel):
    id: int
    product: ProductListResponse
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class OrderResponse(OrderBase, TimestampMixin):
    id: int
    status: OrderStatus
    total_amount: Decimal
    payment_status: PaymentStatus
    items: List[OrderItemResponse]

class OrderListResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
    payment_status: PaymentStatus
    created_at: datetime
    item_count: int
```

### Pagination Schemas
```python
from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
```

### Response Schemas
```python
from pydantic import BaseModel
from typing import Any, Optional, List, Dict

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None

class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorResponse(BaseModel):
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": [
                        {
                            "field": "email",
                            "message": "Invalid email format"
                        }
                    ]
                }
            }
        }

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
```

## Validation Rules

### Business Logic Validation
1. **Stock Management**: Ensure sufficient stock before adding to cart or creating orders
2. **Price Validation**: All prices must be positive decimal values
3. **Email Uniqueness**: Email addresses must be unique across users
4. **SKU Uniqueness**: Product SKUs must be unique
5. **Order Status Flow**: Orders must follow valid status transitions
6. **Cart Constraints**: One cart item per user-product combination

### Input Validation
1. **Email Format**: Valid email address format
2. **Password Strength**: Minimum 8 characters
3. **Phone Format**: Optional international phone format
4. **URL Format**: Valid URL format for image URLs
5. **Decimal Precision**: Prices with 2 decimal places
6. **String Lengths**: Appropriate length limits for all text fields

### Custom Validators
```python
from pydantic import validator
import re

class ProductCreate(ProductBase):
    @validator('sku')
    def validate_sku(cls, v):
        if not re.match(r'^[A-Z0-9-]+$', v):
            raise ValueError('SKU must contain only uppercase letters, numbers, and hyphens')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than zero')
        return v
```

## Model Relationships

### One-to-Many Relationships
- User  ->  Orders (one user can have many orders)
- User  ->  CartItems (one user can have many cart items)
- Category  ->  Products (one category can have many products)
- Order  ->  OrderItems (one order can have many order items)
- Product  ->  CartItems (one product can be in many cart items)
- Product  ->  OrderItems (one product can be in many order items)

### Self-Referencing Relationships
- Category  ->  Category (parent-child relationship for category hierarchy)

### Constraints and Indexes
- Unique constraints on email, SKU, and user-product cart combinations
- Indexes on frequently queried fields (email, category_id, status, etc.)
- Foreign key constraints to maintain referential integrity
- Check constraints for business rules (positive prices, quantities)