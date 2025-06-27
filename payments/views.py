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
    packages = Package.objects.filter(is_active=True)
    
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
    package = get_object_or_404(Package, id=package_id, is_active=True)
    
    if not request.session.session_key:
        request.session.create()
    
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
    
    external_id = f"payment_{uuid.uuid4().hex[:8]}_{package_id}"
    
    transaction = Transaction.objects.create(
        package=package,
        external_id=external_id,
        session_key=request.session.session_key,
        amount=package.price,
        expires_at=timezone.now() + timezone.timedelta(days=1)
    )
    
    request.session['current_transaction_id'] = str(transaction.id)
    request.session['current_external_id'] = external_id
    
    return redirect('payment_methods', transaction_id=transaction.id)

@csrf_exempt
@require_http_methods(["POST"])
def xendit_callback(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        
        logger.info(f"Xendit callback received: {payload}")
        
        external_id = payload.get('external_id')
        if not external_id:
            logger.error("No external_id in callback payload")
            return HttpResponse(status=400)
        
        try:
            transaction = Transaction.objects.get(external_id=external_id)
        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for external_id: {external_id}")
            return HttpResponse(status=404)
        
        transaction.xendit_callback_data = payload
        status = payload.get('status', '').upper()
        logger.info(f"Processing payment status: {status} for transaction {external_id}")
        logger.info(f"Full payload: {json.dumps(payload, indent=2)}")
        
        if status in ['PAID', 'COMPLETED', 'SETTLED', 'SUCCESS']:
            transaction.status = 'PAID'
            transaction.paid_at = timezone.now()
            transaction.payment_method = payload.get('payment_method', payload.get('payment_channel', '')).upper()
            
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
    current_transaction_id = request.session.get('current_transaction_id')
    current_transaction = None
    
    if current_transaction_id:
        try:
            current_transaction = Transaction.objects.get(id=current_transaction_id)
        except Transaction.DoesNotExist:
            pass
    
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
    return render(request, 'payments/payment_failed.html')

def paid_content(request):
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
            user_access.is_active = False
            user_access.save()
            return JsonResponse({'has_access': False})
            
    except UserAccess.DoesNotExist:
        return JsonResponse({'has_access': False})

def verify_payment(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True, 
                'message': 'Payment already confirmed',
                'redirect_url': reverse('paid_content')
            })
        
        xendit_service = XenditService()
        if transaction.invoice_id:
            invoice_data = xendit_service.get_invoice(transaction.invoice_id)
            
            if invoice_data:
                status = invoice_data.get('status', '').upper()
                logger.info(f"Xendit API status for {transaction.external_id}: {status}")
                
                if status in ['PAID', 'SETTLED', 'COMPLETED']:
                    transaction.status = 'PAID'
                    transaction.paid_at = timezone.now()
                    transaction.payment_method = invoice_data.get('payment_method', 'UNKNOWN')
                    transaction.save()
                    
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

@csrf_exempt
def simulate_payment_success(request, transaction_id):
    if not (settings.DEBUG or getattr(settings, 'ENABLE_TEST_ENDPOINTS', False) or getattr(settings, 'USING_XENDIT_TEST_KEYS', False)):
        return JsonResponse({'error': 'This endpoint is only available in test mode'}, status=403)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True,
                'message': 'Payment already confirmed'
            })
        
        transaction.status = 'PAID'
        transaction.paid_at = timezone.now()
        transaction.payment_method = 'TEST_PAYMENT'
        transaction.save()
        
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

