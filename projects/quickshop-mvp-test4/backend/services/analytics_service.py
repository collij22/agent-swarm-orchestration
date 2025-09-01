import os
import requests
from typing import Dict, Optional

class GoogleAnalyticsService:
    def __init__(self):
        # Use environment variables for configuration
        self.measurement_id = os.getenv('GA_MEASUREMENT_ID')
        self.api_secret = os.getenv('GA_API_SECRET')
        self.base_url = 'https://www.google-analytics.com/mp/collect'

    def _send_event(
        self, 
        client_id: str, 
        event_name: str, 
        event_params: Optional[Dict] = None
    ):
        """
        Send an event to Google Analytics 4
        
        :param client_id: Unique identifier for the user/session
        :param event_name: Name of the event to track
        :param event_params: Optional event parameters
        """
        if not all([self.measurement_id, self.api_secret, client_id]):
            print("Google Analytics configuration incomplete. Skipping event.")
            return

        payload = {
            'client_id': client_id,
            'events': [{
                'name': event_name,
                'params': event_params or {}
            }]
        }

        try:
            response = requests.post(
                f"{self.base_url}?measurement_id={self.measurement_id}&api_secret={self.api_secret}",
                json=payload
            )
            response.raise_for_status()
        except requests.RequestException as e:
            # Log error securely without exposing sensitive details
            print(f"Analytics tracking error: {str(e)}")

    def track_purchase(self, client_id: str, order_details: Dict):
        """
        Track a purchase event
        
        :param client_id: User/session identifier
        :param order_details: Details of the completed order
        """
        self._send_event(
            client_id, 
            'purchase', 
            {
                'transaction_id': order_details.get('order_id'),
                'value': order_details.get('total_amount', 0),
                'currency': order_details.get('currency', 'USD')
            }
        )

    def track_product_view(self, client_id: str, product_id: str):
        """
        Track a product view event
        
        :param client_id: User/session identifier
        :param product_id: ID of the viewed product
        """
        self._send_event(
            client_id, 
            'view_item', 
            {
                'item_id': product_id
            }
        )

# Create a singleton analytics service
analytics_service = GoogleAnalyticsService()