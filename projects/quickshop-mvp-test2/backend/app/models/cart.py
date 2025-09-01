"""
Cart and CartItem models for shopping cart functionality
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Dict, Any

from app.core.database import Base


class Cart(Base):
    """Shopping cart model"""
    
    __tablename__ = "carts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User relationship (optional for guest carts)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Session identifier for guest carts
    session_id = Column(String(255), nullable=True, index=True)
    
    # Cart status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Ensure one active cart per user
    __table_args__ = (
        UniqueConstraint("user_id", "is_active", name="uq_user_active_cart"),
        Index("idx_cart_session", "session_id", "is_active"),
    )
    
    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id}, items_count={len(self.items)})>"
    
    @property
    def total_items(self) -> int:
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items)
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total cart price (same as subtotal for now)"""
        return self.subtotal
    
    def get_item_by_product(self, product_id: int) -> "CartItem":
        """Get cart item by product ID"""
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None
    
    def to_dict(self, include_items=True) -> dict:
        """Convert cart to dictionary"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "is_active": self.is_active,
            "total_items": self.total_items,
            "subtotal": float(self.subtotal),
            "total_price": float(self.total_price),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        
        return data


class CartItem(Base):
    """Cart item model"""
    
    __tablename__ = "cart_items"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Item details
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Decimal(10, 2), nullable=False)  # Price at time of adding to cart
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    
    # Unique constraint to prevent duplicate items in same cart
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        Index("idx_cart_item_cart_product", "cart_id", "product_id"),
    )
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, product_id={self.product_id}, quantity={self.quantity})>"
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price for this cart item"""
        return self.unit_price * self.quantity
    
    def to_dict(self, include_product=True) -> dict:
        """Convert cart item to dictionary"""
        data = {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_product and self.product:
            data["product"] = self.product.to_dict(include_category=True)
        
        return data