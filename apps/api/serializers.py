from rest_framework import serializers
from django.contrib.auth.models import User
from apps.wallets.models import Wallet, Transaction


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class WalletSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.ReadOnlyField()
    owner = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'owner', 'balance', 'currency', 'currency_symbol', 'is_active', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    related_user = serializers.SerializerMethodField()
    is_income = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'status', 'status_display',
            'description', 'related_user', 'is_income', 'created_at'
        ]

    def get_related_user(self, obj):
        if obj.related_wallet:
            return obj.related_wallet.user.username
        return None


class TransferSerializer(serializers.Serializer):
    recipient_username = serializers.CharField(max_length=150)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_recipient_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f'User "{value}" not found.')
        return value


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1.00)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)