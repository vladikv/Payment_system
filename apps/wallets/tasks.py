from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_deposit_email(user_email, amount, currency_symbol, balance):
    send_mail(
        subject='Wallet topped up',
        message=f'Your wallet has been topped up by {currency_symbol}{amount}.\nCurrent balance: {currency_symbol}{balance}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )


@shared_task
def send_transfer_sent_email(user_email, amount, currency_symbol, recipient_username):
    send_mail(
        subject='Transfer sent',
        message=f'You sent {currency_symbol}{amount} to {recipient_username}.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )


@shared_task
def send_transfer_received_email(user_email, amount, currency_symbol, sender_username):
    send_mail(
        subject='Transfer received',
        message=f'You received {currency_symbol}{amount} from {sender_username}.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )


@shared_task
def send_withdrawal_email(user_email, amount, currency_symbol, balance):
    send_mail(
        subject='Withdrawal successful',
        message=f'You withdrew {currency_symbol}{amount}.\nCurrent balance: {currency_symbol}{balance}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )