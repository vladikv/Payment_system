from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.wallets import services
from .serializers import (
    RegisterSerializer, UserSerializer,
    WalletSerializer, TransactionSerializer,
    TransferSerializer, WithdrawSerializer,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and return auth token.

    POST /api/auth/register/
    {
        "username": "john",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "secret123",
        "password2": "secret123"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login and return auth token.

    POST /api/auth/login/
    { "username": "john", "password": "secret123" }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout — delete auth token.

    POST /api/auth/logout/
    Authorization: Token <token>
    """
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully.'})


# ── Wallet ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_detail(request):
    """
    Get current user's wallet info.

    GET /api/wallet/
    Authorization: Token <token>
    """
    wallet = request.user.wallet
    return Response(WalletSerializer(wallet).data)


# ── Transactions ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_list(request):
    """
    Get transaction history with optional filters.

    GET /api/transactions/
    GET /api/transactions/?type=deposit
    GET /api/transactions/?type=transfer_in&limit=5
    Authorization: Token <token>
    """
    wallet = request.user.wallet
    transactions = wallet.transactions.select_related('related_wallet__user').all()

    # Filter by type
    tx_type = request.query_params.get('type')
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)

    # Limit results
    limit = request.query_params.get('limit')
    if limit:
        try:
            transactions = transactions[:int(limit)]
        except ValueError:
            pass

    serializer = TransactionSerializer(transactions, many=True)
    return Response({
        'count': transactions.count() if not limit else len(serializer.data),
        'results': serializer.data,
    })


# ── Transfer ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer(request):
    """
    Transfer funds to another user.

    POST /api/transfer/
    Authorization: Token <token>
    {
        "recipient_username": "bob",
        "amount": "100.00",
        "description": "For services"
    }
    """
    serializer = TransferSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    recipient = User.objects.get(username=serializer.validated_data['recipient_username'])

    if recipient == request.user:
        return Response(
            {'error': 'You cannot transfer to yourself.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        tx_out, tx_in = services.transfer(
            sender_wallet=request.user.wallet,
            receiver_wallet=recipient.wallet,
            amount=serializer.validated_data['amount'],
            description=serializer.validated_data.get('description', ''),
        )
        return Response({
            'message': f"Successfully transferred {tx_out.amount} to {recipient.username}.",
            'transaction': TransactionSerializer(tx_out).data,
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)


# ── Withdraw ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw(request):
    """
    Withdraw funds from wallet.

    POST /api/withdraw/
    Authorization: Token <token>
    { "amount": "50.00", "description": "Withdrawal to card" }
    """
    serializer = WithdrawSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        tx = services.withdraw(
            wallet=request.user.wallet,
            amount=serializer.validated_data['amount'],
            description=serializer.validated_data.get('description', ''),
        )
        return Response({
            'message': f"Successfully withdrawn {tx.amount}.",
            'transaction': TransactionSerializer(tx).data,
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile.

    GET /api/profile/
    Authorization: Token <token>
    """
    return Response(UserSerializer(request.user).data)