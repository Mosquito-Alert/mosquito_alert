from typing import List, Optional, Union

import rules

from mosquito_alert.workspaces.models import (
    Workspace,
    WorkspaceMembership,
    WorkspaceCollaborationGroup,
)
from mosquito_alert.users.models import User, TigaUser


@rules.predicate
def is_workspace_member(
    user: Union[User, TigaUser],
    workspaces: Optional[Union[Workspace, List[Workspace]]] = None,
):
    if not isinstance(user, User):
        return False

    if isinstance(workspaces, Workspace):
        workspaces = [workspaces]

    qs = user.workspaces.all()
    if workspaces is not None:
        qs = qs.filter(pk__in=[workspace.pk for workspace in workspaces])

    return qs.exists()


def has_workspace_role(*roles: WorkspaceMembership.Role):
    @rules.predicate
    def predicate(
        user: Union[User, TigaUser],
        workspaces: Optional[Union[Workspace, List[Workspace]]] = None,
    ):
        if not isinstance(user, User):
            return False
        if isinstance(workspaces, Workspace):
            workspaces = [workspaces]

        qs = WorkspaceMembership.objects.filter(user=user, role__in=roles)

        if workspaces is not None:
            qs = qs.filter(workspace__in=workspaces)

        return qs.exists()

    return predicate


@rules.predicate
def is_workspace_reviewer(
    user: Union[User, TigaUser],
    workspaces: Optional[Union[Workspace, List[Workspace]]] = None,
):
    if not isinstance(user, User):
        return False

    qs = WorkspaceCollaborationGroup.objects.filter(
        reviewers=user,
    )

    if isinstance(workspaces, Workspace):
        workspaces = [workspaces]

    if workspaces is not None:
        qs = qs.filter(workspaces__in=workspaces)

    return qs.exists()


@rules.predicate
def in_workspace_collaboration_group_with_role(
    *roles: WorkspaceMembership.Role,
):

    @rules.predicate
    def predicate(
        user: Union[User, TigaUser],
        workspaces: Optional[Union[Workspace, List[Workspace]]] = None,
    ):
        if not isinstance(user, User):
            return False

        if isinstance(workspaces, Workspace):
            workspaces = [workspaces]

        if not workspaces:
            return False

        workspaces_with_desired_roles = Workspace.objects.filter(
            memberships__user=user,
            memberships__role__in=roles,
        )

        return (
            WorkspaceCollaborationGroup.objects.filter(
                workspaces__in=workspaces_with_desired_roles
            )
            .filter(workspaces__in=workspaces)
            .exists()
        )

    return predicate


rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": Workspace._meta.app_label,
        "model_name": Workspace._meta.model_name,
    },
    is_workspace_member | is_workspace_reviewer,
)
