"""
Order and OrderItem models for order management
"""

from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Order(Base):
    """Order model"""
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Order identification
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Order status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # Pricing information
    subtotal = Column(Decimal(10, 2), nullable=False)
    tax_amount = Column(Decimal(10, 2), default=0, nullable=False)
    shipping_amount = Column(Decimal(10, 2), default=0, nullable=False)
    discount_amount = Column(Decimal(10, 2), default=0, nullable=False)
    total_amount = Column(Decimal(10, 2), nullable=False)
    
    # Customer information (snapshot at time of order)
    customer_email = Column(String(255), nullable=False)
    customer_first_name = Column(String(100), nullable=False)
    customer_last_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    
    # Billing address
    billing_address_line1 = Column(String(255), nullable=False)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=False)
    billing_state = Column(String(100), nullable=False)
    billing_postal_code = Column(String(20), nullable=False)
    billing_country = Column(String(100), nullable=False)
    
    # Shipping address
    shipping_address_line1 = Column(String(255), nullable=False)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), nullable=False)
    
    # Shipping information
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    
    # Payment information
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True, index=True)  # Stripe payment intent ID
    
    # Order notes and metadata
    customer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_order_user_status", "user_id", "status"),
        Index("idx_order_created_at", "created_at"),
        Index("idx_order_payment_status", "payment_status"),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"
    
    @classmethod
    def generate_order_number(cls) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4().hex[:8]).upper()
        return f"ORD-{timestamp}-{unique_id}"
    
    @property
    def customer_full_name(self) -> str:
        """Get customer full name"""
        return f"{self.customer_first_name} {self.customer_last_name}".strip()
    
    @property
    def total_items(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items)
    
    @property
    def is_paid(self) -> bool:
        """Check if order is fully paid"""
        return self.payment_status == PaymentStatus.PAID
    
    @property
    def is_completed(self) -> bool:
        """Check if order is completed"""
        return self.status == OrderStatus.DELIVERED
    
    @property
    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    def to_dict(self, include_items=True, include_user=False) -> dict:
        """Convert order to dictionary"""
        data = {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "status": self.status.value,
            "payment_status": self.payment_status.value,
            "subtotal": float(self.subtotal),
            "tax_amount": float(self.tax_amount),
            "shipping_amount": float(self.shipping_amount),
            "discount_amount": float(self.discount_amount),
            "total_amount": float(self.total_amount),
            "customer": {
                "email": self.customer_email,
                "first_name": self.customer_first_name,
                "last_name": self.customer_last_name,
                "full_name": self.customer_full_name,
                "phone": self.customer_phone
            },
            "billing_address": {
                "line1": self.billing_address_line1,
                "line2": self.billing_address_line2,
                "city": self.billing_city,
                "state": self.billing_state,
                "postal_code": self.billing_postal_code,
                "country": self.billing_country
            },
            "shipping_address": {
                "line1": self.shipping_address_line1,
                "line2": self.shipping_address_line2,
                "city": self.shipping_city,
                "state": self.shipping_state,
                "postal_code": self.shipping_postal_code,
                "country": self.shipping_country
            },
            "shipping_method": self.shipping_method,
            "tracking_number": self.tracking_number,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "customer_notes": self.customer_notes,
            "admin_notes": self.admin_notes,
            "total_items": self.total_items,
            "is_paid": self.is_paid,
            "is_completed": self.is_completed,
            "can_cancel": self.can_cancel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
        }
        
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        
        if include_user and self.user:
            data["user"] = self.user.to_dict()
        
        return data


class OrderItem(Base):
    """Order item model"""
    
    __tablename__ = "order_items"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Product information (snapshot at time of order)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=False)
    
    # Pricing and quantity
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Decimal(10, 2), nullable=False)
    total_price = Column(Decimal(10, 2), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_order_item_order", "order_id"),
        Index("idx_order_item_product", "product_id"),
    )
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, quantity={self.quantity})>"
    
    def to_dict(self, include_product=False) -> dict:
        """Convert order item to dictionary"""
        data = {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_product and self.product:
            data["product"] = self.product.to_dict(include_category=True)
        
        return data