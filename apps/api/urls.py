from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='api_register'),
    path('auth/login/',    views.login,    name='api_login'),
    path('auth/logout/',   views.logout,   name='api_logout'),

    # Wallet
    path('wallet/',        views.wallet_detail,    name='api_wallet'),
    path('card/',           views.card_detail,      name='api_card'),

    # Transactions
    path('transactions/',  views.transaction_list, name='api_transactions'),

    # Actions
    path('transfer/',      views.transfer, name='api_transfer'),
    path('transfer/card/',  views.transfer_by_card, name='api_transfer_by_card'),
    path('withdraw/',      views.withdraw, name='api_withdraw'),

    # Profile
    path('profile/',       views.profile,  name='api_profile'),
]