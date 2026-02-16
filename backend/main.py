from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from database import engine, Base, get_db
from config import settings
from models import *
from auth.auth_service import AuthService
from parsers.ocr_integration import OCRIntegration
from analyzers.error_detector import ErrorDetector
from dispute_engine.strategy_builder import StrategyBuilder
from dispute_engine.letter_generator import LetterGenerator
from services.email_service import EmailService
from services.stripe_service import StripeService
from services.notification_scheduler import NotificationScheduler

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Credit Repair SaaS API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_service = AuthService()
ocr_integration = OCRIntegration()
error_detector = ErrorDetector()
strategy_builder = StrategyBuilder()
letter_generator = LetterGenerator()
email_service = EmailService()
stripe_service = StripeService()

# ========== Dependencies ==========

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_staff(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user

# ========== Root Routes ==========

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ========== Auth Routes ==========

@app.post("/api/auth/register-client")
def register_client(client_data: dict, db: Session = Depends(get_db)):
    """Register a new client with user account"""
    return auth_service.register_client(db, client_data)

@app.post("/api/auth/login")
def login(credentials: dict, request: Request, db: Session = Depends(get_db)):
    """Login user"""
    return auth_service.login_user(
        db, 
        credentials.get("email"), 
        credentials.get("password"),
        ip_address=request.client.host
    )

@app.post("/api/auth/refresh")
def refresh_token(refresh_data: dict, db: Session = Depends(get_db)):
    """Refresh access token"""
    return auth_service.refresh_access_token(db, refresh_data.get("refresh_token"))

@app.post("/api/auth/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    """Request password reset"""
    return auth_service.request_password_reset(db, data.get("email"))

@app.post("/api/auth/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    """Reset password with token"""
    return auth_service.reset_password(db, data.get("token"), data.get("new_password"))

@app.post("/api/auth/change-password")
def change_password(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password"""
    return auth_service.change_password(
        db, 
        current_user.id, 
        data.get("current_password"), 
        data.get("new_password")
    )

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "client_id": current_user.client_id
    }

@app.get("/api/auth/notifications")
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user notifications"""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return {"notifications": notifications}

@app.post("/api/auth/admin/create-client-account")
def admin_create_client(
    client_data: dict,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin creates client account"""
    return auth_service.register_client(db, client_data)

# ========== Client Routes ==========

@app.get("/api/clients")
def get_clients(
    skip: int = 0,
    limit: int = 100,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Get all clients (staff/admin only)"""
    clients = db.query(Client).offset(skip).limit(limit).all()
    return {"clients": clients, "total": db.query(Client).count()}

@app.post("/api/clients")
def create_client(
    client_data: dict,
    staff: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Create a new client (staff/admin only)"""
    client = Client(**client_data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"client": client, "message": "Client created"}

@app.get("/api/clients/{client_id}")
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get client details"""
    # Clients can only view their own data
    if current_user.role == "client" and current_user.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {
        "client": client,
        "credit_reports": client.credit_reports,
        "disputes": client.disputes
    }

# ========== Credit Report Routes ==========

@app.post("/api/credit-reports/upload")
async def upload_credit_report(
    file: UploadFile = File(...),
    bureau: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a credit report"""
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="User not associated with a client")
    
    # Save file
    upload_dir = "uploads/credit_reports"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{datetime.utcnow().timestamp()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process with OCR/PDF parser
    result = ocr_integration.process_upload(file_path, file.content_type)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Failed to process file")
    
    # Create credit report record
    report_data = result["data"]
    credit_report = CreditReport(
        client_id=current_user.client_id,
        file_path=file_path,
        original_filename=file.filename,
        file_size=os.path.getsize(file_path),
        bureau=report_data.get("bureau", bureau),
        raw_text=report_data.get("raw_text", ""),
        parsed_data=report_data,
        equifax_score=report_data.get("scores", {}).get("equifax"),
        experian_score=report_data.get("scores", {}).get("experian"),
        transunion_score=report_data.get("scores", {}).get("transunion"),
        total_accounts=len(report_data.get("accounts", [])),
        negative_accounts=sum(1 for a in report_data.get("accounts", []) if a.get("is_negative"))
    )
    
    db.add(credit_report)
    db.commit()
    db.refresh(credit_report)
    
    # Create accounts
    for account_data in report_data.get("accounts", []):
        account = CreditAccount(
            report_id=credit_report.id,
            client_id=current_user.client_id,
            **account_data
        )
        db.add(account)
    
    db.commit()
    
    return {
        "message": "Report uploaded successfully",
        "report_id": credit_report.id,
        "accounts_found": len(report_data.get("accounts", [])),
        "scores": report_data.get("scores", {})
    }

@app.post("/api/credit-reports/{report_id}/analyze")
def analyze_credit_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run error analysis on a credit report"""
    report = db.query(CreditReport).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user.role == "client" and report.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prepare data for analysis
    accounts = db.query(CreditAccount).filter(CreditAccount.report_id == report_id).all()
    
    report_data = {
        "accounts": [
            {
                "creditor_name": a.creditor_name,
                "account_number": a.account_number,
                "current_balance": a.current_balance,
                "credit_limit": a.credit_limit,
                "is_negative": a.is_negative,
                "is_collection": a.is_collection,
                "late_30_count": a.late_30_count,
                "late_60_count": a.late_60_count,
                "late_90_count": a.late_90_count,
                "account_status": a.account_status
            }
            for a in accounts
        ],
        "parsed_data": report.parsed_data or {}
    }
    
    # Run error detection
    analysis = error_detector.analyze_report(report_data)
    
    # Update report with analysis
    report.errors_found = analysis["errors"]
    report.discrepancies = analysis["discrepancies"]
    report.total_errors = analysis["total_errors"]
    report.total_discrepancies = analysis["total_discrepancies"]
    report.analysis_complete = True
    report.analysis_date = datetime.utcnow()
    
    # Update accounts with error flags
    for account in accounts:
        account_errors = [e for e in analysis["errors"] 
                         if e.get("account", {}).get("account_number") == account.account_number]
        if account_errors:
            account.has_errors = True
            account.errors = account_errors
            account.dispute_recommended = True
    
    db.commit()
    
    return {
        "message": "Analysis complete",
        "analysis": analysis
    }

# ========== Dispute Routes ==========

@app.get("/api/disputes/strategy")
def get_dispute_strategy(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dispute strategy for a report"""
    report = db.query(CreditReport).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user.role == "client" and report.client_id != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    client = db.query(Client).get(report.client_id)
    
    errors = report.errors_found or []
    strategy = strategy_builder.build_strategy(errors, {"id": client.id, "full_name": client.full_name})
    
    return strategy

@app.post("/api/disputes/generate-letters")
def generate_dispute_letters(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate dispute letters"""
    dispute_ids = data.get("dispute_ids", [])
    letters = []
    
    for dispute_id in dispute_ids:
        dispute = db.query(Dispute).get(dispute_id)
        if not dispute:
            continue
        
        if current_user.role == "client" and dispute.client_id != current_user.client_id:
            continue
        
        client = db.query(Client).get(dispute.client_id)
        
        letter_content = letter_generator.generate_letter(
            dispute.strategy or "bureau_dispute",
            {
                "bureau": dispute.bureau,
                "creditor_name": dispute.creditor_name,
                "account_number": dispute.account_number,
                "dispute_reason": dispute.dispute_reason,
                "disputed_items": dispute.disputed_items,
                "round_number": dispute.round_number
            },
            {
                "full_name": client.full_name,
                "address": client.address,
                "city": client.city,
                "state": client.state,
                "zip_code": client.zip_code,
                "ssn_last_four": client.ssn_last_four,
                "date_of_birth": client.date_of_birth
            }
        )
        
        dispute.letter_content = letter_content
        dispute.letter_generated_date = datetime.utcnow()
        dispute.status = "generated"
        
        letters.append({
            "dispute_id": dispute.id,
            "bureau": dispute.bureau,
            "content": letter_content
        })
    
    db.commit()
    
    return {"letters": letters, "count": len(letters)}

# ========== Client Portal Routes ==========

@app.get("/api/client/dashboard")
def get_client_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get client dashboard data"""
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="Not a client account")
    
    client = db.query(Client).get(current_user.client_id)
    
    # Get latest scores
    latest_report = db.query(CreditReport).filter(
        CreditReport.client_id == client.id
    ).order_by(CreditReport.upload_date.desc()).first()
    
    # Count disputes
    active_disputes = db.query(Dispute).filter(
        Dispute.client_id == client.id,
        Dispute.status.in_(["pending", "generated", "sent"])
    ).count()
    
    completed_disputes = db.query(Dispute).filter(
        Dispute.client_id == client.id,
        Dispute.status == "resolved"
    ).count()
    
    return {
        "client": {
            "id": client.id,
            "name": client.full_name,
            "email": client.email
        },
        "credit_scores": {
            "equifax": latest_report.equifax_score if latest_report else None,
            "experian": latest_report.experian_score if latest_report else None,
            "transunion": latest_report.transunion_score if latest_report else None
        },
        "stats": {
            "total_reports": len(client.credit_reports),
            "active_disputes": active_disputes,
            "completed_disputes": completed_disputes,
            "total_errors": sum(r.total_errors for r in client.credit_reports)
        }
    }

@app.get("/api/client/reports")
def get_client_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get client's credit reports"""
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="Not a client account")
    
    reports = db.query(CreditReport).filter(
        CreditReport.client_id == current_user.client_id
    ).order_by(CreditReport.upload_date.desc()).all()
    
    return {"reports": reports}

@app.get("/api/client/disputes")
def get_client_disputes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get client's disputes"""
    if not current_user.client_id:
        raise HTTPException(status_code=400, detail="Not a client account")
    
    disputes = db.query(Dispute).filter(
        Dispute.client_id == current_user.client_id
    ).order_by(Dispute.created_date.desc()).all()
    
    return {"disputes": disputes}

# ========== Payment Routes ==========

@app.get("/api/payments/plans")
def get_subscription_plans(db: Session = Depends(get_db)):
    """Get available subscription plans"""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.sort_order).all()
    return {"plans": plans}

