import pytest


from mosquito_alert.identification_tasks.models import IdentificationTask


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask


@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.report.pk}/review"
