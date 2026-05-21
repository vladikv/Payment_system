from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Wallet, Transaction


def deposit(wallet: Wallet, amount: Decimal, description: str = '') -> Transaction:
    """Deposit to wallet."""
    if amount <= 0:
        raise ValidationError('Amount must be greater than zero.')

    with transaction.atomic():
        wallet.balance += amount
        wallet.save(update_fields=['balance', 'updated_at'])

        tx = Transaction.objects.create(
            wallet=wallet,
            transaction_type='deposit',
            amount=amount,
            status='completed',
            description=description or f'Deposit of {amount} {wallet.currency}',
        )
    return tx


def withdraw(wallet: Wallet, amount: Decimal, description: str = '') -> Transaction:
    """Withdraw funds."""
    if amount <= 0:
        raise ValidationError('Amount must be greater than zero.')
    if not wallet.can_withdraw(amount):
        raise ValidationError('Insufficient funds.')

    with transaction.atomic():
        wallet.balance -= amount
        wallet.save(update_fields=['balance', 'updated_at'])

        tx = Transaction.objects.create(
            wallet=wallet,
            transaction_type='withdrawal',
            amount=amount,
            status='completed',
            description=description or f'Withdrawal of {amount} {wallet.currency}',
        )
    return tx


def transfer(sender_wallet: Wallet, receiver_wallet: Wallet, amount: Decimal, description: str = '') -> tuple:
    """Transfer between wallets. Returns (tx_out, tx_in)."""
    if amount <= 0:
        raise ValidationError('Amount must be greater than zero.')
    if sender_wallet == receiver_wallet:
        raise ValidationError('Cannot transfer funds to yourself.')
    if not sender_wallet.can_withdraw(amount):
        raise ValidationError('Insufficient funds.')

    receiver_name = receiver_wallet.user.get_full_name() or receiver_wallet.user.username
    sender_name = sender_wallet.user.get_full_name() or sender_wallet.user.username

    with transaction.atomic():
        sender_wallet.balance -= amount
        sender_wallet.save(update_fields=['balance', 'updated_at'])

        receiver_wallet.balance += amount
        receiver_wallet.save(update_fields=['balance', 'updated_at'])

        tx_out = Transaction.objects.create(
            wallet=sender_wallet,
            related_wallet=receiver_wallet,
            transaction_type='transfer_out',
            amount=amount,
            status='completed',
            description=description or f'Transfer to {receiver_name}',
        )

        tx_in = Transaction.objects.create(
            wallet=receiver_wallet,
            related_wallet=sender_wallet,
            transaction_type='transfer_in',
            amount=amount,
            status='completed',
            description=description or f'Transfer from {sender_name}',
        )

    return tx_out, tx_in
