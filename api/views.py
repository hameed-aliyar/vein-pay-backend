# api/views.py

from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .face_utils import compare_faces
from django.shortcuts import get_object_or_404
from .models import Wallet, Transaction, BiometricData, Bill, User
from .permissions import IsShopOwner
from .serializers import (
    WalletSerializer, TransactionSerializer, AddMoneySerializer,
    CustomerRegistrationSerializer, BillCreationSerializer,
    PaymentSerializer # ADD THIS LINE
)

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

class CustomerListCreateView(generics.ListCreateAPIView):
    """
    An endpoint for the Shop Owner to LIST all their customers (GET)
    or CREATE a new customer (POST).
    """
    queryset = User.objects.filter(role='CUSTOMER')
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [IsShopOwner]

    def perform_create(self, serializer):
        # This is the same logic from before, it hasn't changed.
        biometric_type = serializer.validated_data.pop('biometric_type')
        face_template = serializer.validated_data.pop('face_template')

        with transaction.atomic():
            user = serializer.save(role='CUSTOMER')
            user.set_password(serializer.validated_data['password'])
            user.save()
            Wallet.objects.create(owner=user)
            BiometricData.objects.create(
                owner=user,
                biometric_type=biometric_type,
                face_template=face_template
            )

# Replace the old BillCreateView with this new BillListCreateView


class BillListCreateView(generics.ListCreateAPIView):
    """
    An endpoint for the Shop Owner to LIST all bills (GET)
    or CREATE a new bill for a customer (POST).
    """

    queryset = Bill.objects.all().order_by(
        "-created_at"
    )  # Add this line to fetch all bills
    serializer_class = BillCreationSerializer
    permission_classes = [IsShopOwner]

    def perform_create(self, serializer):
        # This method stays exactly the same as before
        serializer.save(initiating_shop=self.request.user)


# Add this new view at the end of the file
class PaymentView(generics.GenericAPIView):
    """
    The main endpoint for processing a payment.
    Receives a bill_id and a live_image for biometric verification.
    """
    serializer_class = PaymentSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Only the shop owner can trigger a payment

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bill_id = serializer.validated_data['bill_id']
        live_image = serializer.validated_data['live_image']

        # Get the objects from the database
        bill = get_object_or_404(Bill, id=bill_id, status='PENDING')
        customer = bill.customer
        shop = bill.initiating_shop

        # --- Authentication Hub ---
        is_authenticated = False
        try:
            biometric_data = customer.biometric_data
            if biometric_data.biometric_type == 'FACE':
                live_image.seek(0)
                # Call our face comparison logic
                is_authenticated = compare_faces(
                    stored_template_path=biometric_data.face_template.path,
                    live_image_data=live_image
                )
            elif biometric_data.biometric_type == 'VEIN':
                # This is the stub for the future. It will always fail for now.
                is_authenticated = False
                print("Vein authentication is not yet implemented.")

        except BiometricData.DoesNotExist:
            return Response({"error": "Customer has no registered biometric data."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Process Payment if Authenticated ---
        if is_authenticated:
            customer_wallet = customer.wallet
            shop_wallet = shop.wallet
            amount = bill.amount

            if customer_wallet.balance < amount:
                return Response({"error": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

            # Use an atomic transaction for the money transfer
            with transaction.atomic():
                customer_wallet.balance -= amount
                shop_wallet.balance += amount
                bill.status = 'PAID_WALLET'

                # Create a transaction record
                Transaction.objects.create(
                    bill=bill,
                    source_wallet=customer_wallet,
                    destination_wallet=shop_wallet,
                    amount=amount
                )

                customer_wallet.save()
                shop_wallet.save()
                bill.save()

            return Response({"success": f"Payment of {amount} for Bill #{bill.id} successful."}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Biometric authentication failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

class BillPayCashView(generics.UpdateAPIView):
    """
    An endpoint for the Shop Owner to mark a bill as paid in cash.
    """
    queryset = Bill.objects.all()
    permission_classes = [IsShopOwner]

    def update(self, request, *args, **kwargs):
        bill = self.get_object()
        if bill.status != 'PENDING':
            return Response({"error": "This bill is not pending."}, status=status.HTTP_400_BAD_REQUEST)
        
        bill.status = 'PAID_CASH'
        bill.save()
        return Response({"success": f"Bill #{bill.id} has been marked as PAID_CASH."}, status=status.HTTP_200_OK)
