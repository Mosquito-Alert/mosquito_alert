"""Observation Libraries."""
# -*- coding: utf-8 -*-

from collections import OrderedDict
from io import StringIO, BytesIO
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from .base import BaseManager
from .filters import FilterManager
from .notifications import NotificationManager
from tigapublic.constants import (fields_available, managers_group,
                                  superusers_group)
from tigapublic.models import AuthUser, MapAuxReports, ReportsMapData
from tigapublic.resources import GetObservationResource, NotificationResource
from .predictionmodels import predictionModels


def coordinateListToWKTPolygon(coordinates):
    """doStringPolygon."""
    nodes = []
    for i in range(0, len(coordinates)):
        nodes.append(coordinates[i])

    nodes.append(coordinates[0])
    return 'Polygon((' + (', '.join(nodes)) + '))'


class ObservationExporter(BaseManager):
    """Export observations to Excel."""

    """
    Order of the fields in the Excel/CSV file.

    Is a dictionary.
    - Every key of the dictionary is one role.
    - The value of each key is a tuple of field names, as they appear on the
        Excel/CSV file.
    """
    order_of_fields = {
        superusers_group: (
            'version_uuid', 'user_id', 'observation_date', 'lon', 'lat',
            'ref_system', 'municipality__nombre', 'type', 'expert_validated',
            'private_webmap_layer', 'single_report_map_url', 'note'
        ),
        managers_group: (
            'version_uuid', 'user_id', 'observation_date', 'lon', 'lat',
            'ref_system', 'municipality__nombre', 'type', 'expert_validated',
            'private_webmap_layer', 'single_report_map_url'
        ),
        'anonymous': (
            'version_uuid', 'observation_date', 'lon', 'lat', 'ref_system',
            'municipality__nombre', 'type', 'expert_validated',
            'private_webmap_layer', 'single_report_map_url'
        )
    }

    def __init__(self, request):
        """Constructor."""
        # Call parent constructor (we will be using the ExtendedUser object)
        super(ObservationExporter, self).__init__(request)
        # Get the user's highest role
        role = request.user.get_highest_role()
        # Pick and store the order of the fields for this role
        self.export_order = self.order_of_fields[role]
        # All fields available
        fields = OrderedDict(fields_available)
        # Get and store the fields available to this role
        self.fields = [key for key, value in fields.items()
                       if type(value).__name__ == 'str'
                       or 'permissions' not in value
                       or role in value['permissions']]
        # Get and store the headers available to this role
        self.headers = []
        for key, value in fields.items():
            if type(value).__name__ == 'str':
                self.headers.append(value)
            elif 'permissions' not in value or role in value['permissions']:
                self.headers.append(value['label'])

    def _get_export_zip_files(self, obs_dataset, notifs_dataset, export_type):
        """Get observation related files and zip them."""
        BASE_DIR = settings.BASE_DIR

        if self.request.user.is_valid():
            license_file = open(BASE_DIR + "/tigapublic/files/license.txt")
            observations_metadata_file = open(
                BASE_DIR +
                "/tigapublic/files/observations_registered_metadata.txt"
            )
        else:
            license_file = open(
                BASE_DIR +
                "/tigapublic/files/license.and.citation.txt"
            )
            observations_metadata_file = open(
                BASE_DIR +
                "/tigapublic/files/observations_public_metadata.txt"
            )

        in_memory = BytesIO()
        zip = ZipFile(in_memory, "a")
        zip.writestr("license.txt", license_file.read())
        zip.writestr("obs_metadata.txt",
                     observations_metadata_file.read())

        zip.writestr("observations.xls", obs_dataset[export_type])

        # Zip notification files
        if notifs_dataset:
            notifs_metadata_file = open(
                BASE_DIR + "/tigapublic/files/notifications_metadata.txt"
            )
            zip.writestr(
                "notifications_metadata.txt",
                notifs_metadata_file.read()
            )
            zip.writestr(
                "notifications.xls",
                notifs_dataset[export_type]
            )

        # fix for Linux zip files read in Windows
        for file in zip.filelist:
            file.create_system = 0
        zip.close()
        return in_memory

    def get(self, *args, **kwargs):
        """Execute export."""
        # Get ids of the selected observations
        ids = list(kwargs['data'].values_list('id', flat=True))
        # Get notifications (logged user is required)
        notifications = False
        if self.request.user.is_valid():
            qs = NotificationManager(self.request).get(pk=ids)
            resource = NotificationResource().export(qs)
            if qs.count() > 0:
                notifications = {
                    'csv': resource.csv,
                    'xls': resource.xls
                }

        resource = GetObservationResource(
            fields=self.fields,
            headers=self.headers,
            order=self.export_order
        ).export(kwargs['data'])

        observations = {
            'csv': resource.csv,
            'xls': resource.xls
        }

        in_memory = self._get_export_zip_files(
            observations, notifications, kwargs['format']
        )

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = ("attachment;"
                                           "filename=mosquito_alert.zip")

        in_memory.seek(0)
        response.write(in_memory.read())

        return response


