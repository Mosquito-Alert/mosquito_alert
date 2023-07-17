import os
from argparse import ArgumentParser

import pytest
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Point, Polygon
from geopy.extra.rate_limiter import RateLimiter
from geopy.location import Location as GeopyLocation
from geopy.point import Point as GeopyPoint

from ....import_export.data_sources.names import (
    BaseBoundaryNameDataSource,
    GeonamesDataSource,
    Location,
    NominatimDataSource,
)


class ConcreteBaseBoundaryNameDataSource(BaseBoundaryNameDataSource):
    CLI_NAME = "test_cli"

    LOCATION_DICT = {"loc_key1": "loc_val1"}

    # Implement dummy abstractmethods
    def _add_custom_arguments(parser):
        pass

    def reverse(self, geometry, location_type, language_iso="en", exactly_one=True):
        pass


class TestBaseBoundaryNameDataSource:
    def test_location_type_in_arguments(self):
        obj = ConcreteBaseBoundaryNameDataSource()

        dummy_parser = ArgumentParser()
        dummy_parser.add_argument("--init", required=False)
        obj.add_arguments(parser=dummy_parser)

        storeaction = next(
            a for a in dummy_parser._actions if "--location_type" in a.option_strings
        )

        assert list(storeaction.choices) == ["loc_key1"]

        name_space = dummy_parser.parse_args([])
        assert "init" in name_space
        assert "location_type" in name_space

    def test_get_field_by_location_type(self):
        value = ConcreteBaseBoundaryNameDataSource.get_field_by_location_type(
            value="loc_key1"
        )
        assert value == "loc_val1"

    def test_get_field_by_invalid_location_type_should_raise_ValueError(self):
        with pytest.raises(ValueError):
            ConcreteBaseBoundaryNameDataSource.get_field_by_location_type(
                value="random_test"
            )


