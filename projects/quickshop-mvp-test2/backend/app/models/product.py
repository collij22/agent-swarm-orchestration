"""
Product and Category models for catalog management
"""

from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Dict, Any

from app.core.database import Base


class Category(Base):
    """Product category model"""
    
    __tablename__ = "categories"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Category information
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy support
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Display properties
    image_url = Column(String(500), nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Status and ordering
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # SEO fields
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"
    
    def to_dict(self, include_products=False) -> dict:
        """Convert category to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": self.parent_id,
            "image_url": self.image_url,
            "icon": self.icon,
            "color": self.color,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "product_count": len(self.products) if self.products else 0
        }
        
        if include_products:
            data["products"] = [product.to_dict() for product in self.products]
        
        return data


class Product(Base):
    """Product model"""
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic product information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    
    # Pricing
    price = Column(Decimal(10, 2), nullable=False, index=True)
    compare_price = Column(Decimal(10, 2), nullable=True)  # Original price for discounts
    cost_price = Column(Decimal(10, 2), nullable=True)     # Cost for profit calculations
    
    # Inventory
    sku = Column(String(100), unique=True, nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)
    track_inventory = Column(Boolean, default=True, nullable=False)
    
    # Physical properties
    weight = Column(Decimal(8, 2), nullable=True)  # in kg
    dimensions_length = Column(Decimal(8, 2), nullable=True)  # in cm
    dimensions_width = Column(Decimal(8, 2), nullable=True)   # in cm
    dimensions_height = Column(Decimal(8, 2), nullable=True)  # in cm
    
    # Category relationship
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Images and media
    featured_image = Column(String(500), nullable=True)
    gallery_images = Column(Text, nullable=True)  # JSON string of image URLs
    
    # Status and visibility
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_digital = Column(Boolean, default=False, nullable=False)
    
    # SEO and marketing
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Analytics
    view_count = Column(Integer, default=0, nullable=False)
    purchase_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_product_category_active", "category_id", "is_active"),
        Index("idx_product_price_active", "price", "is_active"),
        Index("idx_product_featured_active", "is_featured", "is_active"),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low in stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage"""
        if self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100, 2)
        return 0.0
    
    @property
    def profit_margin(self) -> float:
        """Calculate profit margin percentage"""
        if self.cost_price and self.cost_price > 0:
            return round(((self.price - self.cost_price) / self.price) * 100, 2)
        return 0.0
    
    def to_dict(self, include_category=True) -> dict:
        """Convert product to dictionary"""
        import json
        
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "price": float(self.price) if self.price else 0,
            "compare_price": float(self.compare_price) if self.compare_price else None,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "low_stock_threshold": self.low_stock_threshold,
            "track_inventory": self.track_inventory,
            "weight": float(self.weight) if self.weight else None,
            "dimensions": {
                "length": float(self.dimensions_length) if self.dimensions_length else None,
                "width": float(self.dimensions_width) if self.dimensions_width else None,
                "height": float(self.dimensions_height) if self.dimensions_height else None
            },
            "featured_image": self.featured_image,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "is_digital": self.is_digital,
            "is_in_stock": self.is_in_stock,
            "is_low_stock": self.is_low_stock,
            "discount_percentage": self.discount_percentage,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "view_count": self.view_count,
            "purchase_count": self.purchase_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Parse JSON fields
        try:
            data["gallery_images"] = json.loads(self.gallery_images) if self.gallery_images else []
        except (json.JSONDecodeError, TypeError):
            data["gallery_images"] = []
        
        try:
            data["tags"] = json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            data["tags"] = []
        
        # Include category information
        if include_category and self.category:
            data["category"] = self.category.to_dict(include_products=False)
        else:
            data["category_id"] = self.category_id
        
        return data