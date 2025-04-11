import pytest

from tigaserver_app.models import Photo

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Photo

@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.report.pk}/photos"

@pytest.fixture
def extra_photo(identification_task, dummy_image):
    return Photo.objects.create(
        photo=dummy_image,
        report=identification_task.report,
    )