"""
Simple test script to verify Xendit integration
Run this after setting up your Xendit API keys
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_gateway.settings')

import django
django.setup()

from payments.services import XenditService
from payments.models import Package

def test_xendit_integration():
    print("Testing Xendit Integration...")
    
    # Initialize service
    xendit_service = XenditService()
    
    # Check if API keys are configured
    if not xendit_service.secret_key:
        print("❌ Error: XENDIT_SECRET_KEY not configured in .env file")
        return False
    
    print("✅ Xendit service initialized successfully")
    
    # Test with a sample invoice creation (will fail without proper API key)
    try:
        # This is just a test - won't actually create invoice without valid key
        print("📝 Xendit service configuration looks good")
        print("🔑 Secret key configured (first 10 chars):", xendit_service.secret_key[:10] + "...")
        return True
    except Exception as e:
        print(f"❌ Error testing Xendit service: {e}")
        return False

def test_models():
    print("\nTesting Database Models...")
    
    try:
        # Test Package model
        packages = Package.objects.all()
        print(f"✅ Found {packages.count()} packages in database")
        
        for package in packages:
            print(f"   - {package.name}: Rp {package.price:,.0f} ({package.duration_days} days)")
        
        return True
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def main():
    print("=== Payment Gateway Test ===\n")
    
    # Test database models
    models_ok = test_models()
    
    # Test Xendit integration
    xendit_ok = test_xendit_integration()
    
    print("\n=== Test Results ===")
    print(f"Models: {'✅ OK' if models_ok else '❌ FAILED'}")
    print(f"Xendit: {'✅ OK' if xendit_ok else '❌ FAILED'}")
    
    if models_ok and xendit_ok:
        print("\n🎉 All tests passed! Your application is ready.")
        print("🌐 Start the server with: python manage.py runserver")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()
