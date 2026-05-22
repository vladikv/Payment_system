from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='api_register'),
    path('auth/login/',    views.login,    name='api_login'),
    path('auth/logout/',   views.logout,   name='api_logout'),

    # Wallet
    path('wallet/',        views.wallet_detail,    name='api_wallet'),

    # Transactions
    path('transactions/',  views.transaction_list, name='api_transactions'),

    # Actions
    path('transfer/',      views.transfer, name='api_transfer'),
    path('withdraw/',      views.withdraw, name='api_withdraw'),

    # Profile
    path('profile/',       views.profile,  name='api_profile'),
]