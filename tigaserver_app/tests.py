from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import Report, EuropeCountry, ExpertReportAnnotation, Categories, Notification, NotificationContent, NotificationTopic, SentNotification
from django.core.management import call_command
import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
import tigaserver_project.settings as conf
import os
import requests
from django.utils import timezone
from tigaserver_app.models import TigaUser, Report, Photo
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
import io
from rest_framework import status
from tigacrafting.views import issue_notification
from rest_framework.test import APIRequestFactory
from django.db import transaction
from django.db.utils import IntegrityError

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

class NotificationTestCase(APITestCase):

    fixtures = ['reritja_like.json', 'awardcategory.json', 'europe_countries.json']

    def setUp(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
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
            p = Photo.objects.create(report=r, photo='/home/webuser/webapps/tigaserver/media/tigapics/splash.png')
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
        response = self.client.post('/api/ack_notif/',{'user':'00000000-0000-0000-0000-000000000000','notification':notification_id},format='json')
        # should respond created
        self.assertEqual(response.status_code, 201)
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

    def test_user_subscripted_to_topic_sees_notifications_sent_to_global_topic(self):
        nc = NotificationContent(
            body_html_es="<p>Cuerpo Notificacion</p>",
            body_html_ca="<p>Cos Notificació</p>",
            body_html_en="<p>Notification Body</p>",
            title_es="Titulo notificacion",
            title_ca="Títol notificació",
            title_en="Notification title"
        )
        nc.save()
        n = Notification(expert=self.reritja_user, notification_content=nc)
        n.save()
        # send notif to global topic
        sn = SentNotification(sent_to_topic=self.global_topic, notification=n)
        sn.save()
        # the regular user should see this notification
        some_user = self.regular_user
        self.client.force_authenticate(user=self.reritja_user)
        response = self.client.get('/api/user_notifications/?user_id=' + some_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # acknowledge the notification
        response = self.client.post('/api/ack_notif/', {'user': '00000000-0000-0000-0000-000000000000', 'notification': n.id}, format='json')
        # should respond created
        self.assertEqual(response.status_code, 201)
        # now the notification should be acknowledged
        response = self.client.get('/api/user_notifications/?user_id=' + some_user.user_UUID)
        # response should be ok
        self.assertEqual(response.status_code, 200)
        # should only receive the notification from the global topic
        self.assertEqual(len(response.data), 1)
        # AND it should be ack=True
        self.assertEqual(response.data[0]['acknowledged'], True)
        self.client.logout()

    def test_direct_notifs_and_topic_sort_okay(self):
        some_user = self.regular_user
        nc1 = NotificationContent(
            body_html_es="<p>Cuerpo Notificacion 1</p>",
            body_html_ca="<p>Cos Notificació 1</p>",
            body_html_en="<p>Notification Body 1</p>",
            title_es="Titulo notificacion 1",
            title_ca="Títol notificació 1",
            title_en="Notification title 1"
        )
        nc1.save()

        nc2 = NotificationContent(
            body_html_es="<p>Cuerpo Notificacion 2</p>",
            body_html_ca="<p>Cos Notificació 2</p>",
            body_html_en="<p>Notification Body 2</p>",
            title_es="Titulo notificacion 2",
            title_ca="Títol notificació 2",
            title_en="Notification title 2"
        )
        nc2.save()

        # FIRST direct NOTIFICATION
        n1 = Notification(expert=self.reritja_user, notification_content=nc1)
        n1.save()

        # send notif to user
        sn1 = SentNotification(sent_to_user=some_user, notification=n1)
        sn1.save()

        # GLOBAL notification
        n3 = Notification(expert=self.reritja_user, notification_content=nc1)
        n3.save()
        # send notif to global topic
        sn3 = SentNotification(sent_to_topic=self.global_topic, notification=n3)
        sn3.save()

        # SECOND direct  NOTIFICATION
        n2 = Notification(expert=self.reritja_user, notification_content=nc2)
        n2.save()

        # send notif to user
        sn2 = SentNotification(sent_to_user=some_user, notification=n2)
        sn2.save()

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