class TestNominatimDataSource:
    @pytest.fixture
    def single_reverse_result(self):
        return GeopyLocation(
            address="Random address",
            point=(41.67, 2.784),
            raw={
                "place_id": 11111,
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
                "osm_type": "way",
                "osm_id": 11111,
                "lat": "41.67",
                "lon": "2.784",
                "display_name": "Test Street",
                "address": {
                    "road": "Test Street",
                    "neighbourhood": "Test Hood",
                    "town": "Test Town",
                    "county": "Test Country",
                    "state_district": "Test state_districut",
                    "ISO3166-2-lvl6": "ES-GI",
                    "state": "Test State",
                    "ISO3166-2-lvl4": "ES-CT",
                    "postcode": "17300",
                    "country": "Test Country",
                    "country_code": "es",
                },
                "boundingbox": ["41.6712937", "41.6733194", "2.7830637", "2.7871309"],
            },
        )

    @pytest.fixture
    def multi_reverse_result(self, single_reverse_result):
        return [single_reverse_result, single_reverse_result]

    def test_cli_name_is_nominatim(self):
        assert NominatimDataSource.CLI_NAME == "nominatim"

    def test_location_dict(self):
        assert NominatimDataSource.LOCATION_DICT == {
            "country": "country",
            "state": "state",
            "county": "county",
            "province": "county",
            "village": "village",
        }

    def test_location_type_in_arguments(self):
        obj = NominatimDataSource()

        dummy_parser = ArgumentParser()
        obj.add_arguments(parser=dummy_parser)

        storeaction = next(
            a for a in dummy_parser._actions if "--location_type" in a.option_strings
        )

        assert frozenset(list(storeaction.choices)) == frozenset(
            NominatimDataSource.LOCATION_DICT.keys()
        )

    def test_geopy_is_called_on_init_with_custom_user_agent(self, mocker):
        m = mocker.patch(
            "geopy.geocoders.nominatim.Nominatim.__init__", return_value=None
        )
        mocker.patch("random.choices", return_value="rnd_test")
        _ = NominatimDataSource()
        m.assert_called_once_with(user_agent="mosquito_alert_rnd_test")

    def test_init_rate_limiter(self):
        obj = NominatimDataSource()
        assert isinstance(obj._reverse_func, RateLimiter)

    def test_rate_limiter_has_1_seconds_delay(self):
        obj = NominatimDataSource()
        assert obj._reverse_func.min_delay_seconds == 1

    def test_reverse_uses_rate_limiter(self, mocker, single_reverse_result):
        obj = NominatimDataSource()
        m = mocker.patch.object(
            obj, "_reverse_func", return_value=single_reverse_result
        )

        obj.reverse(geometry=Point(0, 0), location_type="country")
        m.assert_called_once()

    def test_reverse_returns_None_if_location_type_not_in_response(
        self, mocker, multi_reverse_result
    ):
        obj = NominatimDataSource()
        mocker.patch.object(obj, "_reverse_func", return_value=multi_reverse_result)

        result = obj.reverse(geometry=Point(0, 0), location_type="village")

        assert result is None

    def test_reverse_can_deal_with_multiple_response(
        self, mocker, multi_reverse_result
    ):
        obj = NominatimDataSource()
        mocker.patch.object(obj, "_reverse_func", return_value=multi_reverse_result)

        obj.reverse(
            geometry=Point(0, 0),
            location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
        )

    def test_reverse_with_simple_polygon(self, mocker, multi_reverse_result):
        obj = NominatimDataSource()
        m = mocker.patch.object(obj, "_reverse_func", return_value=multi_reverse_result)

        poly = Polygon.from_bbox(bbox=(0, 0, 10, 10))

        obj.reverse(
            geometry=poly,
            location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
        )

        m.assert_called_once_with(
            query=GeopyPoint(5, 5),
            exactly_one=True,
            language="en",
            addressdetails=True,
            namedetails=False,
        )

    def test_reverse_with_multi_polygon(self, mocker, multi_reverse_result):
        obj = NominatimDataSource()
        m = mocker.patch.object(obj, "_reverse_func", return_value=multi_reverse_result)

        big_poly = Polygon.from_bbox(bbox=(0, 0, 10, 10))
        small_poly = Polygon.from_bbox(bbox=(100, 100, 101, 101))
        m_poly = MultiPolygon(small_poly, big_poly)

        obj.reverse(
            geometry=m_poly,
            location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
        )

        m.assert_called_once_with(
            query=GeopyPoint(5, 5),  # Gather a point inside big_poly
            exactly_one=True,
            language="en",
            addressdetails=True,
            namedetails=False,
        )

    def test_reverse_with_single_point(self, mocker, multi_reverse_result):
        obj = NominatimDataSource()
        m = mocker.patch.object(obj, "_reverse_func", return_value=multi_reverse_result)

        point = Point(5, 5)

        obj.reverse(
            geometry=point,
            location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
        )

        m.assert_called_once_with(
            query=GeopyPoint(5, 5),  # Gather a point inside big_poly
            exactly_one=True,
            language="en",
            addressdetails=True,
            namedetails=False,
        )

    def test_reverse_with_multipoint_point_raise_ValueError(self):
        obj = NominatimDataSource()

        with pytest.raises(ValueError):
            obj.reverse(
                geometry=MultiPoint(),
                location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
            )

    def test_reverse_with_invalid_geometry_should_raise_ValueError(self):
        obj = NominatimDataSource()

        with pytest.raises(ValueError):
            obj.reverse(
                geometry="string",
                location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
            )

    def test_reverse_with_invalid_location_type_should_raise_ValueError(self):
        obj = NominatimDataSource()

        with pytest.raises(ValueError):
            obj.reverse(geometry=Point(0, 0), location_type="random_loc")

    def test_reverse_with_invalid_language_iso_should_raise_KeyError(self):
        obj = NominatimDataSource()

        with pytest.raises(KeyError):
            obj.reverse(
                geometry=Point(0, 0),
                location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
                language_iso="rne",  # rne does not exist
            )

    def test_reverse_with_invalid_language_arg_should_raise_ValueError(self):
        obj = NominatimDataSource()

        with pytest.raises(ValueError):
            obj.reverse(
                geometry=Point(0, 0),
                location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
                language_iso="random language",  # rne does not exist
            )

    def test_reverse_geometry_does_not_match(self, mocker):
        # geopy returns none if geometry not match
        # for example, if trying to resolve a point in the middle of the indic ocean
        # e.x: (-24.883590, 79.177107)

        # Mocking reverse function to return None
        obj = NominatimDataSource()
        mocker.patch.object(obj, "_reverse_func", return_value=None)

        result = obj.reverse(
            geometry=Point(-24.883590, 79.177107),
            location_type=list(NominatimDataSource.LOCATION_DICT.keys())[0],
        )

        assert result is None

    def test_reverse_returns_location_object(self, mocker, single_reverse_result):
        obj = NominatimDataSource()
        mocker.patch.object(obj, "_reverse_func", return_value=single_reverse_result)

        result = obj.reverse(
            geometry=Point(0, 0), location_type="country", language_iso="en"
        )

        assert result == Location(
            latitude=41.67,
            longitude=2.784,
            name="Test Country",
            lang="en",
            category="country",
        )


