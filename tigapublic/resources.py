from import_export import resources
from import_export import fields,widgets
from import_export.widgets import DateTimeWidget, DateWidget
from django.conf import settings
from models import MapAuxReports, Notification, StormDrain
import datetime
from pyproj import Proj, transform
import pytz
import re
import datetime
from constants import *

class MapAuxReportsLimitedResource(resources.ModelResource):
    class Meta:
        model = MapAuxReports
        fields = ('version_uuid', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 'expert_validated', 'private_webmap_layer', 'single_report_map_url')
        export_order = ('version_uuid', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 'expert_validated', 'private_webmap_layer', 'single_report_map_url')

    def get_export_headers(self):
        headers = ['ID', 'Date', 'Longitude', 'Latitude', 'Ref. System', 'Type', 'Expert validated', 'Expert validation result', 'Map link']
        return headers

    def dehydrate_single_report_map_url(self, report):
        return settings.SITE_URL+'spain.html#/es/19/' + str(round(report.lat,4)) + '/' + str(round(report.lon,4)) + '/' + report.private_webmap_layer+ '/' + str(report.observation_date.year) +'/all/' + str(report.id)

class MapAuxReportsResource(resources.ModelResource):
    class Meta:
        model = MapAuxReports
        fields = ('version_uuid', 'user_id', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 't_q_1', 't_a_1', 't_q_2', 't_a_2', 't_q_3', 't_a_3', 's_q_1', 's_a_1', 's_q_2', 's_a_2', 's_q_3', 's_a_3', 's_q_4', 's_a_4', 'expert_validated', 'private_webmap_layer', 'single_report_map_url')
        export_order = ('version_uuid', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 't_q_1', 't_a_1', 't_q_2', 't_a_2', 't_q_3', 't_a_3', 's_q_1', 's_a_1', 's_q_2', 's_a_2', 's_q_3', 's_a_3', 's_q_4', 's_a_4', 'expert_validated', 'private_webmap_layer', 'single_report_map_url')

    def get_export_headers(self):
        headers = ['ID', '(PRIVATE COLUMN!!) User', 'Date', 'Longitude', 'Latitude', 'Ref. System', 'Type', 'Adult question 1', 'Adult answer 1', 'Adult question 2', 'Adult answer 2', 'Adult question 3', 'Adult answer 3', 'Site question 1', 'Site answer 1', 'Site question 2', 'Site answer 2', 'Site question 3', 'Site answer 3', 'Site question 4', 'Site answer 4', 'Expert validated', 'Expert validation result', 'Map link']
        return headers

    def dehydrate_single_report_map_url(self, report):
        return settings.SITE_URL+'spain.html#/es/19/' + str(round(report.lat,4)) + '/' + str(round(report.lon,4)) + '/' + report.private_webmap_layer+ '/' + str(report.observation_date.year) +'/all/' + str(report.id)

class MapAuxReportsExtendedResource(resources.ModelResource):
    class Meta:
        model = MapAuxReports
        fields = ('version_uuid', 'user_id', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 't_q_1', 't_a_1', 't_q_2', 't_a_2', 't_q_3', 't_a_3', 's_q_1', 's_a_1', 's_q_2', 's_a_2', 's_q_3', 's_a_3', 's_q_4', 's_a_4', 'expert_validated', 'private_webmap_layer', 'single_report_map_url','note')
        export_order = ('version_uuid', 'user_id', 'observation_date', 'lon', 'lat', 'ref_system', 'type', 't_q_1', 't_a_1', 't_q_2', 't_a_2', 't_q_3', 't_a_3', 's_q_1', 's_a_1', 's_q_2', 's_a_2', 's_q_3', 's_a_3', 's_q_4', 's_a_4', 'expert_validated', 'private_webmap_layer', 'single_report_map_url','note')

    def get_export_headers(self):
        headers = ['ID', '(PRIVATE COLUMN!!) User', 'Date', 'Longitude', 'Latitude', 'Ref. System', 'Type', 'Adult question 1', 'Adult answer 1', 'Adult question 2', 'Adult answer 2', 'Adult question 3', 'Adult answer 3', 'Site question 1', 'Site answer 1', 'Site question 2', 'Site answer 2', 'Site question 3', 'Site answer 3', 'Site question 4', 'Site answer 4', 'Expert validated', 'Expert validation result', 'Map link', '(PRIVATE COLUMN!!) Tags']
        return headers

    def dehydrate_note(self, report):
        return ','.join(re.findall(r'(?<=\W)[#]\S*', report.note))

    def dehydrate_single_report_map_url(self, report):
        return settings.SITE_URL+'spain.html#/es/19/' + str(report.lat) + '/' + str(report.lon) + '/' + report.private_webmap_layer+ '/' + str(report.observation_date.year) +'/all/' + str(report.id)

