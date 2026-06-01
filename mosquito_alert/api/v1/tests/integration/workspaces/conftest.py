import pytest

from mosquito_alert.workspaces.models import Workspace
from mosquito_alert.workspaces.tests.factories import WorkspaceFactory


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Workspace


@pytest.fixture
def workspace(user):
    return WorkspaceFactory(members=[user])


@pytest.fixture
def another_workspace(user):
    return WorkspaceFactory()
