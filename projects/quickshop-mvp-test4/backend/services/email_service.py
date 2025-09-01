import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self):
        self.sg_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@quickshop.com')

    def send_order_confirmation(self, to_email: str, order_details: dict):
        """
        Send order confirmation email
        
        :param to_email: Recipient email address
        :param order_details: Dictionary containing order information
        """
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject='Order Confirmation - QuickShop',
            html_content=f'''
            <h1>Order Confirmation</h1>
            <p>Thank you for your purchase!</p>
            <h2>Order Details:</h2>
            <pre>{order_details}</pre>
            '''
        )
        
        try:
            response = self.sg_client.send(message)
            return {
                'status': 'success', 
                'message': 'Email sent successfully',
                'response_code': response.status_code
            }
        except Exception as e:
            # Log error securely without exposing sensitive details
            return {
                'status': 'error', 
                'message': 'Failed to send email',
                'error': str(e)
            }

    def send_shipping_update(self, to_email: str, tracking_info: dict):
        """
        Send shipping update email
        
        :param to_email: Recipient email address
        :param tracking_info: Dictionary containing shipping information
        """
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject='Shipping Update - QuickShop',
            html_content=f'''
            <h1>Shipping Update</h1>
            <p>Your order is on its way!</p>
            <h2>Tracking Details:</h2>
            <pre>{tracking_info}</pre>
            '''
        )
        
        try:
            response = self.sg_client.send(message)
            return {
                'status': 'success', 
                'message': 'Shipping update sent successfully',
                'response_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'error', 
                'message': 'Failed to send shipping update',
                'error': str(e)
            }

# Create a singleton email service
email_service = EmailService()