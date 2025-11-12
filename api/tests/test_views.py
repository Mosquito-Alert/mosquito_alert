from abc import abstractmethod
from datetime import timedelta
import jwt
import pytest
import time_machine
import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.module_loading import import_string

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from rest_framework_simplejwt.settings import api_settings

from tigacrafting.models import ExpertReportAnnotation, IdentificationTask, PhotoPrediction, FavoritedReports
from tigaserver_app.models import TigaUser, Report, Device, MobileApp, Photo

from api.tests.clients import AppAPIClient
from api.tests.integration.observations.factories import create_observation_object
from api.tests.integration.breeding_sites.factories import create_breeding_site_object
from api.tests.integration.bites.factories import create_bite_object
from api.tests.integration.identification_tasks.factories import create_annotation
from api.tests.factories import create_report_object
from api.tests.utils import grant_permission_to_user
from api.tests.integration.identification_tasks.predictions.factories import create_photo_prediction

from .utils import grant_permission_to_user

User = get_user_model()

# TODO: automatic user subscription on new report.

@pytest.mark.django_db
class BaseReportTest:
    queryset = None
    POST_FORMAT = 'json'

    _common_post_data = {
        'created_at': '2024-01-01T00:00:00Z',
        'sent_at': '2024-01-01T00:30:00Z',
        'location': {
            'source': 'auto',
            'point': {
                'latitude': 0,
                'longitude': 0,
            }
        },
    }

    @pytest.fixture
    def data_create_request(self):
        return self._common_post_data

    @abstractmethod
    def report_object(self):
        raise NotImplemented

    @property
    @abstractmethod
    def endpoint(self):
        raise NotImplementedError

    def test_package_is_set_on_report_create(self, app_user, data_create_request):
        if self.POST_FORMAT == 'multipart':
            pytest.skip("Skipping test for multipart format")

        # Testing here due its a field taken from the JWT token
        app_user.locale = 'es'
        app_user.save()
        app_api_client = AppAPIClient(
            device=Device.objects.create(
                user=app_user,
                device_id='unique_device_id',
                mobile_app=MobileApp.objects.create(
                    package_name='testapp',
                    package_version="1.2.3+4567"
                )
            )
        )
        app_api_client.force_login(user=app_user)

        response = app_api_client.post(
            self.endpoint,
            data={
                **data_create_request,
            },
            format=self.POST_FORMAT
        )
        assert response.status_code == status.HTTP_201_CREATED
        report = self.queryset.get(pk=response.data.get('uuid'))

        assert report.package_name == 'testapp'
        assert report.package_version == 102     # NOTE: only major and minor version are considered.
        assert report.app_language == 'es'

    def test_device_is_set_on_report_create(self, app_user, data_create_request):
        if self.POST_FORMAT == 'multipart':
            pytest.skip("Skipping test for multipart format")

        # Testing here due its a field taken from the JWT token
        app_api_client = AppAPIClient(
            device=Device.objects.create(
                user=app_user,
                device_id='unique_device_id',
                manufacturer='test_make',
                model="test_model",
                os_name="testOs",
                os_version="testv123",
                os_locale='es',
            )
        )
        app_api_client.force_login(user=app_user)

        response = app_api_client.post(
            self.endpoint,
            data={
                **data_create_request,
            },
            format=self.POST_FORMAT
        )

        assert response.status_code == status.HTTP_201_CREATED

        report = self.queryset.get(pk=response.data.get('uuid'))

        assert report.device_manufacturer == 'test_make'
        assert report.device_model == 'test_model'
        assert report.os == 'testOs'
        assert report.os_version == 'testv123'
        assert report.os_language == 'es'

    def test_delete_method_performs_soft_delete(self, app_api_client, report_object):
        # Delete
        response = app_api_client.delete(
            self.endpoint + f"{report_object.pk}/"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        report = self.queryset.get(pk=report_object.pk)
        assert report.deleted

class TestBiteAPI(BaseReportTest):

    endpoint = '/api/v1/bites/'
    queryset = Report.objects.filter(type=Report.TYPE_BITE)

    _common_post_data = BaseReportTest._common_post_data | {'counts': {'head': 1}}

    @pytest.fixture
    def report_object(self, app_user):
        return create_bite_object(user=app_user)

class TestBreedingSiteAPI(BaseReportTest):

    endpoint = '/api/v1/breeding-sites/'
    queryset = Report.objects.filter(type=Report.TYPE_SITE)
    POST_FORMAT = 'multipart'

    @pytest.fixture
    def report_object(self, app_user):
        return create_breeding_site_object(user=app_user)

class TestObservationAPI(BaseReportTest):

    endpoint = '/api/v1/observations/'
    queryset = Report.objects.filter(type=Report.TYPE_ADULT)
    POST_FORMAT = 'multipart'

    @pytest.fixture
    def report_object(self, app_user):
        return create_observation_object(user=app_user)

    @pytest.mark.parametrize("is_published", [True, False])
    def test_observation_has_identification_only_if_published(self, app_api_client, is_published, identification_task):
        observation = identification_task.report
        observation.published_at = timezone.now() if is_published else None
        observation.save()

        response = app_api_client.get(
            self.endpoint + f"{observation.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert (response.data['identification'] is None) != is_published


@pytest.mark.django_db
class TestIdentificationTaskAPI:
    @classmethod
    def build_url(cls, identification_task):
        return f"/api/v1/identification-tasks/{identification_task.pk}/"

    @pytest.fixture
    def permitted_user(self, user):
        grant_permission_to_user(type='view', model_class=IdentificationTask, user=user)
        Token.objects.create(user=user)
        return user

    @pytest.fixture
    def api_client(self, user):
        api_client = APIClient()
        api_client.force_login(user=user)

        return api_client

    @pytest.mark.parametrize(
        "result_source, expect_null",
        [
            (IdentificationTask.ResultSource.AI, False),
            (IdentificationTask.ResultSource.EXPERT, False),
            (None, True)
        ]
    )
    def test_result(self, api_client, permitted_user, identification_task, result_source, expect_null):
        identification_task.result_source = result_source
        identification_task.save()

        response = api_client.get(
            self.build_url(identification_task=identification_task),
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert (response.data['result'] == None) == expect_null

@pytest.mark.django_db
class TestIdentificationTaskPredictionAPI:
    @classmethod
    def build_url(cls, identification_task, photo_uuid: str = None):
        result = f"/api/v1/identification-tasks/{identification_task.pk}/predictions/"
        if photo_uuid:
            result += f"{photo_uuid}/"
        return result

    @pytest.fixture
    def permitted_user(self, user):
        grant_permission_to_user(type='change', model_class=PhotoPrediction, user=user)
        Token.objects.create(user=user)
        return user

    @pytest.fixture()
    def api_client(self, permitted_user):
        from rest_framework.test import APIClient

        client = APIClient()
        token = Token.objects.get(user=permitted_user)
        client.credentials(HTTP_AUTHORIZATION=f"Token {str(token)}")
        return client

    @pytest.mark.parametrize("is_decisive", [False, True])
    def test_is_decisive_False_does_not_set_identification_task(self, api_client, identification_task, is_decisive):
        assert identification_task.result_source != IdentificationTask.ResultSource.AI

        photo = identification_task.photo
        _ = create_photo_prediction(photo=photo)

        response = api_client.patch(
            self.build_url(identification_task=identification_task, photo_uuid=photo.uuid),
            data={
                "is_decisive": is_decisive
            },
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

        identification_task.refresh_from_db()
        assert (identification_task.result_source == IdentificationTask.ResultSource.AI) == is_decisive
        assert identification_task.report.published == is_decisive

    def test_taxon_is_null(self, api_client, user, identification_task):
        photo = identification_task.photo
        photo_prediction = create_photo_prediction(photo=photo)
        PhotoPrediction.objects.filter(pk=photo_prediction.pk).update(taxon=None)

        grant_permission_to_user(type='view', model_class=PhotoPrediction, user=user)

        response = api_client.get(
            self.build_url(identification_task=identification_task, photo_uuid=photo.uuid),
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['taxon'] is None

@pytest.mark.django_db
class TestTokenAPI:

    endpoint = '/api/v1/auth/token/'
    endpoint_refresh = endpoint + 'refresh/'
    endpoint_verify = endpoint + 'verify/'

    @pytest.fixture(params=[pytest.lazy_fixture('user'), pytest.lazy_fixture('app_user')])
    def any_user(self, request):
        return request.param

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_user_last_login_is_updated_on_token_create(self, any_user, user_password, client):
        assert any_user.last_login is None

        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
            }
        )
        assert response.status_code == status.HTTP_200_OK

        any_user.refresh_from_db()
        assert any_user.last_login == timezone.now()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_access_token_expires_after_5_minutes(self, any_user):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
        token = token_class.for_user(any_user)

        assert token.access_token.payload['exp'] == (timezone.now() + timedelta(minutes=5)).timestamp()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_refresh_token_expires_after_1_day(self, any_user):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
        token = token_class.for_user(any_user)

        assert token.payload['exp'] == (timezone.now() + timedelta(days=1)).timestamp()

    def test_user_last_login_is_not_updated_on_token_refresh(self, any_user, client):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token = token_class.for_user(any_user)

            traveller.shift(token.access_token.lifetime + timedelta(seconds=1))

            response = client.post(
                self.endpoint_refresh,
                data={
                    'refresh': str(token),
                }
            )
            assert response.status_code == status.HTTP_200_OK
            any_user.refresh_from_db()

            assert any_user.last_login is None

    def test_jwt_token_includes_user_type_on_obtain(self, any_user, user_password, client):
        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
            }
        )
        assert response.status_code == status.HTTP_200_OK

        token = response.json()['access']
        decoded = jwt.decode(
            token,
            algorithms=["HS256"],
            key='dummy_secretkey'  # get from settings_dev
        )
        assert 'user_type' in decoded
        expected_user_type = 'mobile_only' if isinstance(any_user, TigaUser) else 'regular'
        if isinstance(any_user, (TigaUser, User)):
            assert decoded['user_type'] == expected_user_type
        else:
            raise ValueError("Invalid user type")

    def test_jwt_token_includes_user_type_on_refresh(self, any_user, user_password, client):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token = token_class.for_user(any_user)

            traveller.shift(token.access_token.lifetime + timedelta(seconds=1))

            response = client.post(
                self.endpoint_refresh,
                data={
                    'refresh': str(token),
                }
            )
            assert response.status_code == status.HTTP_200_OK
            token = response.json()['access']
            decoded = jwt.decode(
                token,
                algorithms=["HS256"],
                key='dummy_secretkey'  # get from settings_dev
            )
            assert 'user_type' in decoded
            expected_user_type = 'mobile_only' if isinstance(any_user, TigaUser) else 'regular'
            if isinstance(any_user, (TigaUser, User)):
                assert decoded['user_type'] == expected_user_type
            else:
                raise ValueError("Invalid user type")

    def test_jwt_token_includes_device_id_only_for_tigauser(self, any_user, user_password, client):
        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
                'device_id': 'unique_id_for_device'
            }
        )
        assert response.status_code == status.HTTP_200_OK

        token = response.json()['access']
        decoded = jwt.decode(
            token,
            algorithms=["HS256"],
            key='dummy_secretkey'  # get from settings_dev
        )
        assert ('device_id' in decoded) == isinstance(any_user, TigaUser)
        if isinstance(any_user, TigaUser):
            # Check that the device_id is included in the token
            assert decoded['device_id'] == 'unique_id_for_device'

    @pytest.mark.parametrize(
        "extra_data",
        [{}, {'device_id': ''}]
    )
    def test_device_is_not_created(self, any_user, user_password, client, extra_data):
        assert Device.objects.all().count() == 0

        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
            } | extra_data
        )
        assert response.status_code == status.HTTP_200_OK

        assert Device.objects.all().count() == 0

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_device_is_created_if_not_exist_on_login(self, any_user, user_password, client):
        assert Device.objects.all().count() == 0

        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
                'device_id': 'unique_id_for_device'
            }
        )
        assert response.status_code == status.HTTP_200_OK

        if isinstance(any_user, TigaUser):
            device = Device.objects.get(user=any_user, device_id='unique_id_for_device')
            assert device.type is None
            assert device.date_created == timezone.now()
            assert device.last_login == timezone.now()
        else:
            assert Device.objects.all().count() == 0

    def test_device_last_login_is_updated_on_token_create(self, app_user, user_password, client):
        device = Device.objects.create(
            user=app_user,
            device_id='unique_id_for_device'
        )
        assert device.last_login is None
        assert device.date_created is not None
        date_created = device.date_created

        with time_machine.travel("2024-01-01 00:00:00", tick=False):
            response = client.post(
                self.endpoint,
                data={
                    'username': app_user.username,
                    'password': user_password,
                    'device_id': 'unique_id_for_device'
                }
            )
            assert response.status_code == status.HTTP_200_OK

            device.refresh_from_db()
            assert device.last_login == timezone.now()
            assert device.date_created == date_created

    def test_jwt_token_includes_device_id_after_refresh(self, any_user, user_password, client):
        response = client.post(
            self.endpoint,
            data={
                'username': any_user.username,
                'password': user_password,
                'device_id': 'unique_id_for_device'
            }
        )
        assert response.status_code == status.HTTP_200_OK

        refresh_token = response.json()['refresh']

        response = client.post(
            self.endpoint_refresh,
            data={
                'refresh': str(refresh_token),
            }
        )
        assert response.status_code == status.HTTP_200_OK

        token = response.json()['access']
        decoded = jwt.decode(
            token,
            algorithms=["HS256"],
            key='dummy_secretkey'  # get from settings_dev
        )
        assert ('device_id' in decoded) == isinstance(any_user, TigaUser)
        if isinstance(any_user, TigaUser):
            # Check that the device_id is included in the token
            assert decoded['device_id'] == 'unique_id_for_device'

    def test_device_last_login_is_not_updated_on_token_refresh(self, app_user, user_password, client):
        device = Device.objects.create(
            user=app_user,
            device_id='unique_id_for_device'
        )

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            response = client.post(
                self.endpoint,
                data={
                    'username': app_user.username,
                    'password': user_password,
                    'device_id': 'unique_id_for_device'
                }
            )
            assert response.status_code == status.HTTP_200_OK
            refresh_token = response.json()['refresh']

            device.refresh_from_db()
            last_login = device.last_login
            assert last_login == timezone.now()

            traveller.shift(timedelta(seconds=30))

            response = client.post(
                self.endpoint_refresh,
                data={
                    'refresh': str(refresh_token),
                }
            )
            assert response.status_code == status.HTTP_200_OK

            device.refresh_from_db()
            assert device.last_login == last_login

    def test_device_is_set_to_logged_in_on_login_if_not_logged(self, app_user, user_password, client):
        device = Device.objects.create(
            user=app_user,
            device_id='unique_id_for_device',
            registration_id='fcm_token',
            active_session=False
        )
        assert not device.active
        response = client.post(
            self.endpoint,
            data={
                'username': app_user.username,
                'password': user_password,
                'device_id': 'unique_id_for_device'
            }
        )
        assert response.status_code == status.HTTP_200_OK

        device.refresh_from_db()
        assert device.active_session
        assert device.active

    def test_device_is_set_to_not_logged_in_if_login_with_duplicated_device_id(self, app_user, user_password, client):
        dummy_user = TigaUser.objects.create()
        device = Device.objects.create(
            user=dummy_user,
            device_id='unique_id_for_device',
            registration_id='fcm_token',
            active_session=True
        )
        assert device.active
        # Login with same device_id but different user.
        response = client.post(
            self.endpoint,
            data={
                'username': app_user.username,
                'password': user_password,
                'device_id': 'unique_id_for_device'
            }
        )
        assert response.status_code == status.HTTP_200_OK

        device.refresh_from_db()
        assert not device.active_session
        assert not device.active

    @pytest.mark.parametrize(
        "token_field",
        [
            'access_token',
            None  # this is for refresh token
        ]
    )
    def test_token_verify_return_401_after_expiration(self, any_user, client, token_field):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
            token = token_class.for_user(any_user)

            # Access token
            response = client.post(
                self.endpoint_verify,
                data={
                    'token': str(getattr(token, token_field) if token_field else token),
                }
            )
            assert response.status_code == status.HTTP_200_OK

            traveller.shift(token.access_token.lifetime + timedelta(seconds=1))

            # Access token
            response = client.post(
                self.endpoint_verify,
                data={
                    'token': str(token.access_token),
                }
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestDeviceAPI:
    endpoint = '/api/v1/devices/'

    def test_device_is_set_to_inactive_if_new_duplicated_device_is_created(self, app_api_client):
        dummy_user = TigaUser.objects.create()
        device = Device.objects.create(
            device_id='unique_id',
            registration_id='fcm_unique_token',
            user=dummy_user,
            type='android',
            model='test_model',
            os_name='android',
            os_version='32',
            active=True
        )

        response = app_api_client.post(
            self.endpoint,
            data={
                'device_id': 'another_unique_id',
                'fcm_token': device.registration_id,
                'type': 'ios',
                'manufacturer': 'another_manufacturer',
                'model': 'another_model',
                'os': {
                    'name': 'iOs',
                    'version': 'another_version'
                }
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        device.refresh_from_db()
        assert not device.active

    def test_inactive_device_is_set_to_active_on_registration_id_change(self, app_user, app_api_client):
        device = Device.objects.create(
            device_id='unique_id',
            registration_id='fcm_unique_token',
            user=app_user,
            type='android',
            model='test_model',
            os_name='android',
            os_version='32',
            active=False,
            active_session=True
        )
        response = app_api_client.patch(
            self.endpoint + f"{device.device_id}/",
            data={
                'fcm_token': 'fcm_unique_token2',
            },
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        device.refresh_from_db()
        assert device.active

    def test_device_without_device_id_is_updated_on_create(self, app_user):
        # The legacy API create devices from Report model, which does not set the device_id
        report = create_report_object(user=app_user)
        report.type = Report.TYPE_BITE
        report.device_manufacturer = 'test_make'
        report.device_model = 'test_model'
        report.os = 'iOs'
        report.os_version = 'testv123'
        report.os_language = 'es'
        report.save()

        device = report.device
        assert device
        assert device.device_id is None
        assert device.registration_id is None

        # Need to set a deviec_token for the force_login
        # But not saving.
        device_pk = device.pk
        device.device_id = 'unique_id'
        app_api_client = AppAPIClient(device=device)
        app_api_client.force_login(user=app_user)

        device.refresh_from_db()
        assert device.device_id is None

        response = app_api_client.post(
            self.endpoint,
            data={
                'device_id': 'unique_id',
                'fcm_token': 'fcm_token',
                'type': device.type,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'os': {
                    'name': device.os_name,
                    'version': device.os_version
                }
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        device.refresh_from_db()
        assert device.device_id == 'unique_id'
        assert device.pk == device_pk
        assert Device.objects.filter(user=app_user).count() == 1

@pytest.mark.django_db
@pytest.mark.usefixtures("taxa")
class TestIdentificationTaskAnnotationsApi:
    @pytest.fixture
    def endpoint(self, identification_task):
        return f'/api/v1/identification-tasks/{identification_task.report.pk}/annotations/'

    @pytest.fixture
    def api_client(self, user):
        api_client = APIClient()
        api_client.force_login(user=user)

        return api_client

    @pytest.fixture
    def with_add_permission(self, user):
        return grant_permission_to_user(
            type="add", model_class=ExpertReportAnnotation, user=user
        )

    @pytest.fixture
    def common_post_data(self, taxon_root):
        return {
            'classification': {
                'taxon_id': taxon_root.pk,
                'confidence_label': 'definitely'
            }
        }

    @pytest.mark.parametrize(
        "confidence_label, validation_value",
        [
            ('definitely', ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY),
            ('probably', ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY),
        ]
    )
    def test_confidence_label_sets_obj_validation_value(self, api_client, endpoint, common_post_data, with_add_permission, confidence_label, validation_value):
        post_data = common_post_data
        post_data['classification']['confidence_label'] = confidence_label

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.validation_value == validation_value

    @pytest.mark.parametrize(
        "validation_complete_executive, revise, expected_result",
        [
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, True),
        ]
    )
    def test_is_decisive_representation(self, identification_task, user, api_client, endpoint, validation_complete_executive, revise, expected_result):
        obj = create_annotation(
            identification_task=identification_task,
            user=user,
            validation_complete_executive=validation_complete_executive,
            revise=revise
        )

        response = api_client.get(
            endpoint + f'{obj.pk}/',
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_decisive'] == expected_result

    @pytest.mark.parametrize(
        "is_decisive",
        [True, False]
    )
    def test_is_decisive_sets_validation_complete_executive(self, api_client, endpoint, user_with_role_supervisor_in_country, common_post_data, with_add_permission, is_decisive):
        post_data = common_post_data
        post_data['is_decisive'] = is_decisive

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.validation_complete_executive == is_decisive

    @pytest.mark.parametrize(
        "status, expected_result",
        [
            (ExpertReportAnnotation.STATUS_FLAGGED, True),
            (ExpertReportAnnotation.STATUS_HIDDEN, False),
            (ExpertReportAnnotation.STATUS_PUBLIC, False),
        ]
    )
    def test_is_flagged_representation(self, identification_task, user, api_client, endpoint, status, expected_result):
        obj = create_annotation(
            identification_task=identification_task,
            user=user,
            status=status
        )

        response = api_client.get(
            endpoint + f'{obj.pk}/',
            format='json'
        )
        assert response.status_code == 200
        assert response.data['is_flagged'] == expected_result

    @pytest.mark.parametrize(
        "is_flagged, expected_result",
        [
            (True, ExpertReportAnnotation.STATUS_FLAGGED),
            (False, ExpertReportAnnotation.STATUS_PUBLIC),
        ]
    )
    def test_is_flagged_sets_status_to_flagged(self, api_client, endpoint, common_post_data, with_add_permission, is_flagged, expected_result):
        post_data = common_post_data
        post_data['is_flagged'] = is_flagged

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.status == expected_result

    def test_empty_observation_flags(self, api_client, endpoint, common_post_data, with_add_permission):
        post_data = common_post_data
        # Ensure observation_flags is not set
        post_data.pop('observation_flags', None)

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        assert response.data['observation_flags']['is_favourite'] == False
        assert response.data['observation_flags']['is_visible'] == True

    @pytest.mark.parametrize(
        "is_visible, expected_result",
        [
            (True, ExpertReportAnnotation.STATUS_PUBLIC),
            (False, ExpertReportAnnotation.STATUS_HIDDEN),
        ]
    )
    def test_is_visible_sets_status_to_public(self, api_client, endpoint, common_post_data, with_add_permission, is_visible, expected_result):
        post_data = common_post_data
        post_data['observation_flags'] = {
            'is_visible': is_visible
        }

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.status == expected_result

    @pytest.mark.parametrize(
        "is_favourite",
        [True, False]
    )
    def test_is_favourite_creates_FavoritedReports(self, api_client, endpoint, common_post_data, with_add_permission, is_favourite):
        post_data = common_post_data
        post_data['observation_flags'] = {
            'is_favourite': is_favourite
        }

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['observation_flags']['is_favourite'] == is_favourite

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.is_favourite == is_favourite
        assert FavoritedReports.objects.filter(
            report=annotation.identification_task.report,
            user=annotation.user
        ).exists() == is_favourite

    def test_is_favourite_does_nothing_if_already_exists_FavoritedReports(self, api_client, user, identification_task, endpoint, common_post_data, with_add_permission):
        FavoritedReports.objects.create(
            report=identification_task.report,
            user=user
        )

        post_data = common_post_data
        post_data['is_favourite'] = True

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['observation_flags']['is_favourite'] is True

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.is_favourite
        assert FavoritedReports.objects.filter(
            report=annotation.identification_task.report,
            user=annotation.user
        ).exists()

    @pytest.mark.parametrize(
        "sex, is_blood_fed, is_gravid, expected_genre_blood",
        [
            ('male', False, False, Photo.BLOOD_GENRE_MALE),
            ('male', False, True, Photo.BLOOD_GENRE_MALE),
            ('male', True, False, Photo.BLOOD_GENRE_MALE),
            ('male', True, True, Photo.BLOOD_GENRE_MALE),
            ('female', False, False, Photo.BLOOD_GENRE_FEMALE),
            ('female', False, True, Photo.BLOOD_GENRE_FEMALE_GRAVID),
            ('female', True, False, Photo.BLOOD_GENRE_FEMALE_BLOOD_FED),
            ('female', True, True, Photo.BLOOD_GENRE_FEMALE_GRAVID_BLOOD_FED),
            (None, False, False, Photo.BLOOD_GENRE_UNKNOWN),
            (None, False, True, Photo.BLOOD_GENRE_UNKNOWN),
            (None, True, False, Photo.BLOOD_GENRE_UNKNOWN),
            (None, True, True, Photo.BLOOD_GENRE_UNKNOWN),
        ]
    )
    def test_characteristics_sets_Photo_blood_genre_field(self, api_client, endpoint, identification_task, common_post_data, with_add_permission, sex, is_blood_fed, is_gravid, expected_genre_blood):
        post_data = common_post_data
        post_data['best_photo_uuid'] = identification_task.photo.uuid
        post_data['characteristics'] = {
            'sex': sex,
            'is_blood_fed': is_blood_fed,
            'is_gravid': is_gravid
        }

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        photo = annotation.best_photo
        assert photo.blood_genre == expected_genre_blood

    @pytest.mark.parametrize(
        "pre_assign",
        [True, False]
    )
    def test_POST_always_saves_validation_complete_True(self, pre_assign, api_client, endpoint, identification_task, user, common_post_data, with_add_permission):
        if pre_assign:
            identification_task.assign_to_user(user=user)
            annotation = ExpertReportAnnotation.objects.get(user=user, identification_task=identification_task)

        response = api_client.post(
            endpoint,
            data=common_post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        if pre_assign:
            annotation.refresh_from_db()
        else:
            annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.validation_complete

    def test_classification_null_shoud_set_status_to_hidden(self, api_client, endpoint, common_post_data, with_add_permission):
        post_data = common_post_data
        post_data['classification'] = None
        # NOTE: force is_visible. Should set to hidden anyways.
        post_data['observation_flags'] = {
            "is_visible": True
        }

        response = api_client.post(
            endpoint,
            data=post_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(pk=response.data['id'])
        assert annotation.status == ExpertReportAnnotation.STATUS_HIDDEN
        assert annotation.taxon is None

@pytest.mark.django_db
@pytest.mark.usefixtures("taxa")
class TestIdentificationTaskReviewApi:
    @pytest.fixture
    def endpoint(self, identification_task):
        return f'/api/v1/identification-tasks/{identification_task.report.pk}/review/'

    @pytest.fixture
    def api_client(self, user_with_role_reviewer):
        api_client = APIClient()
        api_client.force_login(user=user_with_role_reviewer)

        return api_client

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_agree_review_create_expertreportannotation(self, api_client, endpoint, user_with_role_reviewer, identification_task):
        assert ExpertReportAnnotation.objects.filter(
            identification_task=identification_task,
            user=user_with_role_reviewer
        ).count() == 0

        # NOTE: this is needed due to the way the review process is structured
        identification_task.is_safe = True
        identification_task.save()

        response = api_client.post(
            endpoint,
            data={
                'action': 'agree'
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(
            identification_task=identification_task,
            user=user_with_role_reviewer
        )
        assert not annotation.validation_complete_executive
        assert annotation.status == ExpertReportAnnotation.STATUS_PUBLIC
        assert annotation.validation_complete
        assert annotation.best_photo is None
        assert annotation.simplified_annotation
        assert not annotation.revise

        identification_task.refresh_from_db()
        assert identification_task.review_type == IdentificationTask.Review.AGREE
        assert identification_task.reviewed_at == timezone.now()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_overwrite_review_create_expertreportannotation(self, api_client, endpoint, user_with_role_reviewer, identification_task, taxon_root, dummy_image):
        assert ExpertReportAnnotation.objects.filter(
            identification_task=identification_task,
            user=user_with_role_reviewer
        ).count() == 0

        another_photo = Photo.objects.create(
            photo=dummy_image,
            report=identification_task.report,
        )

        response = api_client.post(
            endpoint,
            data={
                'action': 'overwrite',
                'public_photo_uuid': another_photo.uuid,
                'is_safe': True,
                'public_note': 'new test public note',
                'result': {
                    'taxon_id': taxon_root.pk,
                    'confidence_label': 'definitely'
                }
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        annotation = ExpertReportAnnotation.objects.get(
            identification_task=identification_task,
            user=user_with_role_reviewer
        )
        assert not annotation.validation_complete_executive
        assert annotation.status == ExpertReportAnnotation.STATUS_PUBLIC
        assert annotation.validation_complete
        assert annotation.best_photo.uuid == another_photo.uuid
        assert not annotation.simplified_annotation
        assert annotation.revise

        identification_task.refresh_from_db()
        assert identification_task.review_type == IdentificationTask.Review.OVERWRITE
        assert identification_task.reviewed_at == timezone.now()
        assert identification_task.is_safe
        assert identification_task.public_note == 'new test public note'
        assert identification_task.taxon == taxon_root
        assert identification_task.confidence == 1
        assert identification_task.photo == another_photo

@pytest.mark.django_db
class TestPermissionsApi:
    @pytest.fixture
    def me_endpoint(self):
        return f'/api/v1/me/permissions/'

    @pytest.fixture
    def api_client(self, user):
        api_client = APIClient()
        api_client.force_login(user=user)

        return api_client

    def test_general_role_base(self, api_client, me_endpoint):
        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'base'

    def test_general_role_annotator(self, api_client, user, group_expert, me_endpoint):
        user.groups.add(group_expert)

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'annotator'
        assert not response.data['general']['permissions']['review']['add']
        assert not response.data['general']['permissions']['review']['view']

    def test_general_role_reviewer(self, api_client, user, group_superexpert, me_endpoint):
        user.groups.add(group_superexpert)

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'reviewer'
        assert response.data['general']['permissions']['review']['add']
        assert response.data['general']['permissions']['review']['view']

    def test_general_role_admin(self, api_client, user, me_endpoint):
        user.is_superuser = True
        user.save()

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'admin'

    @pytest.mark.parametrize(
        "is_staff",
        [True, False]
    )
    def test_general_is_staff(self, user, api_client, me_endpoint, is_staff):
        user.is_staff = is_staff
        user.save()

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['is_staff'] == is_staff

    def test_countries_role_supervisor(self, api_client, user, group_expert, me_endpoint, country):
        user.groups.add(group_expert)

        userstat = user.userstat
        userstat.national_supervisor_of = country
        userstat.save()

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'annotator'
        assert response.data['countries'][0]['country']['id'] == country.pk
        assert response.data['countries'][0]['role'] == 'supervisor'
        assert response.data['countries'][0]['permissions']['annotation']['mark_as_decisive']
        assert response.data['countries'][0]['permissions']['identification_task']['view']
        assert not response.data['countries'][0]['permissions']['review']['add']
        assert not response.data['countries'][0]['permissions']['review']['view']

    def test_countries_role_annotator(self, api_client, user, group_expert, me_endpoint, country):
        user.groups.add(group_expert)

        userstat = user.userstat
        userstat.native_of = country
        userstat.save()

        response = api_client.get(
            me_endpoint,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['general']['role'] == 'annotator'
        assert response.data['countries'][0]['role'] == 'annotator'
        assert response.data['countries'][0]['country']['id'] == country.pk
        assert not response.data['countries'][0]['permissions']['annotation']['mark_as_decisive']
        assert not response.data['countries'][0]['permissions']['identification_task']['view']
        assert not response.data['countries'][0]['permissions']['review']['add']
        assert not response.data['countries'][0]['permissions']['review']['view']