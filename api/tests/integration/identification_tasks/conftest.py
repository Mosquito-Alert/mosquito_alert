import pytest

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation

from api.tests.utils import grant_permission_to_user
from .factories import add_annotation

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask

@pytest.fixture
def identification_task(adult_report):
    return IdentificationTask.objects.get(report=adult_report)

@pytest.fixture
def annotation(identification_task, user):
    return add_annotation(
        identification_task=identification_task,
        user=user
    )

@pytest.fixture
def annotation_from_another_user(identification_task):
    return add_annotation(
        identification_task=identification_task,
    )

@pytest.fixture
def archived_identification_task(identification_task):
    identification_task.status = IdentificationTask.Status.ARCHIVED
    identification_task.save()
    return identification_task

@pytest.fixture
def token_user_can_view_archived_identificationtasks(token_instance_user, model_class):
    permission = grant_permission_to_user(
        codename="view_archived_identificationtasks", model_class=model_class, user=token_instance_user.user
    )

    token_instance_user.refresh_from_db()
    return token_instance_user.key

    permission.delete()

@pytest.fixture
def token_user_can_add_annotations(token_instance_user):
    permission = grant_permission_to_user(
        type="add", model_class=ExpertReportAnnotation, user=token_instance_user.user
    )

    token_instance_user.refresh_from_db()
    return token_instance_user.key

    permission.delete()