class NotificationExtendedResource(resources.ModelResource):
    class Meta:
        model = Notification
        fields = ('report__version_uuid', 'user_id', 'expert__username', 'date_comment','public', 'acknowledged', 'notification_content__title_es','notification_content__body_html_es')
        export_order = ('report__version_uuid', 'user_id', 'date_comment', 'public', 'expert__username', 'acknowledged', 'notification_content__title_es','notification_content__body_html_es')

    def get_export_headers(self):
        headers = ['ID', '(PRIVATE COLUMN!!) User', 'Date notification', 'Notification type', 'Notification sender', 'User reaction', 'Notification title','Notification content']
        return headers

class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        fields = ('report__version_uuid', 'user_id', 'expert__username', 'date_comment','public', 'acknowledged', 'notification_content__title_es','notification_content__body_html_es')
        export_order = ('report__version_uuid', 'date_comment', 'public', 'expert__username', 'acknowledged', 'notification_content__title_es','notification_content__body_html_es')

    def get_export_headers(self):
        headers = ['ID', '(PRIVATE COLUMN!!) User', 'Date notification', 'Notification type', 'Notification sender', 'User reaction', 'Notification title','Notification content']
        return headers

class StormDrainResource(resources.ModelResource):
    date_visit = fields.Field(column_name='date')
    class Meta:
        model = StormDrain
        widgets = {
            'date_visit': DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
        }

    def transformColumnValue(self, value):
        if value != None:
            if value.lower() in true_values:
                return '1'
            else:
                return '0'

    def before_import_row(self, row, *kwargs):

        row['original_lon'] = row['lon']
        row['original_lat'] = row['lat']

        if 'water' in row:
            row['water'] = self.transformColumnValue(row['water'])

        if 'sand' in row:
            row['sand'] = self.transformColumnValue(row['sand'])

        if 'species1' in row:
            row['species1'] = self.transformColumnValue(row['species1'])

        if 'species2' in row:
            row['species2'] = self.transformColumnValue(row['species2'])

        if 'treatment' in row:
            row['treatment'] = self.transformColumnValue(row['treatment'])

        if 'activity' in row:
            row['activity'] = self.transformColumnValue(row['activity'])

        inProj = Proj(init='epsg:25831')
        outProj = Proj(init='epsg:4326')
        row['lon'],row['lat'] = transform(inProj,outProj,row['lon'],row['lat'])

class StormDrainCSVResource(resources.ModelResource):

    class Meta:
        model = StormDrain
        widgets = {
            'date': {'format':'%d/%m/%Y'}
        }

    def transformColumnValue(self, value):
        if value != None:
            if value.lower() in true_values:
                return '1'
            else:
                return '0'

    def before_import_row(self, row, *kwargs):

        row['original_lon'] = row['lon']
        row['original_lat'] = row['lat']

        if 'water' in row:
            row['water'] = self.transformColumnValue(row['water'])

        if 'sand' in row:
            row['sand'] = self.transformColumnValue(row['sand'])

        if 'species1' in row:
            row['species1'] = self.transformColumnValue(row['species1'])

        if 'species2' in row:
            row['species2'] = self.transformColumnValue(row['species2'])

        if 'treatment' in row:
            row['treatment'] = self.transformColumnValue(row['treatment'])

        if 'activity' in row:
            row['activity'] = self.transformColumnValue(row['activity'])

        inProj = Proj(init='epsg:25831')
        outProj = Proj(init='epsg:4326')
        row['lon'],row['lat'] = transform(inProj,outProj,row['lon'],row['lat'])
