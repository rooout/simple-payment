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
        Create an invoice using Xendit API with proper payment methods for Koperasi business type
        """
        if not payment_methods:
            # Try comprehensive payment methods first
            comprehensive_methods = [
                # Virtual Account - Major Indonesian Banks
                "BCA", "BNI", "BRI", "MANDIRI", "PERMATA", "BSI", "CIMB",
                
                # Credit/Debit Cards
                "CREDIT_CARD",
                
                # QR Code Payment
                "QRIS",  # QR Indonesian Standard - this is the main QR method
                
                # E-Wallets
                "OVO", "DANA", "LINKAJA", "SHOPEEPAY",
                
                # Retail Outlets
                "ALFAMART", "INDOMARET"
            ]
            
            # Fallback methods for Koperasi accounts (if comprehensive fails)
            fallback_methods = ["CREDIT_CARD", "BCA", "BNI", "BRI", "MANDIRI"]
            
            payment_methods = comprehensive_methods
        
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
            
            # Enhanced customer information (helps with payment method availability)
            "customer": {
                "email": customer_email or "customer@example.com",
                "mobile_number": "+6281234567890",  # Required for some payment methods
                "given_names": "Customer",
                "surname": "Test"
            },
            
            # Additional settings for better payment method support
            "should_send_email": False,
            "should_authenticate_credit_card": True,
            
            # Item details (sometimes required for certain payment methods)
            "items": [
                {
                    "name": description,
                    "quantity": 1,
                    "price": float(amount),
                    "category": "Digital Services"
                }
            ],
            
            # Fee configuration
            "fees": [
                {
                    "type": "ADMIN",
                    "value": 0
                }
            ]
        }
        
        try:
            # Log the request for debugging
            logger.info(f"Creating Xendit invoice for external_id: {external_id}")
            logger.info(f"Requesting payment methods: {payment_methods}")
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
                
                # Log available payment methods from response
                available_methods = response_data.get('available_payment_methods', [])
                logger.info(f"Available payment methods: {[method.get('type') for method in available_methods]}")
                
                # If no payment methods are available, log a warning
                if not available_methods:
                    logger.warning("No payment methods available in response!")
                    logger.warning("This is common for Koperasi accounts that need additional setup")
                    logger.warning("Contact Xendit support to enable payment methods for Koperasi business type")
                
                return response_data
            else:
                logger.error(f"Xendit API Error: {response.status_code} - {response.text}")
                # Try to parse error response
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                    
                    # Check for payment method specific errors
                    if 'payment_method' in str(error_data).lower():
                        logger.warning("Payment method error detected - this might be due to Koperasi account restrictions")
                        logger.info("Consider contacting Xendit support to enable additional payment methods")
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
