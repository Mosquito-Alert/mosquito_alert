# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
from django.db.models import Case, CharField, Value, When

from tigapublic.models import Irideon

from .base import BaseManager


class irideonData(BaseManager):
    """Manage Irideon data."""

    def get(self):
        """Get irideon data."""
        # Return an Unauthorized 401 message if the user is not authenticated

        if (not self.request.user.is_irideon_traps_viewer()):
            return self._end_unauthorized()

        # get the data
        values = [
            'record_time', 'classification', 'client_name',
            'lat', 'lon'
        ]

        data = Irideon.objects.all().values(
                'record_time', 'client_name', 'lat', 'lon'
            ).exclude(
                classification='Non-target'
            ).annotate(
                spc=Case(
                    When(classification__icontains='Test pulse', then=Value('pulse')),
                    When(classification__icontains='albopictus', then=Value('tig')),
                    When(classification__icontains='pipiens', then=Value('cul')),
                    When(classification__icontains='aegypti', then=Value('zik')),
                    default=Value(''),
                    output_field=CharField(),
                )
            ).annotate(
                sex=Case(
                    #order is important, male is also inside female
                    When(classification__icontains='female', then=Value('f')),
                    When(classification__icontains='male', then=Value('m')),
                    default=Value(''),
                    output_field=CharField(),
                )
            ).order_by('record_time')

        self.response['fields'] = (values)
        self.response['rows'] = list(data)
        self.response['num_rows'] = data.count()

        return self._end()
