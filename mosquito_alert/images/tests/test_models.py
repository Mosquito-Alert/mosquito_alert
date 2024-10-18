import os
import uuid

import pytest
from django.db import models
from PIL import Image

from mosquito_alert.moderation.tests.test_models import BaseTestFlagModeratedModel
from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import Photo
from . import testdata
from .factories import PhotoFactory


@pytest.mark.django_db
class TestPhoto(BaseTestFlagModeratedModel, BaseTestTimeStampedModel):
    model = Photo
    factory_cls = PhotoFactory

    # fields
    def test_user_can_be_null(self):
        assert self.model._meta.get_field("user").null

    def test_user_can_be_blank(self):
        assert self.model._meta.get_field("user").blank

    def test_user_on_delete_set_null(self):
        _on_delete = self.model._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.SET_NULL

    def test_user_related_name(self):
        assert self.model._meta.get_field("user").remote_field.related_name == "photos"

    def test_image_can_not_be_null(self):
        assert not self.model._meta.get_field("image").null

    def test_image_is_uploaded_in_images_path(self):
        p = self.factory_cls()
        assert os.path.dirname(p.image.name) == "images"

    def test_image_filaname_is_replaced_to_uuid_from_id(self):
        new_uuid = uuid.uuid4()
        p = self.factory_cls(id=new_uuid, image__filename="example.jpg")
        filename, _ = os.path.splitext(os.path.basename(p.image.name))
        assert filename == str(new_uuid)

    def test_image_is_converted_to_jpeg(self):
        assert self.model._meta.get_field("image")._original_spec.format == "JPEG"

        # Check filename extension
        p = self.factory_cls(image__filename="example.png", image__format="PNG")
        _, ext = os.path.splitext(os.path.basename(p.image.name))
        assert ext == ".jpg"

        # Check format is JPEG
        assert Image.open(p.image).format == "JPEG"

    def test_image_is_resized_to_1080p(self):
        p = self.factory_cls(image__width=3840, image__height=1620)

        target_sizing_factor = 1620 / 1080
        # It should perform a downsizing for factor 1.5

        # Metatada in the field
        assert p.image.width == 3840 / target_sizing_factor
        assert p.image.height == 1080

    def test_image_is_not_resized_if_smaller_than_1080p(self):
        p = self.factory_cls(image__width=1080, image__height=600)

        assert p.image.width == 1080
        assert p.image.height == 600

    def test_image_large(self):
        p = self.factory_cls(image__width=2160, image__height=1080)

        assert p.image_large is not None
        assert p.image_large.width == 1440
        assert p.image_large.height == 720

    def test_image_medium(self):
        p = self.factory_cls(image__width=2160, image__height=1080)

        assert p.image_medium is not None
        assert p.image_medium.width == 720
        assert p.image_medium.height == 360

    def test_thumbnail(self):
        p = self.factory_cls(image__width=2160, image__height=1080)

        assert p.thumbnail is not None
        assert p.thumbnail.width == 150
        assert p.thumbnail.height == 150

    def test_exif_is_preserved_from_original_image(self):
        p = self.factory_cls(image__from_path=testdata.TESTEXIFIMAGE_PATH)

        original_exif = Image.Exif()
        original_exif.load(data=Image.open(testdata.TESTEXIFIMAGE_PATH).info["exif"])

        new_exif = Image.Exif()
        new_exif.load(data=Image.open(p.image).info["exif"])

        assert original_exif == new_exif

    # properties
    def test_exif_dict(self):
        p = self.factory_cls(image__from_path=testdata.TESTEXIFIMAGE_PATH)
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

    # meta
    def test_default_orderding_shows_newest_first(self):
        assert self.model._meta.ordering == ["-created_at"]

    def test__str__(self):
        new_uuid = uuid.uuid4()

        p = self.factory_cls(id=new_uuid)
        assert p.__str__() == str(new_uuid)
