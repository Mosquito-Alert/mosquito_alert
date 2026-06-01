import pytest

from mosquito_alert.workspaces.models import WorkspaceCollaborationGroup
from mosquito_alert.workspaces.tests.factories import WorkspaceCollaborationGroupFactory


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return WorkspaceCollaborationGroup


@pytest.fixture
def workspace_collaboration(workspace):
    return WorkspaceCollaborationGroupFactory(workspaces=[workspace])


@pytest.fixture
def workspace_collaboration_user_reviewer(user):
    return WorkspaceCollaborationGroupFactory(reviewers=[user])


@pytest.fixture
def another_workspace_collaboration():
    return WorkspaceCollaborationGroupFactory()
