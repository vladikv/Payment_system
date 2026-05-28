# PayFlow 💳

A full-stack payment system built with Django — from database architecture to containerized deployment with real card payments, background notifications, and a REST API.
---

## Features

- 💳 **Stripe card deposits** — Stripe Elements + PaymentIntent API with webhook confirmation; no card data stored on server
- 🔄 **Wallet transfers** — atomic PostgreSQL transactions prevent money loss on server failure
- 📊 **Transaction limits** — configurable per-wallet daily and single operation limits via admin panel
- 🔒 **Fraud protection** — automatic wallet freezing on suspicious activity (10+ transactions in 10 minutes)
- 📧 **Background notifications** — Celery + Redis queue for async email on every deposit, transfer, and withdrawal
- 🌐 **REST API** — full API with token authentication and interactive Swagger documentation
- 💱 **Currency conversion** — real-time exchange rates via ExchangeRate API, cached in Redis for 1 hour
- 📈 **Charts** — income/expense bar charts with Chart.js on dashboard
- 📱 **QR codes** — generate QR code for receiving transfers
- 🛡️ **Admin panel** — manage wallets, transactions, limits, freeze/unfreeze accounts
- 🐳 **Docker** — one command to run everything

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 5 |
| Database | PostgreSQL 17 |
| Queue | Celery + Redis |
| Payments | Stripe API |
| API | Django REST Framework + drf-spectacular |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Auth | Token authentication (DRF) |
| DevOps | Docker + docker-compose |
| Tests | pytest + factory-boy |
| Email | Gmail SMTP via django.core.mail |

---

## Quick Start

### With Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/payflow
cd payflow

# 2. Set up environment variables
cp .env.example .env
# Open .env and fill in your Stripe and database credentials

# 3. Run everything with one command
docker compose up --build

# 4. Apply migrations
docker compose exec web python manage.py migrate

# 5. Create superuser
docker compose exec web python manage.py createsuperuser
```

Open http://localhost:8000

### Without Docker (local development)

```bash
# 1. Clone and create virtual environment
git clone https://github.com/yourusername/payflow
cd payflow
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Open .env and fill in your credentials

# 4. Apply migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start Redis (required for Celery)
redis-server

# 7. Start Celery worker (in separate terminal)
celery -A payment_system worker --loglevel=info --pool=solo

# 8. Run development server
python manage.py runserver
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
DB_NAME=payflow_db
DB_USER=payflow_user
DB_PASSWORD=yourpassword
DB_HOST=localhost       # use 'db' when running with Docker
DB_PORT=5432            # use 5433 if PostgreSQL runs on non-standard port

# Redis + Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Stripe (get from https://dashboard.stripe.com/apikeys)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Gmail SMTP (use App Password, not your regular password)
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# ExchangeRate API (get from https://exchangerate-api.com)
EXCHANGE_RATE_API_KEY=your-api-key
```

---

## API Documentation

Interactive Swagger UI is available at `/api/docs/` after starting the server.

### Endpoints

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| POST | `/api/auth/register/` | Register new user | ❌ |
| POST | `/api/auth/login/` | Login, returns token | ❌ |
| POST | `/api/auth/logout/` | Logout, deletes token | ✅ |
| GET | `/api/wallet/` | Get wallet balance | ✅ |
| GET | `/api/transactions/` | Transaction history | ✅ |
| POST | `/api/transfer/` | Transfer to another user | ✅ |
| POST | `/api/withdraw/` | Withdraw funds | ✅ |
| GET | `/api/profile/` | Get user profile | ✅ |

### Authentication

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

# Response
{"token": "abc123...", "user": {...}}

# Use token in requests
curl http://localhost:8000/api/wallet/ \
  -H "Authorization: Token abc123..."
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_services.py::TestTransfer -v

# Run with coverage
pytest tests/ --cov=apps --cov-report=term-missing
```

Tests cover:
- Deposit / withdraw / transfer business logic
- Insufficient funds validation
- Transaction limit enforcement
- Frozen wallet protection

---

## Stripe Testing

Use these test card details (no real money charged):

| Field | Value |
|-------|-------|
| Card number | `4242 4242 4242 4242` |
| Expiry | Any future date (e.g. `12/28`) |
| CVC | Any 3 digits (e.g. `123`) |
| ZIP | Any 5 digits (e.g. `12345`) |

For webhook testing locally, use [Stripe CLI](https://stripe.com/docs/stripe-cli):
```bash
stripe listen --forward-to localhost:8000/payments/webhook/
```

---

## License

MIT
