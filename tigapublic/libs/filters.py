# -*- coding: utf-8 -*-
"""Filtering Libraries."""
import datetime
from datetime import date
from operator import __or__ as OR
from functools import reduce

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from .base import BaseManager
from tigapublic.models import (AuthUser, MapAuxReports, Municipalities,
                               ObservationNotifications)


def category_filter(qs, categories):
    """Category filter."""
    args = Q()
    if categories is not None:
        categories = categories.split(',')
        for c in categories:
            args.add(Q(private_webmap_layer=c), Q.OR)

    qs = qs.filter(args)
    return qs


class Filter(object):
    """Base Filter object.

    Attributes:
    - filter_wrapper <string>
    - params <string>, <tuple of strings> or <tuple of tuples of strings>

    ** filter_wrapper **

    Name fo the key wrapper when the filter params are inside a wrapper. Ex:

    If ...
    filters = {
        'time': {'years': years, 'months': months}
    }

    Then ...
    filter_wrapper = 'time'

    ** params **

    Name of the dictionary key where the filtering value is stored inside
    manager.filters. It can be one of the following types:

    - string: is_valid() will return True if the string is found as a key in
          manager.filters.
    - tuple of strings: is_valid() will return True if ANY of the strings is
          found as a key in manager.filters.
    - tuple of tuples (of strings): is_valid() will return True if ANY of the
          (sub)tuples is found as a key in manager.filters. For each subtuple
          it will return True if ALL the strings are found in
          manager.filters.
    """

    params = False

    def __init__(self, manager):
        """Constructor."""
        # print
        # print("Doing %s filter" % str(self.__class__.__name__))
        if hasattr(self, 'db_names') and hasattr(manager, 'model'):
            self.db_name = self.db_names[manager.model.__name__]

    def is_valid(self, manager):
        """Validate the filter configuration."""
        # If there is no param, return True
        if not self.params:
            return True

        params = self.params
        # If self.params is a string, convert it to a tuple of tuples
        if type(params).__name__ == 'str':
            params = ((params,),)

        # If self.params is a tuple of strings
        if type(params[0]).__name__ == 'str':
            params = tuple((param,) for param in params)

        # check if we have values for every params
        #
        # For every param in self.params ...
        #           for param in params
        # ... create a set of the param and a set of the filters
        #           set(param)
        #           set(manager.filters)
        # ... check if the first is a subset of the second (result 1)
        #           set(param).issubset(set(manager.filters))
        # ... create a set of one True element
        #           set({True})
        # ... check if it is a subset of the result 1
        #           set({True}).issubset( set(param).issubset ... )
        #
        # It could be done in two steps:
        # matches = set(param).issubset(set(manager.filters))
        #           for param in params
        # return set({True}).issubset(matches)

        # If the filter is wrapped, drill down the wrapper
        if (hasattr(self, 'filter_wrapper') and
                self.filter_wrapper in manager.filters):
            filters = manager.filters[self.filter_wrapper]
        else:
            filters = manager.filters

        return set({True}).issubset(
            set(param).issubset(set(filters)) for param in params
        )

    def run(self, manager, qs):
        """Default filter execution."""
        if self.name is not False:
            if self.name in manager.filters:
                return True
            else:
                return False
        else:
            return True


class BBOXFilter(Filter):
    """Filter by bbox."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = 'bounds'

    def run(self, manager, qs):
        """Execute the filter."""
        # If the filter is not set, bail out
        if not self.is_valid(manager):
            return qs

        box = manager.filters[self.params].split(',')
        return qs.filter(
            lon__gte=box[0],
            lon__lte=box[2],
            lat__gte=box[1],
            lat__lte=box[3]
        )


class ZoomFilter(Filter):
    """Filter by zoom (geohashlevel)."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = 'zoom'

    def run(self, manager, qs):
        """Execute the filter."""
        # If the filter is not set, bail out
        if not self.is_valid(manager):
            return qs

        zoom = int(manager.filters[self.params])
        if zoom < 5:
            hashlength = 3
        elif zoom < 9:
            hashlength = 4
        elif zoom < 12:
            hashlength = 5
        elif zoom < 15:
            hashlength = 7
        else:
            hashlength = 8

        return qs.filter(
            geohashlevel=hashlength
        )


