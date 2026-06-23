import io
from pathlib import Path
from PIL import Image
import pytest
import random

from rest_framework.authtoken.models import Token

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string

from rest_framework_simplejwt.settings import api_settings as simplejwt_settings

from mosquito_alert.api.v1.tests.utils import grant_permission_to_user
from mosquito_alert.api.v1.tests.clients import AppAPIClient

from mosquito_alert.geo.models import Country
from mosquito_alert.geo.tests.factories import CountryFactory
from mosquito_alert.identification_tasks.models import IdentificationTask
from mosquito_alert.notifications.models import (
    Notification,
    NotificationTopic,
    NotificationContent,
)
from mosquito_alert.reports.tests.factories import ObservationReportFactory
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.workspaces.models import WorkspaceMembership
from mosquito_alert.workspaces.tests.factories import WorkspaceCollaborationGroupFactory
from mosquito_alert.users.tests.factories import TigaUserFactory, UserFactory

User = get_user_model()
TEST_DATA_PATH = Path(Path(__file__).parent.absolute(), "test_data/")


@pytest.fixture
def taxa(db):
    call_command("loaddata", "/app/mosquito_alert/taxa/fixtures/taxon.json")


@pytest.fixture
def user_password():
    return "testpassword123_tmp"


@pytest.fixture
def app_user(user_password):
    return TigaUserFactory(password=user_password)


@pytest.fixture
def app_user_token(app_user):
    return str(
        import_string(simplejwt_settings.TOKEN_OBTAIN_SERIALIZER)
        .get_token(user=app_user)
        .access_token
    )


@pytest.fixture
def jwt_token_user(user):
    return str(
        import_string(simplejwt_settings.TOKEN_OBTAIN_SERIALIZER)
        .get_token(user=user)
        .access_token
    )


# TODO: replace to factory_boy (faker) to generate random data
@pytest.fixture
def dummy_image():
    # Prepare a fake image file
    # Create a simple image using Pillow
    img = Image.new(
        "RGB", (100, 100), color=(73, 109, 137)
    )  # Create a 100x100 image with a specific color
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")  # Save the image in JPEG format
    img_byte_arr.seek(0)  # Move to the beginning of the BytesIO buffer

    test_image = SimpleUploadedFile(
        "test_image.jpg", img_byte_arr.read(), content_type="image/jpeg"
    )

    return test_image


@pytest.fixture
def adult_report(app_user, es_country):
    return ObservationReportFactory(
        user=app_user,
        point=es_country.geom.point_on_surface,
    )


@pytest.fixture
def report_photo(adult_report):
    return adult_report.photos.first()


@pytest.fixture
def report_hidden_photo(report_photo):
    report_photo.hide = True
    report_photo.save()
    return report_photo


@pytest.fixture
def identification_task(adult_report):
    return IdentificationTask.objects.get(report=adult_report)


@pytest.fixture
def django_live_url(live_server):
    yield live_server.url


@pytest.fixture
def api_live_url(django_live_url):
    yield django_live_url + "/api/v1"


@pytest.fixture()
def country():
    try:
        obj = Country.objects.get(iso3_code="RND")
    except Country.DoesNotExist:
        obj = CountryFactory(iso3_code="RND", iso2_code="RD", name_engl="Random")
    return obj


@pytest.fixture
def es_country():
    obj, _ = Country.objects.get_or_create(
        name_engl="Spain",
        iso2_code="ES",
        iso3_code="ESP",
        wikidata_id="Q29",
        geom=MultiPolygon(Polygon.from_bbox((-10.0, 35.0, 3.5, 44.0))),
    )
    return obj


@pytest.fixture
def it_country():
    obj, _ = Country.objects.get_or_create(
        name_engl="Italy",
        iso2_code="IT",
        iso3_code="ITA",
        wikidata_id="Q38",
        geom=MultiPolygon(Polygon.from_bbox((6.0, 36.0, 19.0, 47.0))),
    )
    return obj


@pytest.fixture
def user(user_password):
    return UserFactory(password=user_password)


@pytest.fixture
def another_user():
    return UserFactory(
        username=f"user_{random.randint(1, 1000)}",
        password=get_random_string(length=10),
        first_name="Test Another FirstName",
        last_name="Test Another LastName",
    )


