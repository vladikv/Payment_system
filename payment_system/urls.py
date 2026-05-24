from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('wallet/', include('apps.wallets.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.api.urls')),

     # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('', RedirectView.as_view(pattern_name='wallet_dashboard'), name='home'),
]
