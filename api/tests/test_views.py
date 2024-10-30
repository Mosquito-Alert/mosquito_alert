from abc import abstractmethod
from datetime import timedelta
import jwt
import pytest
import time_machine
import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.module_loading import import_string

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.settings import api_settings

from tigacrafting.models import ExpertReportAnnotation
from tigaserver_app.models import TigaUser, Report, Device, MobileApp, IAScore

from api.auth.serializers import AppUserTokenObtainPairSerializer
from api.tests.integration.observations.factories import create_observation_object
from api.tests.integration.breeding_sites.factories import create_breeding_site_object
from api.tests.integration.bites.factories import create_bite_object
from api.tests.factories import create_report_object

from .utils import grant_permission_to_user

User = get_user_model()

@pytest.fixture
def app_api_client(app_user):
    api_client = AppAPIClient()
    api_client.force_login(user=app_user)
    return api_client

# TODO: automatic user subscription on new report.

class AppAPIClient(APIClient):
    def __init__(self, device: Device = None,  *args, **kwargs):
        self.device = device
        super().__init__(self, *args, **kwargs)

    def force_login(self, user, backend=None) -> None:
        self.logout()
        return super().force_login(user, backend)

    def _login(self, user, backend=None):
        if isinstance(user, User):
            return super()._login(user, backend)
        elif isinstance(user, TigaUser):
            token = AppUserTokenObtainPairSerializer.get_token(
                user=user,
                device_id=self.device.device_id if self.device else None
            )
            self.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
        else:
            raise NotImplementedError

