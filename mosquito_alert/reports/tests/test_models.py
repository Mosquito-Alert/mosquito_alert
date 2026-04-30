from datetime import timedelta

# Create your tests here.
from django.test import TestCase, override_settings
from mosquito_alert.devices.models import Device, MobileApp
from mosquito_alert.geo.models import EuropeCountry, LauEurope
from PIL import Image, ExifTags
import os
from django.contrib.gis.geos import Polygon, MultiPolygon, Point
from django.utils import timezone
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.reports.utils import scrub_sensitive_exif
from mosquito_alert.users.models import TigaUser
from mosquito_alert.workspaces.tests.factories import WorkspaceFactory
import io
from django.db.utils import IntegrityError
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
import time_machine
import semantic_version

import piexif
from pillow_heif import HeifFile
import pytest


def get_full_exif_dict(exif) -> dict:
    if not exif:
        return {}
    exif.update(exif.get_ifd(ExifTags.IFD.Exif))
    exif[ExifTags.IFD.GPSInfo] = exif.get_ifd(ExifTags.IFD.GPSInfo)
    exif_dict = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.items()}
    exif_dict.pop("ExifOffset", None)
    return exif_dict


def get_full_exif_dict_from_bytes(img_bytes: bytes) -> dict:
    """Extracts EXIF data from an in-memory image."""
    with Image.open(img_bytes) as img:
        exif = img.getexif()
        if not exif:
            return {}
        return get_full_exif_dict(exif)


