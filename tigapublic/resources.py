# -*- coding: utf-8 -*-
"""MODELS."""
import hashlib
import re

from django.conf import settings
from import_export import resources

# from constants import true_values
from .models import MapAuxReports, ObservationNotifications

# from import_export.widgets import DateTimeWidget
# from pyproj import Proj, transform


def GetObservationResource(*args, **kwargs):
    """Return a Custom ObservationResource."""
    class ObservationResource(resources.ModelResource):
        class Meta:
            model = MapAuxReports
            fields = kwargs['fields']
            if 'order' in kwargs:
                export_order = kwargs['order']

        def dehydrate_user_id(self, report):
            """Return a hash of the user id."""
            m = hashlib.md5()
            m.update(report.user_id.encode('utf-8'))
            return m.hexdigest()

        def dehydrate_note(self, report):
            """Return all hashtags."""
            return ','.join(re.findall(r"#(\w+)", report.note))

        def dehydrate_single_report_map_url(self, report):
            """Generate the observation detail URL."""
            return '%sspain.html#/es/19/%s/%s/%s/%s/all/N/N/%s' % (
                settings.SITE_URL,
                str(round(report.lat, 4)),
                str(round(report.lon, 4)),
                report.private_webmap_layer,
                str(report.observation_date.year),
                str(report.id)
            )

        def get_export_headers(self):
            """Return the header names."""
            return kwargs['headers']

    return ObservationResource()


class NotificationResource(resources.ModelResource):
    """Notifications Resource."""

    class Meta:
        """Meta."""

        model = ObservationNotifications
        fields = ('report__version_uuid', 'user_id', 'expert__username',
                  'date_comment', 'public', 'notification_content__title_es',
                  'notification_content__body_html_es')
        export_order = ('report__version_uuid', 'user_id', 'date_comment',
                        'public', 'expert__username',
                        'notification_content__title_es',
                        'notification_content__body_html_es')

    def get_export_headers(self):
        """Return the header names."""
        headers = ['ID', '(PRIVATE COLUMN!!) User', 'Date notification',
                   'Notification type', 'Notification sender',
                   'Notification title', 'Notification content']
        return headers

    def dehydrate_user_id(self, report):
        """Return a hash of the user id."""
        m = hashlib.md5()
        if type(report).__name__ == 'dict':
            m.update(report['user_id'].encode('utf-8'))
        else:
            m.update(report.user_id.encode('utf-8'))
        return m.hexdigest()

# Les següents classes no es fan servir

# class BaseStormDrainResource(resources.ModelResource):
#     """Base Drain Resource."""
#
#     def transformColumnValue(self, value):
#         """Transform a boolean value to a binary value (0 or 1)."""
#         if value is not None:
#             if value.lower() in true_values:
#                 return '1'
#             else:
#                 return '0'
#
#     def before_import_row(self, row, *kwargs):
#         """Parse values before importing."""
#         row['original_lon'] = row['lon']
#         row['original_lat'] = row['lat']
#
#         if 'water' in row:
#             row['water'] = self.transformColumnValue(row['water'])
#
#         if 'sand' in row:
#             row['sand'] = self.transformColumnValue(row['sand'])
#
#         if 'species1' in row:
#             row['species1'] = self.transformColumnValue(row['species1'])
#
#         if 'species2' in row:
#             row['species2'] = self.transformColumnValue(row['species2'])
#
#         if 'treatment' in row:
#             row['treatment'] = self.transformColumnValue(row['treatment'])
#
#         if 'activity' in row:
#             row['activity'] = self.transformColumnValue(row['activity'])
#
#         inProj = Proj(init='epsg:25831')
#         outProj = Proj(init='epsg:4326')
#         row['lon'], row['lat'] = transform(inProj, outProj,
#                                            row['lon'], row['lat'])
#
#
# class StormDrainResource(BaseStormDrainResource):
#     """Storm Drain Resource."""
#
#     date_visit = fields.Field(column_name='date')
#
#     class Meta:
#         """Meta."""
#
#         model = StormDrain
#         widgets = {
#             'date_visit': DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
#         }
#
#
# class StormDrainCSVResource(BaseStormDrainResource):
#     """Storm Drain CSV Resource."""
#
#     class Meta:
#         """Meta."""
#
#         model = StormDrain
#         widgets = {
#             'date': {'format': '%d/%m/%Y'}
#         }
