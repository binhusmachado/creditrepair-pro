from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Client, CreditReport, Dispute

router = APIRouter(prefix="/client-portal", tags=["Client Portal"])

@router.get("/dashboard/{client_id}")
def get_client_dashboard(client_id: int, db: Session = Depends(get_db)):
    """Get client dashboard data"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {
        "client": {
            "id": client.id,
            "name": client.full_name,
            "email": client.email
        },
        "credit_reports": len(client.credit_reports),
        "active_disputes": len([d for d in client.disputes if d.status == "active"])
    }

@router.get("/reports/{client_id}")
def get_client_reports(client_id: int, db: Session = Depends(get_db)):
    """Get client's credit reports"""
    reports = db.query(CreditReport).filter(CreditReport.client_id == client_id).all()
    return {"reports": reports}

@router.get("/disputes/{client_id}")
def get_client_disputes(client_id: int, db: Session = Depends(get_db)):
    """Get client's disputes"""
    disputes = db.query(Dispute).filter(Dispute.client_id == client_id).all()
    return {"disputes": disputes}