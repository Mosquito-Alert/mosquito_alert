import pytest

from mosquito_alert.tigacrafting.models import ExpertReportAnnotation

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return ExpertReportAnnotation

@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.report.pk}/annotations"

@pytest.fixture
def assignment(assigned_only_identification_task, user):
    return ExpertReportAnnotation.objects.get(
        user=user,
        identification_task=assigned_only_identification_task
    )

@pytest.fixture
def me_endpoint():
    return f"me/identification-tasks/annotations"
