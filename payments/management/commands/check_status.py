from django.core.management.base import BaseCommand
from payments.models import Package, Transaction, UserAccess
from django.conf import settings

class Command(BaseCommand):
    help = 'Check the current status of the payment system'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Payment System Status Check')
        self.stdout.write('=' * 50)
        
        # Check Django settings
        self.stdout.write('\n⚙️  Django Configuration:')
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        self.stdout.write(f'   APP_URL: {settings.APP_URL}')
        
        # Check Xendit configuration
        self.stdout.write('\n💳 Xendit Configuration:')
        xendit_secret = settings.XENDIT_SECRET_KEY
        if xendit_secret:
            if xendit_secret.startswith('xnd_development_'):
                self.stdout.write('   ✅ Using Xendit DEVELOPMENT/TEST keys')
            elif xendit_secret.startswith('xnd_production_'):
                self.stdout.write('   ✅ Using Xendit PRODUCTION/LIVE keys')
            else:
                self.stdout.write('   ⚠️  Xendit key format not recognized')
            self.stdout.write(f'   Secret Key: {xendit_secret[:20]}...')
        else:
            self.stdout.write('   ❌ XENDIT_SECRET_KEY not configured')
        
        # Check packages
        self.stdout.write('\n📦 Packages:')
        packages = Package.objects.filter(is_active=True)
        if packages.exists():
            self.stdout.write(f'   ✅ {packages.count()} active packages found:')
            for package in packages:
                self.stdout.write(f'      - {package.name}: Rp {package.price} ({package.duration_days} days)')
        else:
            self.stdout.write('   ❌ No active packages found!')
            self.stdout.write('   💡 Run: python manage.py setup_packages')
        
        # Check transactions
        self.stdout.write('\n💰 Transactions:')
        total_transactions = Transaction.objects.count()
        paid_transactions = Transaction.objects.filter(status='PAID').count()
        pending_transactions = Transaction.objects.filter(status='PENDING').count()
        
        self.stdout.write(f'   Total: {total_transactions}')
        self.stdout.write(f'   Paid: {paid_transactions}')
        self.stdout.write(f'   Pending: {pending_transactions}')
        
        # Check user access
        self.stdout.write('\n👤 User Access:')
        total_access = UserAccess.objects.count()
        active_access = UserAccess.objects.filter(is_active=True).count()
        
        self.stdout.write(f'   Total: {total_access}')
        self.stdout.write(f'   Active: {active_access}')
        
        # Recent activity
        self.stdout.write('\n📊 Recent Activity:')
        recent_transactions = Transaction.objects.order_by('-created_at')[:5]
        if recent_transactions:
            for trans in recent_transactions:
                status_emoji = '✅' if trans.status == 'PAID' else '⏳' if trans.status == 'PENDING' else '❌'
                self.stdout.write(f'   {status_emoji} {trans.created_at.strftime("%Y-%m-%d %H:%M")} - {trans.external_id} ({trans.status})')
        else:
            self.stdout.write('   No transactions found')
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('✅ Status check completed!')
