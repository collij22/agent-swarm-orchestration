import os
import stripe
from typing import Dict, Any
from fastapi import HTTPException

class StripePaymentService:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    def create_payment_intent(self, amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent with error handling and logging
        
        Args:
            amount (int): Payment amount in cents
            currency (str): Currency code (default: 'usd')
        
        Returns:
            Dict with PaymentIntent details
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=['card'],
                # Add additional configuration as needed
                metadata={
                    'integration_check': 'accept_a_payment',
                    'source': 'quickshop_mvp'
                }
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            # Log the specific Stripe error
            raise HTTPException(
                status_code=400, 
                detail=f"Payment creation failed: {str(e)}"
            )

    def verify_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature and parse event
        
        Args:
            payload (str): Raw webhook payload
            sig_header (str): Signature header from Stripe
        
        Returns:
            Verified Stripe event
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            raise HTTPException(status_code=400, detail="Invalid signature")

    def handle_payment_success(self, payment_intent: Dict[str, Any]):
        """
        Process successful payment
        
        Args:
            payment_intent (Dict): Stripe PaymentIntent object
        """
        # Implement order processing logic
        order_id = payment_intent.get('metadata', {}).get('order_id')
        if order_id:
            # Update order status, create records, etc.
            pass

def get_stripe_service():
    """Dependency injection for Stripe service"""
    return StripePaymentService()