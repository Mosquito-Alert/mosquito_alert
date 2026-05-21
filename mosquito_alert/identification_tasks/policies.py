from dataclasses import dataclass
from typing import Optional

from django.contrib.auth import get_user_model

from mosquito_alert.utils.permissions import CRUDPermission
from mosquito_alert.workspaces.models import WorkspaceMembership, Workspace
from .models import IdentificationTask, ExpertReportAnnotation

User = get_user_model()


@dataclass
class IdentificationTaskPermission(CRUDPermission):
    pass


class IdentificationTaskPolicy:
    def __init__(self, user: "User"):
        self.user = user

    def can_add(self) -> bool:
        return self.user.has_perm(
            "%(app_label)s.add_%(model_name)s"
            % {
                "app_label": IdentificationTask._meta.app_label,
                "model_name": IdentificationTask._meta.model_name,
            }
        )

    def can_change_all(self) -> bool:
        return self.user.has_perm(
            "%(app_label)s.change_%(model_name)s"
            % {
                "app_label": IdentificationTask._meta.app_label,
                "model_name": IdentificationTask._meta.model_name,
            }
        )

    def can_change(self, obj: Optional["IdentificationTask"] = None) -> bool:
        return self.can_change_all()

    def can_view_all(self) -> bool:
        return self.user.has_perm(
            "%(app_label)s.view_%(model_name)s"
            % {
                "app_label": IdentificationTask._meta.app_label,
                "model_name": IdentificationTask._meta.model_name,
            }
        )

    def can_view(self, obj: Optional["IdentificationTask"] = None) -> bool:
        return (
            self.can_view_all()
            or WorkspaceMembership.objects.filter(
                workspace=obj.workspace,
                user=self.user,
                role=WorkspaceMembership.Role.SUPERVISOR,
            ).exists()
            or (
                obj.is_done
                and WorkspaceMembership.objects.filter(
                    workspace=obj.workspace, user=self.user
                ).exists()
            )
            or obj.expert_report_annotations.filter(
                user=self.user, is_finished=True
            ).exists()
        )

    def can_delete_all(self) -> bool:
        return self.user.has_perm(
            "%(app_label)s.delete_%(model_name)s"
            % {
                "app_label": IdentificationTask._meta.app_label,
                "model_name": IdentificationTask._meta.model_name,
            }
        )

    def can_delete(self, obj: Optional["IdentificationTask"] = None) -> bool:
        return self.can_delete_all()

    def get_permission(
        self, workspace: Optional["Workspace"] = None
    ) -> IdentificationTaskPermission:
        return IdentificationTaskPermission(
            add=self.can_add(),
            change=self.can_change_all(),
            view=self.can_view_all()
            or (
                workspace is not None
                and WorkspaceMembership.objects.filter(
                    workspace=workspace,
                    user=self.user,
                ).exists()
            ),
            delete=self.can_delete_all(),
        )


class ExpertReportAnnotationPolicy:
    def __init__(self, user: "User"):
        self.user = user

    def can_add(self, identification_task: "IdentificationTask") -> bool:
        return (
            self.user.has_perm(
                "%(app_label)s.add_%(model_name)s"
                % {
                    "app_label": ExpertReportAnnotation._meta.app_label,
                    "model_name": ExpertReportAnnotation._meta.model_name,
                }
            )
            and WorkspaceMembership.objects.filter(
                workspace=identification_task.workspace,
                user=self.user,
                role=WorkspaceMembership.Role.ANNOTATOR,
            ).exists()
        )
