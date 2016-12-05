from import_export import resources
from django.conf import settings
from models import MapAuxReports


class MapAuxReportsResource(resources.ModelResource):
    class Meta:
        model = MapAuxReports
        fields = ('version_uuid', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 't_q_1', 't_a_1', 't_q_2', 't_a_2', 't_q_3', 't_a_3', 's_q_1', 's_a_1', 's_q_2', 's_a_2', 's_q_3', 's_a_3', 's_q_4', 's_a_4', 'expert_validated', 'expert_validation_result', 'single_report_map_url')

    def get_export_headers(self):
        headers = ['ID', 'Date', 'Longitude', 'Latitude', 'Ref. System', 'Type', 'Adult question 1', 'Adult answer 1', 'Adult question 2', 'Adult answer 2', 'Adult question 3', 'Adult answer 3', 'Site question 1', 'Site answer 1', 'Site question 2', 'Site answer 2', 'Site question 3', 'Site answer 3', 'Site question 4', 'Site answer 4', 'Expert validated', 'Expert validation result', 'Map link']
        return headers

    def dehydrate_single_report_map_url(self, report):
        return settings.SITE_URL+'spain.html#/es/19/' + str(report.lat) + '/' + str(report.lon) + '/' + report.private_webmap_layer+ '/' + str(report.observation_date.year) +'/all/' + str(report.id)
    