def payment_methods(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        if transaction.status == 'PAID':
            return redirect('paid_content')
        
        xendit_service = XenditService()
        available_banks = xendit_service.get_available_banks()
        available_qr_types = xendit_service.get_available_qr_types()
        
        context = {
            'transaction': transaction,
            'available_banks': available_banks,
            'available_qr_types': available_qr_types,
        }
        return render(request, 'payments/payment_methods.html', context)
        
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('home')

@csrf_exempt
@require_http_methods(["POST"])
def process_virtual_account(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        bank_code = request.POST.get('bank_code')
        customer_name = request.POST.get('customer_name', 'Customer')
        
        if not bank_code:
            return JsonResponse({'success': False, 'message': 'Please select a bank'})
        
        xendit_service = XenditService()
        va_data = xendit_service.create_virtual_account(
            external_id=transaction.external_id,
            amount=transaction.amount,
            bank_code=bank_code,
            customer_name=customer_name
        )
        
        if va_data:
            transaction.payment_method = f'VA_{bank_code}'
            transaction.payment_details = json.dumps(va_data)
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'va_number': va_data.get('account_number'),
                'bank_name': va_data.get('bank_code'),
                'amount': va_data.get('expected_amount'),
                'expiry': va_data.get('expiration_date'),
                'transaction_id': transaction_id
            })
        else:
            return JsonResponse({'success': False, 'message': 'Failed to create Virtual Account'})
            
    except Transaction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Transaction not found'})
    except Exception as e:
        logger.error(f"Error processing VA payment: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'})

@csrf_exempt
@require_http_methods(["POST"])
def process_qr_payment(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': False, 
                'message': 'Transaction already paid'
            })
        
        qr_type = request.POST.get('qr_type', 'QRIS_GENERAL')
        
        xendit_service = XenditService()
        
        qr_data = xendit_service.create_qr_code_by_type(
            external_id=transaction.external_id,
            amount=transaction.amount,
            qr_code_type=qr_type
        )
        
        if qr_data and qr_data.get('status') == 'ACTIVE':
            transaction.payment_method = 'QRIS'
            transaction.payment_details = json.dumps(qr_data)
            transaction.xendit_qr_id = qr_data.get('id')
            transaction.save()
            
            logger.info(f"✅ QRIS QR Code created for transaction {transaction_id}")
            logger.info(f"   QR ID: {qr_data.get('id')}")
            logger.info(f"   Type: {qr_type}")
            logger.info(f"   Channel: {qr_data.get('channel_code')}")
            logger.info(f"   Status: {qr_data.get('status')}")
            
            response_data = {
                'success': True,
                'qr_id': qr_data.get('id'),
                'qr_string': qr_data.get('qr_string'),
                'amount': qr_data.get('amount'),
                'channel_code': qr_data.get('channel_code'),
                'expires_at': qr_data.get('expires_at'),
                'status': qr_data.get('status'),
                'qr_type': qr_type,
                'transaction_id': transaction_id,
                'message': f'QRIS QR Code generated successfully! This QR code works with all QRIS-enabled apps.'
            }
            
            if 'qr_code_image' in qr_data and qr_data['qr_code_image']:
                response_data['qr_code_image'] = qr_data['qr_code_image']
                logger.info("   QR Code image included in response")
            else:
                logger.warning("   No QR Code image available")
            
            return JsonResponse(response_data)
        else:
            error_msg = 'Failed to create QRIS QR Code'
            if qr_data:
                error_msg += f" (Status: {qr_data.get('status', 'Unknown')})"
            else:
                error_msg += " - No response from Xendit API"
            
            logger.error(f"❌ {error_msg} for transaction {transaction_id}")
            return JsonResponse({
                'success': False, 
                'message': error_msg
            })
            
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Transaction not found'
        })
    except Exception as e:
        logger.error(f"Error processing QR payment: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'An error occurred while creating QR code'
        })

@csrf_exempt
@require_http_methods(["POST"])
def process_credit_card(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        card_number = request.POST.get('card_number', '').replace(' ', '')
        card_exp_month = request.POST.get('exp_month')
        card_exp_year = request.POST.get('exp_year')
        card_cvn = request.POST.get('cvn')
        card_holder_name = request.POST.get('card_holder_name')
        
        if not all([card_number, card_exp_month, card_exp_year, card_cvn, card_holder_name]):
            return JsonResponse({'success': False, 'message': 'All card details are required'})
        
        xendit_service = XenditService()
        
        token_data = xendit_service.tokenize_card(
            card_number=card_number,
            card_exp_month=card_exp_month,
            card_exp_year=card_exp_year,
            card_cvn=card_cvn,
            card_holder_name=card_holder_name
        )
        
        if not token_data:
            return JsonResponse({'success': False, 'message': 'Invalid card details'})
        
        charge_data = xendit_service.charge_credit_card(
            external_id=transaction.external_id,
            amount=transaction.amount,
            token_id=token_data.get('id'),
            description=f"Payment for {transaction.package.name}"
        )
        
        if charge_data:
            transaction.payment_method = 'CREDIT_CARD'
            transaction.payment_details = json.dumps({
                'charge_id': charge_data.get('id'),
                'status': charge_data.get('status'),
                'last_four': card_number[-4:] if len(card_number) >= 4 else '****'
            })
            
            if charge_data.get('status') in ['CAPTURED', 'COMPLETED']:
                transaction.status = 'PAID'
                transaction.paid_at = timezone.now()
                
                user_access, created = UserAccess.objects.update_or_create(
                    session_key=transaction.session_key,
                    defaults={
                        'package': transaction.package,
                        'transaction': transaction,
                        'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                        'is_active': True
                    }
                )
                
                transaction.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful!',
                    'redirect_url': reverse('paid_content')
                })
            else:
                transaction.save()
                return JsonResponse({
                    'success': False,
                    'message': f'Payment failed: {charge_data.get("failure_reason", "Unknown error")}'
                })
        else:
            return JsonResponse({'success': False, 'message': 'Payment processing failed'})
            
    except Transaction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Transaction not found'})
    except Exception as e:
        logger.error(f"Error processing credit card payment: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred during payment processing'})

@csrf_exempt
@require_http_methods(["POST"])
def simulate_qr_payment(request, transaction_id):
    if not (settings.DEBUG or getattr(settings, 'ENABLE_TEST_ENDPOINTS', False)):
        return JsonResponse({
            'success': False,
            'message': 'This endpoint is only available in test mode'
        }, status=403)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if not transaction.xendit_qr_id:
            return JsonResponse({
                'success': False,
                'message': 'No QR code found for this transaction. Please generate a QR code first.'
            })
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True,
                'message': 'Transaction already paid',
                'redirect_url': reverse('paid_content')
            })
        
        xendit_service = XenditService()
        simulation_result = xendit_service.simulate_qr_payment(
            qr_id=transaction.xendit_qr_id,
            amount=transaction.amount
        )
        
        if simulation_result and simulation_result.get('status') == 'SUCCEEDED':
            transaction.status = 'PAID'
            transaction.paid_at = timezone.now()
            transaction.payment_method = 'QRIS_SIMULATED'
            transaction.xendit_payment_id = simulation_result.get('id')
            transaction.save()
            
            user_access, created = UserAccess.objects.update_or_create(
                session_key=transaction.session_key,
                defaults={
                    'package': transaction.package,
                    'transaction': transaction,
                    'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                    'is_active': True
                }
            )
            
            logger.info(f"✅ QR Payment simulation successful for {transaction.external_id}")
            logger.info(f"   Payment ID: {simulation_result.get('id')}")
            logger.info(f"   Source: {simulation_result.get('payment_detail', {}).get('source', 'SIMULATION')}")
            
            return JsonResponse({
                'success': True,
                'message': 'QRIS payment simulation successful!',
                'payment_id': simulation_result.get('id'),
                'redirect_url': reverse('paid_content')
            })
        else:
            error_msg = 'Payment simulation failed'
            if simulation_result:
                error_msg += f" (Status: {simulation_result.get('status', 'Unknown')})"
            else:
                error_msg += " - No response from Xendit simulation API"
            
            logger.error(f"❌ {error_msg} for transaction {transaction_id}")
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
            
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Transaction not found'
        })
    except Exception as e:
        logger.error(f"Error simulating QR payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Simulation error occurred'
        })

