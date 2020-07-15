# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
from .base import BaseManager
from tigapublic.models import Epidemiology


class EpidemiologyData(BaseManager):
    """Manage Epidemiology data."""

    def get(self):
        """Get epidemiology data."""
        # Return an Unauthorized 401 message if the user is not authenticated

        if (not self.request.user.is_epidemiologist_viewer()):
            return self._end_unauthorized()

        # get the data
        values = [
            'id', 'lat', 'lon', 'province', 'health_center', 'country',
            'age', 'date_arribal', 'date_notification', 'date_symptom',
            'patient_state', 'year'
        ]

        data = Epidemiology.objects.all().values(
                                                    *values
                                                ).order_by('-date_symptom')

        self.response['fields'] = (values)
        self.response['rows'] = list(data)
        self.response['num_rows'] = data.count()

        return self._end()
