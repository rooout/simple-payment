import requests
import json
import base64
from django.conf import settings
from datetime import datetime, timedelta
import logging
import qrcode
from io import BytesIO

logger = logging.getLogger(__name__)

class XenditService:
    def __init__(self):
        self.secret_key = settings.XENDIT_SECRET_KEY
        self.public_key = getattr(settings, 'XENDIT_PUBLIC_KEY', '')
        self.base_url = "https://api.xendit.co"
        
        encoded_key = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json'
        }
    
    def create_virtual_account(self, external_id, amount, bank_code, customer_name="Customer"):
        payload = {
            "external_id": external_id,
            "bank_code": bank_code,
            "name": customer_name,
            "expected_amount": int(float(amount)),
            "is_single_use": True,
            "is_closed": True,
            "expiration_date": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        }
        
        try:
            logger.info(f"Creating {bank_code} Virtual Account for {external_id}")
            
            response = requests.post(
                f"{self.base_url}/callback_virtual_accounts",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"VA Creation Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating virtual account: {str(e)}")
            return None
    
    def create_qr_code(self, external_id, amount, qr_type="DYNAMIC", channel_code="ID_DANA"):
        payload = {
            "reference_id": external_id,
            "type": qr_type,
            "currency": "IDR",
            "amount": int(float(amount)),
            "channel_code": channel_code,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.secret_key}:".encode()).decode()}',
            'Content-Type': 'application/json',
            'api-version': '2022-07-31'
        }
        
        try:
            logger.info(f"Creating {qr_type} QR Code with {channel_code} for {external_id}")
            logger.info(f"Amount: Rp {amount:,}")
            
            response = requests.post(
                f"{self.base_url}/qr_codes",
                headers=headers,
                data=json.dumps(payload)
            )
            
            logger.info(f"QR API Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                qr_data = response.json()
                
                qr_string = qr_data.get('qr_string', '')
                logger.info(f"✅ QR Code created successfully!")
                logger.info(f"   QR ID: {qr_data.get('id')}")
                logger.info(f"   Status: {qr_data.get('status')}")
                logger.info(f"   Channel: {qr_data.get('channel_code')}")
                logger.info(f"   Amount: Rp {qr_data.get('amount'):,}")
                logger.info(f"   QR String Length: {len(qr_string)} characters")
                logger.info(f"   QR String Preview: {qr_string[:100]}...")
                
                qr_string = qr_data.get('qr_string', '')
                
                if qr_string == "some-random-qr-string":
                    logger.info("   Detected test mode - generating realistic test QR code")
                    test_qris_string = self.generate_test_qris_string(
                        amount=qr_data.get('amount', 1000),
                        merchant_name="Test Merchant",
                        reference_id=qr_data.get('reference_id', 'test')
                    )
                    qr_data['qr_code_image'] = self.generate_qr_code_image(test_qris_string)
                    qr_data['qr_string'] = test_qris_string
                    qr_data['test_mode'] = True
                    logger.info(f"   Generated test QRIS string: {test_qris_string[:50]}...")
                    
                elif qr_string and len(qr_string) > 10:  # Valid QRIS string should be longer
                    qr_data['qr_code_image'] = self.generate_qr_code_image(qr_string)
                    logger.info("   QR Code image generated successfully")
                    
                else:
                    logger.warning(f"   Invalid or empty QR string received: '{qr_string}'")
                    fallback_data = f"PAYMENT:{qr_data.get('id')}:IDR:{qr_data.get('amount')}:{qr_data.get('reference_id')}"
                    qr_data['qr_code_image'] = self.generate_qr_code_image(fallback_data)
                    qr_data['qr_string'] = fallback_data
                    qr_data['fallback_mode'] = True
                    logger.info("   Generated fallback QR code")
                
                return qr_data
            else:
                logger.error(f"QR Creation Error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
                if channel_code == "ID_DANA":
                    logger.info("Trying ID_LINKAJA as fallback...")
                    return self._create_qr_code_with_linkaja(external_id, amount, qr_type)
                return None
                
        except Exception as e:
            logger.error(f"Error creating QR code: {str(e)}")
            return None
    
    def _create_qr_code_with_linkaja(self, external_id, amount, qr_type):
        payload = {
            "reference_id": external_id,
            "type": qr_type,
            "currency": "IDR",
            "amount": int(float(amount)),
            "channel_code": "ID_LINKAJA",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.secret_key}:".encode()).decode()}',
            'Content-Type': 'application/json',
            'api-version': '2022-07-31'
        }
        
        try:
            logger.info(f"Trying ID_LINKAJA QR for {external_id}")
            response = requests.post(
                f"{self.base_url}/qr_codes",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                qr_data = response.json()
                
                qr_string = qr_data.get('qr_string', '')
                
                if qr_string == "some-random-qr-string":
                    logger.info("   LinkAja test mode - generating realistic test QR code")
                    test_qris_string = self.generate_test_qris_string(
                        amount=qr_data.get('amount', 1000),
                        merchant_name="LinkAja Test Merchant",
                        reference_id=qr_data.get('reference_id', 'linkaja_test')
                    )
                    qr_data['qr_code_image'] = self.generate_qr_code_image(test_qris_string)
                    qr_data['qr_string'] = test_qris_string
                    qr_data['test_mode'] = True
                    
                elif qr_string and len(qr_string) > 10:
                    qr_data['qr_code_image'] = self.generate_qr_code_image(qr_string)
                    
                else:
                    fallback_data = f"LINKAJA_PAYMENT:{qr_data.get('id')}:IDR:{qr_data.get('amount')}"
                    qr_data['qr_code_image'] = self.generate_qr_code_image(fallback_data)
                    qr_data['qr_string'] = fallback_data
                    qr_data['fallback_mode'] = True
                    
                return qr_data
            else:
                logger.error(f"LINKAJA QR Creation Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with LINKAJA QR endpoint: {str(e)}")
            return None
    
    def tokenize_card(self, card_number, card_exp_month, card_exp_year, card_cvn, card_holder_name):
        payload = {
            "card_number": card_number,
            "card_exp_month": card_exp_month,
            "card_exp_year": card_exp_year,
            "card_cvn": card_cvn,
            "card_holder_name": card_holder_name,
            "is_multiple_use": False
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.public_key}:".encode()).decode()}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/credit_card_tokens",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Card Tokenization Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error tokenizing card: {str(e)}")
            return None
    
    def charge_credit_card(self, external_id, amount, token_id, description):
        payload = {
            "token_id": token_id,
            "external_id": external_id,
            "amount": float(amount),
            "description": description,
            "currency": "IDR"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/credit_card_charges",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Card Charge Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error charging card: {str(e)}")
            return None
    
    def get_available_banks(self):
        banks = [
            {"code": "BCA", "name": "Bank Central Asia", "fee": 0},
            {"code": "BNI", "name": "Bank Negara Indonesia", "fee": 0},
            {"code": "BRI", "name": "Bank Rakyat Indonesia", "fee": 0},
            {"code": "MANDIRI", "name": "Bank Mandiri", "fee": 0},
            {"code": "PERMATA", "name": "Bank Permata", "fee": 0},
            {"code": "BSI", "name": "Bank Syariah Indonesia", "fee": 0},
        ]
        return banks    
    
    def get_available_qr_types(self):
        qr_types = [
            {
                "code": "QRIS_GENERAL",
                "channel_code": "ID_DANA", 
                "name": "QRIS Universal",
                "description": "Universal QRIS - Works with GoPay, OVO, DANA, ShopeePay, LinkAja, BCA Mobile, Mandiri Livin, and all QRIS apps",
                "icon": "🏷️",
                "popular": True
            },
            {
                "code": "DANA_QR",
                "channel_code": "ID_DANA",
                "name": "DANA QR Code", 
                "description": "DANA-optimized QRIS - Works with DANA and all other QRIS-enabled apps",
                "icon": "💙",
                "popular": True
            },
            {
                "code": "LINKAJA_QR", 
                "channel_code": "ID_LINKAJA",
                "name": "LinkAja QR Code",
                "description": "LinkAja-optimized QRIS - Works with LinkAja and all other QRIS-enabled apps", 
                "icon": "🔗",
                "popular": True
            },
            {
                "code": "GOPAY_COMPATIBLE",
                "channel_code": "ID_DANA",
                "name": "GoPay Compatible",
                "description": "QRIS code compatible with GoPay, DANA, OVO, and all QRIS network apps",
                "icon": "�",
                "popular": True
            }
        ]
        return qr_types
    
    def create_qr_code_by_type(self, external_id, amount, qr_code_type="QRIS_GENERAL"):
        qr_types = self.get_available_qr_types()
        qr_type_info = next((qt for qt in qr_types if qt["code"] == qr_code_type), None)
        
        if not qr_type_info:
            logger.error(f"Unknown QR code type: {qr_code_type}")
            return None
        
        channel_code = qr_type_info["channel_code"]
        logger.info(f"Creating {qr_type_info['name']} QR code using channel {channel_code}")
        
        return self.create_qr_code(
            external_id=external_id,
            amount=amount,
            qr_type="DYNAMIC",
            channel_code=channel_code
        )

    def verify_callback_token(self, callback_token):
        return callback_token == settings.XENDIT_CALLBACK_TOKEN
    
    def validate_webhook_signature(self, raw_request_body, signature):
        return True
    
    def create_invoice(self, external_id, amount, description, customer_email="customer@example.com", customer_name="Customer"):
        payload = {
            "external_id": external_id,
            "amount": int(float(amount)),
            "description": description,
            "invoice_duration": 86400,
            "customer": {
                "given_names": customer_name.split()[0] if customer_name else "Customer",
                "surname": customer_name.split()[-1] if len(customer_name.split()) > 1 else "",
                "email": customer_email
            },
            "customer_notification_preference": {
                "invoice_created": ["email"],
                "invoice_reminder": ["email"],
                "invoice_paid": ["email"]
            },
            "success_redirect_url": f"{settings.APP_URL}/payment/success/",
            "failure_redirect_url": f"{settings.APP_URL}/payment/failed/"
        }
        
        try:
            logger.info(f"Creating invoice for {external_id} - Amount: {amount}")
            response = requests.post(
                f"{self.base_url}/v2/invoices",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Invoice Creation Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return None
    
    def simulate_qr_payment(self, qr_id, amount=None):
        payload = {}
        if amount:
            payload["amount"] = int(float(amount))
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.secret_key}:".encode()).decode()}',
            'Content-Type': 'application/json',
            'api-version': '2022-07-31'
        }
        
        try:
            logger.info(f"Simulating QR payment for {qr_id}")
            response = requests.post(
                f"{self.base_url}/qr_codes/{qr_id}/payments/simulate",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"QR Payment Simulation Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error simulating QR payment: {str(e)}")
            return None

    def get_qr_code_by_id(self, qr_id):
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.secret_key}:".encode()).decode()}',
            'Content-Type': 'application/json',
            'api-version': '2022-07-31'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/qr_codes/{qr_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get QR Code Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting QR code: {str(e)}")
            return None

    def generate_qr_code_image(self, qr_string):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating QR code image: {str(e)}")
            return None
    
    def generate_test_qris_string(self, amount, merchant_name="Test Merchant", reference_id="test"):
        try:
            amount_str = f"{float(amount):.2f}"
            
            test_qris = (
                f"00020101"
                f"021230"
                f"2661"
                f"0016COM.TESTBANK.WWW"
                f"0118936000000000000000"
                f"0303UME"
                f"5204{6013:04d}"
                f"5303360"
                f"54{len(amount_str):02d}{amount_str}"
                f"58{len('ID'):02d}ID"
                f"59{len(merchant_name):02d}{merchant_name}"
                f"60{len('Jakarta'):02d}Jakarta"
                f"61{len('12345'):02d}12345"
                f"62{len(reference_id) + 4:02d}01{len(reference_id):02d}{reference_id}"
                f"6304"
            )
            
            test_qris += "ABCD"
            
            return test_qris
            
        except Exception as e:
            logger.error(f"Error generating test QRIS string: {str(e)}")
            return f"TEST_QRIS:{reference_id}:IDR:{amount}:MERCHANT:{merchant_name}"
