from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import Report, EuropeCountry
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
from rest_framework.test import APITestCase
from django.urls import reverse
import io
from rest_framework import status

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

