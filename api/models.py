# api/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import decimal

# Our custom User model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SHOP_OWNER', 'Shop Owner'),
        ('CUSTOMER', 'Customer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')

# The Wallet model, with a one-to-one link to a user
class Wallet(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner.username}'s Wallet"

# The BiometricData model for storing face templates
class BiometricData(models.Model):
    BIOMETRIC_CHOICES = (
        ('FACE', 'Face'),
        ('VEIN', 'Vein'),
    )
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='biometric_data')
    biometric_type = models.CharField(max_length=4, choices=BIOMETRIC_CHOICES, default='FACE')
    # 'upload_to' organizes uploaded files into subdirectories
    face_template = models.ImageField(upload_to='face_templates/')

    def __str__(self):
        return f"Biometric Data for {self.owner.username}"

# The Bill model, initiated by a shop for a customer
class Bill(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID_CASH', 'Paid in Cash'),
        ('PAID_WALLET', 'Paid from Wallet'),
        ('CANCELLED', 'Cancelled'),
    )
    # We use a ForeignKey to link to the shop owner who created the bill
    initiating_shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='issued_bills')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='received_bills')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill of {self.amount} for {self.customer.username} from {self.initiating_shop.username}"

# The Transaction model, which is a record of a wallet payment
class Transaction(models.Model):
    bill = models.OneToOneField(Bill, on_delete=models.PROTECT, related_name='transaction')
    source_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='debit_transactions')
    destination_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='credit_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} from {self.source_wallet.owner.username} to {self.destination_wallet.owner.username}"