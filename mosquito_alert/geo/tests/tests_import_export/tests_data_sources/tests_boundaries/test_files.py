from contextlib import nullcontext as does_not_raise

import pytest

from mosquito_alert.geo.import_export.data_sources.boundaries.files import (
    BucketGdalFileHandler,
    CompressedGdalFile,
    OnlineGdalFileHandler,
    uri_to_vsi_path,
)


@pytest.mark.parametrize(
    "uri, options, expected_output, error",
    [
        (
            "http://example.com/path/to/file.txt",
            {},
            "/vsicurl/http://example.com/path/to/file.txt",
            does_not_raise(),
        ),
        (
            "http://example.com/path/to/file.txt",
            {},
            "/vsicurl/http://example.com/path/to/file.txt",
            does_not_raise(),
        ),
        (
            "ftp://path/to/remote/resource",
            {},
            "/vsicurl/ftp://path/to/remote/resource",
            does_not_raise(),
        ),
        (
            "ssh://path/to/remote/resource",
            {},
            None,
            pytest.raises(ValueError),
        ),
        (
            "http://example.com/path/to/file.txt",
            {"param1": "value1", "param2": "value2"},
            "/vsicurl?param1=value1&param2=value2&url=http://example.com/path/to/file.txt",
            does_not_raise(),
        ),
        (
            "http://example.com/path/to/file.zip",
            {"param1": "value1", "param2": "value2"},
            "/vsizip//vsicurl?param1=value1&param2=value2&url=http://example.com/path/to/file.zip",
            does_not_raise(),
        ),
        (
            "http://example.com/path/to/file.zip!path/to/innferfile.txt",
            {"param1": "value1", "param2": "value2"},
            "/vsizip//vsicurl?param1=value1&param2=value2&"
            "url=http://example.com/path/to/file.zip/path/to/innferfile.txt",
            does_not_raise(),
        ),
        (
            "http://example.com/path/to/file.zip!",
            {},
            "/vsizip//vsicurl/http://example.com/path/to/file.zip",
            does_not_raise(),
        ),
        (
            "s3://example-bucket/path/to/file.zip!path/to/innferfile.txt",
            {},
            "/vsizip//vsis3/example-bucket/path/to/file.zip/path/to/innferfile.txt",
            does_not_raise(),
        ),
        (
            "s3://example-bucket/path/to/file.txt",
            {},
            "/vsis3/example-bucket/path/to/file.txt",
            does_not_raise(),
        ),
    ],
)
def test_uri_to_vsi_path(uri, options, expected_output, error):
    with error:
        assert uri_to_vsi_path(uri=uri, options=options) == expected_output


class TestOnlineGdalFileHandler:
    @pytest.mark.parametrize(
        "uri, options, expected_output, error",
        [
            ("http://example.com", {}, "/vsicurl/http://example.com", does_not_raise()),
            (
                "https://example.com",
                {},
                "/vsicurl/https://example.com",
                does_not_raise(),
            ),
            (
                "ftp://path/to/remote/resource",
                {},
                "/vsicurl/ftp://path/to/remote/resource",
                does_not_raise(),
            ),
            (
                "ssh://path/to/remote/resource",
                {},
                None,
                pytest.raises(ValueError),
            ),
            (
                "https://example.com",
                {"param1": "value1", "param2": "value2"},
                "/vsicurl?param1=value1&param2=value2&url=https://example.com",
                does_not_raise(),
            ),
        ],
    )
    def test_get_vsi_path(self, uri, options, expected_output, error):
        with error:
            assert OnlineGdalFileHandler(options=options).get_vsi_path(uri=uri) == expected_output


class TestBucketGdalFileHandler:
    @pytest.mark.parametrize(
        "uri, expected_output, error",
        [
            (
                "s3://example-bucket/path/to/file",
                "/vsis3/example-bucket/path/to/file",
                does_not_raise(),
            ),
            (
                "gs://example-bucket/path/to/file",
                "/vsigs/example-bucket/path/to/file",
                does_not_raise(),
            ),
            (
                "other://example-bucket/path/to/file",
                None,
                pytest.raises(ValueError),
            ),
        ],
    )
    def test_get_vsi_path(self, uri, expected_output, error):
        with error:
            assert BucketGdalFileHandler().get_vsi_path(uri=uri) == expected_output


class TestCompressedGdalFile:
    @pytest.mark.parametrize(
        "path, dst_path, expected_output, error",
        [
            (
                "/path/to/zipfie.zip",
                None,
                "/vsizip//path/to/zipfie.zip",
                does_not_raise(),
            ),
            (
                "/path/to/zipfie.zip",
                "/path/to/innerfile.txt",
                "/vsizip//path/to/zipfie.zip/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/zipfie.zip",
                "path/to/innerfile.txt",
                "/vsizip//path/to/zipfie.zip/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/tarfile.tar",
                "/path/to/innerfile.txt",
                "/vsitar//path/to/tarfile.tar/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/tarfile.tar.gz",
                "/path/to/innerfile.txt",
                "/vsitar//path/to/tarfile.tar.gz/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/tarfile.tgz",
                "/path/to/innerfile.txt",
                "/vsitar//path/to/tarfile.tgz/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/gzipfile.gz",
                "/path/to/innerfile.txt",
                "/vsigzip//path/to/gzipfile.gz/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "/path/to/audio_file.mp3",
                None,
                None,
                pytest.raises(ValueError),
            ),
            (
                "http:/path/to/tarfile.tar",
                "/path/to/innerfile.txt",
                "/vsitar/http:/path/to/tarfile.tar/path/to/innerfile.txt",
                does_not_raise(),
            ),
            (
                "any-schema:/path/to/tarfile.tar",
                "/path/to/innerfile.txt",
                "/vsitar/any-schema:/path/to/tarfile.tar/path/to/innerfile.txt",
                does_not_raise(),
            ),
        ],
    )
    def test_get_vsi_path(self, path, dst_path, expected_output, error):
        with error:
            assert CompressedGdalFile().get_vsi_path(path=path, dst_path=dst_path) == expected_output
