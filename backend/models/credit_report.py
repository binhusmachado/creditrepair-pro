from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class CreditReport(Base):
    __tablename__ = "credit_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500))
    original_filename = Column(String(255))
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    bureau = Column(String(50))
    report_date = Column(DateTime)
    report_type = Column(String(50))  # SmartCredit, IdentityIQ, etc.
    raw_text = Column(Text)
    parsed_data = Column(JSON)
    
    # Credit scores
    equifax_score = Column(Integer)
    experian_score = Column(Integer)
    transunion_score = Column(Integer)
    
    # Analysis results
    errors_found = Column(JSON)
    discrepancies = Column(JSON)
    total_errors = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    analysis_complete = Column(Boolean, default=False)
    analysis_date = Column(DateTime)
    
    # Statistics
    total_accounts = Column(Integer, default=0)
    negative_accounts = Column(Integer, default=0)
    positive_accounts = Column(Integer, default=0)
    total_inquiries = Column(Integer, default=0)
    hard_inquiries = Column(Integer, default=0)
    public_records = Column(Integer, default=0)
    collections = Column(Integer, default=0)
    total_debt = Column(Float, default=0.0)
    
    # Relationships
    client = relationship("Client", back_populates="credit_reports")
    accounts = relationship("CreditAccount", back_populates="credit_report", cascade="all, delete-orphan")

class CreditAccount(Base):
    __tablename__ = "credit_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("credit_reports.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    
    # Account info
    creditor_name = Column(String(255))
    account_number = Column(String(100))
    account_number_masked = Column(String(100))
    account_type = Column(String(50))
    account_status = Column(String(50))
    
    # Bureau reporting
    reported_equifax = Column(Boolean, default=False)
    reported_experian = Column(Boolean, default=False)
    reported_transunion = Column(Boolean, default=False)
    equifax_data = Column(JSON)
    experian_data = Column(JSON)
    transunion_data = Column(JSON)
    
    # Dates
    date_opened = Column(String(20))
    date_closed = Column(String(20))
    last_payment_date = Column(String(20))
    last_reported = Column(String(20))
    
    # Financial
    credit_limit = Column(Float)
    high_balance = Column(Float)
    current_balance = Column(Float)
    monthly_payment = Column(Float)
    past_due_amount = Column(Float)
    payment_status = Column(String(50))
    
    # Payment history
    late_30_count = Column(Integer, default=0)
    late_60_count = Column(Integer, default=0)
    late_90_count = Column(Integer, default=0)
    late_120_plus_count = Column(Integer, default=0)
    
    # Flags
    is_negative = Column(Boolean, default=False)
    is_collection = Column(Boolean, default=False)
    is_charge_off = Column(Boolean, default=False)
    is_medical = Column(Boolean, default=False)
    is_educational = Column(Boolean, default=False)
    is_authorized_user = Column(Boolean, default=False)
    
    # Errors and disputes
    has_errors = Column(Boolean, default=False)
    has_discrepancies = Column(Boolean, default=False)
    errors = Column(JSON)
    discrepancies = Column(JSON)
    dispute_recommended = Column(Boolean, default=False)
    dispute_reason = Column(Text)
    dispute_strategy = Column(String(100))
    
    # Relationship
    credit_report = relationship("CreditReport", back_populates="accounts")