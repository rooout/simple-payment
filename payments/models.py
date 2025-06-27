from django.db import models
from django.utils import timezone
import uuid

class Package(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - Rp {self.price}"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]    
    PAYMENT_METHOD_CHOICES = [
        ('VIRTUAL_ACCOUNT', 'Virtual Account'),
        ('VA_BCA', 'BCA Virtual Account'),
        ('VA_BNI', 'BNI Virtual Account'),
        ('VA_BRI', 'BRI Virtual Account'),
        ('VA_MANDIRI', 'Mandiri Virtual Account'),
        ('VA_PERMATA', 'Permata Virtual Account'),
        ('VA_BSI', 'BSI Virtual Account'),
        ('CREDIT_CARD', 'Credit/Debit Card'),
        ('QRIS', 'QR Code (QRIS)'),
        ('QR_CODE', 'QR Code'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255, unique=True)
    invoice_id = models.CharField(max_length=255, blank=True, null=True)
    xendit_qr_id = models.CharField(max_length=100, blank=True, null=True)
    xendit_payment_id = models.CharField(max_length=100, blank=True, null=True)
    session_key = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_url = models.URLField(blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)
    xendit_callback_data = models.JSONField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    xendit_callback_data = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"Transaction {self.external_id} - {self.status}"
    
    def is_paid(self):
        return self.status == 'PAID'
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class UserAccess(models.Model):
    session_key = models.CharField(max_length=255, unique=True)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Access for {self.session_key} - {self.package.name}"
    
    def is_valid(self):
        return self.is_active and timezone.now() <= self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=self.package.duration_days)
        super().save(*args, **kwargs)
