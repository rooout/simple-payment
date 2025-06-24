from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
import json
import uuid
import logging

from .models import Package, Transaction, UserAccess
from .services import XenditService

logger = logging.getLogger(__name__)

def home(request):
    """Landing page with available packages"""
    packages = Package.objects.filter(is_active=True)
    
    # Check if user has active access
    user_access = None
    if request.session.session_key:
        try:
            user_access = UserAccess.objects.get(
                session_key=request.session.session_key,
                is_active=True
            )
            if not user_access.is_valid():
                user_access.is_active = False
                user_access.save()
                user_access = None
        except UserAccess.DoesNotExist:
            pass
    
    context = {
        'packages': packages,
        'user_access': user_access,
    }
    return render(request, 'payments/home.html', context)

def buy_package(request, package_id):
    """Handle package purchase"""
    package = get_object_or_404(Package, id=package_id, is_active=True)
    
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    # Check if user already has active access
    try:
        existing_access = UserAccess.objects.get(
            session_key=request.session.session_key,
            is_active=True
        )
        if existing_access.is_valid():
            messages.info(request, 'You already have active access to premium content!')
            return redirect('paid_content')
    except UserAccess.DoesNotExist:
        pass
    
    # Create transaction
    external_id = f"payment_{uuid.uuid4().hex[:8]}_{package_id}"
    
    transaction = Transaction.objects.create(
        package=package,
        external_id=external_id,
        session_key=request.session.session_key,
        amount=package.price,
        expires_at=timezone.now() + timezone.timedelta(days=1)  # 24 hours to pay
    )
      # Create Xendit invoice
    xendit_service = XenditService()
    logger.info(f"Creating invoice for package {package.name} with amount {package.price}")
    
    invoice_data = xendit_service.create_invoice(
        external_id=external_id,
        amount=package.price,
        description=f"Payment for {package.name}",
        payment_methods=["VIRTUAL_ACCOUNT", "CREDIT_CARD", "QR_CODE"]
    )
    
    if invoice_data:
        transaction.invoice_id = invoice_data.get('id')
        transaction.payment_url = invoice_data.get('invoice_url')
        transaction.save()
        
        logger.info(f"Invoice created successfully: {invoice_data.get('id')}")
        logger.info(f"Payment URL: {transaction.payment_url}")
        
        # Redirect to Xendit payment page
        return redirect(transaction.payment_url)
    else:
        logger.error(f"Failed to create invoice for transaction {external_id}")
        messages.error(request, 'Failed to create payment. Please try again.')
        return redirect('home')

@csrf_exempt
@require_http_methods(["POST"])
def xendit_callback(request):
    """Handle Xendit webhook callback"""
    try:
        # Parse the JSON payload
        payload = json.loads(request.body.decode('utf-8'))
        
        # Log the callback for debugging
        logger.info(f"Xendit callback received: {payload}")
        
        # Get transaction by external_id
        external_id = payload.get('external_id')
        if not external_id:
            logger.error("No external_id in callback payload")
            return HttpResponse(status=400)
        
        try:
            transaction = Transaction.objects.get(external_id=external_id)
        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for external_id: {external_id}")
            return HttpResponse(status=404)
        
        # Update transaction with callback data
        transaction.xendit_callback_data = payload
        
        # Check payment status
        status = payload.get('status')
        if status == 'PAID':
            transaction.status = 'PAID'
            transaction.paid_at = timezone.now()
            transaction.payment_method = payload.get('payment_method', '').upper()
            
            # Grant access to user
            UserAccess.objects.update_or_create(
                session_key=transaction.session_key,
                defaults={
                    'package': transaction.package,
                    'transaction': transaction,
                    'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                    'is_active': True
                }
            )
            
            logger.info(f"Payment successful for transaction {external_id}")
            
        elif status == 'EXPIRED':
            transaction.status = 'EXPIRED'
        elif status == 'FAILED':
            transaction.status = 'FAILED'
        
        transaction.save()
        
        return HttpResponse(status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback payload")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing Xendit callback: {str(e)}")
        return HttpResponse(status=500)

def payment_success(request):
    """Payment success page"""
    return render(request, 'payments/payment_success.html')

def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payments/payment_failed.html')

def paid_content(request):
    """Protected content that requires payment"""
    # Check if user has valid access
    if not request.session.session_key:
        messages.error(request, 'You need to purchase a package to access this content.')
        return redirect('home')
    
    try:
        user_access = UserAccess.objects.get(
            session_key=request.session.session_key,
            is_active=True
        )
        
        if not user_access.is_valid():
            user_access.is_active = False
            user_access.save()
            messages.error(request, 'Your access has expired. Please purchase a new package.')
            return redirect('home')
        
        context = {
            'user_access': user_access,
        }
        return render(request, 'payments/paid_content.html', context)
        
    except UserAccess.DoesNotExist:
        messages.error(request, 'You need to purchase a package to access this content.')
        return redirect('home')

def check_payment_status(request, transaction_id):
    """Check payment status via AJAX"""
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        return JsonResponse({
            'status': transaction.status,
            'paid': transaction.is_paid(),
            'redirect_url': reverse('paid_content') if transaction.is_paid() else None
        })
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
