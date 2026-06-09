from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from rest_framework import permissions

from mosquito_alert.identification_tasks.models import ExpertReportAnnotation
from mosquito_alert.notifications.models import Notification, NotificationRecipient
from mosquito_alert.users.models import TigaUser

from .utils import get_fk_fieldnames

User = get_user_model()


class IsMobileUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return isinstance(request.user, TigaUser) and super().has_permission(
            request, view
        )


class IsRegularUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return isinstance(request.user, User) and super().has_permission(request, view)


class DjangoRegularUserModelPermissions(permissions.DjangoModelPermissions):
    def has_permission(self, request, view):
        return isinstance(request.user, User) and super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return isinstance(request.user, User) and super().has_object_permission(
            request, view, obj
        )


class FullDjangoModelPermissions(DjangoRegularUserModelPermissions):
    perms_map = {
        **permissions.DjangoObjectPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }


class DjangoRegularUserObjectPermissions(permissions.DjangoObjectPermissions):
    def has_permission(self, request, view):
        return isinstance(request.user, User) and super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return isinstance(request.user, User) and super().has_object_permission(
            request, view, obj
        )


class FullDjangoObjectPermissions(DjangoRegularUserObjectPermissions):
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


class UserPermissions(FullDjangoModelPermissions):
    def has_permission(self, request, view):
        # Always require authentication
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "list":
            return super().has_permission(request, view)

        return True

    def has_object_permission(self, request, view, obj):
        if obj == request.user:
            if view.action == "retrieve":
                return True
            if view.action in ["update", "partial_update"]:
                return not isinstance(request.user, User)

        if isinstance(request.user, TigaUser):
            return False

        perms = self.get_required_permissions(request.method, obj._meta.model)
        return request.user.has_perms(perms)


class NotificationObjectPermissions(UserObjectPermissions):
    def has_permission(self, request, view):
        if isinstance(request.user, User):
            return False
        return super().has_permission(request, view)

    def _app_user_has_object_permission(
        self, request, view, obj: NotificationRecipient
    ):
        return obj.user == request.user


class MyNotificationPermissions(NotificationObjectPermissions):
    pass


class MessagePermissions(FullDjangoObjectPermissions):
    pass


class MyMessagePermissions(MessagePermissions):
    pass


class MessageTopicPermissions(FullDjangoObjectPermissions):
    def has_permission(self, request, view):
        if isinstance(request.user, TigaUser):
            return False

        can_send_messages = False
        if view.action == "send":
            if request.user.is_authenticated:
                can_send_messages = request.user.has_perm(
                    "%(app_label)s.add_%(model_name)s"
                    % {
                        "app_label": Notification._meta.app_label,
                        "model_name": Notification._meta.model_name,
                    }
                )

        return super().has_permission(request, view) | can_send_messages


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


class IdentificationTaskPermissions(FullDjangoObjectPermissions):
    pass


class MyIdentificationTaskPermissions(DjangoRegularUserModelPermissions):
    pass


class IdentificationTaskAssignmentPermissions(IsRegularUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if view.action == "assign_next":
            # Only people who can add annotations.
            return request.user.has_perm(
                "%(app_label)s.add_%(model_name)s"
                % {
                    "app_label": ExpertReportAnnotation._meta.app_label,
                    "model_name": ExpertReportAnnotation._meta.model_name,
                }
            )

        return False


class IdentificationTaskReviewPermissions(DjangoRegularUserObjectPermissions):
    perms_map = {
        **DjangoRegularUserObjectPermissions.perms_map,
        "POST": ["%(app_label)s.add_review"],
    }


class AnnotationPermissions(FullDjangoObjectPermissions):
    pass


class MyAnnotationPermissions(DjangoRegularUserModelPermissions):
    pass


class PhotoPredictionPermissions(FullDjangoModelPermissions):
    pass


class CountriesPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoModelPermissions.perms_map
