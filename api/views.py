# api/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer, AddMoneySerializer

class WalletDetailView(generics.RetrieveAPIView):
    """
    An endpoint for the logged-in user to see their own wallet details.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # We override this method to ensure a user only ever gets their own wallet.
        return self.request.user.wallet

class AddMoneyView(generics.GenericAPIView):
    """
    An endpoint for the logged-in user to add money to their wallet.
    """
    serializer_class = AddMoneySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']

        wallet = request.user.wallet
        wallet.balance += amount
        wallet.save()

        # Return the updated wallet details
        updated_wallet_serializer = WalletSerializer(wallet)
        return Response(updated_wallet_serializer.data, status=status.HTTP_200_OK)

class TransactionHistoryView(generics.ListAPIView):
    """
    An endpoint for the user to see their transaction history (both sent and received).
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # We override this to filter transactions for the current user's wallet.
        user_wallet = self.request.user.wallet
        # The Q object allows for complex queries, in this case: OR
        from django.db.models import Q
        return Transaction.objects.filter(
            Q(source_wallet=user_wallet) | Q(destination_wallet=user_wallet)
        ).order_by('-timestamp')