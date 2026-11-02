from rest_framework import serializers

from mosquito_alert.identification_tasks.models import (
    ExpertReportAnnotation,
    IdentificationTask,
)
from mosquito_alert.notifications.models import Notification
from mosquito_alert.stats.rules import UNRESTRICTED_PERM, VIEW_STATS_PERM


class BaseCRUDPermissionSerializer(serializers.Serializer):
    add = serializers.BooleanField()
    change = serializers.BooleanField()
    view = serializers.BooleanField()
    delete = serializers.BooleanField()

    model = None

    @staticmethod
    def permission_response(add, change, view, delete):
        return {
            "add": add,
            "change": change,
            "view": view,
            "delete": delete,
        }

    def to_representation(self, instance):
        user = self.context["request"].user

        permissions = {
            action: user.has_perm(
                "%(app_label)s.%(action)s_%(model_name)s"
                % {
                    "app_label": self.model._meta.app_label,
                    "model_name": self.model._meta.model_name,
                    "action": action,
                }
            )
            for action in ("add", "change", "view", "delete")
        }
        return self.permission_response(**permissions)


class PermissionsSerializer(serializers.Serializer):
    class AnnotationPermissionSerializer(BaseCRUDPermissionSerializer):
        model = ExpertReportAnnotation

    class IdentificationTaskPermissionSerializer(BaseCRUDPermissionSerializer):
        model = IdentificationTask

    class ReviewPermissionSerializer(BaseCRUDPermissionSerializer):
        def to_representation(self, instance):
            user = self.context["request"].user

            has_add_review_perm = user.has_perm(
                f"{IdentificationTask._meta.app_label}.add_review"
            )

            return self.permission_response(
                add=has_add_review_perm,
                change=has_add_review_perm,
                view=has_add_review_perm,
                delete=False,
            )

    class MessagePermissionSerializer(BaseCRUDPermissionSerializer):
        model = Notification

    class StatisticsPermissionSerializer(BaseCRUDPermissionSerializer):
        view_world = serializers.BooleanField(read_only=True)  # declared for the schema

        def to_representation(self, instance):
            user = self.context["request"].user
            return {
                "add": False,
                "change": False,
                "delete": False,
                "view": user.has_perm(VIEW_STATS_PERM),
                "view_world": user.has_perm(
                    UNRESTRICTED_PERM
                ),  # True for superusers too
            }

    annotation = AnnotationPermissionSerializer(source="*")
    identification_task = IdentificationTaskPermissionSerializer(source="*")
    review = ReviewPermissionSerializer(source="*")
    message = MessagePermissionSerializer(source="*")
    statistics = StatisticsPermissionSerializer(source="*")
