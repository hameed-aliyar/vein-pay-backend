# api/admin.py

from django.contrib import admin
from .models import User, Wallet, BiometricData, Bill, Transaction

class WalletAdmin(admin.ModelAdmin):
    list_display = ('owner', 'balance', 'updated_at')
    search_fields = ('owner__username',)

class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'initiating_shop', 'customer', 'amount', 'status', 'created_at')
    list_filter = ('status', 'initiating_shop')
    search_fields = ('customer__username', 'initiating_shop__username')

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_wallet', 'destination_wallet', 'amount', 'timestamp')
    search_fields = ('source_wallet__owner__username', 'destination_wallet__owner__username')

# Register your models here.
admin.site.register(User)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(BiometricData)
admin.site.register(Bill, BillAdmin)
admin.site.register(Transaction, TransactionAdmin)