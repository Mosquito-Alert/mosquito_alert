import tablib
from import_export.formats.base_formats import TablibFormat


class ZippedShapefileFormat(TablibFormat):
    """Reads from a DataSource instance"""

    CONTENT_TYPE = "application/zip"

    def get_title(self):
        return "zipped shp"

    def create_dataset(self, in_stream):
        """
        Create dataset from given datasource stream.
        """
        # Getting only first layer from datasource
        layer = in_stream[0]
        dataset = tablib.Dataset(headers=layer.fields + ["geometry"])

        for feature in layer:
            dataset.append(
                list(map(lambda x: feature.get(x), layer.fields))
                + [
                    feature.geom,
                ]
            )

        return dataset

    def export_data(self, dataset, **kwargs):
        """
        Returns format representation for given dataset.
        """
        raise NotImplementedError()

    def get_extension(self):
        """
        Returns extension for this format files.
        """
        return "shp.zip"

    @classmethod
    def is_available(cls):
        return True

    def can_import(self):
        return True

    def can_export(self):
        return False
