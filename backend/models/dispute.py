from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("credit_accounts.id", ondelete="SET NULL"))
    credit_report_id = Column(Integer, ForeignKey("credit_reports.id", ondelete="SET NULL"))
    
    # Dispute details
    bureau = Column(String(50), nullable=False)
    dispute_type = Column(String(100))
    dispute_category = Column(String(100))
    dispute_reason = Column(Text)
    dispute_description = Column(Text)
    
    # Account info (denormalized for letter)
    creditor_name = Column(String(255))
    account_number = Column(String(100))
    disputed_items = Column(JSON)
    
    # Round tracking
    round_number = Column(Integer, default=1)
    strategy = Column(String(100))
    legal_basis = Column(Text)
    
    # Letter
    letter_content = Column(Text)
    letter_file_path = Column(String(500))
    letter_generated_date = Column(DateTime)
    
    # Status tracking
    status = Column(String(50), default="pending")  # pending, generated, sent, response_received, resolved, closed
    created_date = Column(DateTime, default=datetime.utcnow)
    sent_date = Column(DateTime)
    expected_response_date = Column(DateTime)
    response_received_date = Column(DateTime)
    follow_up_date = Column(DateTime)
    resolved_date = Column(DateTime)
    
    # Response tracking
    response_type = Column(String(50))  # deleted, updated, verified, no_response
    response_details = Column(Text)
    follow_up_action = Column(Text)
    next_steps = Column(Text)
    
    # Metadata
    priority = Column(Integer, default=3)  # 1=highest, 5=lowest
    estimated_score_impact = Column(Integer)
    notes = Column(Text)
    
    # Relationships
    client = relationship("Client", back_populates="disputes")

DISPUTE_TYPES = {
    "outdated_negative": "Outdated Negative (7+ Years)",
    "outdated_inquiry": "Outdated Hard Inquiry (2+ Years)",
    "outdated_bankruptcy": "Outdated Bankruptcy (10+ Years)",
    "balance_exceeds_limit": "Balance Exceeds Credit Limit",
    "missing_credit_limit": "Missing Credit Limit",
    "duplicate_account": "Duplicate Account",
    "impossible_late_pattern": "Impossible Late Payment Pattern",
    "contradictory_status": "Contradictory Account Status",
    "paid_collection": "Paid Collection Still Reporting",
    "medical_collection_ncap": "Medical Collection (NCAP Eligible)",
    "tax_lien_ncap": "Tax Lien (NCAP Eligible - 2018+)",
    "charge_off_balance_growth": "Charge-Off Balance Increasing",
    "closed_with_balance": "Closed Account with Balance",
    "future_date": "Future Date Listed",
    "missing_date": "Missing Critical Date",
    "re_aging": "Account Re-Aging",
    "authorized_user_negative": "Authorized User Account Negative",
    "settled_with_balance": "Settled Account with Balance",
    "unauthorized_inquiry": "Unauthorized Hard Inquiry",
    "cross_bureau_discrepancy": "Cross-Bureau Discrepancy",
    "not_my_account": "Account Not Mine",
    "identity_theft": "Identity Theft / Fraud",
    "mixed_file": "Mixed Credit File",
    "wrong_personal_info": "Incorrect Personal Information",
    "late_payment_dispute": "Late Payment Dispute",
    "collection_validation": "Debt Validation Request",
    "goodwill_adjustment": "Goodwill Adjustment Request",
    "fcra_violation": "FCRA Violation",
}