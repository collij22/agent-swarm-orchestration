import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
from typing import Dict, Optional, List

class EmailService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@quickshop.com')
        self.sg_client = SendGridAPIClient(self.sendgrid_api_key)

    async def send_email(
        self, 
        to_email: str, 
        template_id: str, 
        dynamic_template_data: Dict[str, Any]
    ) -> bool:
        """
        Send an email using SendGrid's dynamic template system
        
        Args:
            to_email (str): Recipient email address
            template_id (str): SendGrid template ID
            dynamic_template_data (Dict): Dynamic data for template
        
        Returns:
            bool: Whether email was sent successfully
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email
            )
            message.template_id = template_id
            message.dynamic_template_data = dynamic_template_data

            response = await asyncio.to_thread(
                self.sg_client.send, 
                message
            )
            
            return response.status_code in [200, 201, 202]
        except Exception as e:
            # Log error, but don't block execution
            print(f"Email sending failed: {e}")
            return False

    async def send_order_confirmation(
        self, 
        order_details: Dict[str, Any]
    ) -> bool:
        """
        Send order confirmation email
        
        Args:
            order_details (Dict): Comprehensive order information
        
        Returns:
            bool: Email sending status
        """
        return await self.send_email(
            to_email=order_details['customer_email'],
            template_id='order_confirmation',
            dynamic_template_data={
                'order_id': order_details['order_id'],
                'total_amount': order_details['total'],
                'items': order_details['items']
            }
        )

    async def send_shipping_update(
        self, 
        order_id: str, 
        tracking_number: str, 
        customer_email: str
    ) -> bool:
        """
        Send shipping update email
        
        Args:
            order_id (str): Unique order identifier
            tracking_number (str): Shipping tracking number
            customer_email (str): Customer's email address
        
        Returns:
            bool: Email sending status
        """
        return await self.send_email(
            to_email=customer_email,
            template_id='shipping_update',
            dynamic_template_data={
                'order_id': order_id,
                'tracking_number': tracking_number
            }
        )

def get_email_service():
    """Dependency injection for Email service"""
    return EmailService()