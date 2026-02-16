import stripe
from typing import Dict, Optional, List
from config import settings
import os
import logging

logger = logging.getLogger(__name__)

class StripeService:
    """Complete Stripe payment processing service"""
    
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # ========== Customer Management ==========
    
    def create_customer(self, email: str, name: str, 
                       phone: str = None, metadata: Dict = None) -> Dict:
        """Create a Stripe customer"""
        try:
            params = {
                "email": email,
                "name": name,
            }
            if phone:
                params["phone"] = phone
            if metadata:
                params["metadata"] = metadata
                
            customer = stripe.Customer.create(**params)
            
            logger.info(f"Created Stripe customer: {customer.id}")
            return {"success": True, "customer_id": customer.id}
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_customer(self, customer_id: str, **kwargs) -> Dict:
        """Update a Stripe customer"""
        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)
            return {"success": True, "customer": customer}
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Product & Price Management ==========
    
    def create_product(self, name: str, description: str = None) -> Dict:
        """Create a Stripe product"""
        try:
            product = stripe.Product.create(
                name=name,
                description=description
            )
            return {"success": True, "product_id": product.id}
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    def create_price(self, product_id: str, amount: int, currency: str = "usd",
                     interval: str = None) -> Dict:
        """Create a Stripe price"""
        try:
            params = {
                "product": product_id,
                "unit_amount": amount,  # Amount in cents
                "currency": currency
            }
            
            if interval:
                params["recurring"] = {"interval": interval}
            
            price = stripe.Price.create(**params)
            return {"success": True, "price_id": price.id}
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Checkout Sessions ==========
    
    def create_checkout_session(self, price_id: str, customer_id: str = None,
                                 success_url: str = None, 
                                 cancel_url: str = None,
                                 mode: str = "subscription") -> Dict:
        """Create a Stripe Checkout session"""
        try:
            params = {
                "payment_method_types": ["card"],
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": mode,
                "success_url": success_url or f"{os.getenv('COMPANY_URL')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": cancel_url or f"{os.getenv('COMPANY_URL')}/payment/cancel"
            }
            
            if customer_id:
                params["customer"] = customer_id
            
            session = stripe.checkout.Session.create(**params)
            
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url
            }
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Subscriptions ==========
    
    def create_subscription(self, customer_id: str, price_id: str,
                           payment_behavior: str = "default_incomplete") -> Dict:
        """Create a subscription"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior=payment_behavior,
                expand=["latest_invoice.payment_intent"]
            )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
            }
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    def cancel_subscription(self, subscription_id: str, 
                           immediately: bool = False) -> Dict:
        """Cancel a subscription"""
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    def get_subscription(self, subscription_id: str) -> Dict:
        """Get subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {"success": True, "subscription": subscription}
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Payment Intents ==========
    
    def create_payment_intent(self, amount: int, currency: str = "usd",
                             customer_id: str = None,
                             description: str = None) -> Dict:
        """Create a payment intent for one-time charges"""
        try:
            params = {
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True}
            }
            
            if customer_id:
                params["customer"] = customer_id
            if description:
                params["description"] = description
            
            intent = stripe.PaymentIntent.create(**params)
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Setup Intents ==========
    
    def create_setup_intent(self, customer_id: str) -> Dict:
        """Create a setup intent for saving payment methods"""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=["card"]
            )
            
            return {
                "success": True,
                "client_secret": setup_intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Customer Portal ==========
    
    def create_portal_session(self, customer_id: str,
                             return_url: str = None) -> Dict:
        """Create a customer portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url or f"{os.getenv('COMPANY_URL')}/client/dashboard"
            )
            
            return {"success": True, "url": session.url}
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}
    
    # ========== Webhook Handling ==========
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            event_type = event["type"]
            event_data = event["data"]["object"]
            
            logger.info(f"Processing webhook: {event_type}")
            
            # Handle different event types
            handlers = {
                "checkout.session.completed": self._handle_checkout_completed,
                "invoice.paid": self._handle_invoice_paid,
                "invoice.payment_failed": self._handle_payment_failed,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "payment_intent.succeeded": self._handle_payment_intent_succeeded
            }
            
            handler = handlers.get(event_type)
            if handler:
                result = handler(event_data)
                return {"success": True, "event_type": event_type, "result": result}
            
            return {"success": True, "event_type": event_type, "message": "No handler for this event"}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return {"success": False, "error": "Invalid signature"}
        except Exception as e:
            logger.error(f"Webhook handling error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_checkout_completed(self, data: Dict) -> Dict:
        """Handle checkout.session.completed"""
        return {
            "customer_id": data.get("customer"),
            "subscription_id": data.get("subscription"),
            "status": "completed"
        }
    
    def _handle_invoice_paid(self, data: Dict) -> Dict:
        """Handle invoice.paid"""
        return {
            "customer_id": data.get("customer"),
            "subscription_id": data.get("subscription"),
            "amount_paid": data.get("amount_paid"),
            "status": "paid"
        }
    
    def _handle_payment_failed(self, data: Dict) -> Dict:
        """Handle invoice.payment_failed"""
        return {
            "customer_id": data.get("customer"),
            "subscription_id": data.get("subscription"),
            "status": "failed"
        }
    
    def _handle_subscription_updated(self, data: Dict) -> Dict:
        """Handle customer.subscription.updated"""
        return {
            "subscription_id": data.get("id"),
            "status": data.get("status"),
            "cancel_at_period_end": data.get("cancel_at_period_end")
        }
    
    def _handle_subscription_deleted(self, data: Dict) -> Dict:
        """Handle customer.subscription.deleted"""
        return {
            "subscription_id": data.get("id"),
            "status": "cancelled"
        }
    
    def _handle_payment_intent_succeeded(self, data: Dict) -> Dict:
        """Handle payment_intent.succeeded"""
        return {
            "payment_intent_id": data.get("id"),
            "amount": data.get("amount"),
            "status": "succeeded"
        }
    
    # ========== Initialization ==========
    
    def initialize_plans(self) -> List[Dict]:
        """Initialize default subscription plans"""
        plans = [
            {
                "name": "Basic",
                "slug": "basic",
                "description": "Essential credit repair features",
                "price_monthly": 7999,  # $79.99 in cents
                "features": {
                    "max_disputes": 5,
                    "max_reports": 3,
                    "includes_letters": True,
                    "includes_monitoring": False
                }
            },
            {
                "name": "Professional",
                "slug": "professional", 
                "description": "Advanced credit repair with monitoring",
                "price_monthly": 14999,  # $149.99 in cents
                "features": {
                    "max_disputes": 15,
                    "max_reports": 10,
                    "includes_letters": True,
                    "includes_monitoring": True
                }
            },
            {
                "name": "Premium",
                "slug": "premium",
                "description": "Complete credit repair solution",
                "price_monthly": 24999,  # $249.99 in cents
                "features": {
                    "max_disputes": 999,
                    "max_reports": 999,
                    "includes_letters": True,
                    "includes_monitoring": True,
                    "priority_support": True
                }
            }
        ]
        
        created_plans = []
        
        for plan in plans:
            try:
                # Create product
                product_result = self.create_product(plan["name"], plan["description"])
                if not product_result["success"]:
                    continue
                
                product_id = product_result["product_id"]
                
                # Create monthly price
                monthly_result = self.create_price(
                    product_id, 
                    plan["price_monthly"], 
                    interval="month"
                )
                
                if monthly_result["success"]:
                    created_plans.append({
                        "name": plan["name"],
                        "product_id": product_id,
                        "monthly_price_id": monthly_result["price_id"],
                        "features": plan["features"]
                    })
                    
            except Exception as e:
                logger.error(f"Failed to create plan {plan['name']}: {str(e)}")
        
        return created_plans