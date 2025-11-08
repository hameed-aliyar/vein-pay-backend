# api/serializers.py

import decimal
from rest_framework import serializers
from .models import Wallet, Transaction, User, Bill, BiometricData
from .face_utils import process_and_validate_face_for_registration  # <--- NEW IMPORT
from rest_framework.exceptions import ValidationError  # <--- NEW IMPORT
from .face_utils import (
    process_and_validate_face_for_registration,
    compare_faces,
    validate_face_present,
)

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
    biometric_type = serializers.ChoiceField(
        choices=BiometricData.BIOMETRIC_CHOICES, write_only=True
    )
    face_template = serializers.ImageField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "biometric_type",
            "face_template",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_face_template(self, value):
        """
        Uses face_utils to detect, crop, resize the image, and return a ContentFile
        to be saved in the model.
        """
        try:
            # Process the uploaded file (value is the uploaded file object)
            processed_file = process_and_validate_face_for_registration(value)
            return processed_file
        except ValueError as e:
            # Catch the error from face_utils and raise a standard DRF validation error
            raise ValidationError(str(e))


class BillCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['id', 'customer', 'amount', 'status']

# Add this new serializer at the end of the file
class PaymentSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField()
    live_image = serializers.ImageField()

    def validate_live_image(self, value):
        try:
            validate_face_present(value)
            return value
        except ValueError as e:
            # This turns the ValueError from face_utils into a DRF 400 response
            raise ValidationError(str(e))
