from rest_framework import permissions


class AuthPostOnlyPermission(permissions.BasePermission):
    """
    Permission only for HTTP POST requests.
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        else:
            return False

 #   def has_object_permission(self, request, view, obj):
 #       return request.user and request.user.is_authenticated() and request.method == 'POST'


class AuthGetOnlyPermission(permissions.BasePermission):
    """
    Permission only for HTTP POST requests.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated() and request.method == 'GET'
