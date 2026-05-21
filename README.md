# PayFlow — Django Payment System

## What's implemented

| Module | Features |
|--------|-----------|
| `apps/accounts` | Registration, login, profile, auto wallet creation |
| `apps/wallets` | Wallet, balance, transfers between users, withdrawal, history |
| `apps/payments` | Stripe Elements, PaymentIntent, Webhook, test mode |

## Quick Start

```bash
# 1. Install dependencies
pip install django stripe

# 2. Set Stripe keys in settings.py
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'

# 3. Migrations
python manage.py migrate

# 4. Superuser (optional)
python manage.py createsuperuser

# 5. Run
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Project Structure

```
payment_system/
├── apps/
│   ├── accounts/           # registration + profiles
│   │   ├── models.py       # Profile (OneToOne with User)
│   │   ├── forms.py        # RegisterForm, LoginForm
│   │   ├── views.py        # register, login, logout
│   │   └── admin.py        # Profile inline in User admin
│   │
│   ├── wallets/            # wallets + transactions
│   │   ├── models.py       # Wallet, Transaction
│   │   ├── services.py     # deposit(), withdraw(), transfer()
│   │   ├── forms.py        # DepositForm, WithdrawForm, TransferForm
│   │   ├── views.py        # dashboard, deposit, withdraw, transfer, history
│   │   └── admin.py        # WalletAdmin, TransactionAdmin
│   │
│   └── payments/           # Stripe integration
│       ├── views.py        # stripe_deposit_page, create_payment_intent,
│       │                   # payment_success, stripe_webhook
│       └── templates/      # Stripe Elements form
│
├── templates/
│   └── base.html           # shared template (dark theme)
└── manage.py
```

## Stripe Webhook (production)

```bash
# Local development — Stripe CLI
stripe listen --forward-to localhost:8000/payments/webhook/

# Production — add in Stripe Dashboard:
# URL: https://yourdomain.com/payments/webhook/
# Events: payment_intent.succeeded, payment_intent.payment_failed
```

## Stripe Test Card

| Field | Value |
|-------|-------|
| Number | `4242 4242 4242 4242` |
| Date | Any future date (e.g. 12/28) |
| CVC | Any 3 digits |

## What to add next

- [ ] Email notifications (Celery + Redis)
- [ ] Withdrawal via Stripe Payout
- [ ] Two-factor authentication
- [ ] REST API (Django REST Framework)
- [ ] Currency conversion (Fixer.io API)
- [ ] PDF receipts for transactions
