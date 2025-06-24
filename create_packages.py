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
        print(f"Created package: {package.name}")
    else:
        print(f"Package already exists: {package.name}")

print("Package creation completed!")
