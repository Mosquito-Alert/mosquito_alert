from datetime import datetime, timedelta, timezone as dt_timezone
import uuid

# Create your tests here.
from django.test import override_settings
from mosquito_alert.devices.models import Device, MobileApp
from mosquito_alert.geo.models import EuropeCountry
from django.utils import timezone
from mosquito_alert.fixes.models import Fix
from mosquito_alert.identification_tasks.models import (
    ExpertReportAnnotation,
    IdentificationTask,
)
from mosquito_alert.notifications.models import (
    Notification,
    NotificationContent,
    NotificationTopic,
    UserSubscription,
)
from mosquito_alert.reports.models import Report, ReportResponse, Photo
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.users.models import TigaUser
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APITransactionTestCase
from mosquito_alert.identification_tasks.messages import (
    other_insect_msg_dict,
    albopictus_msg_dict,
    albopictus_probably_msg_dict,
    culex_msg_dict,
)
from django.db import transaction
from django.db.utils import IntegrityError
import time_machine
import semantic_version


class ReportEndpointTestCase(APITestCase):
    def setUp(self):
        t = TigaUser.objects.create(user_UUID="00000000-0000-0000-0000-000000000000")
        Device.objects.create(
            user=t,
            active=True,
            active_session=True,
            registration_id="caM8sSvLQKmX4Iai1xGb9w:APA91bGhzu3DYeYLTh-M9elzrhK492V0J3wDrsFsUDaw13v3Wxzb_9YbemsnMTb3N7_GilKwtS73NtbywSloNRo2alfpIMu29FKszZYr6WxoNdGao6PGNRf4kS1tKCiEAZgFvMkdLkgT",
        )

        user = User.objects.create_user("dummy", "dummy@test.com", "dummypassword")
        self.token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

        # Create simple payload
        self.simple_payload = {
            "version_UUID": str(uuid.uuid4()),
            "version_number": 0,
            "user": str(t.user_UUID),
            "report_id": "test",
            "phone_upload_time": timezone.now().isoformat(),
            "creation_time": timezone.now().isoformat(),
            "version_time": timezone.now().isoformat(),
            "type": "bite",
            "location_choice": "current",
            "current_location_lat": 41.67419000,  # Blanes
            "current_location_lon": 2.79036000,  # Blanes
            "selected_location_lat": 28.291565,  # Tenerife
            "selected_location_lon": -16.629129,  # Tenerife
            "package_name": "testapp",
            "package_version": "99",
            "responses": [],
            "device_manufacturer": "test",
            "device_model": "test",
            "os": "test",
            "os_version": "99",
            "app_language": "en",
        }

    def _test_datetime_field_is_corrected_if_not_POST_with_timezone(self, fieldname):
        self.assertEqual(Report.objects.all().count(), 0)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921",
                    "location_choice": "current",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=14,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

        # Case selected with current location set -> use current location for TZ
        Report.objects.all().delete()
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921",
                    "location_choice": "selected",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=14,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

        # Case selected with current location NOT set -> use selected location for TZ
        Report.objects.all().delete()
        payload = {
            **self.simple_payload,
            **{
                fieldname: "2023-06-08T16:11:51.503921",
                "location_choice": "selected",
            },
        }
        del payload["current_location_lat"]
        del payload["current_location_lon"]
        response = self.client.post(
            "/api/reports/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=15,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

    def _test_datetime_field_is_kept_if_POST_with_timezone(self, fieldname):
        self.assertEqual(Report.objects.all().count(), 0)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921Z",
                    "location_choice": "current",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

        # Case selected with current location set -> use current location for TZ
        Report.objects.all().delete()
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921Z",
                    "location_choice": "selected",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

        # Case selected with current location NOT set -> use selected location for TZ
        Report.objects.all().delete()
        payload = {
            **self.simple_payload,
            **{
                fieldname: "2023-06-08T16:11:51.503921Z",
                "location_choice": "selected",
            },
        }
        del payload["current_location_lat"]
        del payload["current_location_lon"]
        response = self.client.post(
            "/api/reports/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

    def _test_datetime_field_is_kept_if_POST_without_latlon(self, fieldname):
        self.assertEqual(Report.objects.all().count(), 0)

        # Without timezone
        payload = {
            **self.simple_payload,
            **{
                fieldname: "2023-06-08T16:11:51.503921",  # No timezone set
                "location_choice": "current",
            },
        }
        del payload["current_location_lat"]
        del payload["current_location_lon"]
        response = self.client.post(
            "/api/reports/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

        # With timezone
        Report.objects.all().delete()

        payload = {
            **self.simple_payload,
            **{
                fieldname: "2023-06-08T16:11:51.503921Z",  # With timezone set
                "location_choice": "current",
            },
        }
        del payload["current_location_lat"]
        del payload["current_location_lon"]
        response = self.client.post(
            "/api/reports/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

    def _test_datetime_field_is_kept_if_version_number_not_0(self, fieldname):
        # Creating a Report that will be deleted using the API
        _ = self.client.post(
            "/api/reports/",
            self.simple_payload,
            format="json",
        )

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{fieldname: "2024-01-01T01:00:00", "version_number": -1},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime.fromisoformat(self.simple_payload.get(fieldname)),
        )

    def test_version_time_is_corrected_if_not_POST_with_timezone(self):
        self._test_datetime_field_is_corrected_if_not_POST_with_timezone(
            fieldname="version_time"
        )

    def test_version_time_is_kept_if_POST_with_timezone(self):
        self._test_datetime_field_is_kept_if_POST_with_timezone(
            fieldname="version_time"
        )

    def test_version_time_is_kept_if_POST_without_latlon(self):
        self._test_datetime_field_is_kept_if_POST_without_latlon(
            fieldname="version_time"
        )

    def test_creation_time_is_corrected_if_not_POST_with_timezone(self):
        self._test_datetime_field_is_corrected_if_not_POST_with_timezone(
            fieldname="creation_time"
        )

    def test_creation_time_is_kept_if_POST_with_timezone(self):
        self._test_datetime_field_is_kept_if_POST_with_timezone(
            fieldname="creation_time"
        )

    def test_creation_time_is_kept_if_POST_without_latlon(self):
        self._test_datetime_field_is_kept_if_POST_without_latlon(
            fieldname="creation_time"
        )

    def test_phone_upload_time_is_corrected_if_not_POST_with_timezone(self):
        self._test_datetime_field_is_corrected_if_not_POST_with_timezone(
            fieldname="phone_upload_time"
        )

    def test_phone_upload_time_is_kept_if_POST_with_timezone(self):
        self._test_datetime_field_is_kept_if_POST_with_timezone(
            fieldname="phone_upload_time"
        )

    def test_phone_upload_time_is_kept_if_POST_without_latlon(self):
        self._test_datetime_field_is_kept_if_POST_without_latlon(
            fieldname="phone_upload_time"
        )

    def test_phone_upload_time_is_kept_when_version_number_is_not_0(self):
        self._test_datetime_field_is_kept_if_version_number_not_0(
            fieldname="phone_upload_time"
        )

    def test_creation_time_is_kept_when_version_number_is_not_0(self):
        self._test_datetime_field_is_kept_if_version_number_not_0(
            fieldname="creation_time"
        )

    def test_version_time_is_kept_when_upload_diff_is_gt_1day(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_time": "2024-01-05T01:00:00Z",
                    "phone_upload_time": "2024-01-01T00:00:00Z",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, "version_time"),
            datetime(
                year=2024,
                month=1,
                day=5,
                hour=1,
                minute=0,
                second=0,
                tzinfo=dt_timezone.utc,
            ),
        )

    def test_user_locale_is_updated_according_to_app_language(self):
        user = TigaUser.objects.create(locale="en")
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "user": str(user.pk),
                    "app_language": "es",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user.refresh_from_db()

        self.assertEqual(user.locale, "es")

    def test_mobile_app_fk_is_created_if_not_exist(self):
        self.assertEqual(
            MobileApp.objects.filter(
                package_name="testapp", package_version="0.100.0+legacy"
            ).count(),
            0,
        )
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "package_name": "testapp",
                    "package_version": "100",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            MobileApp.objects.filter(
                package_name="testapp", package_version="0.100.0+legacy"
            ).count(),
            1,
        )
        mobile_app = MobileApp.objects.get(
            package_name="testapp", package_version="0.100.0+legacy"
        )
        self.assertEqual(mobile_app.package_name, "testapp")
        self.assertEqual(
            mobile_app.package_version,
            semantic_version.Version(major=0, minor=100, patch=0, build=("legacy",)),
        )

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertEqual(report.mobile_app, mobile_app)

    def test_mobile_app_fk_is_set_correctly_if_exist(self):
        mobile_app = MobileApp.objects.create(
            package_name="testapp", package_version="0.100.0+legacy"
        )
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "package_name": "testapp",
                    "package_version": "100",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertEqual(report.mobile_app, mobile_app)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_device_is_created_if_not_exist_on_new_report(self):
        user = TigaUser.objects.create(locale="en")

        self.assertEqual(Device.objects.filter(user=user).count(), 0)
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "user": str(user.pk),
                    "device_manufacturer": "test_make",
                    "device_model": "test_model",
                    "os": "testOs",
                    "os_version": "testVersion",
                    "os_language": "es-ES",
                    "package_name": "testapp",
                    "package_version": "100",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        device = Device.objects.get(user=report.user)

        self.assertEqual(device.manufacturer, "test_make")
        self.assertEqual(device.model, "test_model")
        self.assertEqual(device.os_name, "testOs")
        self.assertEqual(device.os_version, "testVersion")
        self.assertEqual(device.os_locale, "es-ES")
        self.assertEqual(device.mobile_app, report.mobile_app)
        self.assertEqual(device.active_session, True)
        self.assertEqual(device.last_login, timezone.now())

        self.assertIsNone(device.registration_id)
        self.assertEqual(device.active, False)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_device_with_model_null_is_updated_on_new_report(self):
        user = TigaUser.objects.create(locale="en")
        fcm_token = "fcm_random_token"
        # This is a device that was created using /api/token/ endpoint
        device = Device.objects.create(
            registration_id=fcm_token,
            user=user,
            model=None,
            active=True,
            active_session=True,
            last_login=timezone.now() - timedelta(days=1),
        )
        self.assertIsNone(device.model)
        mobile_app = MobileApp.objects.create(
            package_name="testapp", package_version="0.100.0+legacy"
        )

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "user": str(user.pk),
                    "device_manufacturer": "test_make",
                    "device_model": "test_model",
                    "os": "testOs",
                    "os_version": "testVersion",
                    "os_language": "es-ES",
                    "package_name": "testapp",
                    "package_version": "100",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        device.refresh_from_db()

        self.assertEqual(device.manufacturer, "test_make")
        self.assertEqual(device.model, "test_model")
        self.assertEqual(device.os_name, "testOs")
        self.assertEqual(device.os_version, "testVersion")
        self.assertEqual(device.os_locale, "es-ES")
        self.assertEqual(device.mobile_app, mobile_app)
        self.assertTrue(device.active_session)
        self.assertTrue(device.active)
        self.assertEqual(device.last_login, timezone.now())
        self.assertEqual(device.registration_id, fcm_token)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_device_with_model_is_updated_on_new_report(self):
        user = TigaUser.objects.create(locale="en")
        device = Device.objects.create(
            registration_id="fcm_random_token",
            user=user,
            model="test_model",
            active=True,
            active_session=True,
            last_login=timezone.now() - timedelta(days=1),
        )
        self.assertIsNone(device.type)
        mobile_app = MobileApp.objects.create(
            package_name="testapp", package_version="0.100.0+legacy"
        )

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "user": str(user.pk),
                    "device_manufacturer": "test_make",
                    "device_model": "test_model",
                    "os": "testOs",
                    "os_version": "testVersion",
                    "os_language": "es-ES",
                    "package_name": "testapp",
                    "package_version": "100",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        device.refresh_from_db()

        self.assertEqual(device.manufacturer, "test_make")
        self.assertEqual(device.model, "test_model")
        self.assertEqual(device.os_name, "testOs")
        self.assertEqual(device.os_version, "testVersion")
        self.assertEqual(device.os_locale, "es-ES")
        self.assertEqual(device.mobile_app, mobile_app)
        self.assertEqual(device.active_session, True)
        self.assertEqual(device.last_login, timezone.now())

    def test_POST_with_not_valid_version_number_raise_400(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": -2,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_POST_without_version_number_raise_400(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": None,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_POST_without_version_UUID_raise_400(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_UUID": None,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_POST_with_version_number_0_create_new_reports(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertEqual(report.version_number, 0)

    def test_POST_with_version_number_0_raise_409_if_report_with_same_version_UUID_exists(
        self,
    ):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_POST_with_version_number_1_update_existing_report(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": 0,
                    "location_choice": "current",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": 1,
                    "location_choice": "selected",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertEqual(report.version_number, 0)
        self.assertEqual(report.location_choice, "selected")

    def test_POST_with_version_number_neg1_soft_delete_existing_report(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertFalse(report.deleted)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": -1,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        report.refresh_from_db()
        self.assertTrue(report.deleted)

    def test_POST_with_version_number_not0_raise_404_if_report_not_found(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "report_id": "test",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "version_number": 1,
                    "report_id": "test2",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_note_with_tags_set_tags_field(self):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    "note": "test #tag1 note #tag1 #tag2",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])
        self.assertEqual(
            list(report.tags.values_list("name", flat=True)), ["tag1", "tag2"]
        )


class FixEndpointTestCase(APITestCase):
    def setUp(self):
        user = User.objects.create_user("dummy", "dummy@test.com", "dummypassword")
        self.token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

        # Create simple payload
        self.simple_payload = {
            "user_coverage_uuid": str(uuid.uuid4()),
            "fix_time": timezone.now().isoformat(),
            "phone_upload_time": timezone.now().isoformat(),
            "masked_lat": 41.67419000,  # Blanes
            "masked_lon": 2.79036000,  # Blanes
            "power": 0,
            "mask_size": 0,
        }

    def _test_datetime_field_is_corrected_if_not_POST_with_timezone(self, fieldname):
        self.assertEqual(Fix.objects.all().count(), 0)

        response = self.client.post(
            "/api/fixes/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        fix = Fix.objects.get(
            user_coverage_uuid=self.simple_payload["user_coverage_uuid"]
        )

        self.assertEqual(
            getattr(fix, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=14,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

    def _test_datetime_field_is_kept_if_POST_with_timezone(self, fieldname):
        self.assertEqual(Fix.objects.all().count(), 0)

        response = self.client.post(
            "/api/fixes/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2023-06-08T16:11:51.503921Z",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        fix = Fix.objects.get(
            user_coverage_uuid=self.simple_payload["user_coverage_uuid"]
        )

        self.assertEqual(
            getattr(fix, fieldname),
            datetime(
                year=2023,
                month=6,
                day=8,
                hour=16,
                minute=11,
                second=51,
                microsecond=503921,
                tzinfo=dt_timezone.utc,
            ),
        )

    def test_fix_time_is_corrected_if_not_POST_with_timezone(self):
        self._test_datetime_field_is_corrected_if_not_POST_with_timezone(
            fieldname="fix_time"
        )

    def test_fix_time_is_kept_if_POST_with_timezone(self):
        self._test_datetime_field_is_kept_if_POST_with_timezone(fieldname="fix_time")

    def test_phone_upload_time_is_corrected_if_not_POST_with_timezone(self):
        self._test_datetime_field_is_corrected_if_not_POST_with_timezone(
            fieldname="phone_upload_time"
        )

    def test_phone_upload_time_is_kept_if_POST_with_timezone(self):
        self._test_datetime_field_is_kept_if_POST_with_timezone(
            fieldname="phone_upload_time"
        )


class NotificationTestCase(APITestCase):
    fixtures = [
        "auth_group.json",
        "reritja_like.json",
        "awardcategory.json",
        "europe_countries.json",
        "nuts_europe.json",
        "taxon.json",
    ]

    def setUp(self):
        t = TigaUser.objects.create(user_UUID="00000000-0000-0000-0000-000000000000")
        Device.objects.create(
            user=t,
            active=True,
            active_session=True,
            registration_id="caM8sSvLQKmX4Iai1xGb9w:APA91bGhzu3DYeYLTh-M9elzrhK492V0J3wDrsFsUDaw13v3Wxzb_9YbemsnMTb3N7_GilKwtS73NtbywSloNRo2alfpIMu29FKszZYr6WxoNdGao6PGNRf4kS1tKCiEAZgFvMkdLkgT",
        )

        self.regular_user = t
        non_naive_time = timezone.now()
        a = 1
        for country in EuropeCountry.objects.all():
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a),
                version_number=0,
                user_id="00000000-0000-0000-0000-000000000000",
                phone_upload_time=non_naive_time,
                server_upload_time=non_naive_time,
                creation_time=non_naive_time,
                version_time=non_naive_time,
                location_choice="current",
                current_location_lon=point_on_surface.x,
                current_location_lat=point_on_surface.y,
                type="adult",
            )
            r.save()
            p = Photo.objects.create(report=r, photo="./testdata/splash.png")
            p.save()
            a = a + 1
        self.reritja_user = User.objects.get(pk=25)

        t1 = NotificationTopic(
            topic_code="global", topic_description="This is the global topic"
        )
        t1.save()
        self.global_topic = t1

        t2 = NotificationTopic(
            topic_code="some_topic", topic_description="This is a topic, not the global"
        )
        t2.save()
        self.some_topic = t2

    def test_auto_notification_report_is_issued_and_readable_via_api(self):
        r = Report.objects.get(pk="1")
        _ = Photo.objects.create(report=r, photo="./testdata/splash.png")
        identification_task = r.identification_task

        # this should cause send_finished_identification_task_notification to be called
        aedes_albopictus = Taxon.objects.get(pk=112)
        anno_reritja = ExpertReportAnnotation.objects.create(
            user=self.reritja_user,
            identification_task=identification_task,
            taxon=aedes_albopictus,
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
        )
        anno_reritja.save()

        # there should be a new Notification
        self.assertEqual(Notification.objects.all().count(), 1)
        # with its associated NotificationContent
        self.assertEqual(NotificationContent.objects.all().count(), 1)

        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get(
            "/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000"
        )
        self.client.logout()
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # it should answer with just one notification
        self.assertEqual(len(response.data), 1)

    def test_ack_notification(self):
        r = Report.objects.get(pk="1")
        _ = Photo.objects.create(report=r, photo="./testdata/splash.png")
        identification_task = r.identification_task

        # this should cause send_finished_identification_task_notification to be called
        aedes_albopictus = Taxon.objects.get(pk=112)
        anno_reritja = ExpertReportAnnotation.objects.create(
            user=self.reritja_user,
            identification_task=identification_task,
            taxon=aedes_albopictus,
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
        )
        anno_reritja.save()

        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get(
            "/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000"
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # and the notification should be unread
        self.assertEqual(response.data[0]["acknowledged"], False)
        # mark it as read
        notification_id = response.data[0]["id"]
        response = self.client.delete(
            "/api/mark_notif_as_ack/?user=00000000-0000-0000-0000-000000000000&notif="
            + str(notification_id)
        )
        # should respond no content
        self.assertEqual(response.status_code, 204)
        # try again
        response = self.client.get(
            "/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000"
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # and the notification should be read
        self.assertEqual(response.data[0]["acknowledged"], True)
        self.client.logout()

    def test_subscribe_user_to_topic(self):
        self.client.force_authenticate(user=self.reritja_user)
        code = self.some_topic.topic_code
        user = self.regular_user.user_UUID
        response = self.client.post(
            "/api/subscribe_to_topic/?code=" + code + "&user=" + user
        )
        # should respond created
        self.assertEqual(response.status_code, 201)
        # try resubscribing
        response = None
        # this strange stuff is here because resubscribing throws an IntegrityError exception, which locks
        # the database and breaks subsequent tests. To avoid this, we add the with transaction, which rolls back
        # in case of exception
        try:
            with transaction.atomic():
                response = self.client.post(
                    "/api/subscribe_to_topic/?code=" + code + "&user=" + user
                )
        except IntegrityError:
            pass
        # should fail
        self.assertEqual(response.status_code, 400)
        self.client.logout()

    def test_list_user_subscriptions(self):
        self.client.force_authenticate(user=self.reritja_user)
        user = self.regular_user.user_UUID
        # we make up some topics
        n1 = NotificationTopic(
            topic_code="ru", topic_description="This is a test topic"
        )
        n1.save()
        n2 = NotificationTopic(
            topic_code="es", topic_description="This is a test topic"
        )
        n2.save()
        n3 = NotificationTopic(
            topic_code="en", topic_description="This is a test topic"
        )
        n3.save()
        topics = [n1, n2, n3]
        for t in topics:
            response = self.client.post(
                "/api/subscribe_to_topic/?code=" + t.topic_code + "&user=" + user
            )
            # should respond created
            self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/topics_subscribed/?user=" + user)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should be subscribed to t, n1, n2 and n3
        self.assertEqual(len(response.data), 3)
        self.client.logout()

    def test_user_sees_notifications_sent_to_global_topic(self):
        nc = NotificationContent(
            body_html="<p>Notification Body</p>",
            title="Notification title",
        )
        nc.save()
        n = Notification(expert=self.reritja_user, notification_content=nc)
        n.save()

        UserSubscription.objects.get_or_create(
            user=self.regular_user, topic=self.global_topic
        )

        # send notif to global topic
        n.send_to_topic(topic=self.global_topic)

        # the regular user should see this notification
        some_user = self.regular_user
        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get(
            "/api/user_notifications/?user_id=" + some_user.user_UUID
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # acknowledge the notification
        response = self.client.delete(
            "/api/mark_notif_as_ack/?user=00000000-0000-0000-0000-000000000000&notif="
            + str(n.id)
        )
        # should respond no content
        self.assertEqual(response.status_code, 204)
        # now the notification should be acknowledged
        response = self.client.get(
            "/api/user_notifications/?user_id=" + some_user.user_UUID
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # AND it should be ack=True
        self.assertEqual(response.data[0]["acknowledged"], True)
        self.client.logout()

    def test_subscription_and_unsubscription(self):
        nc = NotificationContent(
            body_html="<p>Notification Body</p>",
            title="Notification title",
        )
        nc.save()
        n = Notification(expert=self.reritja_user, notification_content=nc)
        n.save()

        self.client.force_authenticate(user=self.reritja_user)
        # subscribe user to regular topic
        response = self.client.post(
            "/api/subscribe_to_topic/?code="
            + self.some_topic.topic_code
            + "&user="
            + self.regular_user.user_UUID
        )
        # should respond created
        self.assertEqual(response.status_code, 201)

        # send notif to regular topic
        n.send_to_topic(topic=self.some_topic)

        # list notifications for regular user again
        response = self.client.get(
            "/api/user_notifications/?user_id=" + self.regular_user.user_UUID
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # only the topic notification should be available
        self.assertEqual(len(response.data), 1)

        # now, unsubscribe!
        response = self.client.post(
            "/api/unsub_from_topic/?code="
            + self.some_topic.topic_code
            + "&user="
            + self.regular_user.user_UUID
        )
        # response should be no content
        self.assertEqual(response.status_code, 204)

        # list notifications for regular user again!
        response = self.client.get(
            "/api/user_notifications/?user_id=" + self.regular_user.user_UUID
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # notifications are still available
        self.assertEqual(len(response.data), 1)
        self.client.logout()

    def test_direct_notifs_and_topic_sort_okay(self):
        some_user = self.regular_user
        nc1 = NotificationContent(
            body_html="<p>Notification Body 1</p>",
            title="Notification title 1",
        )
        nc1.save()

        nc2 = NotificationContent(
            body_html="<p>Notification Body 2</p>",
            title="Notification title 2",
        )
        nc2.save()

        # FIRST direct NOTIFICATION
        n1 = Notification(expert=self.reritja_user, notification_content=nc1)
        n1.save()

        # send notif to user
        n1.send_to_user(user=some_user)

        # Ensure user is subscribed to global topic
        UserSubscription.objects.get_or_create(user=some_user, topic=self.global_topic)

        # GLOBAL notification
        n3 = Notification(expert=self.reritja_user, notification_content=nc1)
        n3.save()
        # send notif to global topic
        n3.send_to_topic(topic=self.global_topic)

        # SECOND direct  NOTIFICATION
        n2 = Notification(expert=self.reritja_user, notification_content=nc2)
        n2.save()

        # send notif to user
        n2.send_to_user(user=some_user)

        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get(
            "/api/user_notifications/?user_id=" + some_user.user_UUID
        )
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should receive both direct notifications and global
        self.assertEqual(len(response.data), 3)
        # most recent should be 2
        self.assertEqual(response.data[0]["expert_comment"], nc2.title_en)
        # 0 should be more recent than 1
        self.assertTrue(
            response.data[0]["date_comment"] > response.data[1]["date_comment"]
        )
        # 1 should be more recent than 2
        self.assertTrue(
            response.data[1]["date_comment"] > response.data[2]["date_comment"]
        )
        self.client.logout()


class AnnotateCoarseTestCase(APITestCase):
    fixtures = [
        "photos.json",
        "users.json",
        "europe_countries.json",
        "tigausers.json",
        "reports.json",
        "auth_group.json",
        "movelab_like.json",
        "taxon.json",
    ]

    @classmethod
    def setUpTestData(cls):
        cls.random_user = User.objects.create(
            username="random_user", password="random_password"
        )

    def test_annotate_taken(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        _ = Photo.objects.create(report=r)  # Needed to create an identification task
        annos = ExpertReportAnnotation.objects.filter(
            identification_task=r.identification_task
        )
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Give report to one expert
        _ = ExpertReportAnnotation.objects.create(
            user=self.random_user, identification_task=r.identification_task
        )
        # try to annotate
        data = {
            "report_id": "00042354-ffd6-431e-af1e-cecf55e55364",
            "taxon_id": str(112),  # aedes albopictus
        }
        response = self.client.post("/api/annotate_coarse/", data=data)
        self.assertEqual(
            response.status_code,
            400,
            "Response should be 400, is {0}".format(response.status_code),
        )
        # opcode should be -1
        self.assertEqual(
            response.data["opcode"],
            -1,
            "Opcode should be -1, is {0}".format(response.data["opcode"]),
        )

    def test_flip_taken(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        _ = Photo.objects.create(
            report=r_adult
        )  # Needed to create an identification task
        annos = ExpertReportAnnotation.objects.filter(
            identification_task=r_adult.identification_task
        )
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Give report to one expert
        r_adult.identification_task.assign_to_user(self.random_user)
        # try to annotate
        data = {
            "report_id": r_adult.version_UUID,
            "flip_to_type": "site",
            "flip_to_subtype": "storm_drain_water",
        }
        response = self.client.patch("/api/flip_report/", data=data)
        self.assertEqual(
            response.status_code,
            400,
            "Response should be 400, is {0}".format(response.status_code),
        )
        # opcode should be -1
        self.assertEqual(
            response.data["opcode"],
            -1,
            "Opcode should be -1, is {0}".format(response.data["opcode"]),
        )

    def test_annotate_coarse(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        _ = Photo.objects.create(report=r)  # Needed to create an identification task
        r.refresh_from_db()
        annos = ExpertReportAnnotation.objects.filter(
            identification_task=r.identification_task
        )
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Let's change that
        for t_id in [1, 10, 112]:
            data = {
                "report_id": "00042354-ffd6-431e-af1e-cecf55e55364",
                "taxon_id": str(t_id),
                "confidence": ExpertReportAnnotation.ConfidenceCategory.PROBABLY,
            }
            response = self.client.post("/api/annotate_coarse/", data=data)
            self.assertEqual(
                response.status_code,
                200,
                "Response should be 200, is {0}".format(response.status_code),
            )
            r.refresh_from_db()
            self.assertEqual(r.identification_task.taxon_id, t_id)
            self.assertEqual(
                r.identification_task.confidence, float(data["confidence"])
            )
            notif = Notification.objects.get(report=r)
            notif_content = notif.notification_content
            if t_id == 1:  # other species
                self.assertTrue(
                    other_insect_msg_dict["es"] in notif_content.body_html_es,
                    "Report classified as other species associated notification should contain other insect message, it does not",
                )
                #'no pertenece a la familia de los Culícidos'
            elif t_id == 10:  # culex sp.
                self.assertTrue(
                    culex_msg_dict["es"] in notif_content.body_html_es,
                    "Report classified as culex associated notification should contain culex message, it does not",
                )
                #'no podemos asegurar totalmente que sea un Culex'
            elif t_id == 112:  # aedes albopictus
                self.assertTrue(
                    albopictus_probably_msg_dict["es"] in notif_content.body_html_es,
                    "Report classified as albopictus associated notification should contain probably albopictus message, it does not",
                )
                #'Has conseguido que se pueda identificar perfectamente el mosquito tigre'
            Notification.objects.filter(report=r).delete()
            for annotation in ExpertReportAnnotation.objects.filter(
                identification_task=r.identification_task
            ):
                annotation.delete()
        # test also definitely albopictus
        data = {
            "report_id": "00042354-ffd6-431e-af1e-cecf55e55364",
            "taxon_id": "112",
        }
        data["confidence"] = (
            ExpertReportAnnotation.ConfidenceCategory.DEFINITELY
        )  # Definitely
        response = self.client.post("/api/annotate_coarse/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )
        r.refresh_from_db()
        self.assertEqual(r.identification_task.taxon_id, 112)
        self.assertEqual(r.identification_task.confidence, float(data["confidence"]))
        notif = Notification.objects.get(report=r)
        notif_content = notif.notification_content
        self.assertTrue(
            albopictus_msg_dict["es"] in notif_content.body_html_es,
            "Report classified as albopictus associated notification should contain definitely albopictus message, it does not",
        )
        Notification.objects.filter(report=r).delete()
        ExpertReportAnnotation.objects.filter(
            identification_task=r.identification_task
        ).delete()

    def test_flip_adult_to_adult(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk="004D5A85-1D88-4170-A253-DABF30669EBE")
        self.assertEqual(
            r_adult.type,
            "adult",
            "Report type should be adult, is {0}".format(r_adult.type),
        )
        data = {"report_id": r_adult.version_UUID, "flip_to_type": "adult"}
        response = self.client.patch("/api/flip_report/", data=data)
        self.assertEqual(
            response.status_code,
            400,
            "Response should be 400, is {0}".format(response.status_code),
        )
        self.assertEqual(
            response.data["opcode"],
            -2,
            "Opcode should be -2, is {0}".format(response.data["opcode"]),
        )

    def test_flip_site_to_site(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_site = Report.objects.get(pk="007106f1-6003-4cf5-b049-8f6533a90813")
        self.assertEqual(
            r_site.type,
            "site",
            "Report type should be site, is {0}".format(r_site.type),
        )
        data = {
            "report_id": r_site.version_UUID,
            "flip_to_type": "site",
            "flip_to_subtype": "storm_drain_water",
        }
        response = self.client.patch("/api/flip_report/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )
        r_site_reloaded = Report.objects.get(pk="007106f1-6003-4cf5-b049-8f6533a90813")
        n_responses = ReportResponse.objects.filter(report=r_site_reloaded).count()
        self.assertTrue(
            n_responses == 2,
            "Number of responses should be 2, is {0}".format(n_responses),
        )
        self.assertEqual(r_site_reloaded.type, Report.TYPE_SITE)
        self.assertTrue(r_site_reloaded.flipped, "Report should be marked as flipped")
        self.assertTrue(
            r_site_reloaded.flipped_to == "site#site",
            "Report should be marked as flipped from site to site, field has value of {0}".format(
                r_site_reloaded.flipped_to
            ),
        )
        self.assertEqual(
            r_site_reloaded.breeding_site_type, Report.BreedingSiteType.STORM_DRAIN
        )
        self.assertTrue(r_site_reloaded.breeding_site_has_water)

    def test_flip(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        _ = Photo.objects.create(report=r_adult)

        self.assertEqual(IdentificationTask.objects.filter(report=r_adult).count(), 1)

        # Check report types
        self.assertEqual(
            r_adult.type,
            "adult",
            "Report type should be adult, is {0}".format(r_adult.type),
        )
        r_site = Report.objects.get(pk="00042fb1-408f-4da4-898d-4331a9ec3129")
        _ = Photo.objects.create(report=r_site)

        self.assertEqual(IdentificationTask.objects.filter(report=r_site).count(), 0)
        self.assertEqual(
            r_site.type,
            "site",
            "Report type should be site, is {0}".format(r_site.type),
        )
        # flip adult to storm drain water
        data = {
            "report_id": r_adult.version_UUID,
            "flip_to_type": "site",
            "flip_to_subtype": "storm_drain_water",
        }
        response = self.client.patch("/api/flip_report/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )
        adult_reloaded = Report.objects.get(pk=r_adult.version_UUID)
        self.assertTrue(
            adult_reloaded.type == Report.TYPE_SITE,
            "Report type should have changed to site, is {0}".format(
                adult_reloaded.type
            ),
        )
        self.assertEqual(
            adult_reloaded.breeding_site_type, Report.BreedingSiteType.STORM_DRAIN
        )
        self.assertTrue(adult_reloaded.breeding_site_has_water)
        self.assertEqual(IdentificationTask.objects.filter(report=r_adult).count(), 0)

        n_responses = ReportResponse.objects.filter(report=adult_reloaded).count()
        self.assertTrue(
            n_responses == 2,
            "Number of responses should be 2, is {0}".format(n_responses),
        )
        self.assertEqual(adult_reloaded.type, Report.TYPE_SITE)
        self.assertTrue(adult_reloaded.flipped, "Report should be marked as flipped")
        self.assertTrue(
            adult_reloaded.flipped_to == "adult#site",
            "Report should be marked as flipped from adult to site, field has value of {0}".format(
                adult_reloaded.flipped_to
            ),
        )
        try:
            _ = ReportResponse.objects.get(
                report=adult_reloaded, question_id="12", answer_id="121"
            )
        except Exception:
            self.assertTrue(False, "Report does not have the storm drain response")
        try:
            _ = ReportResponse.objects.get(
                report=adult_reloaded, question_id="10", answer_id="101"
            )
        except Exception:
            self.assertTrue(False, "Report does not have the water response")
        # flip site to adult
        data = {"report_id": r_site.version_UUID, "flip_to_type": "adult"}
        response = self.client.patch("/api/flip_report/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )
        site_reloaded = Report.objects.get(pk=r_site.version_UUID)
        self.assertTrue(
            site_reloaded.type == Report.TYPE_ADULT,
            "Report type should have changed to adult, is {0}".format(
                site_reloaded.type
            ),
        )

        n_responses = ReportResponse.objects.filter(report=site_reloaded).count()
        self.assertTrue(
            n_responses == 0,
            "Number of responses should be 0, is {0}".format(n_responses),
        )
        self.assertEqual(site_reloaded.type, Report.TYPE_ADULT)
        self.assertTrue(site_reloaded.flipped, "Report should be marked as flipped")
        self.assertTrue(
            site_reloaded.flipped_to == "site#adult",
            "Report should be marked as flipped from site to adult, field has value of {0}".format(
                adult_reloaded.flipped_to
            ),
        )
        # print(site_reloaded.flipped_on)
        self.assertEqual(IdentificationTask.objects.filter(report=r_site).count(), 1)

    def test_hide(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        self.assertTrue(not r_adult.hide, "Report should be visible, is not")
        data = {"report_id": r_adult.version_UUID, "hide": "true"}
        response = self.client.patch("/api/hide_report/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )
        r_adult_reloaded = Report.objects.get(pk="00042354-ffd6-431e-af1e-cecf55e55364")
        self.assertTrue(r_adult_reloaded.hide, "Report should be hidden, is not")

    def test_quick_upload(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_site = Report.objects.get(pk="00042fb1-408f-4da4-898d-4331a9ec3129")
        self.assertFalse(r_site.published)

        data = {"report_id": r_site.version_UUID}
        response = self.client.post("/api/quick_upload_report/", data=data)
        self.assertEqual(
            response.status_code,
            200,
            "Response should be 200, is {0}".format(response.status_code),
        )

        r_site.refresh_from_db()
        self.assertTrue(r_site.published)


class ApiTokenViewTest(APITestCase):
    ENDPOINT = "/api/token/"

    @classmethod
    def setUpTestData(cls):
        cls.mobile_user = User.objects.create_user(username="mobile_test")
        cls.tiga_user = TigaUser.objects.create()

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_post_fcm_token_creates_new_device_if_no_device_exist(self):
        self.client.force_authenticate(user=self.mobile_user)

        fcm_token = "randomFCMtoken_test"

        # Define the query parameters
        query_params = {"user_id": self.tiga_user.pk, "token": fcm_token}
        # Construct the URL with query parameters
        url = (
            self.ENDPOINT
            + "?"
            + "&".join(f"{key}={value}" for key, value in query_params.items())
        )

        # Make the POST request
        response = self.client.post(url, format="json")

        # Assert response status code or other checks
        self.assertEqual(response.status_code, 200)

        # Check the response JSON
        expected_response = {"token": fcm_token}
        self.assertJSONEqual(response.content, expected_response)

        # Check that exist an active Device for the user with the registartion_id
        device = Device.objects.get(user=self.tiga_user, registration_id=fcm_token)
        self.assertTrue(device.active)
        self.assertTrue(device.active_session)
        self.assertEqual(device.last_login, timezone.now())
        self.assertIsNone(device.model)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_post_fcm_token_updates_device_with_same_registration_id(self):
        self.client.force_authenticate(user=self.mobile_user)

        fcm_token = "randomFCMtoken_test"

        device = Device.objects.create(
            user=self.tiga_user,
            registration_id=fcm_token,
            active=True,
            active_session=True,
            last_login=timezone.now() - timedelta(days=1),
        )

        # Define the query parameters
        query_params = {"user_id": self.tiga_user.pk, "token": fcm_token}
        # Construct the URL with query parameters
        url = (
            self.ENDPOINT
            + "?"
            + "&".join(f"{key}={value}" for key, value in query_params.items())
        )

        # Make the POST request
        response = self.client.post(url, format="json")
        # Assert response status code or other checks
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Device.objects.filter(user=self.tiga_user).count(), 1)
        # Check that exist an active Device for the user with the registartion_id
        device.refresh_from_db()

        self.assertEqual(device.registration_id, fcm_token)
        self.assertTrue(device.active)
        self.assertTrue(device.active_session)
        self.assertEqual(device.last_login, timezone.now())


class ApiUsersViewTest(APITransactionTestCase):
    ENDPOINT = "/api/users/"

    def setUp(self):
        self.mobile_user = User.objects.create_user(username="mobile_test")
        # Needed to test user subscription does not raise.
        self.global_topic = NotificationTopic.objects.create(topic_code="global")
        self.language_topic = NotificationTopic.objects.create(topic_code="en")

    @override_settings(DEFAULT_TIGAUSER_PASSWORD="DEFAULT_PASSWORD_FOR_TESTS")
    def test_POST_new_user(self):
        self.client.force_authenticate(user=self.mobile_user)
        new_user_uuid = uuid.uuid4()

        request_payload = {
            "user_UUID": str(new_user_uuid)  # The mobile is setting the user uuid.
        }
        response = self.client.post(
            self.ENDPOINT,
            request_payload,
            format="json",
        )

        # Check the status code
        self.assertEqual(response.status_code, 201)

        # Check the response JSON
        expected_response = {"user_UUID": str(new_user_uuid)}
        self.assertJSONEqual(response.content, expected_response)

        user = TigaUser.objects.get(pk=str(new_user_uuid))

        self.assertTrue(user.check_password("DEFAULT_PASSWORD_FOR_TESTS"))

        # Check if the user is subscribed to the global topic
        self.assertTrue(
            UserSubscription.objects.filter(user=user, topic=self.global_topic).exists()
        )

        # Check if the user is subscribed to the language topic ('en')
        self.assertTrue(
            UserSubscription.objects.filter(
                user=user, topic=self.language_topic
            ).exists()
        )

    def test_POST_new_user_without_providing_uuid_should_return_400(self):
        self.client.force_authenticate(user=self.mobile_user)
        response = self.client.post(
            self.ENDPOINT,
            format="json",
        )
        # Check the status code
        self.assertEqual(response.status_code, 400)

    def test_POST_new_user_providing_non_uuid_should_return_400(self):
        self.client.force_authenticate(user=self.mobile_user)
        request_payload = {"user_UUID": "random_text"}
        response = self.client.post(
            self.ENDPOINT,
            request_payload,
            format="json",
        )
        # Check the status code
        self.assertEqual(response.status_code, 400)

    def test_GET_list_users_with_filter(self):
        self.client.force_authenticate(user=self.mobile_user)

        tigauser = TigaUser.objects.create()
        filter_params = {"user_UUID": str(tigauser.pk)[:10]}
        response = self.client.get(
            self.ENDPOINT,
            filter_params,
            format="json",
        )
        # Check the status code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["user_UUID"], str(tigauser.pk))
