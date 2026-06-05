import rules
from typing import Optional, Union

from django.contrib.auth.backends import ModelBackend

from mosquito_alert.users.models import User, TigaUser

from mosquito_alert.workspaces.rules import (
    is_workspace_member,
    is_workspace_reviewer,
    has_workspace_role,
    in_workspace_collaboration_group_with_role,
)
from mosquito_alert.workspaces.models import WorkspaceMembership

from .models import IdentificationTask, ExpertReportAnnotation, PhotoPrediction


model_backend = ModelBackend()


def has_global_permission(
    klass, type: Optional[str] = None, name: Optional[str] = None
) -> bool:
    perm = "%(app_label)s.%(name)s" % {
        "app_label": klass._meta.app_label,
        "name": name or f"{type}_{klass._meta.model_name}",
    }

    @rules.predicate
    def user_has_global_permission(user: User):
        return model_backend.has_perm(user, perm)

    return user_has_global_permission


def has_global_identification_task_permission(
    type: Optional[str] = None, name: Optional[str] = None
) -> bool:
    return has_global_permission(IdentificationTask, type=type, name=name)


@rules.predicate
def can_view_identification_task(
    user: Union[User, TigaUser], identification_task: Optional[IdentificationTask]
):
    if not isinstance(user, User):
        return False

    if identification_task is None:
        return is_workspace_member(user=user) or is_workspace_reviewer(user=user)

    if identification_task.annotators.filter(pk=user.pk).exists():
        return True

    workspaces = identification_task.workspaces
    if not workspaces.exists():
        return False

    return is_workspace_member(
        user=user, workspaces=workspaces
    ) or is_workspace_reviewer(user=user, workspaces=workspaces)


@rules.predicate
def can_add_annotation(
    user: Union[User, TigaUser], identification_task: Optional[IdentificationTask]
):
    if not isinstance(user, User):
        return False

    if identification_task is None:
        return has_workspace_role(
            WorkspaceMembership.Role.ANNOTATOR,
            WorkspaceMembership.Role.SUPERVISOR,
        )(user=user) or is_workspace_reviewer(user=user)

    if identification_task.status in IdentificationTask.CLOSED_STATUS:
        return False

    workspaces = identification_task.workspaces
    if not workspaces.exists():
        return False

    return (
        has_workspace_role(
            WorkspaceMembership.Role.ANNOTATOR,
            WorkspaceMembership.Role.SUPERVISOR,
        )(user=user, workspaces=workspaces)
        or in_workspace_collaboration_group_with_role(
            WorkspaceMembership.Role.ANNOTATOR,
            WorkspaceMembership.Role.SUPERVISOR,
        )(user=user, workspaces=workspaces)
        or is_workspace_reviewer(user=user, workspaces=workspaces)
    )


@rules.predicate
def can_view_annotation(
    user: Union[User, TigaUser], annotation: Optional[ExpertReportAnnotation]
):
    if not isinstance(user, User):
        return False

    if annotation is None:
        return can_view_identification_task(user=user, identification_task=None)

    if annotation.user == user:
        return True

    if not annotation.is_finished:
        return False

    return can_view_identification_task(
        user=user, identification_task=annotation.identification_task
    )


@rules.predicate
def can_set_executive_annotation(
    user: Union[User, TigaUser], obj: Union[IdentificationTask, ExpertReportAnnotation]
):
    if not isinstance(user, User):
        return False

    if isinstance(obj, ExpertReportAnnotation):
        identification_task = obj.identification_task
    else:
        identification_task = obj

    workspaces = identification_task.workspaces
    if not workspaces.exists():
        return False

    return has_workspace_role(
        WorkspaceMembership.Role.SUPERVISOR,
    )(user=user, workspaces=workspaces) or is_workspace_reviewer(
        user=user, workspaces=workspaces
    )


@rules.predicate
def can_review_identification_task(
    user: Union[User, TigaUser], identification_task: Optional[IdentificationTask]
):
    if not isinstance(user, User):
        return False

    if identification_task is None:
        return is_workspace_reviewer(user=user)

    workspaces = identification_task.workspaces
    if not workspaces.exists():
        return False

    return is_workspace_reviewer(user=user, workspaces=workspaces)


@rules.predicate
def can_view_photo_prediction(
    user: Union[User, TigaUser], photo_prediction: Optional[PhotoPrediction]
):
    if not isinstance(user, User):
        return False

    if photo_prediction is None:
        return False

    identification_task = photo_prediction.identification_task
    workspaces = identification_task.workspaces
    if not workspaces.exists():
        return False

    return can_view_identification_task(
        user=user, identification_task=identification_task
    )


rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": IdentificationTask._meta.app_label,
        "model_name": IdentificationTask._meta.model_name,
    },
    can_view_identification_task
    | has_global_identification_task_permission(type="view"),
)
rules.add_perm(
    "%(app_label)s.add_%(model_name)s"
    % {
        "app_label": ExpertReportAnnotation._meta.app_label,
        "model_name": ExpertReportAnnotation._meta.model_name,
    },
    can_add_annotation | has_global_permission(ExpertReportAnnotation, type="add"),
)
rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": ExpertReportAnnotation._meta.app_label,
        "model_name": ExpertReportAnnotation._meta.model_name,
    },
    can_view_annotation | has_global_permission(ExpertReportAnnotation, type="view"),
)
rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": PhotoPrediction._meta.app_label,
        "model_name": PhotoPrediction._meta.model_name,
    },
    can_view_photo_prediction | has_global_permission(PhotoPrediction, type="view"),
)
rules.add_rule("can_set_executive_annotation", can_set_executive_annotation)
rules.add_perm(
    "%(app_label)s.add_review" % {"app_label": IdentificationTask._meta.app_label},
    can_review_identification_task
    | has_global_identification_task_permission(name="add_review"),
)
