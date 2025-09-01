import os
from typing import Dict, Any
import stripe
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class ExternalIntegrations:
    def __init__(self):
        # Stripe Configuration
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
        self.stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
        
        # SendGrid Configuration
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')
        
    def create_payment_intent(self, amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a Stripe payment intent
        :param amount: Amount in cents
        :param currency: Currency code
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
                'intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            # Log error and handle appropriately
            return {'error': str(e)}
    
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """
        Send transactional email via SendGrid
        :param to_email: Recipient email
        :param subject: Email subject
        :param content: Email body
        :return: Whether email was sent successfully
        """
        try:
            message = Mail(
                from_email=os.getenv('SENDGRID_FROM_EMAIL', 'noreply@quickshop.com'),
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            
            sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
            response = sendgrid_client.send(message)
            
            return response.status_code in [200, 201, 202]
        except Exception as e:
            # Log error and handle appropriately
            return False

# Singleton instance for easy importing
external_integrations = ExternalIntegrations()