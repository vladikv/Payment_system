from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Wallet, Transaction
from .tasks import (
    send_deposit_email,
    send_transfer_sent_email,
    send_transfer_received_email,
    send_withdrawal_email,
)


def deposit(wallet: Wallet, amount: Decimal, description: str = '') -> Transaction:
    """Credit funds to a wallet."""
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
            description=description or f'Deposit {amount} {wallet.currency}',
        )

    # Send email in background
    if wallet.user.email:
        send_deposit_email.delay(
            user_email=wallet.user.email,
            amount=str(amount),
            currency_symbol=wallet.currency_symbol,
            balance=str(wallet.balance),
        )

    return tx


def withdraw(wallet: Wallet, amount: Decimal, description: str = '') -> Transaction:
    """Debit funds from a wallet."""
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
            description=description or f'Withdrawal {amount} {wallet.currency}',
        )

    # Send email in background
    if wallet.user.email:
        send_withdrawal_email.delay(
            user_email=wallet.user.email,
            amount=str(amount),
            currency_symbol=wallet.currency_symbol,
            balance=str(wallet.balance),
        )

    return tx


def transfer(sender_wallet: Wallet, receiver_wallet: Wallet, amount: Decimal, description: str = '') -> tuple:
    """Transfer funds between two wallets. Returns (tx_out, tx_in)."""
    if amount <= 0:
        raise ValidationError('Amount must be greater than zero.')
    if sender_wallet == receiver_wallet:
        raise ValidationError('Cannot transfer to yourself.')
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

    # Send emails in background
    if sender_wallet.user.email:
        send_transfer_sent_email.delay(
            user_email=sender_wallet.user.email,
            amount=str(amount),
            currency_symbol=sender_wallet.currency_symbol,
            recipient_username=receiver_name,
        )

    if receiver_wallet.user.email:
        send_transfer_received_email.delay(
            user_email=receiver_wallet.user.email,
            amount=str(amount),
            currency_symbol=receiver_wallet.currency_symbol,
            sender_username=sender_name,
        )

    return tx_out, tx_in