@pytest.mark.parametrize(
    "photo_path, expected_exif",
    [
        (
            "./testdata/exif/Canon_40D.jpg",
            {
                "Orientation": 1,
                "DateTime": "2008:07:31 10:38:11",
                "DateTimeDigitized": "2008:05:30 15:56:01",
                "DateTimeOriginal": "2008:05:30 15:56:01",
                "GPSInfo": {0: b"\x02\x02\x00\x00"},
            },
        ),
        (
            "./testdata/exif/DSCN0025.jpg",
            {
                "DateTime": "2008:11:01 21:15:09",
                "DateTimeDigitized": "2008:10:22 16:43:21",
                "DateTimeOriginal": "2008:10:22 16:43:21",
                "GPSInfo": {
                    1: "N",
                    2: (43.0, 28.0, 6.114),
                    3: "E",
                    4: (11.0, 52.0, 53.8859999),
                    5: b"\x00",
                    7: (14.0, 41.0, 49.03),
                    8: "05",
                    16: "\x00",
                    18: "WGS-84   ",
                    29: "2008:10:23",
                },
                "Orientation": 1,
            },
        ),
        (
            "./testdata/exif/DSCN0027.jpg",
            {
                "DateTime": "2008:11:01 21:15:09",
                "DateTimeDigitized": "2008:10:22 16:44:01",
                "DateTimeOriginal": "2008:10:22 16:44:01",
                "GPSInfo": {
                    1: "N",
                    2: (43.0, 28.0, 6.39),
                    3: "E",
                    4: (11.0, 52.0, 53.454),
                    5: b"\x00",
                    7: (14.0, 42.0, 29.03),
                    8: "05",
                    16: "\x00",
                    18: "WGS-84   ",
                    29: "2008:10:23",
                },
                "Orientation": 1,
            },
        ),
        (
            "./testdata/exif/DSCN0029.jpg",
            {
                "DateTime": "2008:11:01 21:15:09",
                "DateTimeDigitized": "2008:10:22 16:46:53",
                "DateTimeOriginal": "2008:10:22 16:46:53",
                "GPSInfo": {
                    1: "N",
                    2: (43.0, 28.0, 5.67599999),
                    3: "E",
                    4: (11.0, 52.0, 48.6179999),
                    5: b"\x00",
                    7: (14.0, 45.0, 20.91),
                    8: "05",
                    16: "\x00",
                    18: "WGS-84   ",
                    29: "2008:10:23",
                },
                "Orientation": 1,
            },
        ),
        (
            "./testdata/exif/Fujifilm_FinePix6900ZOOM.jpg",
            {
                "DateTime": "2008:07:31 17:17:56",
                "DateTimeDigitized": "2001:02:19 06:40:05",
                "DateTimeOriginal": "2001:02:19 06:40:05",
                "GPSInfo": {},
                "Orientation": 1,
            },
        ),
        ("./testdata/exif/image00971.jpg", {}),
        ("./testdata/exif/image01137.jpg", {}),
        ("./testdata/exif/image01551.jpg", {}),
        (
            "./testdata/exif/Nikon_COOLPIX_P1.jpg",
            {
                "DateTime": "2008:07:31 17:43:03",
                "DateTimeDigitized": "2008:03:07 09:55:46",
                "DateTimeOriginal": "2008:03:07 09:55:46",
                "GPSInfo": {},
                "Orientation": 1,
            },
        ),
    ],
)
def test_scrub_sensitive_exif_function(photo_path, expected_exif):
    """Helper function to test that EXIF data is scrubbed correctly."""
    current_directory = os.path.dirname(__file__)

    # Construct the path to the file
    file_path = os.path.join(current_directory, photo_path)
    scrubbed_exif = scrub_sensitive_exif(Image.open(file_path).getexif())
    scrubbed_exif_dict = get_full_exif_dict(scrubbed_exif)
    assert scrubbed_exif_dict == expected_exif


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class PhotoModelTest(TestCase):
    def setUp(self):
        self.report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=0,
            current_location_lat=0,
        )

    @classmethod
    def create_image_file(cls, name, size, format) -> SimpleUploadedFile:
        # Helper to create an image in memory and return as SimpleUploadedFile
        image = Image.new("RGB", size, color=(255, 0, 0))  # Create a red image
        image_file = io.BytesIO()
        if format.upper() == "HEIF":
            heif_file = HeifFile()
            heif_file.add_from_pillow(image)
            image = heif_file
        image.save(image_file, format=format)
        image_file.seek(0)
        return SimpleUploadedFile(
            name, image_file.read(), content_type=f"image/{format.lower()}"
        )

    @classmethod
    def _create_raw_file(cls, path):
        # Get the directory of the current script
        current_directory = os.path.dirname(__file__)

        # Construct the path to the file
        file_path = os.path.join(current_directory, path)
        _, extension = os.path.splitext(file_path)
        with open(file_path, "rb") as file:
            file_bytes = file.read()
        return SimpleUploadedFile(
            os.path.basename(path),
            file_bytes,
            content_type=f"image/{extension.lower()}",
        )

    @classmethod
    def create_dng_file(cls):
        # See: https://www.rawsamples.ch/
        return cls._create_raw_file(path="./testdata/test.DNG")

    @classmethod
    def create_arw_file(cls):
        # See: https://www.rawsamples.ch/
        return cls._create_raw_file(path="./testdata/test.ARW")

    @classmethod
    def create_image_with_exif(cls):
        """Creates an in-memory image with EXIF metadata, including GPS data."""
        img = Image.new("RGB", (100, 100), color="red")
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"Dummy Camera",
                piexif.ImageIFD.Model: b"Dummy Model",
                piexif.ImageIFD.Software: b"Pillow Test",
                piexif.ImageIFD.DateTime: b"2024:11:05 10:00:00",
                piexif.ImageIFD.Orientation: 1,  # Normal orientation
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: b"2024:11:05 09:00:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: [(34, 1), (0, 1), (0, 1)],  # 34°0'0" N
                piexif.GPSIFD.GPSLongitudeRef: b"E",
                piexif.GPSIFD.GPSLongitude: [(118, 1), (0, 1), (0, 1)],  # 118°0'0" E
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSAltitude: (100, 1),  # 100 meters
            },
        }
        exif_bytes = piexif.dump(exif_dict)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", exif=exif_bytes)
        img.close()
        img_bytes.seek(0)
        return img_bytes

    def test_photo_processing_with_jpeg(self):
        # Test the processing of a standard JPEG image
        photo_instance = Photo.objects.create(
            photo=self.create_image_file("test.jpg", (3000, 4000), format="JPEG"),
            report=self.report,
        )
        self.assert_image_properties(photo_instance)

    def test_photo_processing_with_png(self):
        # Test the processing of a standard JPEG image
        photo_instance = Photo.objects.create(
            photo=self.create_image_file("test.png", (3000, 4000), format="PNG"),
            report=self.report,
        )
        self.assert_image_properties(photo_instance)

    def test_photo_processing_with_heic(self):
        photo_instance = Photo.objects.create(
            photo=self.create_image_file("test.heic", (3000, 4000), format="HEIF"),
            report=self.report,
        )
        self.assert_image_properties(photo_instance)

    def test_small_photo_doest_not_upscale(self):
        photo_instance = Photo.objects.create(
            photo=self.create_image_file("test.heic", (300, 400), format="HEIF"),
            report=self.report,
        )
        self.assert_image_properties(photo_instance, expected_heigt=400)

    def test_photo_processing_with_dng(self):
        photo_instance = Photo.objects.create(
            photo=self.create_dng_file(), report=self.report
        )
        self.assert_image_properties(photo_instance)

    def test_photo_processing_with_arw(self):
        photo_instance = Photo.objects.create(
            photo=self.create_arw_file(), report=self.report
        )
        self.assert_image_properties(photo_instance)

    def assert_image_properties(self, photo_instance, expected_heigt=2160):
        # Refresh from database to get the processed image
        photo_instance.refresh_from_db()

        # Open the processed image to check its properties
        with Image.open(photo_instance.photo.path) as processed_image:
            self.assertEqual(processed_image.height, expected_heigt)
            self.assertEqual(processed_image.format, "JPEG")

    def test_photo_processing_without_exif(self):
        # Create a simple image without EXIF data
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img.close()
        img_bytes.seek(0)

        photo_instance = Photo.objects.create(
            photo=SimpleUploadedFile(
                "test_no_exif.jpg", img_bytes.read(), content_type="image/jpeg"
            ),
            report=self.report,
        )
        photo_instance.refresh_from_db()

        processed_exif = get_full_exif_dict_from_bytes(photo_instance.photo)
        self.assertEqual(processed_exif, {})  # Expecting no EXIF data

    def test_sensitive_exif_data_is_scrubbed(self):
        # Step 1: Create a dummy image with EXIF metadata
        original_img_bytes = self.create_image_with_exif()

        # Step 2: Process the image
        photo_instance = Photo.objects.create(
            photo=SimpleUploadedFile(
                "test_exif.jpg", original_img_bytes.read(), content_type="image/jpeg"
            ),
            report=self.report,
        )
        photo_instance.refresh_from_db()

        processed_exif = get_full_exif_dict_from_bytes(photo_instance.photo)

        # Step 3: Assert EXIF data is the same before and after processing
        self.assertEqual(
            processed_exif,
            {
                "GPSInfo": {
                    piexif.GPSIFD.GPSLatitudeRef: "N",
                    piexif.GPSIFD.GPSLatitude: (34.0, 0.0, 0.0),  # 34°0'0" N
                    piexif.GPSIFD.GPSLongitudeRef: "E",
                    piexif.GPSIFD.GPSLongitude: (118.0, 0.0, 0.0),  # 118°0'0" E
                    piexif.GPSIFD.GPSAltitudeRef: b"\x00",
                    piexif.GPSIFD.GPSAltitude: 100.0,  # 100 meters
                },
                "DateTime": "2024:11:05 10:00:00",
                "DateTimeOriginal": "2024:11:05 09:00:00",
                "Orientation": 1,
            },
        )


