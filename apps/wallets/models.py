from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import random
from django.contrib.auth.hashers import make_password, check_password


class Wallet(models.Model):
    CURRENCY_CHOICES = [
        ('UAH', '₴ Hryvnia'),
        ('USD', '$ Dollar'),
        ('EUR', '€ Euro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    is_active = models.BooleanField(default=True)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Wallet {self.user.username} — {self.balance} {self.currency}'

    @property
    def currency_symbol(self):
        symbols = {'UAH': '₴', 'USD': '$', 'EUR': '€'}
        return symbols.get(self.currency, self.currency)

    def can_withdraw(self, amount):
        return self.balance >= Decimal(str(amount))



class VirtualCard(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, related_name='card')
    number = models.CharField(max_length=16, unique=True)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    cvv_hash = models.CharField(max_length=255)
    cvv = models.CharField(max_length=3, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Card **** {self.number[-4:]} — {self.wallet.user.username}'

    @property
    def expiry_display(self):
        return f'{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}'

    @property
    def masked_number(self):
        return f'**** **** **** {self.number[-4:]}'

    def check_cvv(self, raw_cvv):
        return check_password(str(raw_cvv), self.cvv_hash)


def generate_luhn_number():
    """Generate a valid 16-digit card number using Luhn algorithm."""
    # Start with prefix 4 (Visa-like) + 14 random digits
    prefix = [4]
    digits = prefix + [random.randint(0, 9) for _ in range(14)]

    # Calculate Luhn check digit
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    check = (10 - (total % 10)) % 10
    digits.append(check)

    return ''.join(map(str, digits))


def generate_unique_card_number():
    """Generate unique card number that doesn't exist in DB."""
    while True:
        number = generate_luhn_number()
        if not VirtualCard.objects.filter(number=number).exists():
            return number


def create_virtual_card(wallet):
    """Create virtual card for wallet."""
    from django.utils import timezone
    import random

    now = timezone.now()
    expiry_month = now.month
    expiry_year = now.year + 3

    raw_cvv = str(random.randint(100, 999))

    return VirtualCard.objects.create(
        wallet=wallet,
        number=generate_unique_card_number(),
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvv_hash=make_password(raw_cvv),
        cvv=raw_cvv,
    ), raw_cvv


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer_out', 'Transfer (sent)'),
        ('transfer_in', 'Transfer (received)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    related_wallet = models.ForeignKey(
        Wallet, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='related_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.CharField(max_length=255, blank=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.amount} — {self.wallet.user.username}'

    @property
    def is_income(self):
        return self.transaction_type in ('deposit', 'transfer_in')

class TransactionLimit(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, related_name='limits')
    max_single_transfer = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('1000.00'),
        help_text='Maximum amount per single transfer'
    )
    max_daily_withdrawal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('2000.00'),
        help_text='Maximum total withdrawal per day'
    )
    max_single_withdrawal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('500.00'),
        help_text='Maximum amount per single withdrawal'
    )

    def __str__(self):
        return f'Limits for {self.wallet.user.username}'

    def get_daily_withdrawn(self):
        """Total amount withdrawn today."""
        from django.utils import timezone
        today = timezone.now().date()
        from django.db.models import Sum
        result = self.wallet.transactions.filter(
            transaction_type='withdrawal',
            status='completed',
            created_at__date=today,
        ).aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')