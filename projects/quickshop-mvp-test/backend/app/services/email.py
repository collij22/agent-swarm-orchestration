import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Dict, Any, Optional

class EmailService:
    def __init__(self):
        # Use environment variables for API key
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        if not self.sendgrid_api_key:
            raise ValueError("SendGrid API key not configured")
        
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@quickshop.com')

    def send_template_email(
        self, 
        to_email: str, 
        template_id: str, 
        dynamic_template_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Send an email using a SendGrid dynamic template
        
        :param to_email: Recipient email address
        :param template_id: SendGrid template ID
        :param dynamic_template_data: Dynamic data for template
        :return: Message ID or None if sending fails
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email
            )
            message.template_id = template_id
            message.dynamic_template_data = dynamic_template_data

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            return response.headers.get('X-Message-Id')
        except Exception as e:
            # Log error in actual implementation
            print(f"Email sending failed: {str(e)}")
            return None

    def send_order_confirmation(
        self, 
        to_email: str, 
        order_details: Dict[str, Any]
    ) -> Optional[str]:
        """
        Send order confirmation email
        
        :param to_email: Customer email
        :param order_details: Order information dictionary
        :return: Message ID or None
        """
        # Assuming a predefined template for order confirmations
        return self.send_template_email(
            to_email=to_email,
            template_id='d-order-confirmation',  # Replace with actual template ID
            dynamic_template_data={
                'order_number': order_details.get('order_number'),
                'total_amount': order_details.get('total_amount'),
                'items': order_details.get('items', [])
            }
        )

email_service = EmailService()