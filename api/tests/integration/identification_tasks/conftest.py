import pytest

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation, UserStat

from api.tests.utils import grant_permission_to_user
from tigaserver_app.models import Photo, Report

from ..observations.factories import create_observation_object
from .predictions.factories import create_photo_prediction
from .factories import create_annotation

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask

@pytest.fixture
def annotation(identification_task, user):
    return create_annotation(
        identification_task=identification_task,
        user=user
    )

@pytest.fixture
def annotation_from_another_user(identification_task, another_user):
    return create_annotation(
        identification_task=identification_task,
        user=another_user
    )

@pytest.fixture
def another_identification_task(app_user, dummy_image):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    return observation.identification_task

@pytest.fixture
def annotation_from_another_user_another_identification_task(another_identification_task, another_user):
    return create_annotation(
        identification_task=another_identification_task,
        user=another_user
    )

@pytest.fixture
def another_identification_task_another_country(app_user, dummy_image, country):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    Report.objects.filter(pk=observation.pk).update(country=country)
    return observation.identification_task

@pytest.fixture
def identification_task_fully_predicted(app_user, dummy_image):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    create_photo_prediction(photo=photo)

    return observation.identification_task

@pytest.fixture
def identification_task_with_pending_predictions(app_user, dummy_image):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    create_photo_prediction(photo=photo)
    _ = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )

    return observation.identification_task

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
def perm_user_can_view_archived_identificationtasks(user, model_class):
    return grant_permission_to_user(
        codename="view_archived_identificationtasks", model_class=model_class, user=user
    )

@pytest.fixture
def token_user_can_view_archived_identificationtasks(token_instance_user, model_class):
    permission = grant_permission_to_user(
        codename="view_archived_identificationtasks", model_class=model_class, user=token_instance_user.user
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
    return grant_permission_to_user(
        type="view", model_class=UserStat, user=user
    )