@csrf_exempt
@require_http_methods(["POST"])
def simulate_payment(request, transaction_id):
    if not (settings.DEBUG or getattr(settings, 'XENDIT_TEST_MODE', False)):
        return JsonResponse({
            'success': False,
            'message': 'This endpoint is only available in Xendit Sandbox/test mode'
        }, status=403)
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        if transaction.status == 'PAID':
            return JsonResponse({
                'success': True,
                'message': 'Transaction already completed',
                'redirect_url': reverse('paid_content')
            })
        
        transaction.status = 'PAID'
        transaction.paid_at = timezone.now()
        transaction.payment_method = 'XENDIT_SIMULATION'
        transaction.xendit_payment_id = f'sim_{uuid.uuid4().hex[:16]}'
        
        transaction.xendit_callback_data = {
            'event': 'payment.simulation',
            'api_version': '2022-07-31',
            'data': {
                'id': transaction.xendit_payment_id,
                'status': 'SUCCEEDED',
                'amount': float(transaction.amount),
                'currency': 'IDR',
                'created': timezone.now().isoformat(),
                'payment_method': 'SIMULATION',
                'reference_id': transaction.external_id,
                'description': f'Simulated payment for {transaction.package.name}',
                'simulation_mode': True
            }
        }
        
        transaction.save()
        
        user_access, created = UserAccess.objects.update_or_create(
            session_key=transaction.session_key,
            defaults={
                'package': transaction.package,
                'transaction': transaction,
                'expires_at': timezone.now() + timezone.timedelta(days=transaction.package.duration_days),
                'is_active': True
            }
        )
        
        logger.info(f"✅ Universal Payment Simulation successful for {transaction.external_id}")
        logger.info(f"   Amount: Rp. {transaction.amount}")
        logger.info(f"   Package: {transaction.package.name}")
        logger.info(f"   Payment ID: {transaction.xendit_payment_id}")
        logger.info(f"   Access granted until: {user_access.expires_at}")
        logger.info(f"   Session: {transaction.session_key}")
        
        return JsonResponse({
            'success': True,
            'message': 'Payment simulation successful using Xendit Sandbox!',
            'payment_id': transaction.xendit_payment_id,
            'amount': float(transaction.amount),
            'package_name': transaction.package.name,
            'access_expires': user_access.expires_at.isoformat(),
            'redirect_url': reverse('paid_content')
        })
        
    except Transaction.DoesNotExist:
        logger.error(f"❌ Transaction {transaction_id} not found for simulation")
        return JsonResponse({
            'success': False,
            'message': 'Transaction not found'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Error simulating payment for {transaction_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Payment simulation error occurred'
        }, status=500)