class TestGeonamesDataSource:
    @pytest.fixture
    def file_path(self):
        return os.path.join(os.path.dirname(__file__), "files", "names")

    @pytest.fixture
    def geoname_filepath(self, file_path):
        return os.path.join(file_path, "dummy_geonames.txt")

    @pytest.fixture
    def alternate_names_filepath(self, file_path):
        return os.path.join(file_path, "dummy_altnames.txt")

    @pytest.fixture
    def geomnames_ds(self, geoname_filepath, alternate_names_filepath):
        return GeonamesDataSource(
            geonames_filepath=geoname_filepath,
            alternate_names_filepath=alternate_names_filepath,
        )

    def test_cli_name_is_geonames(self):
        assert GeonamesDataSource.CLI_NAME == "geonames"

    def test_location_dict(self):
        assert GeonamesDataSource.LOCATION_DICT == {
            "state": "ADM1",
            "province": "ADM2",
            "county": "ADM2",
            "region": "ADMD",
            "village": "ADM3",
        }

    def test_location_type_in_arguments(self):
        obj = GeonamesDataSource

        dummy_parser = ArgumentParser()
        obj.add_arguments(parser=dummy_parser)

        # Is required
        name_space = dummy_parser.parse_args(["--country_iso", "ES"])
        assert "country_iso" in name_space
        assert "filters" in name_space

    def test_create_for_country_call_from_online_source(self, mocker):
        m = mocker.patch.object(
            GeonamesDataSource, "from_online_source", return_value=None
        )
        GeonamesDataSource.create_for_country(country_iso="iso")

        m.assert_called_once_with(country_iso="iso")

    def test_from_online_source_invalid_language_iso_should_raise(self):
        with pytest.raises(KeyError):
            GeonamesDataSource.from_online_source(country_iso="RND")

    def test_from_online_source_calls_correct_urls(
        self, mocker, module_mocker, tmp_path
    ):
        m_tmpfile = mocker.patch("tempfile.NamedTemporaryFile")

        dummy_file_path = tmp_path / "tmpfile.zip"
        m_tmpfile.return_value.__enter__.return_value.name = dummy_file_path

        m_download_file = mocker.patch(
            "mosquito_alert.geo.import_export.data_sources.base.download_file",
            return_value=None,
        )
        mocker.patch.object(GeonamesDataSource, "__init__", return_value=None)

        GeonamesDataSource.from_online_source(country_iso="ES")

        m_download_file.assert_has_calls(
            [
                module_mocker.call(
                    url="http://download.geonames.org/export/dump/ES.zip",
                    filename=dummy_file_path,
                ),
                module_mocker.call(
                    url="http://download.geonames.org/export/dump/alternatenames/ES.zip",
                    filename=dummy_file_path,
                ),
            ]
        )

    @pytest.mark.parametrize(
        "filters, expected_num",
        [({}, 145), ({"featurecode": "PPLA"}, 0), ({"featurecode": "ADM3"}, 145)],
    )
    def test_init_with_filter(
        self, geoname_filepath, alternate_names_filepath, filters, expected_num
    ):
        obj = GeonamesDataSource(
            geonames_filepath=geoname_filepath,
            alternate_names_filepath=alternate_names_filepath,
            filters=filters,
        )

        assert len(obj.df) == expected_num

    def test_reverse_returns_None_if_location_type_not_in_response(self, geomnames_ds):
        result = geomnames_ds.reverse(
            geometry=Polygon.from_bbox(bbox=(-65, 18, -60, 20)), location_type="county"
        )

        assert result is None

    def test_reverse_with_simple_polygon(self, geomnames_ds):
        poly = Polygon.from_bbox(bbox=(-65, 18, -60, 20))

        result = geomnames_ds.reverse(
            geometry=poly, location_type="village", language_iso="eng"
        )

        assert result == Location(
            latitude=18.21667,
            longitude=-63.05,
            name="Anguilla",
            lang="eng",
            category="village",
        )

    @pytest.mark.parametrize(
        "language_iso,expected_name",
        [("eng", "Anguilla"), ("cat", "Anguilla"), ("zh", "安圭拉"), ("jpn", None)],
    )
    def test_reverse_with_languages(self, geomnames_ds, language_iso, expected_name):
        poly = Polygon.from_bbox(bbox=(-65, 18, -60, 20))

        result = geomnames_ds.reverse(
            geometry=poly, location_type="village", language_iso=language_iso
        )

        assert result == Location(
            latitude=18.21667,
            longitude=-63.05,
            name=expected_name,
            lang=language_iso,
            category="village",
        )

    def test_reverse_with_multi_polygon(self, geomnames_ds):
        poly = Polygon.from_bbox(bbox=(-65, 18, -60, 20))
        m_poly = MultiPolygon()
        m_poly.append(poly)

        result = geomnames_ds.reverse(
            geometry=m_poly, location_type="village", language_iso="eng"
        )

        assert result == Location(
            latitude=18.21667,
            longitude=-63.05,
            name="Anguilla",
            lang="eng",
            category="village",
        )

    def test_reverse_with_single_point_raise_ValueError(self, geomnames_ds):
        point = Point(18.21667, -63.05)

        with pytest.raises(ValueError):
            _ = geomnames_ds.reverse(
                geometry=point, location_type="village", language_iso="eng"
            )

    def test_reverse_with_invalid_geometry_should_raise_ValueError(self, geomnames_ds):
        with pytest.raises(ValueError):
            geomnames_ds.reverse(
                geometry="string", location_type="village", language_iso="eng"
            )

    def test_reverse_with_invalid_location_type_should_raise_ValueError(
        self, geomnames_ds
    ):
        with pytest.raises(ValueError):
            geomnames_ds.reverse(
                geometry=Polygon.from_bbox(bbox=(-65, 18, -60, 20)),
                location_type="random_loc",
            )

    def test_reverse_with_invalid_language_iso_should_raise_KeyError(
        self, geomnames_ds
    ):
        with pytest.raises(KeyError):
            geomnames_ds.reverse(
                geometry=Polygon.from_bbox(bbox=(-65, 18, -60, 20)),
                location_type="village",
                language_iso="rne",  # rne does not exist
            )

    def test_reverse_with_invalid_language_arg_should_raise_ValueError(
        self, geomnames_ds
    ):
        with pytest.raises(ValueError):
            geomnames_ds.reverse(
                geometry=Polygon.from_bbox(bbox=(-65, 18, -60, 20)),
                location_type="village",
                language_iso="random language",  # rne does not exist
            )

    def test_reverse_geometry_does_not_match(self, geomnames_ds):
        result = geomnames_ds.reverse(
            geometry=Polygon.from_bbox(bbox=(0, 0, 1, 1)),
            location_type="village",
        )

        assert result is None

    def test_get_by_id_work(self, geomnames_ds):
        assert geomnames_ds.get_by_id(id=3573511).name == 3573511

    def test_get_by_id_not_exist_should_raise_keyerror(self, geomnames_ds):
        with pytest.raises(KeyError):
            geomnames_ds.get_by_id(id=0)

    def test_get_id_by_name(self, geomnames_ds):
        assert geomnames_ds.get_id_by_name(name="Anguilla") == 3573511

    def test_get_id_by_name_not_found_should_raise_keyerror(self, geomnames_ds):
        with pytest.raises(KeyError):
            geomnames_ds.get_id_by_name(name="Other Name")

    @pytest.mark.parametrize(
        "lang_iso, expected_result",
        [("eng", "Anguilla"), ("cat", "Anguilla"), (None, "Anguilla")],
    )
    def test_get_locale_by_id(self, geomnames_ds, lang_iso, expected_result):
        assert (
            geomnames_ds.get_locale_by_id(id=3573511, language_iso=lang_iso)
            == expected_result
        )

    def test_search(self, geomnames_ds):
        # TODO
        assert len(list(geomnames_ds.search(name="Anguilla"))) == 145
