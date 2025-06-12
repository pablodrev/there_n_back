from rest_framework import permissions
from api.models import CustomUser

class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == CustomUser.RoleChoices.CLIENT)

class IsDispatcher(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == CustomUser.RoleChoices.DISPATCHER)
