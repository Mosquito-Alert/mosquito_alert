import tempfile

from django.contrib.gis.gdal import DataSource
from import_export.tmp_storages import BaseStorage, TempFolderStorage

from .data_sources.boundaries.boundaries import uri_to_vsi_path


class InMemoryGDALFileSystemStorage(BaseStorage):
    def save(self, data):
        pass

    def read(self):
        return DataSource(uri_to_vsi_path(uri=self.name))

    def remove(self):
        pass


class TempFolderZippedGDALFileSystemStorage(TempFolderStorage):
    def __init__(self, name=None, *args, **kwargs):
        if not name:
            _tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            name = _tmp_file.name
        super().__init__(name, *args, **kwargs)

    def save(self, data):
        with open(self.get_full_path(), mode="wb") as file:
            file.write(data)

    def read(self):
        return DataSource(uri_to_vsi_path(uri=self.get_full_path()))
