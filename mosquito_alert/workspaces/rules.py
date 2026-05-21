import rules

from mosquito_alert.workspaces.models import (
    Workspace,
    WorkspaceMembership,
    WorkspaceCollaborationGroup,
)


@rules.predicate
def is_workspace_member(user, workspace: Workspace):
    return workspace.members.filter(pk=user.pk).exists()


def workspace_role_is(*roles: WorkspaceMembership.Role):
    @rules.predicate
    def predicate(user, workspace: Workspace):
        return workspace.memberships.filter(user=user, role__in=roles).exists()

    return predicate


@rules.predicate
def is_collaboration_reviewer(user, workspace):
    return WorkspaceCollaborationGroup.objects.filter(
        workspaces=workspace,
        reviewers=user,
    ).exists()
