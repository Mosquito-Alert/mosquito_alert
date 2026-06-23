import pytest

from mosquito_alert.identification_tasks.models import (
    IdentificationTask,
    ExpertReportAnnotation,
)
from mosquito_alert.identification_tasks.tests.factories import (
    IdentificationTaskFactory,
)
from mosquito_alert.reports.tests.factories import PhotoFactory
from mosquito_alert.users.models import UserStat

from mosquito_alert.api.v1.tests.utils import grant_permission_to_user

from .predictions.factories import create_photo_prediction
from .factories import create_annotation


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask


@pytest.fixture
def annotation(identification_task, user):
    return create_annotation(identification_task=identification_task, user=user)


@pytest.fixture
def annotation_from_another_user(identification_task, another_user):
    return create_annotation(identification_task=identification_task, user=another_user)


@pytest.fixture
def another_identification_task(es_country):
    return IdentificationTaskFactory(report__point=es_country.geom.point_on_surface)


@pytest.fixture
def annotation_from_another_user_another_identification_task(
    another_identification_task, another_user
):
    return create_annotation(
        identification_task=another_identification_task, user=another_user
    )


@pytest.fixture
def another_identification_task_another_country(country):
    return IdentificationTaskFactory(report__point=country.geom.point_on_surface)


@pytest.fixture
def identification_task_fully_predicted(db):
    identification_task = IdentificationTaskFactory()

    for photo in identification_task.report.photos.all():
        create_photo_prediction(photo=photo)

    return identification_task


@pytest.fixture
def identification_task_with_pending_predictions(db):
    identification_task = IdentificationTaskFactory()

    for photo in identification_task.report.photos.all():
        create_photo_prediction(photo=photo)

    PhotoFactory(report=identification_task.report)

    return identification_task


@pytest.fixture
def archived_identification_task(identification_task):
    identification_task.status = IdentificationTask.Status.ARCHIVED
    identification_task.save()
    return identification_task


@pytest.fixture
def assigned_only_identification_task(identification_task, user):
    identification_task.assign_to_user(user)
    return identification_task


@pytest.fixture
def perm_user_can_view_identificationtasks(user):
    return grant_permission_to_user(
        type="view", model_class=IdentificationTask, user=user
    )


@pytest.fixture
def perm_user_can_view_archived_identificationtasks(user, model_class):
    return grant_permission_to_user(
        codename="view_archived_identificationtasks", model_class=model_class, user=user
    )


@pytest.fixture
def token_user_can_view_archived_identificationtasks(token_instance_user, model_class):
    permission = grant_permission_to_user(
        codename="view_archived_identificationtasks",
        model_class=model_class,
        user=token_instance_user.user,
    )

    token_instance_user.refresh_from_db()
    return token_instance_user.key

    permission.delete()


@pytest.fixture
def perm_user_can_add_annotations(user):
    return grant_permission_to_user(
        type="add", model_class=ExpertReportAnnotation, user=user
    )


@pytest.fixture
def perm_user_can_view_assignees(user):
    return grant_permission_to_user(type="view", model_class=UserStat, user=user)
