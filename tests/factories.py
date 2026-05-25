import factory
from django.contrib.auth.models import User
from apps.wallets.models import Wallet, TransactionLimit
from decimal import Decimal


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


def make_wallet(balance=Decimal('1000.00'), currency='USD', is_frozen=False):
    """Create user and return their auto-created wallet with custom balance."""
    user = UserFactory()
    wallet = user.wallet
    wallet.balance = balance
    wallet.currency = currency
    wallet.is_frozen = is_frozen
    wallet.save()
    return wallet


def make_wallet_with_limits(balance=Decimal('1000.00'), max_single_transfer=Decimal('500.00'),
                             max_single_withdrawal=Decimal('300.00'), max_daily_withdrawal=Decimal('1000.00')):
    """Create wallet with transaction limits."""
    wallet = make_wallet(balance=balance)
    TransactionLimit.objects.filter(wallet=wallet).update(
        max_single_transfer=max_single_transfer,
        max_single_withdrawal=max_single_withdrawal,
        max_daily_withdrawal=max_daily_withdrawal,
    )
    wallet.refresh_from_db()
    return wallet