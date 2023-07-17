import tempfile

from django.contrib.gis.gdal.datasource import DataSource
from import_export.tmp_storages import TempFolderStorage

from .data_sources.boundaries.boundaries import uri_to_vsi_path


class TempFolderZippedGDALFileSystemStorage(TempFolderStorage):
    def __init__(self, name=None, *args, **kwargs):
        if name is None:
            _tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            name = _tmp_file.name
        super().__init__(name, *args, **kwargs)

    def save(self, data):
        with open(self.get_full_path(), mode="wb") as file:
            file.write(data)

    def read(self):
        return DataSource(uri_to_vsi_path(uri=self.get_full_path()))
