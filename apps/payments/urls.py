from django.urls import path
from . import views

urlpatterns = [
    path('deposit/', views.stripe_deposit_page, name='stripe_deposit'),
    path('create-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('success/', views.payment_success, name='payment_success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
