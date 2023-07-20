from argparse import ArgumentParser
from contextlib import nullcontext as does_not_raise

import pytest

from mosquito_alert.geo.import_export.data_sources.boundaries import GadmBoundarySource, NutsBoundarySource
from mosquito_alert.geo.models import BoundaryLayer


class TestNutsBoundarySource:
    def test_CLI_NAME_is_nuts(self):
        assert NutsBoundarySource.CLI_NAME == "nuts"

    def test_default_bl_type_is_stats(self):
        assert NutsBoundarySource.DEFAULT_BOUNDARY_LEVEL_TYPE == BoundaryLayer.BoundaryType.STATISTICAL

    def test_custom_arguments(self):
        obj = NutsBoundarySource

        dummy_parser = ArgumentParser()
        dummy_parser.add_argument("--init", required=False)
        obj.add_arguments(parser=dummy_parser)

        name_space = dummy_parser.parse_args(["--level", "0"])
        assert "init" in name_space
        assert "level" in name_space
        assert "db_version" in name_space
        assert "scale" in name_space
        assert "coor" in name_space

    def test_from_online_source(self, mocker):
        m = mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        NutsBoundarySource.from_online_source(db_version="2021", scale="60M", coor="4326", level="0")

        vsi_handlers = "/vsizip//vsicurl/"
        url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/shp/NUTS_RG_60M_2021_4326_LEVL_0.shp.zip"
        inner_file = "NUTS_RG_60M_2021_4326_LEVL_0.shp"
        m.assert_called_once_with(f"{vsi_handlers}{url}/{inner_file}")

    @pytest.mark.parametrize(
        "level, error",
        [
            (-1, pytest.raises(ValueError)),
            (0, does_not_raise()),
            (1, does_not_raise()),
            (2, does_not_raise()),
            (3, does_not_raise()),
            (4, pytest.raises(ValueError)),
        ],
    )
    def test__init__level_argument(self, mocker, level, error):
        mocker.patch(
            "mosquito_alert.geo.import_export.data_sources.boundaries.boundaries.uri_to_vsi_path",
            return_value=None,
        )
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        with error:
            _ = NutsBoundarySource(uri=None, level=level)

    @pytest.mark.parametrize(
        "uri, expected_result",
        [
            (
                "http://example.com/path/to/file.shp",
                "/vsicurl/http://example.com/path/to/file.shp",
            ),
            (
                "http://example.com/path/to/file.shp.zip",
                "/vsizip//vsicurl/http://example.com/path/to/file.shp.zip",
            ),
            (
                "http://example.com/path/to/file.shp.zip!file0.shp",
                "/vsizip//vsicurl/http://example.com/path/to/file.shp.zip/file0.shp",
            ),
        ],
    )
    def test__init__uri(self, mocker, uri, expected_result):
        m = mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        _ = NutsBoundarySource(uri=uri, level=0)

        m.assert_called_once_with(expected_result)

    def test_code_field_name_is_NUTS_ID(self, mocker):
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        obj = NutsBoundarySource(uri="http://example.com", level=0)

        assert obj.code_field_name == "NUTS_ID"

    def test_level_name_is_NUTS_and_level(self, mocker):
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        obj = NutsBoundarySource(uri="http://example.com", level=0)

        assert obj.level_name == "NUTS 0"
        obj.level = 1
        assert obj.level_name == "NUTS 1"

    def test_name_field_name_is_NAME_LATN(self, mocker):
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        obj = NutsBoundarySource(uri="http://example.com", level=0)

        assert obj.name_field_name == "NAME_LATN"


class TestGadmBoundarySource:
    def test_CLI_NAME_is_nuts(self):
        assert GadmBoundarySource.CLI_NAME == "gadm"

    def test_default_bl_type_is_adm(self):
        assert GadmBoundarySource.DEFAULT_BOUNDARY_LEVEL_TYPE == BoundaryLayer.BoundaryType.ADMINISTRATIVE

    def test_custom_arguments(self):
        obj = GadmBoundarySource

        dummy_parser = ArgumentParser()
        dummy_parser.add_argument("--init", required=False)
        obj.add_arguments(parser=dummy_parser)

        name_space = dummy_parser.parse_args(["--level", "0", "--country", "ES"])
        assert "init" in name_space
        assert "country_code" in name_space

    def test_from_online_source(self, mocker):
        m = mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        GadmBoundarySource.from_online_source(db_version="4.1", country_code="ES", level=0)

        vsi_handlers = "/vsizip//vsicurl/"
        url = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_ESP_shp.zip"
        inner_file = "gadm41_ESP_0.shp"
        m.assert_called_once_with(f"{vsi_handlers}{url}/{inner_file}")

    @pytest.mark.parametrize(
        "uri, expected_result",
        [
            (
                "http://example.com/path/to/file.shp",
                "/vsicurl/http://example.com/path/to/file.shp",
            ),
            (
                "http://example.com/path/to/file.shp.zip",
                "/vsizip//vsicurl/http://example.com/path/to/file.shp.zip",
            ),
            (
                "http://example.com/path/to/file.shp.zip!file0.shp",
                "/vsizip//vsicurl/http://example.com/path/to/file.shp.zip/file0.shp",
            ),
        ],
    )
    def test__init__uri(self, mocker, uri, expected_result):
        m = mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        _ = GadmBoundarySource(uri=uri, level=0)

        m.assert_called_once_with(expected_result)

    def test_code_field_name_depends_on_level(self, mocker):
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        obj = GadmBoundarySource(uri="http://example.com", level=0)

        assert obj.code_field_name == "GID_0"
        obj.level = 1
        assert obj.code_field_name == "GID_1"

    def test_name_field_name(self, mocker):
        mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__",
            return_value=None,
        )

        obj = GadmBoundarySource(uri="http://example.com", level=0)

        assert obj.name_field_name == "COUNTRY"
        obj.level = 1
        assert obj.name_field_name == "NAME_1"