class ObservationManager(BaseManager):
    """Observation Manager Class."""

    returning_fields = {
        'ReportsMapData': (
            'c', 'category', 'expert_validation_result', 'month', 'lon', 'lat',
            'id'
        ),
        'MapAuxReports': (
            'c', 'category', 'expert_validation_result',
            'month', 'lon', 'lat', 'id'
        ),
        'single': ['id', 'version_uuid', 'observation_date', 'lon', 'lat',
                   'ref_system', 'type', 'breeding_site_answers',
                   'mosquito_answers', 'expert_validated',
                   'expert_validation_result',
                   'simplified_expert_validation_result', 'site_cat',
                   'storm_drain_status', 'edited_user_notes', 'photo_url',
                   'photo_license', 'dataset_license',
                   'single_report_map_url', 'n_photos', 'visible',
                   'final_expert_status', 'private_webmap_layer',
                   'municipality', 'notifiable']
    }

    def __init__(self, request, **filters):
        """Constructor."""
        super(ObservationManager, self).__init__(request)
        self.filter = FilterManager(request, **filters)

    def _get_filtered_data(self, model=False, extra=False):
        """Get filtered observations."""
        # Define model
        self.model = ReportsMapData if model is False else model

        # Define field definition/transformation
        extra = {'select': {}} if not extra else extra

        if self.model.__name__ == 'MapAuxReports':
            extra['select']['c'] = 1
            extra['select']['category'] = 'private_webmap_layer'
            extra['select']['month'] = (
                "to_Char(observation_date,'YYYYMM')"
            )

        # Get all data
        self.filter.objects(self.model, extra=extra)

        # Run filters
        try:
            self.filter.run()
        except ObjectDoesNotExist as e:
            self.response['error'] = str(e)

        return self.filter.queryset

    def export(self, *args, **kwargs):
        """Export data to Excel."""
        # Get data
        kwargs['data'] = self._get_filtered_data(model=MapAuxReports)
        # Order by most recent first
        kwargs['data'] = kwargs['data'].order_by('-observation_date')
        # Call exporter and return
        return ObservationExporter(self.request).get(*args, **kwargs)

    def get(self, model=False, extra=False):
        """Get observations.

        Applies all filters.
        """
        self.filter.queryset = self._get_filtered_data(
            model=model, extra=extra
        )

        # Build response
        self.response['rows'] = list(self.filter.queryset.values(
            *self.returning_fields[self.model.__name__]
        ))
        self.response['num_rows'] = self.filter.queryset.count()
        return self._end()

    def get_intersecting(self, extra=False):
        """Get observations intersecting polygon."""
        # If user is not authorized, bail out
        if not self.request.user.is_authorized:
            return self._end_unauthorized()

        # Get the filtered data
        qs = self._get_filtered_data(MapAuxReports, extra)
        # Create WKT polygon
        poly = coordinateListToWKTPolygon(
                    self.request.POST.getlist('selection[]'))
        # Define SQL intersection
        cadena = ("ST_Intersects(ST_Point(lon,lat), St_GeomFromText('%s'))" %
                  poly)
        # Execute intersection filter
        qs = qs.extra(where=[cadena])

        self.response = {
            'success': True,
            'rows': list(qs.values('id', 'user_id')),
            'num_rows': qs.count()
        }

        return self._end()

    def _is_notifiable(self, pk):
        """Return 1 if is notifiable and 0 if it is not."""
        if self.request.user.is_root():
            return 1
        elif self.request.user.is_manager():
            return MapAuxReports.objects.filter(
                id=int(pk),
                municipality__in=AuthUser.objects.filter(
                    id=self.request.user.id
                ).values('municipalities')
            ).count()

        else:
            return 0

    def _get_returning_fields(self, key):
        """Return a list of fields to return to the client."""
        fields = self.returning_fields[key]
        # If getting single observation and user is logged
        # add additional fields
        if key == 'single' and self.request.user.is_valid():
            fields.extend(['note'])

        return fields

    def get_single(self, pk=None):
        """Return the data for a single observation."""
        # Get all notifications from this observation
        notifications = NotificationManager(self.request).get(int(pk))
        # Define fields to return
        fields = self._get_returning_fields('single')
        # Define 'notifiable' variable
        notifiable = self._is_notifiable(pk)
        # Get observation data
        qs = MapAuxReports.objects.filter(id=pk).extra(
            select={
                'notifiable': notifiable
            }
        ).values(*fields)

        self.response = qs[0]
        self.response['notifs'] = list(notifications.values(
                'expert__username',
                'notification_content__body_html_es',
                'notification_content__title_es',
                'date_comment').order_by('-date_comment','expert__username'))

        return self._end()

    def get_report(self):
        """Return the data for the observation's HTML report."""
        # Define fields to return
        fields = self._get_returning_fields('single')
        # Remove the notifiable field, only used in get_single
        if 'notifiable' in fields:
            fields.remove('notifiable')
        # Get data
        data = self._get_filtered_data(model=MapAuxReports)
        # Prepare response
        self.response = {
            'rows': list(data.values(*fields)),
            'num_rows': data.count()
        }

        return self._end()
