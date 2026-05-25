import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from .factories import make_wallet, make_wallet_with_limits
from apps.wallets import services
from apps.wallets.models import Transaction


@pytest.mark.django_db
class TestDeposit:
    def test_deposit_increases_balance(self):
        wallet = make_wallet(balance=Decimal('100.00'))
        services.deposit(wallet, Decimal('50.00'))
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('150.00')

    def test_deposit_creates_transaction(self):
        wallet = make_wallet()
        services.deposit(wallet, Decimal('100.00'))
        assert Transaction.objects.filter(
            wallet=wallet,
            transaction_type='deposit',
            status='completed'
        ).exists()

    def test_deposit_zero_raises_error(self):
        wallet = make_wallet()
        with pytest.raises(ValidationError):
            services.deposit(wallet, Decimal('0.00'))

    def test_deposit_negative_raises_error(self):
        wallet = make_wallet()
        with pytest.raises(ValidationError):
            services.deposit(wallet, Decimal('-10.00'))


@pytest.mark.django_db
class TestWithdraw:
    def test_withdraw_decreases_balance(self):
        wallet = make_wallet(balance=Decimal('500.00'))
        services.withdraw(wallet, Decimal('200.00'))
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('300.00')

    def test_withdraw_insufficient_funds(self):
        wallet = make_wallet(balance=Decimal('50.00'))
        with pytest.raises(ValidationError):
            services.withdraw(wallet, Decimal('100.00'))

    def test_withdraw_frozen_wallet(self):
        wallet = make_wallet(balance=Decimal('500.00'), is_frozen=True)
        with pytest.raises(ValidationError):
            services.withdraw(wallet, Decimal('100.00'))

    def test_withdraw_exceeds_single_limit(self):
        wallet = make_wallet_with_limits(
            balance=Decimal('1000.00'),
            max_single_withdrawal=Decimal('200.00')
        )
        with pytest.raises(ValidationError):
            services.withdraw(wallet, Decimal('300.00'))


@pytest.mark.django_db
class TestTransfer:
    def test_transfer_moves_funds(self):
        sender = make_wallet(balance=Decimal('500.00'))
        receiver = make_wallet(balance=Decimal('0.00'))
        services.transfer(sender, receiver, Decimal('200.00'))
        sender.refresh_from_db()
        receiver.refresh_from_db()
        assert sender.balance == Decimal('300.00')
        assert receiver.balance == Decimal('200.00')

    def test_transfer_creates_two_transactions(self):
        sender = make_wallet(balance=Decimal('500.00'))
        receiver = make_wallet(balance=Decimal('0.00'))
        services.transfer(sender, receiver, Decimal('100.00'))
        assert Transaction.objects.filter(
            wallet=sender,
            transaction_type='transfer_out'
        ).exists()
        assert Transaction.objects.filter(
            wallet=receiver,
            transaction_type='transfer_in'
        ).exists()

    def test_transfer_insufficient_funds(self):
        sender = make_wallet(balance=Decimal('50.00'))
        receiver = make_wallet(balance=Decimal('0.00'))
        with pytest.raises(ValidationError):
            services.transfer(sender, receiver, Decimal('100.00'))

    def test_transfer_to_self_raises_error(self):
        wallet = make_wallet(balance=Decimal('500.00'))
        with pytest.raises(ValidationError):
            services.transfer(wallet, wallet, Decimal('100.00'))

    def test_transfer_frozen_wallet(self):
        sender = make_wallet(balance=Decimal('500.00'), is_frozen=True)
        receiver = make_wallet(balance=Decimal('0.00'))
        with pytest.raises(ValidationError):
            services.transfer(sender, receiver, Decimal('100.00'))

    def test_transfer_exceeds_limit(self):
        sender = make_wallet_with_limits(
            balance=Decimal('1000.00'),
            max_single_transfer=Decimal('200.00')
        )
        receiver = make_wallet(balance=Decimal('0.00'))
        with pytest.raises(ValidationError):
            services.transfer(sender, receiver, Decimal('300.00'))