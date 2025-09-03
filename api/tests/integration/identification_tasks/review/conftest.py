import pytest

from api.tests.utils import grant_permission_to_user

from tigacrafting.models import IdentificationTask

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask

@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.report.pk}/review"

