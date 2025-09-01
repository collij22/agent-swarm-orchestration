import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from core.config import settings
from typing import Dict, Optional

class EmailService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY.get_secret_value())
        self.from_email = Email("noreply@quickshop.com")

    def send_order_confirmation(self, order: Dict, recipient_email: str):
        """
        Send order confirmation email
        
        Args:
            order (Dict): Order details
            recipient_email (str): Customer's email address
        """
        subject = f"Order Confirmation #{order['order_number']}"
        content = Content(
            "text/html", 
            f"""
            <h1>Order Confirmation</h1>
            <p>Thank you for your purchase!</p>
            <h2>Order Details:</h2>
            <ul>
                <li>Order Number: {order['order_number']}</li>
                <li>Total Amount: ${order['total_amount']}</li>
            </ul>
            """
        )
        
        try:
            mail = Mail(
                from_email=self.from_email,
                to_emails=To(recipient_email),
                subject=subject,
                html_content=content
            )
            response = self.sg.client.mail.send.post(request_body=mail.get())
            return {
                'status': 'success', 
                'message_id': response.headers.get('X-Message-Id')
            }
        except Exception as e:
            # Log error, potentially retry or use fallback mechanism
            return {
                'status': 'error', 
                'message': str(e)
            }

    def send_shipping_update(self, order: Dict, shipping_status: str):
        """
        Send shipping status update email
        
        Args:
            order (Dict): Order details
            shipping_status (str): Current shipping status
        """
        subject = f"Shipping Update for Order #{order['order_number']}"
        content = Content(
            "text/html", 
            f"""
            <h1>Shipping Update</h1>
            <p>Your order is now: {shipping_status}</p>
            <h2>Order Details:</h2>
            <ul>
                <li>Order Number: {order['order_number']}</li>
                <li>Estimated Delivery: {order.get('estimated_delivery', 'Not Available')}</li>
            </ul>
            """
        )
        
        try:
            mail = Mail(
                from_email=self.from_email,
                to_emails=To(order['customer_email']),
                subject=subject,
                html_content=content
            )
            response = self.sg.client.mail.send.post(request_body=mail.get())
            return {
                'status': 'success', 
                'message_id': response.headers.get('X-Message-Id')
            }
        except Exception as e:
            return {
                'status': 'error', 
                'message': str(e)
            }

email_service = EmailService()