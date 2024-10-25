from datetime import timedelta
import time_machine

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.module_loading import import_string

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.settings import api_settings

from tigaserver_app.models import TigaUser, Report

User = get_user_model()

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

class ReportAPITest(APITestCase):

    client_class = AppAPIClient

    @classmethod
    def setUpTestData(cls) -> None:
        cls.endpoint = '/api/v1/reports/'

    def setUp(self) -> None:
        self.app_user = TigaUser.objects.create()

        self.data_create_request = {
            'type': 'adult',
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

    def test_user_is_set_to_authenticated_user(self):
        self.client.force_login(self.app_user)

        response = self.client.post(
            self.endpoint,
            data=self.data_create_request,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get(pk=response.data.get('uuid'))

        self.assertEqual(str(report.user.pk), str(self.app_user.pk))

    def test_timezone_is_save_on_report_create(self):
        # Testing here due its write_only field
        self.client.force_login(self.app_user)

        response = self.client.post(
            self.endpoint,
            data=self.data_create_request,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get(pk=response.data.get('uuid'))

        self.assertEqual(str(report.phone_timezone), self.data_create_request['timezone'])

    def test_package_is_set_on_report_create(self):
        # Testing here due its write_only field
        self.client.force_login(self.app_user)

        response = self.client.post(
            self.endpoint,
            data={
                **self.data_create_request,
                **{
                    'package': {
                        'name': 'testapp',
                        'version': 1234,
                        'language': 'en'
                    }
                }
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get(pk=response.data.get('uuid'))

        self.assertEqual(report.package_name, 'testapp')
        self.assertEqual(report.package_version, 1234)
        self.assertEqual(report.app_language, 'en')

    def test_device_is_set_on_report_create(self):
        # Testing here due its write_only field
        self.client.force_login(self.app_user)

        response = self.client.post(
            self.endpoint,
            data={
                **self.data_create_request,
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
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get(pk=response.data.get('uuid'))

        self.assertEqual(report.device_manufacturer, 'test_make')
        self.assertEqual(report.device_model, 'test_model')
        self.assertEqual(report.os, 'testOs')
        self.assertEqual(report.os_version, 'testv123')
        self.assertEqual(report.os_language, 'testen')

    def test_delete_method_performs_soft_delete(self):
        self.client.force_login(self.app_user)

        # Create dummy report
        response_post = self.client.post(
            self.endpoint,
            data=self.data_create_request,
            format='json'
        )
        report_uuid = response_post.data.get('uuid')

        # Delete
        response = self.client.delete(
            self.endpoint + f"{report_uuid}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        report = Report.objects.get(pk=report_uuid)
        self.assertTrue(report.deleted)

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
