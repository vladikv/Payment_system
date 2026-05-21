from django import forms
from django.contrib.auth.models import User
from decimal import Decimal


class DepositForm(forms.Form):
    amount = forms.DecimalField(
        label='Deposit Amount',
        min_value=Decimal('1.00'),
        max_value=Decimal('100000.00'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': '100.00', 'step': '0.01'})
    )
    description = forms.CharField(
        label='Comment (optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Deposit from card'})
    )


class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        label='Withdrawal Amount',
        min_value=Decimal('1.00'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': '100.00', 'step': '0.01'})
    )
    description = forms.CharField(
        label='Comment (optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Withdraw to card'})
    )


class TransferForm(forms.Form):
    recipient_username = forms.CharField(
        label='Recipient Username',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'john_smith'})
    )
    amount = forms.DecimalField(
        label='Transfer Amount',
        min_value=Decimal('0.01'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': '100.00', 'step': '0.01'})
    )
    description = forms.CharField(
        label='Purpose (optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'For services'})
    )

    def clean_recipient_username(self):
        username = self.cleaned_data['recipient_username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f'User "{username}" not found.')
        return username
