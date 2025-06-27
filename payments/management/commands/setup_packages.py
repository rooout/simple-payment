from django.core.management.base import BaseCommand
from payments.models import Package

class Command(BaseCommand):
    help = 'Create initial packages for the payment system'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating initial packages...')
        
        packages = [
            {
                'name': 'Basic Premium',
                'description': 'Get access to premium content for 30 days. Perfect for trying out our premium features.',
                'price': 50000,
                'duration_days': 30,
            },
            {
                'name': 'Premium Plus',
                'description': 'Extended access to all premium content for 90 days. Great value for regular users.',
                'price': 120000,
                'duration_days': 90,
            },
            {
                'name': 'Premium Pro',
                'description': 'Complete access to all premium content for 180 days. Best value for power users.',
                'price': 200000,
                'duration_days': 180,
            }
        ]
        
        created_count = 0
        
        for package_data in packages:
            package, created = Package.objects.get_or_create(
                name=package_data['name'],
                defaults={
                    'description': package_data['description'],
                    'price': package_data['price'],
                    'duration_days': package_data['duration_days'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created package: {package.name} - Rp {package.price}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Package already exists: {package.name}')
                )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully created {created_count} packages!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  All packages already exist.')
            )
        
        self.stdout.write('\n📦 Current packages:')
        for package in Package.objects.filter(is_active=True):
            self.stdout.write(f'   - {package.name}: Rp {package.price} ({package.duration_days} days)')
