import pytest

from tigacrafting.models import IdentificationTask

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask

@pytest.fixture
def identification_task(adult_report):
    return IdentificationTask.objects.get(report=adult_report)