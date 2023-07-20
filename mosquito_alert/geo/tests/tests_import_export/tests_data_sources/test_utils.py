import os
from contextlib import nullcontext as does_not_raise

import pytest
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Point, Polygon
from requests.exceptions import HTTPError

from ....import_export.data_sources.utils import (
    download_file,
    get_biggest_polygon,
    get_country_from_iso_code,
    get_language_from_iso_code,
)


def test_download_file_creates_tmpfile_if_args_None(mocker, tmp_path, requests_mock):
    m_tmpfile = mocker.patch("tempfile.NamedTemporaryFile")
    dummy_file_path = tmp_path / "tmpfile.txt"
    m_tmpfile.return_value.name = dummy_file_path

    URL = "http://example.com/file.txt"
    requests_mock.get(URL, content=b"data")

    f = download_file(url=URL, filename=None)

    assert str(f) == str(dummy_file_path)
    assert open(dummy_file_path).read() == "data"


def test_download_file_raise_if_status_is_not_200(tmp_path, requests_mock):
    URL = "http://example.com/file.txt"
    requests_mock.get(URL, content=b"data", status_code=400)

    tmp_file = os.path.join(tmp_path, "file.txt")

    with pytest.raises(HTTPError):
        _ = download_file(url=URL, filename=tmp_file)


def test_download_file_returns_file_with_content(tmp_path, requests_mock):
    tmp_file = os.path.join(tmp_path, "file.txt")

    URL = "http://example.com/file.txt"
    requests_mock.get(URL, content=b"data")
    f = download_file(url=URL, filename=tmp_file)

    assert open(f).read() == "data"


@pytest.mark.parametrize(
    "language_iso, expected_iso2, expected_iso3, error",
    [
        ("es", "es", "spa", does_not_raise()),
        ("ES", "es", "spa", does_not_raise()),
        ("eS", "es", "spa", does_not_raise()),
        ("spa", "es", "spa", does_not_raise()),
        ("SPA", "es", "spa", does_not_raise()),
        ("xyz", None, None, pytest.raises(KeyError)),
        ("long-iso-language", None, None, pytest.raises(ValueError)),
    ],
)
def test_get_language_from_iso_code(language_iso, expected_iso2, expected_iso3, error):
    with error:
        lang = get_language_from_iso_code(language_iso=language_iso)
        assert lang.alpha_2 == expected_iso2
        assert lang.alpha_3 == expected_iso3


@pytest.mark.parametrize(
    "country_iso, expected_iso2, expected_iso3, error",
    [
        ("es", "ES", "ESP", does_not_raise()),
        ("ES", "ES", "ESP", does_not_raise()),
        ("eS", "ES", "ESP", does_not_raise()),
        ("esp", "ES", "ESP", does_not_raise()),
        ("ESP", "ES", "ESP", does_not_raise()),
        ("xyz", None, None, pytest.raises(KeyError)),
        ("long-iso-language", None, None, pytest.raises(ValueError)),
    ],
)
def test_get_country_from_iso_code(country_iso, expected_iso2, expected_iso3, error):
    with error:
        lang = get_country_from_iso_code(country_iso=country_iso)
        assert lang.alpha_2 == expected_iso2
        assert lang.alpha_3 == expected_iso3


@pytest.mark.parametrize(
    "geometry, expected_output, error",
    [
        (
            Polygon.from_bbox(bbox=(0, 0, 10, 10)),
            Polygon.from_bbox(bbox=(0, 0, 10, 10)),
            does_not_raise(),
        ),
        (
            MultiPolygon(Polygon.from_bbox(bbox=(0, 0, 10, 10))),
            Polygon.from_bbox(bbox=(0, 0, 10, 10)),
            does_not_raise(),
        ),
        (
            MultiPolygon(
                Polygon.from_bbox(bbox=(0, 0, 1, 1)),
                Polygon.from_bbox(bbox=(0, 0, 10, 10)),
            ),
            Polygon.from_bbox(bbox=(0, 0, 10, 10)),
            does_not_raise(),
        ),
        (
            Point(0, 0),
            None,
            pytest.raises(ValueError),
        ),
        (
            MultiPoint(Point(0, 0)),
            None,
            pytest.raises(ValueError),
        ),
        (
            "random string",
            None,
            pytest.raises(ValueError),
        ),
    ],
)
def test_get_biggest_polygon_single_poly_should_return(geometry, expected_output, error):
    with error:
        assert get_biggest_polygon(geometry=geometry) == expected_output
