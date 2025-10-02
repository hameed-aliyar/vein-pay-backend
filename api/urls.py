# api/urls.py

from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Auth endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Wallet endpoints
    path('wallet/', views.WalletDetailView.as_view(), name='wallet-detail'),
    path('wallet/add/', views.AddMoneyView.as_view(), name='wallet-add-money'),
    path('wallet/transactions/', views.TransactionHistoryView.as_view(), name='wallet-transactions'),
]

urlpatterns += [
    # Shop Owner endpoints
    path('shop/customers/', views.CustomerListCreateView.as_view(), name='shop-customer-list-create'),
    path('shop/bills/', views.BillCreateView.as_view(), name='shop-create-bill'),
    path('pay/', views.PaymentView.as_view(), name='process-payment'),
]