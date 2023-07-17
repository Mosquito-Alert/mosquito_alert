from ...import_export.tmp_storage import TempFolderZippedGDALFileSystemStorage


class TestTempFolderZippedGDALFileSystemStorage:
    def test_tmpfile_is_created_if_name_is_None(self, mocker):
        class DummyFile:
            def __init__(self, *args, **kwargs) -> None:
                pass

            name = "test.zip"

        mocker.patch("tempfile.NamedTemporaryFile", DummyFile)
        tmp_file = TempFolderZippedGDALFileSystemStorage(name=None)

        assert tmp_file.name == "test.zip"

    def test_read_returns_datasource(self, mocker):
        m = mocker.patch(
            "django.contrib.gis.gdal.datasource.DataSource.__init__", return_value=None
        )

        tmp_file = TempFolderZippedGDALFileSystemStorage(name="/path/to/file.shp.zip")
        tmp_file.read()

        m.assert_called_once_with("/vsizip//path/to/file.shp.zip")
