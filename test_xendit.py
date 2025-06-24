"""
Test Xendit integration directly
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_gateway.settings')

import django
django.setup()

from payments.services import XenditService
from payments.models import Package
import uuid

def test_xendit_api():
    print("=== Testing Xendit API Integration ===\n")
    
    # Initialize service
    xendit_service = XenditService()
    print(f"✅ Service initialized")
    print(f"🔑 Secret key: {xendit_service.secret_key[:15]}...")
    print(f"🌐 Base URL: {xendit_service.base_url}")
    print(f"📡 Authorization header: {xendit_service.headers['Authorization'][:20]}...")
    
    # Get first package
    try:
        package = Package.objects.first()
        if not package:
            print("❌ No packages found in database")
            return
        
        print(f"\n📦 Testing with package: {package.name} (Rp {package.price})")
        
        # Create test invoice
        external_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"🆔 External ID: {external_id}")
        
        result = xendit_service.create_invoice(
            external_id=external_id,
            amount=package.price,
            description=f"Test payment for {package.name}"
        )
        
        if result:
            print(f"\n✅ SUCCESS! Invoice created:")
            print(f"   - Invoice ID: {result.get('id')}")
            print(f"   - Status: {result.get('status')}")
            print(f"   - Amount: {result.get('amount')}")
            print(f"   - Currency: {result.get('currency')}")
            print(f"   - Payment URL: {result.get('invoice_url')}")
            print(f"   - Expires: {result.get('expiry_date')}")
        else:
            print(f"\n❌ FAILED! Could not create invoice")
            print("Check the Django server logs for detailed error messages")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_xendit_api()
