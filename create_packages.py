#!/usr/bin/env python
"""
Script to create initial packages for the payment gateway
Run with: python create_packages.py
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

from payments.models import Package

# Create sample packages
packages_data = [
    {
        'name': 'Basic Premium',
        'description': 'Access to basic premium content including tutorials and guides.',
        'price': 50000.00,  # Rp 50,000
        'duration_days': 7,
    },
    {
        'name': 'Standard Premium',
        'description': 'Full access to premium content, videos, and downloadable resources.',
        'price': 150000.00,  # Rp 150,000
        'duration_days': 30,
    },
    {
        'name': 'Pro Premium',
        'description': 'Complete access including premium content, priority support, and exclusive webinars.',
        'price': 300000.00,  # Rp 300,000
        'duration_days': 90,
    },
]

for package_data in packages_data:
    package, created = Package.objects.get_or_create(
        name=package_data['name'],
        defaults=package_data
    )
    if created:
        print(f"✅ Created package: {package.name} - Rp {package.price:,.0f} ({package.duration_days} days)")
    else:
        print(f"ℹ️  Package already exists: {package.name}")

print("\n🎉 Package setup completed!")
print("You can now run your Django server and see the packages on the homepage.")
