from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='wallet_dashboard'),
    path('deposit/', views.deposit_view, name='wallet_deposit'),
    path('withdraw/', views.withdraw_view, name='wallet_withdraw'),
    path('transfer/', views.transfer_view, name='wallet_transfer'),
    path('history/', views.history_view, name='wallet_history'),
    path('qr/', views.qr_code, name='wallet_qr'),
]
