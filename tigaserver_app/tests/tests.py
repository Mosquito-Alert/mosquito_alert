from django.test import TestCase
from datetime import datetime
import uuid

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import Report, EuropeCountry, ExpertReportAnnotation, Categories, Notification, NotificationContent, NotificationTopic, ReportResponse
from tigacrafting.models import BookMark
from django.core.management import call_command
import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
import tigaserver_project.settings as conf
import os
import requests
from django.utils import timezone
from tigaserver_app.models import TigaUser, Report, Photo, Fix
from tigacrafting.models import FavoritedReports
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
import io
from rest_framework import status
from tigacrafting.views import issue_notification
from tigacrafting.views import other_insect, albopictus, culex, notsure, albopictus_probably
from rest_framework.test import APIRequestFactory
from django.db import transaction
from django.db.utils import IntegrityError
import urllib
import json

'''
class PictureTestCase(APITestCase):

    def create_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        r = Report(
            version_UUID='0001a39b-742e-4928-a8ec-91f0b866a2e5',
            version_number=0,
            user_id='00000000-0000-0000-0000-000000000000',
            phone_upload_time=non_naive_time,
            server_upload_time=non_naive_time,
            creation_time=non_naive_time,
            version_time=non_naive_time,
            location_choice="current",
            type='adult',
        )
        r.save()
        user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        user.save()
        token = Token.objects.create(user=user)
        token.save()

    def test_load_picture(self):
        img = PIL.Image.open(conf.BASE_DIR + '/tigaserver_app/fixtures/test_pictures/Canon_40D.jpg')
        self.assertTrue(img is not None, msg="Failed to open image")

    def test_images_have_metadata(self):
        files = os.listdir(conf.BASE_DIR + '/tigaserver_app/fixtures/test_pictures/')
        for file in files:
            if 'jpg' in file:
                img = PIL.Image.open(conf.BASE_DIR + '/tigaserver_app/fixtures/test_pictures/' + file)
                try:
                    exif = { PIL.ExifTags.TAGS[key]: value for key, value in img._getexif().items() if key in PIL.ExifTags.TAGS or key in PIL.ExifTags.GPSTAGS }
                    self.assertTrue(len(exif) > 0, msg="Image {0} has no readable metadata!".format(file))
                except:
                    print("Image {0} has no metadata!".format(file))

    def test_metadata_removal(self):
        self.create_report_pool()
        t = Token.objects.get(user__username='john')
        auth_key = t.key
        files = os.listdir(conf.BASE_DIR + '/tigaserver_app/fixtures/test_pictures/')
        url = '/api/photos/'
        numfiles = 0
        for file in files:
            if 'jpg' in file:
                numfiles += 1
                self.client.credentials(HTTP_AUTHORIZATION='Token ' + auth_key)
                with open(conf.BASE_DIR + '/tigaserver_app/fixtures/test_pictures/' + file,'rb') as img:
                    picture_data = io.BytesIO(img.read())
                    data = { 'photo' : picture_data, 'report' : '0001a39b-742e-4928-a8ec-91f0b866a2e5' }
                    response = self.client.post(url, data, format='multipart')
                    self.assertEqual(response.status_code, status.HTTP_200_OK)

        photos = Photo.objects.filter(report__version_UUID='0001a39b-742e-4928-a8ec-91f0b866a2e5')
        self.assertEqual(len(photos), numfiles)
        for photo in photos:
            #print(photo.photo.path)
            img = PIL.Image.open(photo.photo.path)
            self.assertEqual(img._getexif(), None)

'''

