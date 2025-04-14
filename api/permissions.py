from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from rest_framework import exceptions
from rest_framework import permissions

from tigacrafting.models import ExpertReportAnnotation
from tigaserver_app.models import TigaUser, Notification

from .utils import get_fk_fieldnames

User = get_user_model()


class FullDjangoModelPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        **permissions.DjangoObjectPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }

class UserObjectPermissions(FullDjangoModelPermissions):
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


class MyReportPermissions(ReportPermissions):
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and isinstance(user, TigaUser):
            return super().has_permission(request=request, view=view)
        return False

class IdentificationTaskPermissions(FullDjangoModelPermissions):
    pass

class MyIdentificationTaskPermissions(permissions.DjangoModelPermissions):
    pass

class IdentificationTaskBacklogPermissions(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if request.method != "GET":
            raise exceptions.MethodNotAllowed(request.method)

        return request.user.has_perm('%(app_label)s.add_%(model_name)s' % {
            'app_label': ExpertReportAnnotation._meta.app_label,
            'model_name': ExpertReportAnnotation._meta.model_name
        })

class AnnotationPermissions(FullDjangoModelPermissions):
    # Always allow retrieve owned annotations

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and view.action == 'retrieve':
            return True
        return super().has_permission(request=request, view=view)

    def has_object_permission(self, request, view, obj):
        # Allow retrieve if user is the owner
        if view.action == 'retrieve':
            if obj.user == request.user:
                return True
            return super().has_permission(request=request, view=view)
        return super().has_object_permission(request, view, obj)

class MyAnnotationPermissions(permissions.DjangoModelPermissions):
    pass

class TaxaPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoModelPermissions.perms_map