@pytest.fixture
def token_instance_user(user):
    token, _ = Token.objects.get_or_create(user=user)

    return token

    token.delete()


@pytest.fixture
def token_user(token_instance_user):
    return token_instance_user.key


@pytest.fixture
def perm_user_can_add(user, model_class):
    return grant_permission_to_user(type="add", model_class=model_class, user=user)


@pytest.fixture
def jwt_token_user_can_add(jwt_token_user, perm_user_can_add):
    return jwt_token_user


@pytest.fixture
def token_user_can_add(token_instance_user, perm_user_can_add):
    return token_instance_user.key

    # permission.delete()


@pytest.fixture
def jwt_token_user_can_view(jwt_token_user, perm_user_can_view):
    return jwt_token_user


@pytest.fixture
def perm_user_can_view(user, model_class):
    return grant_permission_to_user(type="view", model_class=model_class, user=user)


@pytest.fixture
def token_user_can_view(token_instance_user, perm_user_can_view):
    return token_instance_user.key


@pytest.fixture
def jwt_token_user_can_change(jwt_token_user, perm_user_can_change):
    return jwt_token_user


@pytest.fixture
def perm_user_can_change(user, model_class):
    return grant_permission_to_user(type="change", model_class=model_class, user=user)


@pytest.fixture
def token_user_can_change(token_instance_user, perm_user_can_change):
    return token_instance_user.key


@pytest.fixture
def jwt_token_user_can_delete(jwt_token_user, perm_user_can_delete):
    return jwt_token_user


@pytest.fixture
def perm_user_can_delete(user, model_class):
    return grant_permission_to_user(type="delete", model_class=model_class, user=user)


@pytest.fixture
def token_user_can_delete(token_instance_user, perm_user_can_delete):
    return token_instance_user.key


@pytest.fixture
def app_api_client(app_user):
    api_client = AppAPIClient()
    api_client.force_login(user=app_user)
    return api_client


@pytest.fixture
def non_app_api_client(user):
    api_client = AppAPIClient()
    api_client.force_login(user=user)
    return api_client


@pytest.fixture
def api_client():
    return AppAPIClient()


@pytest.fixture
def test_png_image_path():
    return Path(TEST_DATA_PATH, Path("white_image.png"))


@pytest.fixture
def test_jpg_image_path():
    return Path(TEST_DATA_PATH, Path("black_image.jpg"))


@pytest.fixture
def test_non_image_path():
    return Path(TEST_DATA_PATH, Path("non_image.txt"))


@pytest.fixture
def taxon_root():
    return Taxon.get_root() or Taxon.add_root(
        rank=Taxon.TaxonomicRank.CLASS, name="Insecta", common_name=""
    )


@pytest.fixture
def user_with_role_member_in_country(user, es_country):
    WorkspaceMembership.objects.create(
        user=user,
        workspace=es_country.workspaces.first(),
        role=WorkspaceMembership.Role.MEMBER,
    )

    return user


@pytest.fixture
def user_with_role_annotator_in_country(user, es_country):
    WorkspaceMembership.objects.create(
        user=user,
        workspace=es_country.workspaces.first(),
        role=WorkspaceMembership.Role.ANNOTATOR,
    )

    return user


@pytest.fixture
def user_with_role_supervisor_in_country(user, es_country):
    WorkspaceMembership.objects.create(
        user=user,
        workspace=es_country.workspaces.first(),
        role=WorkspaceMembership.Role.SUPERVISOR,
    )

    return user


@pytest.fixture
def user_with_role_reviewer_in_country(user, es_country):
    WorkspaceCollaborationGroupFactory(
        reviewers=[user],
        workspaces=[es_country.workspaces.first()],
    )

    return user


@pytest.fixture
def user_with_role_admin(user):
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture(autouse=True)
def use_dummy_cache_backend(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }


@pytest.fixture()
def use_test_cache_backend(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-test-cache",
        }
    }


@pytest.fixture
def topic():
    return NotificationTopic.objects.create(
        topic_code="test", topic_description="test description"
    )


@pytest.fixture
def user_notification(app_user, user):
    notification = Notification.objects.create(
        expert=user,
        notification_content=NotificationContent.objects.create(
            title_en="Test title", body_html_en="Test body"
        ),
    )
    notification.send_to_user(user=app_user)

    return notification
