from django.contrib import admin
from .models import Wallet, Transaction, TransactionLimit

class TransactionInline(admin.TabularInline):
    fk_name = 'wallet'
    model = Transaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'status', 'description', 'created_at')
    can_delete = False
    max_num = 20
    ordering = ('-created_at',)


class LimitsInline(admin.StackedInline):
    model = TransactionLimit
    can_delete = False
    verbose_name = 'Transaction Limits'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency', 'is_active', 'created_at')
    list_filter = ('currency', 'is_active')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (LimitsInline, TransactionInline)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('wallet__user__username', 'description', 'stripe_payment_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(TransactionLimit)
class TransactionLimitAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'max_single_transfer', 'max_single_withdrawal', 'max_daily_withdrawal')
    search_fields = ('wallet__user__username',)