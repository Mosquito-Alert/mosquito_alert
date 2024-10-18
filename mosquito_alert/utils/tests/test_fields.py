import pytest

from ..fields import ShortIDField
from .models import DummyShortIDModel


@pytest.mark.django_db
class TestShortIDField:
    def test_short_id_length(self):
        instance = DummyShortIDModel.objects.create()
        assert instance.short_id is not None
        assert len(instance.short_id) == 11  # Ensure length matches the specified size

    def test_short_id_is_url_safe(self):
        instance = DummyShortIDModel.objects.create()
        assert all(c.isalnum() or c in "-_" for c in instance.short_id)  # Check for URL-safe characters

    def test_short_id_uniqueness(self):
        instances = [DummyShortIDModel.objects.create() for _ in range(100)]  # Create multiple instances
        short_ids = [instance.short_id for instance in instances]
        assert len(short_ids) == len(set(short_ids))  # Ensure all short IDs are unique

    def test_short_id_generation_on_create(self):
        instance1 = DummyShortIDModel.objects.create()
        instance2 = DummyShortIDModel.objects.create()
        assert instance1.short_id != instance2.short_id  # Ensure different IDs are generated

    def test_size_is_required(self):
        with pytest.raises(TypeError) as excinfo:
            ShortIDField()  # Attempt to create a ShortIDField without the size parameter
        assert "missing 1 required positional argument: 'size'" in str(excinfo.value)

    @pytest.mark.parametrize("size", [-1, 0, "str", None, 1.5])
    def test_size_raise_if_not_positive_integer(self, size):
        with pytest.raises(ValueError):
            ShortIDField(size=size)
