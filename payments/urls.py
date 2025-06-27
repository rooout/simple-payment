from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buy/<int:package_id>/', views.buy_package, name='buy_package'),
    path('payment/methods/<uuid:transaction_id>/', views.payment_methods, name='payment_methods'),
    path('payment/va/<uuid:transaction_id>/', views.process_virtual_account, name='process_va'),
    path('payment/qr/<uuid:transaction_id>/', views.process_qr_payment, name='process_qr'),
    path('payment/card/<uuid:transaction_id>/', views.process_credit_card, name='process_card'),
    path('callback/xendit/', views.xendit_callback, name='xendit_callback'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('paid-content/', views.paid_content, name='paid_content'),
    path('check-payment/<uuid:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('check-access/', views.check_user_access, name='check_user_access'),
    path('verify-payment/<uuid:transaction_id>/', views.verify_payment, name='verify_payment'),
    path('simulate-payment/<uuid:transaction_id>/', views.simulate_payment_success, name='simulate_payment'),
    path('payments/simulate-payment/<uuid:transaction_id>/', views.simulate_payment, name='universal_simulate_payment'),
    path('payment/simulate-qr/<uuid:transaction_id>/', views.simulate_qr_payment, name='simulate_qr_payment'),
]
