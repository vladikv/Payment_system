"""
apps/payments/ — Stripe integration

Installation:
    pip install stripe

In settings.py add:
    STRIPE_PUBLIC_KEY = 'pk_test_...'
    STRIPE_SECRET_KEY = 'sk_test_...'
    STRIPE_WEBHOOK_SECRET = 'whsec_...'

In payment_system/urls.py add:
    path('payments/', include('apps.payments.urls')),
"""
