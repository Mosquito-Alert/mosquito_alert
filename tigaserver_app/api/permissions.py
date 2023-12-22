from rest_framework import permissions


class CanCreateNotifications(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user has the general permission to create notifications
        return request.user.has_perm("your_app.add_notificationcontent")

    def has_object_permission(self, request, view, obj):
        # Check if the user has the specific permission to enable notify_all
        return request.user.has_perm("your_app.can_create_notifications")
