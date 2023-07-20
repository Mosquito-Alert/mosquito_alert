from argparse import ArgumentParser

from ....import_export.data_sources.base import (
    BaseDataSource,
    CompressedDataSourceMixin,
    DownloadableDataSource,
    FileDataSource,
    OnlineDataSource,
)


class ConcreteBaseDataSource(BaseDataSource):
    CLI_NAME = "concrete_test_ds"

    @classmethod
    def _add_custom_arguments(cls, parser):
        parser.add_argument(
            "-t",
            "--test_argument",
            required=False,
        )


class TestBaseDataSource:
    def test_add_arguments(self):
        obj = ConcreteBaseDataSource()

        dummy_parser = ArgumentParser()
        dummy_parser.add_argument("--init", required=False)
        obj.add_arguments(parser=dummy_parser)

        name_space = dummy_parser.parse_args([])
        assert "init" in name_space
        assert "test_argument" in name_space


class TestCompressedDataSourceMixin:
    def test_get_compressed_desired_filename_without_override(self):
        # Using original class
        assert CompressedDataSourceMixin._get_compressed_desired_filename() is None

    def test_get_compressed_desired_filename_with_override(self):
        class DummyCompressedDataSourceMixin(CompressedDataSourceMixin):
            COMPRESSED_DESIRED_FILENAME = "test_filename_{variable}"

        # Using default
        assert (
            DummyCompressedDataSourceMixin._get_compressed_desired_filename(variable="random")
            == "test_filename_random"
        )

        # Override in function
        assert (
            DummyCompressedDataSourceMixin._get_compressed_desired_filename(
                desired_filename="new_name_{variable}", variable="random"
            )
            == "new_name_random"
        )

        # Without args
        assert (
            DummyCompressedDataSourceMixin._get_compressed_desired_filename(
                desired_filename="new_name", variable="random"
            )
            == "new_name"
        )


class DummyFileDataSource(FileDataSource):
    CLI_NAME = "test_cli"

    @classmethod
    def _add_custom_arguments(cls, parser):
        pass


class DummyCompressedFileDataSource(DummyFileDataSource):
    COMPRESSED_DESIRED_FILENAME = "filename_{variable}.txt"


class TestFileDataSourceCompressed:
    def test_init_file_path_None(self):
        obj = DummyCompressedFileDataSource(file_path=None)

        assert obj.file_path is None
        assert obj.file is None

    def test_init_file_path_is_path(self, dummy_zipfile_path):
        obj = DummyCompressedFileDataSource(file_path=dummy_zipfile_path, variable="test")

        assert obj.file_path == dummy_zipfile_path
        assert obj.file.read() == b"TEST CONTENT"


class TestFileDataSourceNotCompressed:
    def test_init_file_path_None(self):
        obj = DummyFileDataSource(file_path=None)

        assert obj.file_path is None
        assert obj.file is None

    def test_init_file_path_is_path(self, dummy_txt_path):
        obj = DummyFileDataSource(file_path=dummy_txt_path)
        print(dummy_txt_path)

        assert obj.file_path == dummy_txt_path
        assert obj.file.read() == "TEST CONTENT"


class ConcreteOnlineDataSource(OnlineDataSource):
    CLI_NAME = "test_cli"
    URL = "http://example.com"

    def _add_custom_arguments(cls, parser):
        pass


class TestOnlineDataSource:
    def test_from_online_source_without_url_arg(self):
        obj = ConcreteOnlineDataSource.from_online_source(url=None)
        assert obj.url == "http://example.com"

    def test_from_online_source_with_url_arg(self):
        obj = ConcreteOnlineDataSource.from_online_source(url="http://anotherweb.com")
        assert obj.url == "http://anotherweb.com"

    def test_from_online_source_kwargs(self):
        obj = ConcreteOnlineDataSource.from_online_source(url="http://anotherweb.com/{variable}/test", variable="page")
        assert obj.url == "http://anotherweb.com/page/test"

    def test_from_online_source_with_parms_arg(self):
        obj = ConcreteOnlineDataSource.from_online_source(url=None, params={"key": "1"})
        assert obj.url == "http://example.com?key=1"


class DummyDownloadableDataSource(DownloadableDataSource):
    URL = "http://example.com/{variable}/{file}.txt"
    DOWNLOAD_FILE_SUFFIX = ".random"


class TestDownloadableDataSource:
    def test__get_download_file_extension(self):
        ext = DownloadableDataSource._get_download_file_extension(url="http://example.com/file.tgz")

        assert ext == ".tar"

    def test__get_download_file_extension_when_overrided(self):
        ext = DummyDownloadableDataSource._get_download_file_extension(url="http://example.com/file.txt")
        assert ext == ".random"

    def test_from_online_source(self, mocker, tmpdir):
        m_tmpfile = mocker.patch("tempfile.NamedTemporaryFile")

        dummy_file_path = tmpdir.mkdir("sub").join("hello.txt")
        dummy_file_path.write("content")
        m_tmpfile.return_value.__enter__.return_value.name = dummy_file_path

        URL = "http://example.com/file.txt"
        mocker.patch(
            "mosquito_alert.geo.import_export.data_sources.base.download_file",
            return_value=dummy_file_path,
        )

        # Overriding url arg
        obj = DownloadableDataSource.from_online_source(url=URL)

        assert obj.url == URL
        assert obj.file_path == dummy_file_path
        assert obj.file.name == str(dummy_file_path)
