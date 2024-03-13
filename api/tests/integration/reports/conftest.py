from pathlib import Path
import pytest

from tigapublic.models import MapAuxReports
from tigaserver_app.models import Report


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report


@pytest.fixture
def published_adult_report(adult_report):
    _ = MapAuxReports.objects.get_or_create(
        version_uuid=adult_report,
        defaults={
            "user_id": adult_report.user.pk,
            "ref_system": 4326,
            "type": adult_report.type,
            "final_expert_status": 1,
            "visible": True,
        },
    )
    return adult_report


@pytest.fixture
def deleted_adult_report(adult_report):
    adult_report.soft_delete()

    return adult_report


@pytest.fixture
def deleted_published_adult_report(deleted_adult_report):
    _ = MapAuxReports.objects.get_or_create(
        version_uuid=deleted_adult_report,
        defaults={
            "user_id": deleted_adult_report.user.pk,
            "ref_system": 4326,
            "type": deleted_adult_report.type,
            "final_expert_status": 1,
            "visible": True,
        },
    )
    return deleted_adult_report


@pytest.fixture
def test_data_path():
    return Path(Path(__file__).parent.absolute(), "test_data/")


@pytest.fixture
def test_png_image_path(test_data_path):
    return Path(test_data_path, Path("white_image.png"))


@pytest.fixture
def test_jpg_image_path(test_data_path):
    return Path(test_data_path, Path("black_image.jpg"))


@pytest.fixture
def test_non_image_path(test_data_path):
    return Path(test_data_path, Path("non_image.txt"))
