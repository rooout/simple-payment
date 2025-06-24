from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
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
        
        # Store transaction ID in session for later reference
        request.session['current_transaction_id'] = str(transaction.id)
        request.session['current_external_id'] = external_id
        
        # Redirect to Xendit payment page
        return redirect(transaction.payment_url)
    else:
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
        transaction.xendit_callback_data = payload        # Check payment status - handle both live and test modes
        status = payload.get('status', '').upper()
        logger.info(f"Processing payment status: {status} for transaction {external_id}")
        logger.info(f"Full payload: {json.dumps(payload, indent=2)}")
        
        # Handle various success statuses (test and live modes)
        if status in ['PAID', 'COMPLETED', 'SETTLED', 'SUCCESS']:
            transaction.status = 'PAID'
            transaction.paid_at = timezone.now()
            transaction.payment_method = payload.get('payment_method', payload.get('payment_channel', '')).upper()
            
            # Grant access to user
            user_access, created = UserAccess.objects.update_or_create(
                session_key=transaction.session_key,
                defaults={
                    'package': transaction.package,
                    'transaction': transaction,
                    'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                    'is_active': True
                }
            )
            
            logger.info(f"Payment successful for transaction {external_id}")
            logger.info(f"User access {'created' if created else 'updated'} for session {transaction.session_key}")
            
        elif status in ['EXPIRED', 'INACTIVE']:
            transaction.status = 'EXPIRED'
            logger.info(f"Transaction {external_id} expired")
        elif status in ['FAILED', 'FAILED_CAPTURE']:
            transaction.status = 'FAILED'
            logger.info(f"Transaction {external_id} failed")
        else:
            logger.warning(f"Unknown payment status: {status} for transaction {external_id}")
        
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
    # Get current transaction ID from session
    current_transaction_id = request.session.get('current_transaction_id')
    current_transaction = None
    
    if current_transaction_id:
        try:
            current_transaction = Transaction.objects.get(id=current_transaction_id)
        except Transaction.DoesNotExist:
            pass
    
    # Check if user has active access (payment completed)
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
        'user_access': user_access,
        'current_transaction': current_transaction,
        'current_transaction_id': current_transaction_id,
    }
    return render(request, 'payments/payment_success.html', context)

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

def check_user_access(request):
    """Check if current user has premium access (for AJAX calls)"""
    if not request.session.session_key:
        return JsonResponse({'has_access': False})
    
    try:
        user_access = UserAccess.objects.get(
            session_key=request.session.session_key,
            is_active=True
        )
        
        if user_access.is_valid():
            return JsonResponse({
                'has_access': True,
                'package_name': user_access.package.name,
                'expires_at': user_access.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                'redirect_url': reverse('paid_content')
            })
        else:
            # Access expired
            user_access.is_active = False
            user_access.save()
            return JsonResponse({'has_access': False})
            
    except UserAccess.DoesNotExist:
        return JsonResponse({'has_access': False})

def verify_payment(request, transaction_id):
    """Manually verify payment status with Xendit (useful for test mode)"""
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True, 
                'message': 'Payment already confirmed',
                'redirect_url': reverse('paid_content')
            })
        
        # Check with Xendit API
        xendit_service = XenditService()
        if transaction.invoice_id:
            invoice_data = xendit_service.get_invoice(transaction.invoice_id)
            
            if invoice_data:
                status = invoice_data.get('status', '').upper()
                logger.info(f"Xendit API status for {transaction.external_id}: {status}")
                
                # Check if payment is successful
                if status in ['PAID', 'SETTLED', 'COMPLETED']:
                    # Update transaction
                    transaction.status = 'PAID'
                    transaction.paid_at = timezone.now()
                    transaction.payment_method = invoice_data.get('payment_method', 'UNKNOWN')
                    transaction.save()
                    
                    # Grant access
                    user_access, created = UserAccess.objects.update_or_create(
                        session_key=transaction.session_key,
                        defaults={
                            'package': transaction.package,
                            'transaction': transaction,
                            'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                            'is_active': True
                        }
                    )
                    
                    logger.info(f"Manual verification successful for {transaction.external_id}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Payment verified and access granted!',
                        'redirect_url': reverse('paid_content')
                    })
                elif status in ['PENDING', 'UNPAID']:
                    return JsonResponse({
                        'success': False,
                        'message': 'Payment is still pending. Please complete the payment first.',
                        'status': 'pending'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Payment failed or expired (Status: {status})',
                        'status': 'failed'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Unable to verify payment with Xendit API',
                    'status': 'error'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No invoice ID found for this transaction',
                'status': 'error'
            })
            
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Transaction not found',
            'status': 'error'
        }, status=404)
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while verifying payment',
            'status': 'error'
        }, status=500)

def simulate_payment_success(request, transaction_id):
    """Simulate successful payment for test mode (development only)"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'This endpoint is only available in DEBUG mode'}, status=403)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True,
                'message': 'Payment already confirmed'
            })
        
        # Simulate successful payment
        transaction.status = 'PAID'
        transaction.paid_at = timezone.now()
        transaction.payment_method = 'TEST_PAYMENT'
        transaction.save()
        
        # Grant access
        user_access, created = UserAccess.objects.update_or_create(
            session_key=transaction.session_key,
            defaults={
                'package': transaction.package,
                'transaction': transaction,
                'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                'is_active': True
            }
        )
        
        logger.info(f"Test payment simulated for {transaction.external_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Test payment completed successfully!',
            'redirect_url': reverse('paid_content')
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    except Exception as e:
        logger.error(f"Error simulating payment: {str(e)}")
        return JsonResponse({'error': 'Failed to simulate payment'}, status=500)
