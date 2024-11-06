from abc import abstractmethod
from datetime import timedelta
import pytest
import time_machine

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.module_loading import import_string

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.settings import api_settings

from tigaserver_app.models import TigaUser, Report

from api.tests.integration.observations.factories import create_observation_object
from api.tests.integration.breeding_sites.factories import create_breeding_site_object
from api.tests.integration.bites.factories import create_bite_object

User = get_user_model()

@pytest.fixture
def app_api_client(app_user):
    api_client = AppAPIClient()
    api_client.force_login(user=app_user)
    return api_client

# TODO: automatic user subscription on new report.

class AppAPIClient(APIClient):
    def force_login(self, user, backend=None) -> None:
        self.logout()
        return super().force_login(user, backend)

    def _login(self, user, backend=None):
        if isinstance(user, User):
            return super()._login(user, backend)
        elif isinstance(user, TigaUser):
            token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
            token = token_class.for_user(user)
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
        'timezone': 'Europe/Madrid',
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

    def test_timezone_is_save_on_report_create(self, app_api_client, data_create_request):
        if self.POST_FORMAT == 'multipart':
            pytest.skip("Skipping test for multipart format")
        # Testing here due its write_only field

        response = app_api_client.post(
            self.endpoint,
            data=data_create_request,
            format=self.POST_FORMAT
        )

        assert response.status_code == status.HTTP_201_CREATED

        report = self.queryset.get(pk=response.data.get('uuid'))

        assert str(report.phone_timezone) == data_create_request['timezone']

    def test_package_is_set_on_report_create(self, app_api_client, data_create_request):
        if self.POST_FORMAT == 'multipart':
            pytest.skip("Skipping test for multipart format")
        # Testing here due its write_only field

        response = app_api_client.post(
            self.endpoint,
            data={
                **data_create_request,
                **{
                    'package': {
                        'name': 'testapp',
                        'version': 1234,
                        'language': 'en'
                    }
                }
            },
            format=self.POST_FORMAT
        )
        assert response.status_code == status.HTTP_201_CREATED
        report = self.queryset.get(pk=response.data.get('uuid'))

        assert report.package_name == 'testapp'
        assert report.package_version == 1234
        assert report.app_language == 'en'

    def test_device_is_set_on_report_create(self, app_api_client, data_create_request):
        if self.POST_FORMAT == 'multipart':
            pytest.skip("Skipping test for multipart format")
        # Testing here due its write_only field
        response = app_api_client.post(
            self.endpoint,
            data={
                **data_create_request,
                **{
                    'device': {
                        'manufacturer': 'test_make',
                        'model': 'test_model',
                        'os': 'testOs',
                        'os_version': 'testv123',
                        'os_language': 'testen'
                    }
                }
            },
            format=self.POST_FORMAT
        )

        assert response.status_code == status.HTTP_201_CREATED

        report = self.queryset.get(pk=response.data.get('uuid'))

        assert report.device_manufacturer == 'test_make'
        assert report.device_model == 'test_model'
        assert report.os == 'testOs'
        assert report.os_version == 'testv123'
        assert report.os_language == 'testen'

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

class TokenAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.endpoint = '/api/v1/token/'
        cls.endpoint_refresh = cls.endpoint + 'refresh/'

    def setUp(self) -> None:
        self.app_user = TigaUser.objects.create(device_token=123456)
        self.app_user.set_password('testpassword123_tmp')
        self.app_user.save()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_user_last_login_is_updated_on_token_create(self):
        self.assertIsNone(self.app_user.last_login)

        response = self.client.post(
            self.endpoint,
            data={
                'uuid': self.app_user.pk,
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
