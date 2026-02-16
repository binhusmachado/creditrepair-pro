from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    # Pricing
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float)
    stripe_price_id_monthly = Column(String(100))
    stripe_price_id_yearly = Column(String(100))
    stripe_product_id = Column(String(100))
    
    # Features
    max_disputes_per_month = Column(Integer, default=15)
    max_reports = Column(Integer, default=5)
    includes_letters = Column(Boolean, default=True)
    includes_monitoring = Column(Boolean, default=False)
    includes_direct_creditor = Column(Boolean, default=False)
    includes_phone_support = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    # Stripe
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))
    stripe_payment_method_id = Column(String(100))
    
    # Status
    status = Column(String(50), default="active")  # active, cancelled, past_due, unpaid
    billing_interval = Column(String(20), default="monthly")
    amount = Column(Float)
    currency = Column(String(3), default="usd")
    
    # Dates
    start_date = Column(DateTime, default=datetime.utcnow)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"))
    
    # Stripe
    stripe_payment_intent_id = Column(String(100), unique=True)
    stripe_charge_id = Column(String(100))
    stripe_invoice_id = Column(String(100))
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), default="pending")  # pending, succeeded, failed
    payment_type = Column(String(50), default="subscription")  # subscription, one_time
    
    # Card info
    payment_method_type = Column(String(20))
    card_brand = Column(String(20))
    card_last_four = Column(String(4))
    
    # Metadata
    description = Column(String(255))
    failure_reason = Column(String(255))
    receipt_url = Column(String(500))
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)
    
    # Relationships
    client = relationship("Client", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

class OneTimeCharge(Base):
    __tablename__ = "one_time_charges"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    
    # Stripe
    stripe_payment_intent_id = Column(String(100))
    
    # Charge details
    amount = Column(Float, nullable=False)
    description = Column(String(255))
    status = Column(String(50), default="pending")
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)