@app.post("/api/payments/create-checkout")
def create_checkout(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session"""
    plan = db.query(SubscriptionPlan).get(data.get("plan_id"))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get or create customer
    if current_user.client_id:
        client = db.query(Client).get(current_user.client_id)
        stripe_customer = stripe_service.create_customer(
            current_user.email,
            client.full_name
        )
    else:
        stripe_customer = stripe_service.create_customer(
            current_user.email,
            f"{current_user.first_name} {current_user.last_name}"
        )
    
    if not stripe_customer["success"]:
        raise HTTPException(status_code=400, detail=stripe_customer.get("error"))
    
    # Create checkout session
    price_id = plan.stripe_price_id_monthly if data.get("interval") == "monthly" else plan.stripe_price_id_yearly
    
    session = stripe_service.create_checkout_session(
        price_id=price_id,
        customer_id=stripe_customer["customer_id"]
    )
    
    if not session["success"]:
        raise HTTPException(status_code=400, detail=session.get("error"))
    
    return {"checkout_url": session["url"]}

@app.post("/api/payments/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    result = stripe_service.handle_webhook(payload, signature)
    
    if result["success"]:
        # Process the event
        event_type = result.get("event_type")
        event_data = result.get("event", {}).get("data", {}).get("object", {})
        
        # Update database based on event
        if event_type == "checkout.session.completed":
            # Create subscription record
            pass
        elif event_type == "invoice.paid":
            # Create payment record
            pass
    
    return {"status": "ok"}

@app.get("/api/payments/billing-portal")
def get_billing_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Stripe billing portal URL"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    portal = stripe_service.create_portal_session(subscription.stripe_customer_id)
    
    if not portal["success"]:
        raise HTTPException(status_code=400, detail=portal.get("error"))
    
    return {"url": portal["url"]}

# ========== Admin Routes ==========

@app.post("/api/admin/initialize")
def initialize_system(admin_data: dict, db: Session = Depends(get_db)):
    """Initialize system with admin account and default plans"""
    # Check if admin exists
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return {"message": "System already initialized"}
    
    # Create admin user
    result = auth_service.register_user(db, {
        "email": admin_data.get("email"),
        "password": admin_data.get("password"),
        "first_name": admin_data.get("first_name", "Admin"),
        "last_name": admin_data.get("last_name", "User"),
        "role": "admin"
    })
    
    if not result.get("success"):
        return result
    
    # Create default subscription plans
    default_plans = [
        {
            "name": "Basic",
            "slug": "basic",
            "description": "Essential credit repair with up to 5 disputes per month",
            "price_monthly": 79.99,
            "max_disputes_per_month": 5,
            "max_reports": 3,
            "includes_letters": True,
            "includes_monitoring": False,
            "sort_order": 1
        },
        {
            "name": "Professional",
            "slug": "professional",
            "description": "Advanced credit repair with monitoring and up to 15 disputes",
            "price_monthly": 149.99,
            "max_disputes_per_month": 15,
            "max_reports": 10,
            "includes_letters": True,
            "includes_monitoring": True,
            "sort_order": 2
        },
        {
            "name": "Premium",
            "slug": "premium",
            "description": "Unlimited credit repair with priority support",
            "price_monthly": 249.99,
            "max_disputes_per_month": 999,
            "max_reports": 999,
            "includes_letters": True,
            "includes_monitoring": True,
            "priority_support": True,
            "sort_order": 3
        }
    ]
    
    for plan_data in default_plans:
        plan = SubscriptionPlan(**plan_data)
        db.add(plan)
    
    db.commit()
    
    return {
        "message": "System initialized successfully",
        "admin_id": result.get("user_id")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)