class ReportModelTest(TestCase):
    def test_tags_are_set_from_note_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=0,
            current_location_lat=0,
            note="this a dummy note #tag1, with differents #tag2 tags.",
        )

        report.refresh_from_db()

        # Check if tags are correctly set by comparing tag names
        tag_names = list(report.tags.values_list("name", flat=True))
        self.assertEqual(sorted(tag_names), ["tag1", "tag2"])

    def test_tags_from_note_are_unique(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=0,
            current_location_lat=0,
            note="this is a repeated tag #tag1 #tag1 #tag2",
        )

        report.refresh_from_db()

        # Check if tags are correctly set by comparing tag names
        tag_names = list(report.tags.values_list("name", flat=True))
        self.assertEqual(sorted(tag_names), ["tag1", "tag2"])

    def test_report_above_greenland_should_be_marked_as_masked(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=0,
            current_location_lat=84,
        )
        report.refresh_from_db()

        self.assertTrue(report.location_is_masked)

    def test_report_below_antartic_circle_should_be_marked_as_masked(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=-63,
            current_location_lat=-67,
        )
        report.refresh_from_db()

        self.assertTrue(report.location_is_masked)

    def test_report_in_the_ocean_should_be_marked_as_masked(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=0,
            current_location_lat=0,
        )
        report.refresh_from_db()

        self.assertTrue(report.location_is_masked)

    def test_report_in_land_should_not_be_marked_as_masked(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        report.refresh_from_db()

        self.assertFalse(report.location_is_masked)

    def test_device_is_deleted_on_save_failure(self):
        self.assertEqual(Device.objects.all().count(), 0)
        user = TigaUser.objects.create()
        report = Report.objects.create(
            user=user,
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
            device_manufacturer="test_make",
            device_model="test_model",
            os="testOs",
            os_version="testVersion",
            os_language="es-ES",
        )
        self.assertEqual(Device.objects.all().count(), 1)

        device = Device.objects.get(user=user)
        self.assertEqual(device.history.all().count(), 1)

        with self.assertRaises(IntegrityError):
            # Trying to create a new report with the same PK, which will raise.
            _ = Report.objects.create(
                pk=report.pk,
                user=user,
                report_id="1235",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice=Report.LOCATION_CURRENT,
                current_location_lon=41,
                current_location_lat=2,
                device_manufacturer=report.device_manufacturer,
                device_model=report.device_model,
                os=report.os,
                os_version="testVersion2",
                os_language=report.os_language,
            )

        device.refresh_from_db()
        self.assertEqual(device.os_version, "testVersion")
        self.assertEqual(device.history.all().count(), 1)

    def test_mobile_app_is_deleted_on_save_failure(self):
        self.assertEqual(MobileApp.objects.all().count(), 0)
        user = TigaUser.objects.create()
        report = Report.objects.create(
            user=user,
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
            package_name="testapp",
            package_version="100",
        )
        self.assertEqual(MobileApp.objects.all().count(), 1)

        mobile_app = MobileApp.objects.get(
            package_name=report.package_name,
            package_version=semantic_version.Version(
                major=0, minor=int(report.package_version), patch=0, build=("legacy",)
            ),
        )

        with self.assertRaises(IntegrityError):
            # Trying to create a new report with the same PK, which will raise.
            _ = Report.objects.create(
                pk=report.pk,
                user=user,
                report_id="1235",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice=Report.LOCATION_CURRENT,
                current_location_lon=41,
                current_location_lat=2,
                package_name=report.package_name,
                package_version="101",
            )

        mobile_app.refresh_from_db()
        self.assertEqual(str(mobile_app.package_version), "0.100.0+legacy")

    def test_device_is_updated_if_previous_model_exist_and_new_model_None_also(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            user = TigaUser.objects.create()
            device = Device.objects.create(
                user=user,
                model="test_model",
                registration_id="fcm_token",
                active=True,
                active_session=True,
                last_login=timezone.now() - timedelta(days=1),
            )
            _ = Report.objects.create(
                user=user,
                report_id="1234",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice=Report.LOCATION_CURRENT,
                current_location_lon=41,
                current_location_lat=2,
                device_manufacturer="test_make",
                device_model="test_model",
                os="testOs",
                os_version="testVersion",
                os_language="es-ES",
            )

            device.refresh_from_db()
            self.assertEqual(device.model, "test_model")
            self.assertEqual(device.last_login, timezone.now())

            traveller.shift(timedelta(days=1))

            # This would be a post to /api/token/ endpoint.
            device_model_null = Device.objects.create(
                user=user,
                model=None,
                registration_id="new_fcm_token",
                active=True,
                active_session=True,
                last_login=timezone.now() - timedelta(minutes=1),
            )

            device_model_null2 = Device.objects.create(
                user=user,
                model=None,
                registration_id="new_fcm_token2",
                active=True,
                active_session=True,
                last_login=timezone.now(),
            )

            # Creating a new report with the same previous model
            _ = Report.objects.create(
                user=user,
                report_id="1235",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice=Report.LOCATION_CURRENT,
                current_location_lon=41,
                current_location_lat=2,
                device_manufacturer="test_make",
                device_model="test_model",
                os="testOs",
                os_version="testVersion",
                os_language="es-ES",
            )

            device.refresh_from_db()
            self.assertEqual(device.model, "test_model")
            self.assertEqual(device.last_login, timezone.now())
            self.assertEqual(device.registration_id, "new_fcm_token2")

            self.assertRaises(Device.DoesNotExist, device_model_null.refresh_from_db)
            self.assertRaises(Device.DoesNotExist, device_model_null2.refresh_from_db)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_bite_is_published_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_BITE,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        self.assertEqual(report.published_at, timezone.now())
        self.assertEqual(report.published, True)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_bite_is_not_published_if_country_does_not_allow_public_on_create(self):
        disabled_publish_country = EuropeCountry.objects.create(
            cntr_id="RD",
            name_engl="Random",
            iso3_code="RND",
            fid="RD",
            geom=MultiPolygon(Polygon.from_bbox((-10.0, 35.0, 3.5, 44.0))),
        )
        WorkspaceFactory(country=disabled_publish_country, is_public=False)
        point_on_surface = disabled_publish_country.geom.point_on_surface
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_BITE,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=point_on_surface.x,
            current_location_lat=point_on_surface.y,
        )
        self.assertEqual(report.country, disabled_publish_country)
        self.assertIsNone(report.published_at)
        self.assertEqual(report.published, False)

    def test_breeding_site_with_picture_is_published_in_two_days_on_create(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            report = Report.objects.create(
                user=TigaUser.objects.create(),
                report_id="1234",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_SITE,
                location_choice=Report.LOCATION_CURRENT,
                current_location_lon=41,
                current_location_lat=2,
            )
            _ = Photo.objects.create(report=report, photo="./testdata/splash.png")
            report.refresh_from_db()
            self.assertEqual(report.published_at, timezone.now() + timedelta(days=2))
            self.assertEqual(report.published, False)

            traveller.shift(timedelta(days=2))

            self.assertEqual(report.published, True)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_breeding_site_without_picture_is_published_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_SITE,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        self.assertEqual(report.published_at, timezone.now())
        self.assertEqual(report.published, True)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_breeding_site_without_picture_is_not_published_if_country_does_not_allow_public_on_create(
        self,
    ):
        disabled_publish_country = EuropeCountry.objects.create(
            cntr_id="RD",
            name_engl="Random",
            iso3_code="RND",
            fid="RD",
            geom=MultiPolygon(Polygon.from_bbox((-10.0, 35.0, 3.5, 44.0))),
        )
        WorkspaceFactory(country=disabled_publish_country, is_public=False)
        point_on_surface = disabled_publish_country.geom.point_on_surface
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_SITE,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=point_on_surface.x,
            current_location_lat=point_on_surface.y,
        )
        self.assertEqual(report.country, disabled_publish_country)
        self.assertIsNone(report.published_at)
        self.assertEqual(report.published, False)

    def test_adult_without_picture_is_published_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        self.assertEqual(report.published, True)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_adult_without_picture_is_not_published_if_country_does_not_allow_public_on_create(
        self,
    ):
        disabled_publish_country = EuropeCountry.objects.create(
            cntr_id="RD",
            name_engl="Random",
            iso3_code="RND",
            fid="RD",
            geom=MultiPolygon(Polygon.from_bbox((-10.0, 35.0, 3.5, 44.0))),
        )
        WorkspaceFactory(country=disabled_publish_country, is_public=False)
        point_on_surface = disabled_publish_country.geom.point_on_surface
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=point_on_surface.x,
            current_location_lat=point_on_surface.y,
        )
        self.assertEqual(report.country, disabled_publish_country)
        self.assertIsNone(report.published_at)
        self.assertEqual(report.published, False)

    def test_adult_with_picture_is_not_published_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        _ = Photo.objects.create(report=report, photo="./testdata/splash.png")
        report.refresh_from_db()
        self.assertEqual(report.published, False)

    def test_mission_is_not_published_on_create(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_MISSION,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        self.assertEqual(report.published, False)

    def test_published_report_is_unpublished_if_hide(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        report.published_at = timezone.now()
        report.save()

        self.assertEqual(report.published, True)

        report.hide = True
        report.save()

        self.assertEqual(report.published, False)

    def test_published_report_is_unpublished_if_tag_345(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_BITE,
            published_at=timezone.now(),
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
            note="#345",
        )

        self.assertEqual(report.tags.filter(name="345").exists(), True)

        self.assertEqual(report.hide, True)
        self.assertEqual(report.published, False)

    def test_published_report_is_unpublished_if_soft_deleted(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        report.published_at = timezone.now()
        report.save()

        self.assertEqual(report.published, True)

        report.soft_delete()

        self.assertEqual(report.published, False)

    def test_published_report_is_unpublished_if_location_is_masked(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_BITE,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )
        report.published_at = timezone.now()
        report.save()

        self.assertEqual(report.published, True)

        report.location_choice = Report.LOCATION_CURRENT
        report.current_location_lon = 0
        report.current_location_lat = 84
        report.save()

        self.assertEqual(report.published, False)

    def test_published_and_hide_raise_IntegrityError(self):
        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice=Report.LOCATION_CURRENT,
            current_location_lon=41,
            current_location_lat=2,
        )

        with self.assertRaises(IntegrityError):
            Report.objects.filter(pk=report.pk).update(
                hide=True, published_at=timezone.now()
            )

    def test_lau_fk_is_set_on_create(self):
        lau = LauEurope.objects.create(
            fid="test_lau_id",
            lau_id="test_lau_id",
            lau_name="test_lau_name",
            geom=MultiPolygon(Polygon.from_bbox((-10, 40, 10, 60))),
        )

        point = lau.geom.point_on_surface

        report = Report.objects.create(
            user=TigaUser.objects.create(),
            report_id="1234",
            phone_upload_time=timezone.now(),
            creation_time=timezone.now(),
            version_time=timezone.now(),
            type=Report.TYPE_ADULT,
            location_choice="current",
            current_location_lon=point.x,
            current_location_lat=point.y,
        )

        assert report.lau_fk == lau

    def test_report_location_is_forced_if_missing(self):
        for t, _ in Report.TYPE_CHOICES:
            report = Report.objects.create(
                user=TigaUser.objects.create(),
                report_id="1234",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=t,
            )

            report.refresh_from_db()

            if t != Report.TYPE_MISSION:
                self.assertEqual(report.location_choice, Report.LOCATION_SELECTED)
                self.assertEqual(report.current_location_lon, 0)
                self.assertEqual(report.current_location_lat, 0)
                self.assertEqual(report.location_is_masked, True)
            else:
                self.assertEqual(report.location_choice, "")
                self.assertIsNone(report.current_location_lon)
                self.assertIsNone(report.current_location_lat)

    def test_report_location_is_used_on_user_last_location(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            user = TigaUser.objects.create(
                last_location=None, last_location_update=None
            )

            report_point = Point(x=10, y=10, srid=4326)
            report = Report.objects.create(
                user=user,
                report_id="1234",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice="current",
                current_location_lon=report_point.x,
                current_location_lat=report_point.y,
            )

            user.refresh_from_db()
            self.assertEqual(user.last_location, report_point)
            self.assertEqual(user.last_location_update, report.server_upload_time)

            traveller.shift(timedelta(days=1))

            new_report_point = Point(x=5, y=5, srid=4326)
            new_report = Report.objects.create(
                user=user,
                report_id="1235",
                phone_upload_time=timezone.now(),
                creation_time=timezone.now(),
                version_time=timezone.now(),
                type=Report.TYPE_ADULT,
                location_choice="current",
                current_location_lon=new_report_point.x,
                current_location_lat=new_report_point.y,
            )

            user.refresh_from_db()
            self.assertEqual(user.last_location, new_report_point)
            self.assertEqual(user.last_location_update, new_report.server_upload_time)