class ExcludeCategoriesFilter(Filter):
    """Exclude categories filter."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = 'excluded_categories'

    def run(self, manager, qs):
        """Execute the ExcludeCategories filter."""
        # If the filter is not set, bail out
        if not self.is_valid(manager):
            return qs

        args = Q()
        if manager.filters[self.params] is not None:
            categories = manager.filters[self.params].split(',')
            for c in categories:
                args.add(Q(private_webmap_layer=c), Q.OR)

            qs = qs.exclude(
                id__in=MapAuxReports.objects.all().values(
                    'id'
                ).filter(args))

        return qs


class CategoriesFilter(Filter):
    """categories filter."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = 'categories'

    def run(self, manager, qs):
        """Execute the Categories filter."""
        # If the filter is not set, bail out
        if not self.is_valid(manager):
            return qs

        args = Q()
        if manager.filters[self.params] is not None:
            categories = manager.filters[self.params].split(',')
            for c in categories:
                args.add(Q(private_webmap_layer=c), Q.OR)

            qs = qs.filter(
                id__in=MapAuxReports.objects.all().values(
                    'id'
                ).filter(args))

        return qs


class TimeFilter(Filter):
    """Filter by time.

    If daterange was provided use this. Otherwise check if years+months was
    provided and use it. If none of them was provided, don't filter.
    """

    # Name of the dictionary keys used in manager.filters to store the
    # filtering values. Should be a tuple, each element of which should contain
    # all parameters required for each filtering option available.
    params = (
        ('date_start', 'date_end'),
        ('years',),
        ('months',)
    )
    filter_wrapper = 'time'

    def run(self, manager, qs):
        """Execute the filter."""
        # Check if the filter is set
        if not self.is_valid(manager):
            return qs

        filters = manager.filters[self.filter_wrapper]
        if (self.params[0][0] in filters and self.params[0][1] in filters):
            # Get Max time of date_end
            date_end = date(*map(
                int,
                filters[self.params[0][1]].split('-')
            ))
            date_end = datetime.datetime.combine(date_end, datetime.time.max)

            qs = qs.filter(observation_date__range=(
                filters[self.params[0][0]],
                date_end
            ))

        else:
            if self.params[1][0] in filters:
                years = filters[self.params[1][0]].split(',')
                years_lst = []
                for i in years:
                    years_lst.append(Q(observation_date__year=str(i).zfill(2)))
                qs = qs.filter(reduce(OR, years_lst))

            if self.params[2][0] in filters:
                months = filters[self.params[2][0]].split(',')
                lst = []
                for i in months:
                    lst.append(Q(observation_date__month=str(i).zfill(2)))
                qs = qs.filter(reduce(OR, lst))

        return qs


