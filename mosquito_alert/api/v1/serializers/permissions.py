from rest_framework import serializers

from mosquito_alert.identification_tasks.models import (
    ExpertReportAnnotation,
    IdentificationTask,
)
from mosquito_alert.notifications.models import Notification


class BaseCRUDPermissionSerializer(serializers.Serializer):
    add = serializers.BooleanField()
    change = serializers.BooleanField()
    view = serializers.BooleanField()
    delete = serializers.BooleanField()

    model = None

    def to_representation(self, instance):
        user = self.context["request"].user

        return {
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

            return {
                "add": has_add_review_perm,
                "change": has_add_review_perm,
                "view": has_add_review_perm,
                "delete": False,
            }

    class MessagePermissionSerializer(BaseCRUDPermissionSerializer):
        model = Notification

    annotation = AnnotationPermissionSerializer(source="*")
    identification_task = IdentificationTaskPermissionSerializer(source="*")
    review = ReviewPermissionSerializer(source="*")
    message = MessagePermissionSerializer(source="*")
