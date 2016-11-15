from import_export import resources

from models import MapAuxReports


class MapAuxReportsResource(resources.ModelResource):
    class Meta:
        model = MapAuxReports
        # fields = ('version_uuid', 'observation_date')
