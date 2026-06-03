from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.db import models

from rest_framework import permissions

from mosquito_alert.identification_tasks.models import (
    IdentificationTask,
    ExpertReportAnnotation,
)
from mosquito_alert.notifications.models import Notification, NotificationRecipient
from mosquito_alert.users.models import TigaUser
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership

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


class IsWorkspaceUser(FullDjangoModelPermissions):
    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        result = super().has_permission(request, view)
        if not result and view.action in ["list", "retrieve", "list_mine"]:
            result = (
                request.user
                and request.user.is_authenticated
                and Workspace.objects.filter(
                    models.Q(members=request.user)
                    | models.Q(collaboration_groups__reviewers=request.user)
                ).exists()
            )

        return result


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


class MessagePermissions(FullDjangoModelPermissions):
    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        role_perm = False
        if request.method in ["GET", "POST"]:
            role_perm = request.user.collaboration_groups_as_reviewer.all().exists()

        return role_perm or super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if view.action == "recipients":
            if isinstance(request.user, User):
                return self.has_permission(request, view) or obj.expert == request.user
            return False

        return super().has_object_permission(request, view, obj)


class MyMessagePermissions(MessagePermissions):
    pass


class MessageTopicPermissions(FullDjangoModelPermissions):
    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        role_perm = False
        is_reviewer = request.user.collaboration_groups_as_reviewer.all().exists()
        if request.method == "GET":
            role_perm = is_reviewer

        if view.action == "send":
            # Workaround to ensure DjangoModelPermissions are not applied
            # to the root view when using DefaultRouter.
            if getattr(view, "_ignore_model_permissions", False):
                return True

            perms = self.get_required_permissions(request.method, Notification)

            role_perm = is_reviewer or request.user.has_perms(perms)

        return role_perm or super().has_permission(request, view)


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


class BaseIdentificationTaskPermissions(IsWorkspaceUser):
    def _check_is_annotator(self, request, view, obj) -> bool:
        if isinstance(request.user, TigaUser):
            return False

        if isinstance(obj, IdentificationTask):
            task = obj
        else:
            inferred_fieldnames = get_fk_fieldnames(
                model=obj._meta.model, related_model=IdentificationTask
            )
            if len(inferred_fieldnames) > 1:
                raise MultipleObjectsReturned(
                    f"Model {obj._meta.model} has {len(inferred_fieldnames)} relation to model {TigaUser}."
                )
            task_fname = inferred_fieldnames[0]
            if not hasattr(obj, task_fname):
                return False
            task = getattr(obj, task_fname)
        return task.annotators.filter(pk=request.user.pk).exists()

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False

        result = super().has_permission(request, view)

        if not result and view.action == "retrieve":
            if self._check_is_annotator(request, view, obj):
                result = True

        return result


class IdentificationTaskPermissions(BaseIdentificationTaskPermissions):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role_perm = False
        if request.method == "GET" and isinstance(request.user, User):
            role_perm = (
                request.user.workspace_memberships.all().exists()
                or request.user.collaboration_groups_as_reviewer.all().exists()
            )

        return super().has_permission(request, view) or role_perm


class MyIdentificationTaskPermissions(DjangoRegularUserModelPermissions):
    pass


class IdentificationTaskAssignmentPermissions(IsRegularUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        return (
            request.user.has_perm(
                "%(app_label)s.add_%(model_name)s"
                % {
                    "app_label": ExpertReportAnnotation._meta.app_label,
                    "model_name": ExpertReportAnnotation._meta.model_name,
                }
            )
            or request.user.collaboration_groups_as_reviewer.all().exists()
            or request.user.workspace_memberships.filter(
                role__in=[
                    WorkspaceMembership.Role.ANNOTATOR,
                    WorkspaceMembership.Role.SUPERVISOR,
                ]
            ).exists()
        )


class IdentificationTaskReviewPermissions(IsRegularUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        has_review_permissions = request.user.has_perm(
            "%(app_label)s.add_review"
            % {"app_label": IdentificationTask._meta.app_label}
        )

        return (
            has_review_permissions
            or request.user.collaboration_groups_as_reviewer.all().exists()
        )


class BaseIdentificationTaskAttributePermissions(BaseIdentificationTaskPermissions):
    pass


class AnnotationPermissions(BaseIdentificationTaskAttributePermissions):
    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        result = super().has_permission(request, view)
        if not result and view.action in ["create"]:
            # Only annotators, supervisors or reviewers can create annotations.
            result = Workspace.objects.filter(
                models.Q(
                    memberships__user=request.user,
                    memberships__role__in=[
                        WorkspaceMembership.Role.ANNOTATOR,
                        WorkspaceMembership.Role.SUPERVISOR,
                    ],
                )
                | models.Q(collaboration_groups__reviewers=request.user)
            ).exists()

        return result

    # Always allow retrieve owned attributes
    def has_object_permission(self, request, view, obj):
        # Allow retrieve if user is the owner
        if view.action == "retrieve":
            if obj.user == request.user:
                return True
        return super().has_object_permission(request, view, obj)


class MyAnnotationPermissions(DjangoRegularUserModelPermissions):
    pass


class PhotoPredictionPermissions(BaseIdentificationTaskAttributePermissions):
    pass


class CountriesPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoModelPermissions.perms_map
