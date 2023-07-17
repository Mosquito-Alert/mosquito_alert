from collections import OrderedDict

import pytest

from ...import_export.formats import ZippedShapefileFormat


class DummyGdalDataSource:
    def __init__(self, layers):
        self.layers = layers

    def __getitem__(self, index):
        return self.layers[index]


class DummyGdalLayer:
    fields = ["name", "code"]

    def __init__(self, features):
        self.features = features

    def __iter__(self):
        return self.features.__iter__()


class DummyGdalFeature:
    def __init__(self, name, code, geom):
        self.name = name
        self.code = code
        self.geom = geom

    def get(self, value):
        return getattr(self, value)


@pytest.fixture
def gdal_ds():
    features = [
        DummyGdalFeature(name="feat1", code="f1", geom="geom1"),
        DummyGdalFeature(name="feat2", code="f2", geom="geom2"),
    ]

    layers = [DummyGdalLayer(features=features)]

    return DummyGdalDataSource(layers=layers)


class TestZippedShapefileFormat:
    obj = ZippedShapefileFormat()

    def test_get_title(self):
        assert self.obj.get_title() == "zipped shp"

    def test_create_dataset(self, gdal_ds):
        dataset = self.obj.create_dataset(in_stream=gdal_ds)

        assert frozenset(dataset.headers) == frozenset(["name", "code", "geometry"])
        assert dataset.dict == [
            OrderedDict([("name", "feat1"), ("code", "f1"), ("geometry", "geom1")]),
            OrderedDict([("name", "feat2"), ("code", "f2"), ("geometry", "geom2")]),
        ]

    def test_get_extension(self):
        assert self.obj.get_extension() == "shp.zip"
