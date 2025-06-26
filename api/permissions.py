from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from rest_framework import permissions

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation, UserStat
from tigaserver_app.models import TigaUser, Notification

from .utils import get_fk_fieldnames

User = get_user_model()


class IsMobileUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return isinstance(
            request.user, TigaUser
        ) and super().has_permission(request, view)

class IsRegularUser(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return isinstance(
            request.user, User
        ) and super().has_permission(request, view)

class DjangoRegularUserModelPermissions(permissions.DjangoModelPermissions):
    def has_permission(self, request, view):
        return isinstance(
            request.user, User
        ) and super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return isinstance(
            request.user, User
        ) and super().has_object_permission(request, view, obj)

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

        if view.action == 'list':
            return super().has_permission(request, view)

        return True

    def has_object_permission(self, request, view, obj):
        if obj == request.user:
            if view.action == 'retrieve':
                return True
            if view.action in ['update', 'partial_update']:
                return not isinstance(request.user, User)

        if isinstance(request.user, TigaUser):
            return False

        perms = self.get_required_permissions(request.method, obj._meta.model)
        return request.user.has_perms(perms)

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

class MyNotificationPermissions(NotificationObjectPermissions):
    def has_permission(self, request, view):
        return isinstance(request.user, TigaUser) and super().has_permission(request, view)

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

class UserRolePermission(permissions.BasePermission):
    ACTION_TO_PERMISSION = {
        'retrieve': 'view',
        'list': 'view',
        'update': 'change',
        'create': 'add',
        'destroy': 'delete'
    }

    def check_permissions(self, user, action, obj_or_klass) -> bool:
        if isinstance(user, User):
            user = UserStat.objects.filter(user=user).first()
            if not user:
                return False

        return user.has_role_permission(
            action=action,
            obj_or_klass=obj_or_klass
        ) if action is not None else False

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not view.action:
            return False

        return self.check_permissions(
            user=request.user,
            action=self.ACTION_TO_PERMISSION.get(view.action),
            obj_or_klass=view.get_queryset().model
        )

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if not view.action:
            return False

        return self.check_permissions(
            user=request.user,
            action=self.ACTION_TO_PERMISSION.get(view.action),
            obj_or_klass=obj
        )

class BaseIdentificationTaskPermissions(FullDjangoModelPermissions):
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
                    "Model {obj._meta.model} has {len(inferred_fieldnames)} relation to model {TigaUser}."
                )
            task_fname = inferred_fieldnames[0]
            if not hasattr(obj, task_fname):
                return False
            task = getattr(obj, task_fname)
        return task.annotators.filter(pk=request.user.pk).exists()

    def has_permission(self, request, view):
        if isinstance(request.user, TigaUser):
            return False
        if request.user and request.user.is_authenticated:
            if view.action == 'retrieve':
                return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view,obj):
            return False

        if view.action == 'retrieve' and self._check_is_annotator(request, view, obj):
            return True

        perms = self.get_required_permissions(request.method, obj._meta.model)
        return request.user.has_perms(perms)

class IdentificationTaskPermissions(BaseIdentificationTaskPermissions):
    def has_permission(self, request, view):
        role_perm = False
        if view.action == 'list':
            role_perm = UserRolePermission().check_permissions(
                user=request.user,
                action='add',
                obj_or_klass=ExpertReportAnnotation
            )

        return super().has_permission(request, view) or role_perm

class MyIdentificationTaskPermissions(DjangoRegularUserModelPermissions):
    pass

class IdentificationTaskAssignmentPermissions(IsRegularUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        return request.user.has_perm('%(app_label)s.add_%(model_name)s' % {
            'app_label': ExpertReportAnnotation._meta.app_label,
            'model_name': ExpertReportAnnotation._meta.model_name
        }) or UserRolePermission().check_permissions(
            user=request.user,
            action='add',
            obj_or_klass=ExpertReportAnnotation
        )

class BaseIdentificationTaskAttributePermissions(BaseIdentificationTaskPermissions):
    pass


class AnnotationPermissions(BaseIdentificationTaskAttributePermissions):
    # Always allow retrieve owned attributes
    def has_object_permission(self, request, view, obj):
        # Allow retrieve if user is the owner
        if view.action == 'retrieve':
            if obj.user == request.user:
                return True
        return super().has_object_permission(request, view, obj)

class MyAnnotationPermissions(DjangoRegularUserModelPermissions):
    pass

class PhotoPredictionPermissions(BaseIdentificationTaskAttributePermissions):
    pass

class TaxaPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoModelPermissions.perms_map

class CountriesPermissions(UserObjectPermissions):
    perms_map = permissions.DjangoModelPermissions.perms_map