class HashtagFilter(Filter):
    """Filter by hashtag."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = 'hashtag'

    def run(self, manager, qs):
        """Execute the filter."""
        # If the filter is not set, bail out
        if not self.is_valid(manager):
            return qs

        if not manager.request.user.is_authorized():
            e = manager.filters[self.params].replace(':','')
            qs = qs.filter(note__icontains=manager.filters[self.params])
        else:
            search = manager.filters[self.params].split(',')
            for e in search:
                if e.startswith(":"):
                    e = e.replace(':','')
                    qs = qs.filter(note__icontains=e)
                else:
                    qs = qs.filter(tags__icontains=e)
        return qs


class NotificationFilter(Filter):
    """Filter by notification."""

    # Name of the dictionary keys where the filtering values are stored inside
    # manager.filters
    params = ('mynotifs', 'notif_types')
    filter_wrapper = 'notifications'

    def run(self, manager, qs):
        """Execute the filter."""
        # If can not send, then can not filter either
        if (not manager.request.user.is_authorized or not
                self.is_valid(manager)):
            return qs

        filters = manager.filters[self.filter_wrapper]

        if self.params[0] in filters:
            MY_NOTIFICATIONS = "1"
            NOT_MY_NOTIFICATIONS = "0"

            if filters[self.params[0]] == MY_NOTIFICATIONS:
                qs = qs.filter(
                    version_uuid__in=ObservationNotifications.objects.values(
                        'report'
                    ).filter(expert=manager.request.user.id))

            elif filters[self.params[0]] == NOT_MY_NOTIFICATIONS:
                qs = qs.exclude(
                    version_uuid__in=ObservationNotifications.objects.values(
                        'report'
                    ).filter(expert=manager.request.user.id))

        elif self.params[1] in filters:
            notif_types = filters[self.params[1]].split(',')
            qs = qs.filter(
                version_uuid__in=ObservationNotifications.objects.values(
                    'report'
                ).filter(preset_notification__in=notif_types))

        return qs


class MunicipalityFilter(Filter):
    """Filter by municipality."""

    # Name of the dictionary key where the filtering value is stored inside
    # manager.filters
    params = 'municipalities'
    db_names = {
        'ReportsMapData': 'municipality',
        'MapAuxReports': 'municipality'
    }

    def run(self, manager, qs):
        """Execute the filter."""
        # If the filter is not set, bail out
        # db_filter = '%s__in' % self.db_name
        if not self.is_valid(manager):
            return qs

        if (manager.request.user.is_authenticated and
                manager.filters[self.params] == '0'):
            if manager.request.user.is_manager():
                # All municipalities of registered user
                qs = qs.filter(
                        municipality__in=AuthUser.objects.filter(
                            id__exact=manager.request.user.id
                        ).values('municipalities__gid')
                    )

            elif manager.request.user.is_root():
                # All municipalities of spain
                qs = qs.filter(
                    municipality__in=Municipalities.objects.values(
                        'gid'
                    ).filter(
                        tipo__exact='Municipio'
                    )
                )

        else:
            # Only selected municipalities
            # Turn sring array to integer array
            print ('no logged')
            municipalities = map(
                int,
                manager.filters[self.params].split(',')
            )
            qs = qs.filter(
                municipality__in=Municipalities.objects.values(
                    'gid'
                ).filter(
                    gid__in=municipalities
                )
            )

        return qs


class FilterManager(BaseManager):
    """Common filtering methods."""

    filters = {}
    queryset = False
    available_filters = {
        'exclude_categories': ExcludeCategoriesFilter,
        'excluded_categories': ExcludeCategoriesFilter,  # alias
        'time': TimeFilter,
        'date': TimeFilter,  # alias
        'hashtag': HashtagFilter,
        'notifications': NotificationFilter,
        'notification': NotificationFilter,  # alias
        'notification': NotificationFilter,  # alias
        'municipalities': MunicipalityFilter,
        'municipality': MunicipalityFilter,  # alias
        'bounds': BBOXFilter,
        'bbox': BBOXFilter,  # alias
        'zoom': ZoomFilter,
        'categories': CategoriesFilter
    }

    def __init__(self, request, **filters):
        """Constructor."""
        # Call the parent class constructor
        super(FilterManager, self).__init__(request)
        # Store all filters into the filters attribute
        self.filters = self._clean_filters(**filters)

    def _clean_filters(self, **filters):
        """Clean up filters.

        - Remove all 'ALL' and 'N' values.
        - Remove private filters
        """
        # If we are anonymous user, remove notification filters
        if not self.request.user.is_valid() and 'notifications' in filters:
            if 'mynotifs' in filters['notifications']:
                del filters['notifications']['mynotifs']
            if 'notif_types' in filters['notifications']:
                del filters['notifications']['notif_types']

        cleaned_filters = {}
        for key, value in filters.items():
            if type(value).__name__ == 'dict':
                hasvalue = False
                inner_filter = {}
                for key2, value2 in value.items():
                    if (value2 != 'all' and value2 != 'N'
                            and value2 is not None):
                        hasvalue = True
                        inner_filter[key2] = value2
                if hasvalue:
                    cleaned_filters[key] = inner_filter
            elif value != 'all' and value != 'N' and value is not None:
                cleaned_filters[key] = filters[key]

        return self._structure_filters(**cleaned_filters)

    def _structure_filters(self, **filters):
        """Provide structure to the filters."""
        result = {}
        structure = {'time': ['years', 'months', 'date_start', 'date_end'],
                     'notifications': ['mynotifs', 'notif_types']}

        for key, value in filters.items():
            if type(value).__name__ == 'str':
                found = False
                for cat, items in structure.items():
                    if key in items:
                        found = True
                        if cat not in result:
                            result[cat] = {}
                        result[cat].update({key: value})
                if not found:
                    result[key] = value
            else:
                result[key] = value

        return result

    def objects(self, model=MapAuxReports, **kwargs):
        """Define the base object pool."""
        # print
        # print("Getting objects from model %s" % model.__name__)
        # print
        # self.model = model
        qs = model.objects.all()
        for key, value in kwargs.items():
            if key == 'extra':
                if 'select' in value:
                    qs = qs.extra(select=value['select'])

        # Remove null values in required fields
        self.queryset = qs.filter(
            lon__isnull=False, lat__isnull=False
        )

        if model.__name__ == 'MapAuxReports':
            self.queryset = self.queryset.filter(
                private_webmap_layer__isnull=False)
        else:
            self.queryset = self.queryset.filter(category__isnull=False)

    def run(self, filter_names=False):
        """Run all filters."""

        # If we didn't get the list of filter_names, get it from the data
        filter_names = tuple(
            {key for key, value in self.filters.items()}
        ) if not filter_names else filter_names

        # If we got a string convert it to tuple
        if (type(filter_names).__name__ == 'str'):
            filter_names = (filter_names,)

        # Run each of the filters available
        for filter_name in filter_names:
            # warn if the filter_name is not found
            if filter_name not in self.available_filters:
                print("%s filter is not known at FilterManager.get()"
                      % filter_name)
            # get the filter
            if filter_name not in self.available_filters:
                raise ObjectDoesNotExist(
                    'Filter %s does not exist' % filter_name
                )

            filter = self.available_filters[filter_name](self)
            self.queryset = filter.run(self, self.queryset)
