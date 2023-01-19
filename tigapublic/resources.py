# -*- coding: utf-8 -*-
"""MODELS."""
import hashlib
import re

from django.conf import settings
from import_export import resources

from .models import MapAuxReports, ObservationNotifications


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
