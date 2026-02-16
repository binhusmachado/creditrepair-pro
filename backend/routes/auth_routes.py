from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

@router.post("/register")
def register(user_data: dict, db: Session = Depends(get_db)):
    """Register a new user"""
    return auth_service.register_user(db, user_data)

@router.post("/login")
def login(credentials: dict, db: Session = Depends(get_db)):
    """Login user"""
    return auth_service.login_user(db, credentials)

@router.post("/logout")
def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    """Get current logged in user"""
    return {"message": "Current user endpoint"}