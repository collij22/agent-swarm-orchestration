"""
Payment model for payment processing and tracking
"""

from sqlalchemy import Column, Integer, String, Text, Decimal, Boolean, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Payment(Base):
    """Payment model for tracking all payment transactions"""
    
    __tablename__ = "payments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Order relationship
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    
    # Payment identification
    payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)  # Stripe payment intent ID
    transaction_id = Column(String(255), unique=True, nullable=True, index=True)     # External transaction ID
    
    # Payment details
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # Amount information
    amount = Column(Decimal(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Payment processor information
    processor = Column(String(50), nullable=False)  # stripe, paypal, etc.
    processor_fee = Column(Decimal(10, 2), nullable=True)
    
    # Card information (for card payments)
    card_brand = Column(String(20), nullable=True)    # visa, mastercard, etc.
    card_last4 = Column(String(4), nullable=True)     # Last 4 digits
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    
    # Billing information
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)     # JSON string
    
    # Payment metadata
    metadata = Column(Text, nullable=True)            # JSON string for additional data
    failure_reason = Column(Text, nullable=True)      # Reason for failed payments
    
    # Refund information
    refunded_amount = Column(Decimal(10, 2), default=0, nullable=False)
    refund_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_payment_order_status", "order_id", "status"),
        Index("idx_payment_processor", "processor", "status"),
        Index("idx_payment_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, amount={self.amount}, status={self.status})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_refundable(self) -> bool:
        """Check if payment can be refunded"""
        return (
            self.status == PaymentStatus.SUCCEEDED and 
            self.refunded_amount < self.amount
        )
    
    @property
    def refundable_amount(self) -> Decimal:
        """Get remaining refundable amount"""
        if not self.is_refundable:
            return Decimal('0.00')
        return self.amount - self.refunded_amount
    
    @property
    def is_fully_refunded(self) -> bool:
        """Check if payment is fully refunded"""
        return self.refunded_amount >= self.amount
    
    def to_dict(self, include_sensitive=False) -> dict:
        """Convert payment to dictionary"""
        import json
        
        data = {
            "id": self.id,
            "order_id": self.order_id,
            "method": self.method.value,
            "status": self.status.value,
            "amount": float(self.amount),
            "currency": self.currency,
            "processor": self.processor,
            "processor_fee": float(self.processor_fee) if self.processor_fee else None,
            "refunded_amount": float(self.refunded_amount),
            "refund_reason": self.refund_reason,
            "is_successful": self.is_successful,
            "is_refundable": self.is_refundable,
            "refundable_amount": float(self.refundable_amount),
            "is_fully_refunded": self.is_fully_refunded,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None
        }
        
        # Card information (masked for security)
        if self.card_brand or self.card_last4:
            data["card"] = {
                "brand": self.card_brand,
                "last4": self.card_last4,
                "exp_month": self.card_exp_month,
                "exp_year": self.card_exp_year
            }
        
        # Include sensitive information only if requested
        if include_sensitive:
            data.update({
                "payment_intent_id": self.payment_intent_id,
                "transaction_id": self.transaction_id,
                "billing_name": self.billing_name,
                "billing_email": self.billing_email
            })
            
            # Parse JSON fields
            try:
                data["billing_address"] = json.loads(self.billing_address) if self.billing_address else None
            except (json.JSONDecodeError, TypeError):
                data["billing_address"] = None
            
            try:
                data["metadata"] = json.loads(self.metadata) if self.metadata else {}
            except (json.JSONDecodeError, TypeError):
                data["metadata"] = {}
        
        return data