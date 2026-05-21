import rules

from django.contrib.auth.models import User

from mosquito_alert.workspaces.rules import (
    is_collaboration_reviewer,
    is_workspace_member,
    workspace_role_is,
)
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership

from .models import IdentificationTask, ExpertReportAnnotation


def has_global_view_identificationtask_perm(user: User):
    return user.has_perm(
        "%(app_label)s.view_%(model_name)s"
        % {
            "app_label": IdentificationTask._meta.app_label,
            "model_name": IdentificationTask._meta.model_name,
        }
    )


def has_global_add_annotation_perm(user: User):
    return user.has_perm(
        "%(app_label)s.add_%(model_name)s"
        % {
            "app_label": ExpertReportAnnotation._meta.app_label,
            "model_name": ExpertReportAnnotation._meta.model_name,
        }
    )


@rules.predicate
def can_view_task(user: User, task: IdentificationTask):
    if has_global_view_identificationtask_perm(user):
        return True

    if task.annotators.filter(user=user).exists():
        return True

    workspace = task.workspace
    if not workspace:
        return False

    return (
        (task.is_done and is_workspace_member(user, workspace))
        or (
            not task.status == IdentificationTask.Status.ARCHIVED
            and workspace_role_is(
                user, workspace, roles=[WorkspaceMembership.Role.SUPERVISOR]
            )
        )
        or is_collaboration_reviewer(user, workspace)
    )


@rules.predicate
def can_view_tasks_from_workspace(user: User, workspace: Workspace):
    if is_workspace_member(user, workspace):
        return True

    return is_collaboration_reviewer(user, workspace)


@rules.predicate
def can_add_annotations_to_workspace(user: User, workspace: Workspace):
    return workspace_role_is(
        user,
        workspace,
        roles=[WorkspaceMembership.Role.ANNOTATOR, WorkspaceMembership.Role.SUPERVISOR],
    ) or is_collaboration_reviewer(user, workspace)


@rules.predicate
def can_add_annotation_to_task(user: User, task: IdentificationTask):
    if has_global_add_annotation_perm(user):
        return True

    if task.status in IdentificationTask.CLOSED_STATUS:
        return False

    workspace = task.workspace
    if not workspace:
        return True

    return can_add_annotations_to_workspace(user, workspace)


@rules.predicate
def can_add_executive_annotations_to_workspace(user: User, workspace: Workspace):
    return workspace_role_is(
        user, workspace, roles=[WorkspaceMembership.Role.SUPERVISOR]
    ) or is_collaboration_reviewer(user, workspace)


@rules.predicate
def can_add_executive_annotation_to_task(user: User, task: IdentificationTask):
    if has_global_add_annotation_perm(user):
        return True

    workspace = task.workspace
    if not workspace:
        return True

    return can_add_executive_annotations_to_workspace(user, workspace)


def has_global_add_review_perm(user: User):
    return user.has_perm(
        "%(app_label)s.add_review"
        % {
            "app_label": IdentificationTask._meta.app_label,
        }
    )


@rules.predicate
def can_review_to_task(user: User, task: IdentificationTask):
    if has_global_add_review_perm(user):
        return True

    workspace = task.workspace
    if not workspace:
        return False

    return is_collaboration_reviewer(user, workspace)


rules.add_rule("tasks.view_identificationtask", can_view_task)
rules.add_rule(
    "tasks.view_identificationtasks_from_workspace", can_view_tasks_from_workspace
)

rules.add_rule("tasks.add_annotation_to_task", can_add_annotation_to_task)
rules.add_rule("tasks.add_annotations_to_workspace", can_add_annotations_to_workspace)

rules.add_rule(
    "tasks.add_executive_annotation_to_task", can_add_executive_annotation_to_task
)
rules.add_rule(
    "tasks.add_executive_annotations_to_workspace",
    can_add_executive_annotations_to_workspace,
)

rules.add_rule("tasks.add_review_to_task", can_review_to_task)
rules.add_rule("tasks.change_review_to_task", can_review_to_task)
rules.add_rule("tasks.view_review_to_task", can_review_to_task)
