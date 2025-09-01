import os
import stripe
from typing import Dict, Any
from fastapi import HTTPException

class StripePaymentService:
    def __init__(self):
        # Use environment variables for API key
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            raise ValueError("Stripe API key not configured")

    def create_payment_intent(self, amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent
        
        :param amount: Payment amount in cents
        :param currency: Currency code (default: usd)
        :return: Payment intent details
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=['card']
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            # Log the error and raise a more generic exception
            raise HTTPException(status_code=400, detail=f"Payment processing error: {str(e)}")

    def verify_webhook(self, payload: bytes, sig_header: str):
        """
        Verify Stripe webhook signature
        
        :param payload: Raw request body
        :param sig_header: Signature header from Stripe
        """
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            raise ValueError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            raise HTTPException(status_code=400, detail="Invalid signature")

payment_service = StripePaymentService()