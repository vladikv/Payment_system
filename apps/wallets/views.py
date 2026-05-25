from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Transaction
from .forms import DepositForm, WithdrawForm, TransferForm
from . import services
from .currency import convert_amount
import qrcode
import io
from django.http import HttpResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import json

@login_required
def dashboard(request):
    wallet = request.user.wallet
    recent_transactions = wallet.transactions.select_related('related_wallet__user')[:10]

    # Currency conversion
    convert_to = request.GET.get('convert_to', '')
    converted_balance = None
    if convert_to and convert_to != wallet.currency:
        from .currency import convert_amount
        converted_balance = {
            'amount': convert_amount(wallet.balance, wallet.currency, convert_to),
            'currency': convert_to,
        }

    # Chart data — last 6 months
    from django.utils import timezone
    six_months_ago = timezone.now() - timezone.timedelta(days=180)

    income_by_month = wallet.transactions.filter(
        transaction_type__in=['deposit', 'transfer_in'],
        status='completed',
        created_at__gte=six_months_ago,
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    expense_by_month = wallet.transactions.filter(
        transaction_type__in=['withdrawal', 'transfer_out'],
        status='completed',
        created_at__gte=six_months_ago,
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    chart_labels = sorted(set(
        [item['month'].strftime('%b %Y') for item in income_by_month] +
        [item['month'].strftime('%b %Y') for item in expense_by_month]
    ))

    income_data = {item['month'].strftime('%b %Y'): float(item['total']) for item in income_by_month}
    expense_data = {item['month'].strftime('%b %Y'): float(item['total']) for item in expense_by_month}

    context = {
        'wallet': wallet,
        'transactions': recent_transactions,
        'converted_balance': converted_balance,
        'currencies': ['USD', 'EUR', 'UAH'],
        'convert_to': convert_to,
        'chart_labels': json.dumps(chart_labels),
        'chart_income': json.dumps([income_data.get(l, 0) for l in chart_labels]),
        'chart_expense': json.dumps([expense_data.get(l, 0) for l in chart_labels]),
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

@login_required
def qr_code(request):
    """Generate QR code for receiving transfers."""
    username = request.user.username
    transfer_url = request.build_absolute_uri(f'/wallet/transfer/?to={username}')

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(transfer_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    # Return as PNG image
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')