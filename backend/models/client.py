from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    ssn_last_four = Column(String(4))
    date_of_birth = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    credit_reports = relationship("CreditReport", back_populates="client", cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="client", cascade="all, delete-orphan")
    user_account = relationship("User", back_populates="client", uselist=False)
    subscriptions = relationship("Subscription", back_populates="client")
    payments = relationship("Payment", back_populates="client")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = [self.address, f"{self.city}, {self.state} {self.zip_code}"]
        return "\n".join([p for p in parts if p])