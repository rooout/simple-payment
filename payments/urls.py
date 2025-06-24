from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buy/<int:package_id>/', views.buy_package, name='buy_package'),
    path('callback/xendit/', views.xendit_callback, name='xendit_callback'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('paid-content/', views.paid_content, name='paid_content'),
    path('check-payment/<uuid:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('check-access/', views.check_user_access, name='check_user_access'),
    path('verify-payment/<uuid:transaction_id>/', views.verify_payment, name='verify_payment'),
    path('simulate-payment/<uuid:transaction_id>/', views.simulate_payment_success, name='simulate_payment'),
]
