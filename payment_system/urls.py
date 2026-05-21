from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('wallet/', include('apps.wallets.urls')),
    path('payments/', include('apps.payments.urls')),
    path('', RedirectView.as_view(pattern_name='wallet_dashboard'), name='home'),
]
