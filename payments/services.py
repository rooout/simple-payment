import requests
import json
import base64
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class XenditService:
    def __init__(self):
        self.secret_key = settings.XENDIT_SECRET_KEY
        self.base_url = "https://api.xendit.co"
        
        # Encode the secret key properly for Xendit
        encoded_key = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json'
        }
    
    def create_invoice(self, external_id, amount, description, customer_email=None, payment_methods=None):
        """
        Create an invoice using Xendit API
        """
        if not payment_methods:
            payment_methods = [
                "VIRTUAL_ACCOUNT",
                "CREDIT_CARD", 
                "QR_CODE"
            ]
        
        # Calculate expiry time (24 hours from now)
        expiry_date = datetime.utcnow() + timedelta(hours=24)
        
        payload = {
            "external_id": external_id,
            "amount": float(amount),
            "description": description,
            "invoice_duration": 86400,  # 24 hours in seconds
            "currency": "IDR",
            "payment_methods": payment_methods,
            "success_redirect_url": f"{settings.APP_URL}/payment/success/",
            "failure_redirect_url": f"{settings.APP_URL}/payment/failed/",
        }
        
        if customer_email:
            payload["customer"] = {
                "email": customer_email
            }
        
        try:
            # Log the request for debugging
            logger.info(f"Creating Xendit invoice for external_id: {external_id}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/v2/invoices",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            logger.info(f"Xendit API response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                logger.info(f"Invoice created successfully: {response_data.get('id')}")
                return response_data
            else:
                logger.error(f"Xendit API Error: {response.status_code} - {response.text}")
                # Try to parse error response
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"Error creating Xendit invoice: {str(e)}")
            return None
    
    def get_invoice(self, invoice_id):
        """
        Get invoice details from Xendit
        """
        try:
            response = requests.get(
                f"{self.base_url}/v2/invoices/{invoice_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting invoice: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting invoice: {str(e)}")
            return None
    
    def verify_callback_token(self, callback_token):
        """
        Verify the callback token from Xendit webhook
        """
        return callback_token == settings.XENDIT_CALLBACK_TOKEN
    
    def validate_webhook_signature(self, raw_request_body, signature):
        """
        Validate webhook signature (optional but recommended for production)
        """
        # This is a simplified version. In production, you should implement
        # proper webhook signature validation using HMAC
        return True
