from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from rest_framework import permissions

from tigaserver_app.models import TigaUser, Notification

from .utils import get_fk_fieldnames

User = get_user_model()


class UserObjectPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        **permissions.DjangoObjectPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }

    def has_permission(self, request, view):
        if isinstance(request.user, TigaUser):
            return True

        return super().has_permission(request, view)

    def _app_user_has_object_permission(self, request, view, obj):
        # If the model is TigaUser, allow only if the
        # obj is the same as the loggined user.
        if obj._meta.model == TigaUser:
            return obj == request.user

        inferred_fieldnames = get_fk_fieldnames(
            model=obj._meta.model, related_model=TigaUser
        )

        if len(inferred_fieldnames) == 0:
            # No relations found to TigaUser.
            return True
        elif len(inferred_fieldnames) > 1:
            raise MultipleObjectsReturned(
                "Model {obj._meta.model} has {len(inferred_fieldnames)} relation to model {TigaUser}."
            )

        # Return if the user is the owner of that object.
        return getattr(obj, inferred_fieldnames[0]) == request.user

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, TigaUser):
            return self._app_user_has_object_permission(
                request=request, view=view, obj=obj
            )

        return super().has_object_permission(request, view, obj)


class NotificationObjectPermissions(UserObjectPermissions):
    def has_permission(self, request, view):
        if request.method == "POST":
            # Allow only User Model to create
            if not isinstance(request.user, User):
                return False

        return super().has_permission(request, view)

    def _app_user_has_object_permission(self, request, view, obj):
        return (
            Notification.objects.for_user(user=request.user).filter(pk=obj.pk).exists()
        )


class ReportPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoObjectPermissions.perms_map
    authenticated_users_only = False

    def _app_user_has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super()._app_user_has_object_permission(request, view, obj)
