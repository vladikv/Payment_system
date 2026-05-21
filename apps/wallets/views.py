from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Transaction
from .forms import DepositForm, WithdrawForm, TransferForm
from . import services


@login_required
def dashboard(request):
    wallet = request.user.wallet
    recent_transactions = wallet.transactions.select_related('related_wallet__user')[:10]
    context = {
        'wallet': wallet,
        'transactions': recent_transactions,
    }
    return render(request, 'wallets/dashboard.html', context)


@login_required
def deposit_view(request):
    wallet = request.user.wallet

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            try:
                tx = services.deposit(
                    wallet=wallet,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data.get('description', ''),
                )
                messages.success(request, f'✅ Successfully deposited {tx.amount} {wallet.currency_symbol}')
                return redirect('wallet_dashboard')
            except ValidationError as e:
                messages.error(request, str(e.message))
    else:
        form = DepositForm()

    return render(request, 'wallets/deposit.html', {'form': form, 'wallet': wallet})


@login_required
def withdraw_view(request):
    wallet = request.user.wallet

    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            try:
                tx = services.withdraw(
                    wallet=wallet,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data.get('description', ''),
                )
                messages.success(request, f'✅ Withdrawn {tx.amount} {wallet.currency_symbol}')
                return redirect('wallet_dashboard')
            except ValidationError as e:
                messages.error(request, str(e.message))
    else:
        form = WithdrawForm()

    return render(request, 'wallets/withdraw.html', {'form': form, 'wallet': wallet})


@login_required
def transfer_view(request):
    wallet = request.user.wallet

    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                recipient = User.objects.get(username=form.cleaned_data['recipient_username'])
                if recipient == request.user:
                    messages.error(request, 'Cannot transfer funds to yourself.')
                else:
                    tx_out, _ = services.transfer(
                        sender_wallet=wallet,
                        receiver_wallet=recipient.wallet,
                        amount=form.cleaned_data['amount'],
                        description=form.cleaned_data.get('description', ''),
                    )
                    receiver_name = recipient.get_full_name() or recipient.username
                    messages.success(request, f'✅ Transferred {tx_out.amount} {wallet.currency_symbol} → {receiver_name}')
                    return redirect('wallet_dashboard')
            except ValidationError as e:
                messages.error(request, str(e.message))
    else:
        form = TransferForm()

    return render(request, 'wallets/transfer.html', {'form': form, 'wallet': wallet})


@login_required
def history_view(request):
    wallet = request.user.wallet
    transactions = wallet.transactions.select_related('related_wallet__user').all()
    return render(request, 'wallets/history.html', {'wallet': wallet, 'transactions': transactions})
