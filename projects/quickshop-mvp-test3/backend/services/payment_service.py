import stripe
from typing import Dict, Any
from fastapi import HTTPException
from core.config import settings

class StripePaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(self, amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent with idempotency and error handling
        
        Args:
            amount (int): Payment amount in cents
            currency (str): Currency code, defaults to USD
        
        Returns:
            Dict containing PaymentIntent client secret
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=['card'],
                # Add additional configuration as needed
                metadata={
                    'integration_type': 'quickshop_mvp',
                    'version': '1.0.0'
                }
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            # Comprehensive error handling
            error_msg = str(e)
            if isinstance(e, stripe.error.CardError):
                # Specific card-related errors
                raise HTTPException(status_code=400, detail=f"Card Error: {error_msg}")
            elif isinstance(e, stripe.error.RateLimitError):
                raise HTTPException(status_code=429, detail="Too many requests to Stripe")
            elif isinstance(e, stripe.error.InvalidRequestError):
                raise HTTPException(status_code=400, detail=f"Invalid Stripe Request: {error_msg}")
            else:
                # Generic Stripe error
                raise HTTPException(status_code=500, detail=f"Payment Processing Error: {error_msg}")

    def handle_webhook(self, payload: str, sig_header: str):
        """
        Securely handle Stripe webhooks with signature verification
        
        Args:
            payload (str): Raw webhook payload
            sig_header (str): Stripe signature header
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Process different event types
            if event.type == 'payment_intent.succeeded':
                self._handle_successful_payment(event.data.object)
            elif event.type == 'payment_intent.payment_failed':
                self._handle_failed_payment(event.data.object)
            
            return {'status': 'success'}
        
        except ValueError as e:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    def _handle_successful_payment(self, payment_intent):
        """Process successful payment, update order status"""
        order_id = payment_intent.metadata.get('order_id')
        # Implement order status update logic
        pass

    def _handle_failed_payment(self, payment_intent):
        """Handle failed payment scenarios"""
        order_id = payment_intent.metadata.get('order_id')
        # Implement failed payment notification logic
        pass

payment_service = StripePaymentService()