@pytest.mark.django_db
class BaseReportTest:
    queryset = None
    POST_FORMAT = 'json'

    _common_post_data = {
        'created_at': '2024-01-01T00:00:00Z',
        'sent_at': '2024-01-01T00:30:00Z',
        'location': {
            'type': 'current',
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
                    package_version=1234
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
        assert report.package_version == 1234
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

@pytest.mark.django_db
class TestPredictionAPI:
    @classmethod
    def build_url(cls, photo):
        return f"/api/v1/photos/{photo.uuid}/predictions/"

    @pytest.fixture
    def permitted_user(self, user):
        grant_permission_to_user(type='add', model_class=IAScore, user=user)
        Token.objects.create(user=user)
        return user

    @pytest.fixture
    def data_create_request(self):
        """Fixture for the data create request."""
        return {
            "bbox": {"x_min": 0, "y_min": 0, "x_max": 0, "y_max": 0},
            "insect_confidence": 0.9,
            "scores": {
                "ae_aegypti": 0.1,
                "ae_albopictus": 0.8,
                "ae_japonicus": 0.05,
                "ae_koreicus": 0.05,
                "anopheles": 0.05,
                "culex": 0.05,
                "culiseta": 0.05,
                "other_species": 0,
                "not_sure": 0
            },
            "is_executive_validation": False
        }

    @pytest.fixture()
    def api_client(self, permitted_user):
        from rest_framework.test import APIClient

        client = APIClient()
        token = Token.objects.get(user=permitted_user)
        client.credentials(HTTP_AUTHORIZATION=f"Token {str(token)}")
        return client

    def test_is_execution_validation_False_does_not_create_annotations(self, api_client, report_photo, data_create_request):
        assert not ExpertReportAnnotation.objects.filter(
            report__photos__in=[report_photo]
        ).exists()

        response = api_client.post(
            self.build_url(photo=report_photo),
            data={
                **data_create_request,
                **{
                    "is_executive_validation": False
                }
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        assert not ExpertReportAnnotation.objects.filter(
            report__photos__in=[report_photo]
        ).exists()

    def test_is_execution_validation_True_does_create_annotations(self, api_client, report_photo, data_create_request):
        assert not ExpertReportAnnotation.objects.filter(
            report__photos__in=[report_photo]
        ).exists()

        response = api_client.post(
            self.build_url(photo=report_photo),
            data={
                **data_create_request,
                **{
                    "is_executive_validation": True
                }
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert ExpertReportAnnotation.objects.filter(
            report__photos__in=[report_photo]
        ).count() == 4
        assert ExpertReportAnnotation.objects.filter(
            report__photos__in=[report_photo],
            user__username='aima',
            validation_complete_executive=True
        ).count() == 1

@pytest.mark.django_db
class TokenAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.endpoint = '/api/v1/auth/token/'
        cls.endpoint_refresh = cls.endpoint + 'refresh/'
        cls.endpoint_verify = cls.endpoint + 'verify/'

    def setUp(self) -> None:
        self.app_user = TigaUser.objects.create()
        self.app_user.set_password('testpassword123_tmp')
        self.app_user.save()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_user_last_login_is_updated_on_token_create(self):
        self.assertIsNone(self.app_user.last_login)

        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.app_user.refresh_from_db()
        self.assertEqual(self.app_user.last_login, timezone.now())

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_access_token_expires_after_5_minutes(self):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
        token = token_class.for_user(self.app_user)

        self.assertEqual(
            token.access_token.payload['exp'], 
            (timezone.now() + timedelta(minutes=5)).timestamp()
        )

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_refresh_token_expires_after_1_day(self):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
        token = token_class.for_user(self.app_user)

        self.assertEqual(
            token.payload['exp'],
            (timezone.now() + timedelta(days=1)).timestamp()
        )

    def test_user_last_login_is_not_updated_on_token_refresh(self):
        token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token = token_class.for_user(self.app_user)

            traveller.shift(token.access_token.lifetime + timedelta(seconds=1))

            response = self.client.post(
                self.endpoint_refresh,
                data={
                    'refresh': str(token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.app_user.refresh_from_db()
            self.assertIsNone(self.app_user.last_login)

    def test_jwt_token_includes_device_id(self):
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': 'unique_id_for_device'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = response.json()['access']
        decoded = jwt.decode(
            token,
            algorithms=["HS256"],
            key='dummy_secretkey'  # get from settings_dev
        )
        self.assertEqual(decoded['device_id'], 'unique_id_for_device')

    def test_device_is_not_created_if_device_not_specified_on_login(self):
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Device.objects.filter(user=self.app_user).count(), 0)
    
    def test_device_is_not_created_if_device_is_voidon_login(self):
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': ''
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Device.objects.filter(user=self.app_user).count(), 0)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_device_is_created_if_not_exist_on_login(self):
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': 'unique_id_for_device'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        device = Device.objects.get(user=self.app_user, device_id='unique_id_for_device')
        self.assertIsNone(device.type)
        self.assertEqual(device.date_created, timezone.now())
        self.assertEqual(device.last_login, timezone.now())

    def test_device_last_login_is_updated_on_token_create(self):
        device = Device.objects.create(
            user=self.app_user,
            device_id='unique_id_for_device'
        )
        self.assertIsNone(device.last_login)
        self.assertIsNotNone(device.date_created)
        date_created = device.date_created

        with time_machine.travel("2024-01-01 00:00:00", tick=False):
            response = self.client.post(
                self.endpoint,
                data={
                    'username': self.app_user.username,
                    'password': 'testpassword123_tmp',
                    'device_id': 'unique_id_for_device'
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            device.refresh_from_db()
            self.assertEqual(device.last_login, timezone.now())
            self.assertEqual(device.date_created, date_created)

    def test_jwt_token_includes_device_id_after_refresh(self):
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': 'unique_id_for_device'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        refresh_token = response.json()['refresh']

        response = self.client.post(
            self.endpoint_refresh,
            data={
                'refresh': str(refresh_token),
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['access']
        decoded = jwt.decode(
            token,
            algorithms=["HS256"],
            key='dummy_secretkey'  # get from settings_dev
        )
        self.assertEqual(decoded['device_id'], 'unique_id_for_device')

    def test_device_last_login_is_not_updated_on_token_refresh(self):
        device = Device.objects.create(
            user=self.app_user,
            device_id='unique_id_for_device'
        )

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            response = self.client.post(
                self.endpoint,
                data={
                    'username': self.app_user.username,
                    'password': 'testpassword123_tmp',
                    'device_id': 'unique_id_for_device'
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            refresh_token = response.json()['refresh']

            device.refresh_from_db()
            last_login = device.last_login
            self.assertEqual(last_login, timezone.now())

            traveller.shift(timedelta(seconds=30))

            response = self.client.post(
                self.endpoint_refresh,
                data={
                    'refresh': str(refresh_token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            device.refresh_from_db()
            self.assertEqual(device.last_login, last_login)

    def test_device_is_set_to_logged_in_on_login_if_not_logged(self):
        device = Device.objects.create(
            user=self.app_user,
            device_id='unique_id_for_device',
            registration_id='fcm_token',
            is_logged_in=False
        )
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': 'unique_id_for_device'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        self.assertEqual(device.is_logged_in, True)

    def test_device_is_set_to_not_logged_in_if_login_with_duplicated_device_id(self):
        dummy_user = TigaUser.objects.create()
        device = Device.objects.create(
            user=dummy_user,
            device_id='unique_id_for_device',
            registration_id='fcm_token',
            is_logged_in=True
        )
        # Login with same device_id but different user.
        response = self.client.post(
            self.endpoint,
            data={
                'username': self.app_user.username,
                'password': 'testpassword123_tmp',
                'device_id': 'unique_id_for_device'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        self.assertEqual(device.is_logged_in, False)

    def test_access_token_verify_return_401_after_expiration(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
            token = token_class.for_user(self.app_user)

            # Access token
            response = self.client.post(
                self.endpoint_verify,
                data={
                    'token': str(token.access_token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            traveller.shift(token.access_token.lifetime + timedelta(seconds=1))

            # Access token
            response = self.client.post(
                self.endpoint_verify,
                data={
                    'token': str(token.access_token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_verify_return_401_after_expiration(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
            token = token_class.for_user(self.app_user)

            # Access token
            response = self.client.post(
                self.endpoint_verify,
                data={
                    'token': str(token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            traveller.shift(token.lifetime + timedelta(seconds=1))

            # Access token
            response = self.client.post(
                self.endpoint_verify,
                data={
                    'token': str(token),
                }
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
            is_logged_in=True
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