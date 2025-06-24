#!/usr/bin/env python
"""
Production setup script for Railway deployment
This script sets up the database and creates initial packages for production
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_gateway.settings')
django.setup()

from django.core.management import execute_from_command_line
from payments.models import Package

def setup_database():
    """Run migrations to set up the database"""
    print("🔧 Setting up database...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Database migrations completed!")
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False
    return True

def create_packages():
    """Create initial packages"""
    print("\n� Creating initial packages...")
    
    packages_data = [
        {
            'name': 'Basic Premium',
            'description': 'Access to basic premium content including tutorials and guides.',
            'price': 50000.00,  # Rp 50,000
            'duration_days': 7,
            'is_active': True,
        },
        {
            'name': 'Standard Premium',
            'description': 'Full access to premium content, videos, and downloadable resources.',
            'price': 150000.00,  # Rp 150,000
            'duration_days': 30,
            'is_active': True,
        },
        {
            'name': 'Pro Premium',
            'description': 'Complete access including premium content, priority support, and exclusive webinars.',
            'price': 300000.00,  # Rp 300,000
            'duration_days': 90,
            'is_active': True,
        },
    ]

    created_count = 0
    for package_data in packages_data:
        package, created = Package.objects.get_or_create(
            name=package_data['name'],
            defaults=package_data
        )
        if created:
            created_count += 1
            print(f"✅ Created package: {package.name} - Rp {package.price:,.0f} ({package.duration_days} days)")
        else:
            print(f"ℹ️  Package already exists: {package.name}")
    
    print(f"\n📊 Summary: {created_count} new packages created, {len(packages_data)} total packages available")
    return True

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'XENDIT_SECRET_KEY',
        'XENDIT_PUBLIC_KEY', 
        'APP_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   Make sure to set these in your Railway environment variables.")
    else:
        print("✅ All required environment variables are set!")
    
    return len(missing_vars) == 0

def main():
    """Main setup function"""
    print("� Starting production setup for Payment Gateway")
    print("=" * 60)
    
    # Check environment
    env_ok = check_environment()
    
    # Setup database
    db_ok = setup_database()
    if not db_ok:
        print("❌ Setup failed at database migration step")
        sys.exit(1)
    
    # Create packages
    packages_ok = create_packages()
    if not packages_ok:
        print("❌ Setup failed at package creation step")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Production setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Visit your Railway app URL to verify packages are visible")
    print("2. Test a payment flow in test mode")
    if not env_ok:
        print("3. Set any missing environment variables in Railway dashboard")
    print("\n🔗 Your app should be available at:", os.environ.get('APP_URL', 'your-railway-url'))

if __name__ == "__main__":
    main()
