# api/permissions.py

from rest_framework import permissions

class IsShopOwner(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'SHOP_OWNER' role.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and if their role is 'SHOP_OWNER'
        return request.user and request.user.is_authenticated and request.user.role == 'SHOP_OWNER'
