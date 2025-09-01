import os
import stripe
from fastapi import HTTPException
from typing import Dict, Any

# Configure Stripe with secure key management
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripePaymentService:
    @staticmethod
    def create_payment_intent(amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a Stripe payment intent with error handling
        
        :param amount: Payment amount in cents
        :param currency: Currency code (default: usd)
        :return: Payment intent details
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=['card'],
                # Add additional configuration as needed
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            # Log error details securely
            raise HTTPException(
                status_code=400, 
                detail=f"Payment processing error: {str(e)}"
            )

    @staticmethod
    def verify_webhook(payload, sig_header):
        """
        Verify Stripe webhook signature for security
        
        :param payload: Raw webhook payload
        :param sig_header: Signature header from Stripe
        :return: Verified webhook event
        """
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
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
            raise HTTPException(status_code=403, detail="Invalid signature")

# Expose service for FastAPI dependency injection
payment_service = StripePaymentService()