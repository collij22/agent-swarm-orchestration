from typing import Dict, Optional
import requests
from core.config import settings

class GoogleAnalyticsService:
    def __init__(self, tracking_id: str):
        self.tracking_id = tracking_id
        self.measurement_protocol_url = "https://www.google-analytics.com/mp/collect"

    def track_page_view(self, user_id: str, page_path: str):
        """
        Track page view event
        
        Args:
            user_id (str): Unique user identifier
            page_path (str): Path of the page viewed
        """
        payload = {
            "client_id": user_id,
            "events": [{
                "name": "page_view",
                "params": {
                    "page_path": page_path,
                    "page_title": page_path.split('/')[-1]
                }
            }]
        }
        
        self._send_event(payload)

    def track_product_view(self, user_id: str, product: Dict):
        """
        Track product view event
        
        Args:
            user_id (str): Unique user identifier
            product (Dict): Product details
        """
        payload = {
            "client_id": user_id,
            "events": [{
                "name": "view_item",
                "params": {
                    "items": [{
                        "item_id": product.get('id'),
                        "item_name": product.get('name'),
                        "price": product.get('price'),
                        "currency": "USD"
                    }]
                }
            }]
        }
        
        self._send_event(payload)

    def track_purchase(self, user_id: str, order: Dict):
        """
        Track purchase event
        
        Args:
            user_id (str): Unique user identifier
            order (Dict): Order details
        """
        payload = {
            "client_id": user_id,
            "events": [{
                "name": "purchase",
                "params": {
                    "transaction_id": order.get('order_number'),
                    "value": order.get('total_amount'),
                    "currency": "USD",
                    "items": [
                        {
                            "item_id": item.get('product_id'),
                            "item_name": item.get('product_name'),
                            "price": item.get('price'),
                            "quantity": item.get('quantity')
                        } for item in order.get('items', [])
                    ]
                }
            }]
        }
        
        self._send_event(payload)

    def _send_event(self, payload: Dict):
        """
        Send event to Google Analytics Measurement Protocol
        
        Args:
            payload (Dict): Event payload
        """
        try:
            response = requests.post(
                f"{self.measurement_protocol_url}?measurement_id={self.tracking_id}&api_secret={settings.GOOGLE_ANALYTICS_API_SECRET}",
                json=payload
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Log error, potentially implement retry mechanism
            print(f"Google Analytics tracking failed: {e}")

# Initialize with tracking ID from configuration
analytics_service = GoogleAnalyticsService(tracking_id="G-XXXXXXXXXX")