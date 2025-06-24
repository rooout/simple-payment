from django.contrib import admin
from .models import Package, Transaction, UserAccess

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['external_id', 'package', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['external_id', 'invoice_id', 'session_key']
    readonly_fields = ['id', 'external_id', 'created_at', 'updated_at']
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'package', 'granted_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'granted_at', 'expires_at']
    search_fields = ['session_key']
    readonly_fields = ['granted_at']