class ReportEndpointTestCase(APITestCase):
    def setUp(self):
        t = TigaUser.objects.create(user_UUID="00000000-0000-0000-0000-000000000000")
        t.device_token = "caM8sSvLQKmX4Iai1xGb9w:APA91bGhzu3DYeYLTh-M9elzrhK492V0J3wDrsFsUDaw13v3Wxzb_9YbemsnMTb3N7_GilKwtS73NtbywSloNRo2alfpIMu29FKszZYr6WxoNdGao6PGNRf4kS1tKCiEAZgFvMkdLkgT"
        t.save()

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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
            ),
        )

    def _test_datetime_field_is_kept_if_version_number_not_0(self, fieldname):
        response = self.client.post(
            "/api/reports/",
            {
                **self.simple_payload,
                **{
                    fieldname: "2024-01-01T01:00:00",
                    "version_number": -1
                }
            },
            format="json"
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, fieldname),
            datetime(
                year=2024,
                month=1,
                day=1,
                hour=1,
                minute=0,
                second=0,
                tzinfo=timezone.utc
            )
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
                    "version_number": -1
                }
            },
            format="json"
        )
        self.assertEqual(response.status_code, 201)

        report = Report.objects.get(version_UUID=self.simple_payload["version_UUID"])

        self.assertEqual(
            getattr(report, 'version_time'),
            datetime(
                year=2024,
                month=1,
                day=5,
                hour=1,
                minute=0,
                second=0,
                tzinfo=timezone.utc
            )
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
                tzinfo=timezone.utc,
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
                tzinfo=timezone.utc,
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

    fixtures = ['reritja_like.json', 'awardcategory.json', 'europe_countries.json', 'nuts_europe.json']

    def setUp(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.device_token = 'caM8sSvLQKmX4Iai1xGb9w:APA91bGhzu3DYeYLTh-M9elzrhK492V0J3wDrsFsUDaw13v3Wxzb_9YbemsnMTb3N7_GilKwtS73NtbywSloNRo2alfpIMu29FKszZYr6WxoNdGao6PGNRf4kS1tKCiEAZgFvMkdLkgT'
        t.save()
        self.regular_user = t
        non_naive_time = timezone.now()
        a = 1
        for country in EuropeCountry.objects.all():
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a),
                version_number=0,
                user_id='00000000-0000-0000-0000-000000000000',
                phone_upload_time=non_naive_time,
                server_upload_time=non_naive_time,
                creation_time=non_naive_time,
                version_time=non_naive_time,
                location_choice="current",
                current_location_lon=point_on_surface.x,
                current_location_lat=point_on_surface.y,
                type='adult',
            )
            r.save()
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1
        self.reritja_user = User.objects.get(pk=25)
        c_1 = Categories.objects.create(pk=1, name="Unclassified", specify_certainty_level=False)
        c_1.save()
        c_2 = Categories.objects.create(pk=2, name="Other species", specify_certainty_level=False)
        c_2.save()
        c_3 = Categories.objects.create(pk=3, name="Aedes albopictus", specify_certainty_level=True)
        c_3.save()
        c_4 = Categories.objects.create(pk=4, name="Aedes aegypti", specify_certainty_level=True)
        c_4.save()
        c_5 = Categories.objects.create(pk=5, name="Aedes japonicus", specify_certainty_level=True)
        c_5.save()
        c_6 = Categories.objects.create(pk=6, name="Aedes koreicus", specify_certainty_level=True)
        c_6.save()
        c_7 = Categories.objects.create(pk=7, name="Complex", specify_certainty_level=False)
        c_7.save()
        c_8 = Categories.objects.create(pk=8, name="Not sure", specify_certainty_level=False)
        c_8.save()
        c_9 = Categories.objects.create(pk=9, name="Culex sp.", specify_certainty_level=True)
        c_9.save()

        self.categories = [c_1, c_2, c_3, c_4, c_5, c_6, c_7, c_8, c_9]

        self.validation_value_possible = 1
        self.validation_value_confirmed = 2

        t1 = NotificationTopic(topic_code="global", topic_description="This is the global topic")
        t1.save()
        self.global_topic = t1

        t2 = NotificationTopic(topic_code="some_topic", topic_description="This is a topic, not the global")
        t2.save()
        self.some_topic = t2


    def test_auto_notification_report_is_issued_and_readable_via_api(self):
        r = Report.objects.get(pk='1')

        # this should cause issue_notification to be called
        anno_reritja = ExpertReportAnnotation.objects.create(user=self.reritja_user, report=r, category=self.categories[2], validation_complete=True, revise=True, validation_value=self.validation_value_confirmed)
        anno_reritja.save()

        issue_notification(anno_reritja, "http://127.0.0.1:8000")

        # there should be a new Notification
        self.assertEqual(Notification.objects.all().count(), 1)
        # with its associated NotificationContent
        self.assertEqual(NotificationContent.objects.all().count(), 1)

        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get('/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000')
        self.client.logout()
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # it should answer with just one notification
        self.assertEqual(len(response.data), 1)

    def test_ack_notification(self):
        r = Report.objects.get(pk='1')

        # this should cause issue_notification to be called
        anno_reritja = ExpertReportAnnotation.objects.create(user=self.reritja_user, report=r,
                                                             category=self.categories[2], validation_complete=True,
                                                             revise=True,
                                                             validation_value=self.validation_value_confirmed)
        anno_reritja.save()

        issue_notification(anno_reritja, "http://127.0.0.1:8000")
        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get('/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000')
        # response should be ok
        self.assertEqual( response.status_code, 200 )
        # and the notification should be unread
        self.assertEqual(response.data[0]['acknowledged'], False)
        # mark it as read
        notification_id = response.data[0]['id']
        #response = self.client.post('/api/ack_notif/',{'user':'00000000-0000-0000-0000-000000000000','notification':notification_id},format='json')
        response = self.client.delete('/api/mark_notif_as_ack/?user=00000000-0000-0000-0000-000000000000&notif=' + str(notification_id))
        # should respond no content
        self.assertEqual(response.status_code, 204)
        # try again
        response = self.client.get('/api/user_notifications/?user_id=00000000-0000-0000-0000-000000000000')
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # and the notification should be read
        self.assertEqual(response.data[0]['acknowledged'], True)
        self.client.logout()

    def test_subscribe_user_to_topic(self):
        self.client.force_authenticate(user=self.reritja_user)
        code = self.some_topic.topic_code
        user = self.regular_user.user_UUID
        response = self.client.post('/api/subscribe_to_topic/?code=' + code + '&user=' + user)
        # should respond created
        self.assertEqual(response.status_code, 201)
        # try resubscribing
        response = None
        # this strange stuff is here because resubscribing throws an IntegrityError exception, which locks
        # the database and breaks subsequent tests. To avoid this, we add the with transaction, which rolls back
        # in case of exception
        try:
            with transaction.atomic():
                response = self.client.post('/api/subscribe_to_topic/?code=' + code + '&user=' + user)
        except IntegrityError:
            pass
        #should fail
        self.assertEqual(response.status_code, 400)
        self.client.logout()

    def test_list_user_subscriptions(self):
        self.client.force_authenticate(user=self.reritja_user)
        user = self.regular_user.user_UUID
        # we make up some topics
        n1 = NotificationTopic(topic_code="ru", topic_description="This is a test topic")
        n1.save()
        n2 = NotificationTopic(topic_code="es", topic_description="This is a test topic")
        n2.save()
        n3 = NotificationTopic(topic_code="en", topic_description="This is a test topic")
        n3.save()
        topics = [n1, n2, n3]
        for t in topics:
            response = self.client.post('/api/subscribe_to_topic/?code=' + t.topic_code + '&user=' + user)
            # should respond created
            self.assertEqual(response.status_code, 201)

        response = self.client.get('/api/topics_subscribed/?user=' + user)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should be subscribed to t, n1, n2 and n3
        self.assertEqual(len(response.data), 3)
        self.client.logout()

    def test_user_sees_notifications_sent_to_global_topic(self):
        nc = NotificationContent(
            body_html_en="<p>Notification Body</p>",
            body_html_native="<p>Native Notification Body</p>",
            title_en="Notification title",
            title_native="Títol notificació",
            native_locale="ca"
        )
        nc.save()
        n = Notification(expert=self.reritja_user, notification_content=nc)
        n.save()
        # send notif to global topic
        n.send_to_topic(topic=self.global_topic, push=False)

        # the regular user should see this notification
        some_user = self.regular_user
        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get('/api/user_notifications/?user_id=' + some_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # acknowledge the notification
        #response = self.client.post('/api/ack_notif/', {'user': '00000000-0000-0000-0000-000000000000', 'notification': n.id}, format='json')
        response = self.client.delete('/api/mark_notif_as_ack/?user=00000000-0000-0000-0000-000000000000&notif=' + str(n.id))
        # should respond no content
        self.assertEqual(response.status_code, 204)
        # now the notification should be acknowledged
        response = self.client.get('/api/user_notifications/?user_id=' + some_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # AND it should be ack=True
        self.assertEqual(response.data[0]['acknowledged'], True)
        self.client.logout()

    def test_subscription_and_unsubscription(self):
        nc = NotificationContent(
            body_html_en="<p>Notification Body</p>",
            body_html_native="<p>Native Notification Body</p>",
            title_en="Notification title",
            title_native="Títol notificació",
            native_locale="ca"
        )
        nc.save()
        n = Notification(expert=self.reritja_user, notification_content=nc)
        n.save()

        # send notif to regular topic
        n.send_to_topic(topic=self.some_topic, push=False)

        self.client.force_authenticate(user=self.reritja_user)
        # list notifications for regular user
        response = self.client.get('/api/user_notifications/?user_id=' + self.regular_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # no notifications should be available
        self.assertEqual(len(response.data), 0)

        # subscribe user to regular topic
        response = self.client.post('/api/subscribe_to_topic/?code=' + self.some_topic.topic_code + '&user=' + self.regular_user.user_UUID)
        # should respond created
        self.assertEqual(response.status_code, 201)

        # list notifications for regular user again
        response = self.client.get('/api/user_notifications/?user_id=' + self.regular_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # only the topic notification should be available
        self.assertEqual(len(response.data), 1)
        # the only notification should be about the topic
        self.assertEqual(response.data[0]['topic'], 'some_topic')

        # now, unsubscribe!
        response = self.client.post('/api/unsub_from_topic/?code=' + self.some_topic.topic_code + '&user=' + self.regular_user.user_UUID)
        # response should be no content
        self.assertEqual(response.status_code, 204)

        # list notifications for regular user again!
        response = self.client.get('/api/user_notifications/?user_id=' + self.regular_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # no notifications available
        self.assertEqual(len(response.data), 0)
        self.client.logout()




    def test_direct_notifs_and_topic_sort_okay(self):
        some_user = self.regular_user
        nc1 = NotificationContent(
            body_html_en="<p>Notification Body 1</p>",
            body_html_native="<p>Native Notification Body 1</p>",
            title_en="Notification title 1",
            title_native="Títol notificació 1",
            native_locale="ca"
        )
        nc1.save()

        nc2 = NotificationContent(
            body_html_en="<p>Notification Body 2</p>",
            body_html_native="<p>Native Notification Body 2</p>",
            title_en="Notification title 2",
            title_native="Títol notificació 2",
            native_locale="ca"
        )
        nc2.save()

        # FIRST direct NOTIFICATION
        n1 = Notification(expert=self.reritja_user, notification_content=nc1)
        n1.save()

        # send notif to user
        n1.send_to_user(user=some_user, push=False)

        # GLOBAL notification
        n3 = Notification(expert=self.reritja_user, notification_content=nc1)
        n3.save()
        # send notif to global topic
        n3.send_to_topic(topic=self.global_topic, push=False)

        # SECOND direct  NOTIFICATION
        n2 = Notification(expert=self.reritja_user, notification_content=nc2)
        n2.save()

        # send notif to user
        n2.send_to_user(user=some_user, push=False)

        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get('/api/user_notifications/?user_id=' + some_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should receive both direct notifications and global
        self.assertEqual(len(response.data), 3)
        # global should be in the middle
        self.assertEqual(response.data[1]['topic'], 'global')
        # most recent should be 2
        self.assertEqual(response.data[0]['expert_comment'], nc2.title_en)
        # 0 should be more recent than 1
        self.assertTrue( response.data[0]['date_comment'] > response.data[1]['date_comment'] )
        # 1 should be more recent than 2
        self.assertTrue(response.data[1]['date_comment'] > response.data[2]['date_comment'])
        self.client.logout()

    def test_post_notification_content_via_api(self):
        notif_content = {
            'body_html_en': '<p>Hello world body</p>',
            'title_en': 'Hello world title',
            'body_html_native': '<p>Hola món cos</p>',
            'title_native': 'Hola món títol',
            'native_locale': 'ca'
        }
        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.put('/api/notification_content/',notif_content)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        notif_id = response.data['id']
        # retrieve notification written to db
        nc = NotificationContent.objects.get(pk=notif_id)
        # sould be the same as written to database
        self.assertEqual(response.data['body_html_en'], nc.body_html_en)
        # sould be the same as params
        self.assertEqual(response.data['body_html_en'], notif_content['body_html_en'])
        self.client.logout()

    def test_push_notifications_single_user(self):
        # send push to android
        self.client.force_authenticate(user=self.reritja_user)
        data = {
            'user_id': self.regular_user.user_UUID,
            'message': 'This is a test message',
            'title': 'This is the message title'
        }
        response = self.client.post('/api/msg_android/?' + urllib.parse.urlencode(data))
        self.client.logout()

    def test_favorite_endpoint(self):
        self.client.force_authenticate(user=self.reritja_user)
        r = Report.objects.get(pk=1)
        data = {
            'user_id': self.reritja_user.id,
            'report_id': r.version_UUID,
            'note': 'some note'
        }

        d = {
            'user_id': self.reritja_user.id
        }

        response = self.client.get('/api/user_favorites/', data=d)
        resp_data = response.data
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        self.assertTrue(len(resp_data) == 0, "Response should be an array of length 0, is not")

        response = self.client.post('/api/favorite/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        my_fav = FavoritedReports.objects.filter(user=self.reritja_user,report=r).first()
        self.assertTrue( my_fav is not None, "Favorite object should be created but id does not exist" )
        consistent_write = my_fav.user == self.reritja_user and my_fav.report == r and my_fav.note == 'some note'
        self.assertTrue(consistent_write, "Favorite object should be correctly written, but has the values {0} {1} {2}".format( self.reritja_user.id, my_fav.report.version_UUID, my_fav.note ) )

        response = self.client.get('/api/user_favorites/', data=d)
        resp_data = response.data
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        self.assertTrue(len(resp_data) == 1, "Response should be an array of length 1, is not")

        response = self.client.post('/api/favorite/', data=data)
        self.assertEqual(response.status_code, 204, "Response should be 204, is {0}".format(response.status_code))
        my_fav = FavoritedReports.objects.filter(user=self.reritja_user, report=r).first()
        self.assertTrue(my_fav is None, "Favorite object should not exist")

        self.client.logout()

class AnnotateCoarseTestCase(APITestCase):
    fixtures = ['photos.json', 'categories.json','users.json','europe_countries.json','tigaprofile.json','tigausers.json','reports.json','auth_group.json', 'movelab_like.json']
    def test_annotate_taken(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        annos = ExpertReportAnnotation.objects.filter(report=r)
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Give report to one expert
        innie = User.objects.get(pk=150) #innie
        anno = ExpertReportAnnotation(user=innie, report=r)
        anno.save()
        # try to annotate
        category = Categories.objects.get(pk=2)
        data = {
            'report_id': '00042354-ffd6-431e-af1e-cecf55e55364',
            'category_id': str(2)
        }
        response = self.client.post('/api/annotate_coarse/', data=data)
        self.assertEqual(response.status_code, 400, "Response should be 400, is {0}".format(response.status_code))
        # opcode should be -1
        self.assertEqual(response.data['opcode'], -1, "Opcode should be -1, is {0}".format(response.data['opcode']))

    def test_flip_taken(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        annos = ExpertReportAnnotation.objects.filter(report=r_adult)
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Give report to one expert
        innie = User.objects.get(pk=150)  # innie
        anno = ExpertReportAnnotation(user=innie, report=r_adult)
        anno.save()
        # try to annotate
        data = {
            'report_id': r_adult.version_UUID,
            'flip_to_type': 'site',
            'flip_to_subtype': 'storm_drain_water'
        }
        response = self.client.patch('/api/flip_report/', data=data)
        self.assertEqual(response.status_code, 400, "Response should be 400, is {0}".format(response.status_code))
        # opcode should be -1
        self.assertEqual(response.data['opcode'], -1, "Opcode should be -1, is {0}".format(response.data['opcode']))

    def test_bookmark(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        data= { "report_id": r.version_UUID, "user_id": u.id, "label": "bookmark label", "module": "coarse", "json_filter": ""}
        response = self.client.post('/api/bookmark_report/', data=data)
        self.assertEqual(response.status_code, 201, "Response should be 201, is {0}".format(response.status_code))
        response = self.client.get('/api/bookmarks/', data=data)
        self.assertTrue(len(response.data) == 1, "There should be a single bookmark, is not")
        bookmark_id = response.data[0]['id']
        data = { "id":bookmark_id }
        response = self.client.delete('/api/bookmark_report/', data=data)
        self.assertEqual(response.status_code, 204, "Response should be 204, is {0}".format(response.status_code))


    def test_annotate_coarse(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        annos = ExpertReportAnnotation.objects.filter(report=r)
        self.assertTrue(annos.count() == 0, "Report should not have any annotations")
        # Let's change that
        for c_id in [2, 10, 4, 9]:
            category = Categories.objects.get(pk=c_id)
            data = {
                'report_id': '00042354-ffd6-431e-af1e-cecf55e55364',
                'category_id': str(c_id)
            }
            if category.specify_certainty_level:
                data['validation_value'] = '1'
            response = self.client.post('/api/annotate_coarse/', data=data)
            self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
            classification = json.loads(r.get_final_combined_expert_category_euro_struct_json())
            category_text = classification['category']
            category_id = int(classification['category_id'])
            value = classification['value']
            self.assertEqual(category_text, category.name, "Category should be {0}, is {1}".format(category.name, category_text))
            self.assertEqual(category_id, category.id, "Category id should be {0}, is {1}".format(category.id, category_id))
            if category.specify_certainty_level:
                self.assertEqual(value, data['validation_value'], "Validation value should be {0}, is {1}".format(data['validation_value'], value))
            else:
                self.assertEqual(value, None, "Validation value should be None, is {0}".format(value))
            notif = Notification.objects.get(report=r)
            notif_content = notif.notification_content
            if c_id == 2: #other species
                self.assertTrue( other_insect['es'] in notif_content.body_html_native, "Report classified as other species associated notification should contain other insect message, it does not" )
                #'no pertenece a la familia de los Culícidos'
            elif c_id == 10: #culex sp.
                self.assertTrue(culex['es'] in notif_content.body_html_native, "Report classified as culex associated notification should contain culex message, it does not")
                #'no podemos asegurar totalmente que sea un Culex'
            elif c_id == 4: #aedes albopictus
                self.assertTrue(albopictus_probably['es'] in notif_content.body_html_native, "Report classified as albopictus associated notification should contain probably albopictus message, it does not")
                #'Has conseguido que se pueda identificar perfectamente el mosquito tigre'
            else: #c_id == 9 not_sure
                self.assertTrue(notsure['es'] in notif_content.body_html_native, "Report classified as not_sure associated notification should contain not_sure message, it does not")
                #'Con esta foto no podemos identificar ninguna especie'
            Notification.objects.filter(report=r).delete()
            ExpertReportAnnotation.objects.filter(report=r).delete()
        # test also definitely albopictus
        category = Categories.objects.get(pk=4)
        data = {
            'report_id': '00042354-ffd6-431e-af1e-cecf55e55364',
            'category_id': "4"
        }
        data['validation_value'] = '2'
        response = self.client.post('/api/annotate_coarse/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        classification = json.loads(r.get_final_combined_expert_category_euro_struct_json())
        category_text = classification['category']
        category_id = int(classification['category_id'])
        value = classification['value']
        self.assertEqual(category_text, category.name,"Category should be {0}, is {1}".format(category.name, category_text))
        self.assertEqual(category_id, category.id, "Category id should be {0}, is {1}".format(category.id, category_id))
        notif = Notification.objects.get(report=r)
        notif_content = notif.notification_content
        self.assertTrue(albopictus['es'] in notif_content.body_html_native,"Report classified as albopictus associated notification should contain definitely albopictus message, it does not")
        Notification.objects.filter(report=r).delete()
        ExpertReportAnnotation.objects.filter(report=r).delete()

    def test_flip_adult_to_adult(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk="004D5A85-1D88-4170-A253-DABF30669EBE")
        self.assertEqual(r_adult.type, 'adult', "Report type should be adult, is {0}".format(r_adult.type))
        data = {
            'report_id': r_adult.version_UUID,
            'flip_to_type': 'adult'
        }
        response = self.client.patch('/api/flip_report/', data=data)
        self.assertEqual(response.status_code, 400, "Response should be 400, is {0}".format(response.status_code))
        self.assertEqual(response.data['opcode'], -2, "Opcode should be -2, is {0}".format(response.data['opcode']))

    def test_flip_site_to_site(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_site = Report.objects.get(pk='007106f1-6003-4cf5-b049-8f6533a90813')
        self.assertEqual(r_site.type, 'site', "Report type should be site, is {0}".format(r_site.type))
        data = {
            'report_id': r_site.version_UUID,
            'flip_to_type': 'site',
            'flip_to_subtype': 'storm_drain_water'
        }
        response = self.client.patch('/api/flip_report/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        r_site_reloaded = Report.objects.get(pk='007106f1-6003-4cf5-b049-8f6533a90813')
        n_responses = ReportResponse.objects.filter(report=r_site_reloaded).count()
        self.assertTrue(n_responses == 2, "Number of responses should be 2, is {0}".format(n_responses))
        self.assertTrue(r_site_reloaded.flipped, "Report should be marked as flipped")
        self.assertTrue(r_site_reloaded.flipped_to == 'site#site',"Report should be marked as flipped from site to site, field has value of {0}".format(r_site_reloaded.flipped_to))
        self.assertEqual(r_site_reloaded.breeding_site_type, Report.BREEDING_SITE_TYPE_STORM_DRAIN)
        self.assertTrue(r_site_reloaded.breeding_site_has_water)

    def test_flip(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        # Check report types
        self.assertEqual(r_adult.type, 'adult', "Report type should be adult, is {0}".format(r_adult.type))
        r_site = Report.objects.get(pk='00042fb1-408f-4da4-898d-4331a9ec3129')
        self.assertEqual(r_site.type, 'site', "Report type should be site, is {0}".format(r_site.type))
        # flip adult to storm drain water
        data = {
            'report_id': r_adult.version_UUID,
            'flip_to_type': 'site',
            'flip_to_subtype': 'storm_drain_water'
        }
        response = self.client.patch('/api/flip_report/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        adult_reloaded = Report.objects.get(pk=r_adult.version_UUID)
        self.assertTrue(adult_reloaded.type==Report.TYPE_SITE,"Report type should have changed to site, is {0}".format(adult_reloaded.type))
        self.assertEqual(adult_reloaded.breeding_site_type, Report.BREEDING_SITE_TYPE_STORM_DRAIN)
        self.assertTrue(adult_reloaded.breeding_site_has_water)

        n_responses = ReportResponse.objects.filter(report=adult_reloaded).count()
        self.assertTrue( n_responses == 2, "Number of responses should be 2, is {0}".format(n_responses) )
        self.assertTrue( adult_reloaded.flipped, "Report should be marked as flipped" )
        self.assertTrue( adult_reloaded.flipped_to == 'adult#site', "Report should be marked as flipped from adult to site, field has value of {0}".format(adult_reloaded.flipped_to))
        try:
            response_type = ReportResponse.objects.get(report=adult_reloaded,question_id='12',answer_id='121')
        except:
            self.assertTrue(False,"Report does not have the storm drain response")
        try:
            response_type = ReportResponse.objects.get(report=adult_reloaded,question_id='10',answer_id='101')
        except:
            self.assertTrue(False,"Report does not have the water response")
        # flip site to adult
        data = {
            'report_id': r_site.version_UUID,
            'flip_to_type': 'adult'
        }
        response = self.client.patch('/api/flip_report/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        site_reloaded = Report.objects.get(pk=r_site.version_UUID)
        self.assertTrue(site_reloaded.type == Report.TYPE_ADULT, "Report type should have changed to adult, is {0}".format(site_reloaded.type))

        n_responses = ReportResponse.objects.filter(report=site_reloaded).count()
        self.assertTrue(n_responses == 0, "Number of responses should be 0, is {0}".format(n_responses))
        self.assertTrue(site_reloaded.flipped, "Report should be marked as flipped")
        self.assertTrue(site_reloaded.flipped_to == 'site#adult',"Report should be marked as flipped from site to adult, field has value of {0}".format(adult_reloaded.flipped_to))
        #print(site_reloaded.flipped_on)

    def test_hide(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_adult = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        self.assertTrue(not r_adult.hide, "Report should be visible, is not")
        data = {
            'report_id': r_adult.version_UUID,
            'hide': 'true'
        }
        response = self.client.patch('/api/hide_report/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        r_adult_reloaded = Report.objects.get(pk='00042354-ffd6-431e-af1e-cecf55e55364')
        self.assertTrue(r_adult_reloaded.hide, "Report should be hidden, is not")

    def test_quick_upload(self):
        u = User.objects.get(pk=25)
        self.client.force_authenticate(user=u)
        r_site = Report.objects.get(pk='00042fb1-408f-4da4-898d-4331a9ec3129')
        n_annotations = ExpertReportAnnotation.objects.filter(report=r_site).count()
        self.assertTrue(n_annotations == 0, "Report annotations should be 0, is not (is {0})".format(n_annotations))
        data = {
            'report_id': r_site.version_UUID
        }
        response = self.client.post('/api/quick_upload_report/', data=data)
        self.assertEqual(response.status_code, 200, "Response should be 200, is {0}".format(response.status_code))
        r_site_reloaded = Report.objects.get(pk='00042fb1-408f-4da4-898d-4331a9ec3129')
        n_annotations = ExpertReportAnnotation.objects.filter(report=r_site_reloaded).count()
        self.assertTrue(n_annotations == 1, "Report annotations should be 1, is not (is {0})".format(n_annotations))
        annotation = ExpertReportAnnotation.objects.filter(report=r_site_reloaded).first()
        self.assertTrue(annotation.best_photo_id is not None, "Report annotation should have picture, it has not")
        self.assertTrue(annotation.site_certainty_notes == 'auto', "Report annotation notes should be 'auto'")
        self.assertTrue(annotation.validation_complete, "Report annotation validation should be done")
        self.assertTrue(annotation.revise, "Report annotation revision should be done")