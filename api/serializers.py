# api/serializers.py

import decimal
from rest_framework import serializers
from .models import Wallet, Transaction, User, Bill, BiometricData

class WalletSerializer(serializers.ModelSerializer):
    # We add this to show the username instead of just the user's ID.
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'owner_username', 'balance', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__' # For now, we'll show all fields.

class AddMoneySerializer(serializers.Serializer):
    # This serializer is not based on a model. It's for validating the input
    # when the user wants to add money.
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=decimal.Decimal('0.01'))

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    # We add these fields to handle the biometric data upload
    biometric_type = serializers.ChoiceField(choices=BiometricData.BIOMETRIC_CHOICES, write_only=True)
    face_template = serializers.ImageField(write_only=True)

    class Meta:
        model = User
        # We define the fields the shop owner needs to provide
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'biometric_type', 'face_template']
        extra_kwargs = {
            'password': {'write_only': True} # Ensures password isn't sent back in the response
        }

class BillCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['customer', 'amount']

# Add this new serializer at the end of the file
class PaymentSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField()
    live_image = serializers.ImageField()