from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services.stripe_service import StripeService

router = APIRouter(prefix="/payments", tags=["Payments"])
stripe_service = StripeService()

@router.post("/create-customer")
def create_customer(data: dict):
    """Create a Stripe customer"""
    return stripe_service.create_customer(data["email"], data["name"])

@router.post("/create-subscription")
def create_subscription(data: dict):
    """Create a subscription"""
    return stripe_service.create_subscription(
        data["customer_id"], 
        data["price_id"]
    )

@router.post("/cancel-subscription")
def cancel_subscription(data: dict):
    """Cancel a subscription"""
    return stripe_service.cancel_subscription(data["subscription_id"])

@router.post("/webhook")
def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = request.body()
    signature = request.headers.get("stripe-signature")
    return stripe_service.handle_webhook(payload, signature)