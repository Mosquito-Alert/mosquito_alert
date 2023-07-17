import os
from datetime import timedelta

import pytest
from django.utils import timezone
from PIL import Image

from ..models import Photo
from . import testdata
from .factories import PhotoFactory


@pytest.mark.django_db
class TestPhoto:
    def test_user_can_be_null(self):
        PhotoFactory(user=None)

    def test_user_is_set_null_if_deleted(self, user):
        p = PhotoFactory(user=user)

        user.delete()

        p.refresh_from_db()
        assert p.user is None

    def test_image_is_uploaded_in_images_path(self):
        p = PhotoFactory()
        assert os.path.dirname(p.image.name) == "images"

    def test_image_filaname_is_replaced_to_uuid(self, mocker):
        mocker.patch("uuid.uuid4", return_value="mocked_uuid")

        p = PhotoFactory(image__filename="example.jpg")
        filename, _ = os.path.splitext(os.path.basename(p.image.name))
        assert filename == "mocked_uuid"

    def test_image_filename_is_kept_if_already_uuid(self):
        p = PhotoFactory(image__filename="5c240771-4f46-4d0b-972e-a2c0edd31451.png")
        filename, _ = os.path.splitext(os.path.basename(p.image.name))
        assert filename == "5c240771-4f46-4d0b-972e-a2c0edd31451"

    def test_image_is_converted_to_webp(self):
        assert Photo._meta.get_field("image")._original_spec.format == "WEBP"

        # Check filename extension
        p = PhotoFactory(image__filename="example.png", image__format="PNG")
        _, ext = os.path.splitext(os.path.basename(p.image.name))
        assert ext == ".webp"

        # Check format is WEBP
        assert Image.open(p.image).format == "WEBP"

    def test_image_is_resized_to_720p(self):
        p = PhotoFactory(image__width=2049, image__height=1080)

        target_sizing_factor = 1080 / 720
        # It should perform a downsizing for factor 1.5

        # Metatada in the field
        assert p.image.width == 2049 / target_sizing_factor
        assert p.image.height == 720

    def test_image_is_not_resized_if_smaller_than_720p(self):
        p = PhotoFactory(image__width=1080, image__height=600)

        assert p.image.width == 1080
        assert p.image.height == 600

    def test_created_at_field_is_automatically_set(self, freezer):
        p = PhotoFactory()
        assert p.created_at == timezone.now()

    def test_exif_is_preserved_from_original_image(self):
        p = PhotoFactory(image__from_path=testdata.TESTEXIFIMAGE_PATH)

        original_exif = Image.Exif()
        original_exif.load(data=Image.open(testdata.TESTEXIFIMAGE_PATH).info["exif"])

        new_exif = Image.Exif()
        new_exif.load(data=Image.open(p.image).info["exif"])

        assert original_exif == new_exif

    def test_exif_dict(self):
        p = PhotoFactory(image__from_path=testdata.TESTEXIFIMAGE_PATH)
        assert p.exif_dict == {
            "ImageWidth": "4000",
            "ImageLength": "3000",
            "GPSInfo": {
                "GPSLatitudeRef": "N",
                "GPSLatitude": "(42.0, 14.0, 9.7548)",
                "GPSLongitudeRef": "E",
                "GPSLongitude": "(2.0, 30.0, 24.0228)",
                "GPSAltitudeRef": "b'\\x00'",
                "GPSAltitude": "621.399",
                "GPSTimeStamp": "(16.0, 36.0, 26.0)",
                "GPSProcessingMethod": "b'ASCII\\x00\\x00\\x00CELLID\\x00'",
                "GPSDateStamp": "2019:08:10",
            },
            "ResolutionUnit": "2",
            "ExifOffset": "206",
            "Make": "Xiaomi",
            "Model": "MI 9",
            "Orientation": "6",
            "DateTime": "2019:08:10 18:36:38",
            "YCbCrPositioning": "1",
            "XResolution": "72.0",
            "YResolution": "72.0",
            "ExifVersion": "b'0220'",
            "ComponentsConfiguration": "b'\\x01\\x02\\x03\\x00'",
            "ExifImageWidth": "4000",
            "ExifImageHeight": "3000",
            "DateTimeDigitized": "2019:08:10 18:36:38",
            "ExifInteroperabilityOffset": "703",
            "FocalLengthIn35mmFilm": "27",
            "MeteringMode": "2",
            "LightSource": "20",
            "Flash": "16",
            "FocalLength": "4.75",
            "MaxApertureValue": "1.61",
            "ExposureBiasValue": "0.0",
            "ColorSpace": "1",
            "SubsecTime": "833137",
            "SubsecTimeOriginal": "833137",
            "SubsecTimeDigitized": "833137",
            "DateTimeOriginal": "2019:08:10 18:36:38",
            "34965": "0",
            "ShutterSpeedValue": "5.643",
            "SensingMethod": "1",
            "39321": '{"mirror":false,"sensor_type":"rear"}',
            "ExposureTime": "0.02",
            "ApertureValue": "1.61",
            "FNumber": "1.75",
            "ISOSpeedRatings": "1649",
            "FlashPixVersion": "b'0100'",
            "WhiteBalance": "0",
        }

    def test_default_orderding_shows_newest_first(self):
        t = timezone.now()
        old = PhotoFactory(created_at=t)
        oldest = PhotoFactory(created_at=t - timedelta(seconds=10))
        newest = PhotoFactory(created_at=t + timedelta(seconds=10))

        assert frozenset(list(Photo.objects.all())) == frozenset([oldest, old, newest])

    def test__str__(self):
        p = PhotoFactory(image__filename="5c240771-4f46-4d0b-972e-a2c0edd31451.webp")
        assert p.__str__() == "5c240771-4f46-4d0b-972e-a2c0edd31451.webp"
