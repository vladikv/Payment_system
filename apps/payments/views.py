import stripe
import json
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from apps.wallets.models import Wallet, Transaction
from apps.wallets import services

stripe.api_key = settings.STRIPE_SECRET_KEY
print("views.py stripe key:", settings.STRIPE_SECRET_KEY)

# ──────────────────────────────────────────
# 1. Deposit page via Stripe
# ──────────────────────────────────────────

@login_required
def stripe_deposit_page(request):
    """Render the Stripe Elements form page."""
    return render(request, 'payments/stripe_deposit.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'wallet': request.user.wallet,
    })


# ──────────────────────────────────────────
# 2. Create PaymentIntent (AJAX)
# ──────────────────────────────────────────

@login_required
def create_payment_intent(request):
    """
    POST { amount: 150.00 }
    Returns { client_secret: '...' }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))

        if amount < Decimal('1.00'):
            return JsonResponse({'error': 'Minimum amount — 1.00'}, status=400)
        if amount > Decimal('50000.00'):
            return JsonResponse({'error': 'Maximum amount — 50 000'}, status=400)

        wallet = request.user.wallet

        # Stripe accepts amount in smallest units (cents)
        amount_in_cents = int(amount * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='usd',
            metadata={
                'user_id': str(request.user.id),
                'wallet_id': str(wallet.id),
                'amount': str(amount),
            },
            description=f'Wallet top-up #{wallet.id} for {request.user.username}',
        )

        # Save pending transaction
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='deposit',
            amount=amount,
            status='pending',
            stripe_payment_id=intent.id,
            description=f'Top-up via Stripe',
        )

        return JsonResponse({'client_secret': intent.client_secret})

    except stripe.error.StripeError as e:
        print("Stripe error:", e)
        return JsonResponse({'error': str(e.user_message)}, status=400)
    except Exception as e:
        print("General error:", e)
        return JsonResponse({'error': 'Server error'}, status=500)


# ──────────────────────────────────────────
# 3. Successful completion (redirect after payment)
# ──────────────────────────────────────────

@login_required
def payment_success(request):
    payment_intent_id = request.GET.get('payment_intent')

    if payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == 'succeeded':
                tx = Transaction.objects.filter(
                    stripe_payment_id=payment_intent_id,
                    status='pending'
                ).first()

                if tx:
                    wallet = tx.wallet
                    wallet.balance += tx.amount
                    wallet.save(update_fields=['balance', 'updated_at'])
                    tx.status = 'completed'
                    tx.save(update_fields=['status'])
                    messages.success(request, f'✅ Wallet topped up by {wallet.currency_symbol}{tx.amount}')
                else:
                    messages.info(request, 'Payment already processed.')
            else:
                messages.error(request, 'Payment not confirmed.')

        except stripe.error.StripeError:
            messages.error(request, 'Payment verification error.')

    return redirect('wallet_dashboard')


# ──────────────────────────────────────────
# 4. Stripe Webhook — reliable confirmation method
# ──────────────────────────────────────────

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe sends events here after successful payment.
    Configure in Stripe Dashboard → Webhooks:
      URL: https://yourdomain.com/payments/webhook/
      Events: payment_intent.succeeded, payment_intent.payment_failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse('Invalid payload', status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse('Invalid signature', status=400)

    # ── Payment succeeded ──
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        _handle_payment_succeeded(intent)

    # ── Payment failed ──
    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        _handle_payment_failed(intent)

    return HttpResponse(status=200)


def _handle_payment_succeeded(intent):
    """Credit funds to the wallet."""
    tx = Transaction.objects.filter(
        stripe_payment_id=intent['id'],
        status='pending'
    ).first()

    if not tx:
        return  # already processed or not found

    wallet = tx.wallet

    # Atomic balance update
    from django.db import transaction as db_transaction
    with db_transaction.atomic():
        wallet.balance += tx.amount
        wallet.save(update_fields=['balance', 'updated_at'])
        tx.status = 'completed'
        tx.save(update_fields=['status'])


def _handle_payment_failed(intent):
    """Mark transaction as failed."""
    Transaction.objects.filter(
        stripe_payment_id=intent['id'],
        status='pending'
    ).update(status='failed')
