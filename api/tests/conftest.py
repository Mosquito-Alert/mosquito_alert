import pytest
import random

from rest_framework.authtoken.models import Token

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.tests.utils import grant_permission_to_user
from tigaserver_app.models import EuropeCountry, TigaUser, Report, Photo

User = get_user_model()


@pytest.fixture
def user_password():
    return "testpassword123_tmp"

@pytest.fixture
def app_user(user_password):
    user = TigaUser.objects.create(device_token="123456789")
    user.set_password(user_password)
    user.save(0)
    return user

@pytest.fixture
def dummy_image():
    # Prepare a fake image file
    image_content = b"fake image content"  # Replace with actual binary data if needed
    test_image = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpeg")

    return test_image

@pytest.fixture
def adult_report(app_user, dummy_image):
    r = Report.objects.create(
        user=app_user,
        report_id=1234,  # TODO: change
        phone_upload_time=timezone.now(),
        creation_time=timezone.now(),
        version_time=timezone.now(),
        type=Report.TYPE_ADULT,
        location_choice=Report.LOCATION_CURRENT,
        current_location_lon=2,
        current_location_lat=2,
    )

    _ = Photo.objects.create(
        photo=dummy_image,
        report=r,
    )

    return r

@pytest.fixture
def report_photo(adult_report):
    return adult_report.photos.first()

@pytest.fixture
def report_hidden_photo(report_photo):
    report_photo.hide = True
    report_photo.save()
    return report_photo

@pytest.fixture
def django_live_url(live_server):
    yield live_server.url


@pytest.fixture
def api_live_url(django_live_url):
    yield django_live_url + "/api/v1"


@pytest.fixture()
def country():
    obj, _ = EuropeCountry.objects.get_or_create(
        cntr_id="RD", name_engl="Random", iso3_code="RND", fid="RD"
    )
    return obj


@pytest.fixture
def es_country():
    obj, _ = EuropeCountry.objects.get_or_create(
        cntr_id="ES", name_engl="Spain", iso3_code="ESP", fid="ES"
    )
    return obj


@pytest.fixture
def it_country():
    obj, _ = EuropeCountry.objects.get_or_create(
        cntr_id="IT", name_engl="Italy", iso3_code="ITA", fid="IT"
    )
    return obj


@pytest.fixture
def user():
    return User.objects.create_user(
        username=f"user_{random.randint(1,1000)}",
        password=User.objects.make_random_password(),
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
def token_user_can_add(token_instance_user, model_class):
    permission = grant_permission_to_user(
        type="add", model_class=model_class, user=token_instance_user.user
    )

    return token_instance_user.key

    permission.delete()


@pytest.fixture
def token_user_can_view(token_instance_user, model_class):
    permission = grant_permission_to_user(
        type="view", model_class=model_class, user=token_instance_user.user
    )

    token_instance_user.refresh_from_db()
    return token_instance_user.key

    permission.delete()


@pytest.fixture
def token_user_can_change(token_instance_user, model_class):
    permission = grant_permission_to_user(
        type="change", model_class=model_class, user=token_instance_user.user
    )

    yield token_instance_user.key

    permission.delete()


@pytest.fixture
def token_user_can_delete(token_instance_user, model_class):
    permission = grant_permission_to_user(
        type="delete", model_class=model_class, user=token_instance_user.user
    )

    yield token_instance_user.key

    permission.delete()
