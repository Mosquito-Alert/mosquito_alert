import pytest

from tigaserver_app.models import ExpertReportAnnotation

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return ExpertReportAnnotation

@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.report.pk}/annotations"

@pytest.fixture
def assignation(assigned_only_identification_task, user):
    return assigned_only_identification_task.assignments.get(user=user, identification_task=assigned_only_identification_task)

@pytest.fixture
def me_endpoint():
    return f"me/identification-tasks/annotations"