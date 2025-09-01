from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.core.database import Base


class OrderStatus(PyEnum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(PyEnum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    """Order model for order management"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Pricing
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    shipping_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Shipping information
    shipping_first_name = Column(String(100), nullable=False)
    shipping_last_name = Column(String(100), nullable=False)
    shipping_email = Column(String(255), nullable=False)
    shipping_phone = Column(String(20), nullable=True)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_country = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    
    # Billing information (can be same as shipping)
    billing_first_name = Column(String(100), nullable=False)
    billing_last_name = Column(String(100), nullable=False)
    billing_email = Column(String(255), nullable=False)
    billing_phone = Column(String(20), nullable=True)
    billing_address = Column(Text, nullable=False)
    billing_city = Column(String(100), nullable=False)
    billing_state = Column(String(100), nullable=False)
    billing_country = Column(String(100), nullable=False)
    billing_postal_code = Column(String(20), nullable=False)
    
    # Payment information
    payment_method = Column(String(50), nullable=True)  # stripe, paypal, etc.
    payment_intent_id = Column(String(255), nullable=True)  # Stripe payment intent ID
    transaction_id = Column(String(255), nullable=True)
    
    # Order notes
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Tracking
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def shipping_full_name(self):
        """Get full shipping name"""
        return f"{self.shipping_first_name} {self.shipping_last_name}"

    @property
    def billing_full_name(self):
        """Get full billing name"""
        return f"{self.billing_first_name} {self.billing_last_name}"

    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == PaymentStatus.COMPLETED

    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Product details at time of order (for historical accuracy)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100), nullable=False)
    product_image_url = Column(String(500), nullable=True)
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product='{self.product_name}', quantity={self.quantity})>"