# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
import datetime
import json
import os
import tempfile
from operator import __or__ as OR
from io import BytesIO
from zipfile import ZipFile

from django.db import connection
from django.db.models import Q
from django.http import HttpResponse
from pyproj import Proj, transform
from tablib import Dataset

from .base import BaseManager
from tigapublic.constants import (compulsatory_stormdrain_fields,
                                  defaultStormDrainStyle, false_values,
                                  null_values, optional_stormdrain_fields,
                                  stormdrain_templates_path, tematic_fields,
                                  true_values)
from tigapublic.models import AuthUser, StormDrain, StormDrainUserVersions
from functools import reduce


class StormDrainVersioningMixin(BaseManager):
    """Common function to manage storm drain versions.

    Attributes available:
        - versions
        - my_versions

    Methods available:
        - _get_last_version_id(request)
        - _add_version(request, version_id)
    """

    # get all versions with user different than null
    # and store them in a class attribute
    """A QuerySet of all versions:
        - Returning fields are: title, version, date, style_json, visible,
            user__username and user__id
        - Date field is a string formatted as DD/MM/YYYY
        - Excludes versions with a null user
        - Records are sorted first by date (DESC) and
            then by username (DESC)"""
    versions = StormDrainUserVersions.objects.extra(
            select={
                'date': 'TO_CHAR(published_date, \'DD/MM/YYYY\')'
            }
        ).exclude(
            user__username__isnull=True
        ).values(
            'title', 'version', 'date', 'style_json',
            'visible', 'user__username', 'user'
        ).order_by('-date', '-user__username')

    def __init__(self, request):
        """Constructor."""
        """A QuerySet of all versions belonging to the current
            user. It is a subset of self.versions."""

        self.my_versions = self.versions.filter(user=request.user.id)
        super(StormDrainVersioningMixin, self).__init__(request)

    def _get_last_version_id(self, request):
        """Return the last uploaded version (integer).

        If there is no version, returns 0.
        """
        # If user is root or manager
        if request.user.is_authorized:
            # Get all versions (except null) from this user's storm drains
            # Last version is the first record
            qs = StormDrain.objects.values(
                'version'
            ).filter(
                user__exact=request.user.id,
                version__isnull=False
            ).distinct().order_by('-version')

            if len(qs) > 0:
                # Get the first element (last version)
                version = qs[0]['version']
            else:
                version = 0
        # If user is neither root nor manager return -1
        else:
            version = -1

        return version

    def _add_version(self, request, version_id=None):
        """Add a new storm drain version.

        Returns the id of the created version.
        If user is not authorized (is anonymous) returns 0.
        """
        # User must be authorized (either root or manager)
        if request.user.is_authorized:
            # If no version_id was provided, get the last one from the
            # database and increase it by 1.
            if version_id is None:
                version_id = self._get_last_version_id(request) + 1

            # Get the default style
            style = defaultStormDrainStyle
            # update the version number
            style['version_data'] = version_id
            # Convert it into a string
            defaultStyle = json.dumps(style)

            # Hide (set visible to False) all current versions of the user
            if (len(self.my_versions) > 0):
                StormDrainUserVersions.objects.filter(
                    user=self.request.user.id
                ).update(visible=False)

            # Get the user object
            user = AuthUser.objects.only('id').get(id=request.user.id)

            # Add the new version as visible
            new = StormDrainUserVersions(
                user=user,
                version=version_id,
                published_date=datetime.datetime.now(),
                style_json=defaultStyle,
                visible=True,
                title=request.POST.get('title', '')
            )
            new.save()

            return version_id
        else:
            return 0


class StormDrainData(StormDrainVersioningMixin, BaseManager):
    """Manage the storm drain data."""

    def _get_visible_styles(self):
        """Return the version number and its styles."""
        visible_versions = self.my_versions.values(
            'version', 'style_json'
        ).filter(
            visible__exact=True
        )[:1]

        if len(visible_versions) > 0:
            version = visible_versions[0]['version']
            jstyle = json.loads(visible_versions[0]['style_json'])
        else:
            # Style by default
            # jstyle = {'categories': [{"color": "#0000ff", "conditions": []}]}
            jstyle = {'categories': [
                {"color": "#ff0000",
                 "conditions": [
                    {"operator": "=",
                     "field": "water",
                     "value": "true"}
                     ]
                 }]}
            version = -1

        return {"version": version, "jstyle": jstyle}

    def _get_sql_style_conditions(self, visible_styles):
        """Return an SQL representing the styling conditions."""
        counter = 0
        ends = []
        cases = []
        self.response['colors'] = []

        # loop through each category in jstyle['categories']

        for category in visible_styles['jstyle']['categories']:
            # get the color of this category
            self.response['colors'].append(category['color'])
            cond = []

            for oneCondition in category['conditions']:
                field = oneCondition['field']
                value = oneCondition['value']
                operator = oneCondition['operator']

                if (StormDrain._meta.get_field(field).get_internal_type()
                        == 'DateTimeField'):
                    field = 'TO_CHAR(' + field + ', \'YYYY/MM\')'

                if value in null_values:
                    if operator == '=':
                        operator = ' IS NULL '
                    else:
                        operator = ' IS NOT NULL '

                    cond.append(field + operator)
                else:
                    cond.append(field + operator + "'" + value.lower() + "'")

            conds = ' AND '.join(cond)
            t = 'CASE WHEN ('+conds+') THEN '+str(counter)+' ELSE '
            ends.append(' END ')
            cases.append(t)
            counter += 1

            # Add default value -1 to the last else
            # and close cases when ... end.
        cases = ''.join(cases) + '-1' + ''.join(ends)

        # When no categories exist
        if (cases == '-1'):
            cases = None

        return cases

    def _get_data(self, cases, visible_styles):
        """Return the data of the visible layers."""
        if cases is None:
            data = StormDrain.objects.all().extra(
                select={
                    'date': 'TO_CHAR(date, \'YYYY/MM\')',
                    'n': '1'
                }
            )
        else:
            data = StormDrain.objects.all().extra(
                select={
                    'date': 'TO_CHAR(date, \'YYYY/MM\')',
                    'n': cases
                },
                where=[cases + " != %s"], params=[-1]
            )
        # FILTER THE DATA
        if self.request.user.is_root():
            # if it's root get any storm drain of the selected user versions
            if ('users_version' in visible_styles['jstyle']):
                user_ver_conds = []
                for user_ver in visible_styles['jstyle']['users_version']:
                    if user_ver['version'] != "0":
                        user_ver_conds.append(Q(
                            user=user_ver['user_id'],
                            version=user_ver['version']
                        ))
                data = data.filter(reduce(OR, user_ver_conds))
        else:
            # limit to the user's data if it is not root
            data = data.filter(
                user=self.request.user.id,
                version=visible_styles['version']
            )

        return data

    def get(self):
        """Get the storm drain data."""
        # Return an Unauthorized 401 message if the user is not authenticated
        if not self.request.user.is_authorized:
            return self._end_unauthorized()

        # Get json style structure from StormDrainUserVersions where visible
        visible_styles = self._get_visible_styles()

        # Get the SQL conditions matching the styling conditions
        cases = self._get_sql_style_conditions(visible_styles)

        # get the data
        data = self._get_data(cases, visible_styles)

        self.response['style_json'] = visible_styles['jstyle']
        self.response['rows'] = list(data.values_list('lat', 'lon', 'n'))
        self.response['num_rows'] = len(data)

        return self._end()


class StormDrainUserSetup(StormDrainVersioningMixin, BaseManager):
    """Manage the storm drains display configuration."""

    def _get_field_distinct_values(self, fieldname):
        """Return the distinct values of a field."""
        # Get the distinct values of the field
        result = StormDrain.objects.extra(
                select={
                    'date': 'TO_CHAR(date, \'YYYY/MM\')'
                }
            ).values(
                'version', 'user_id', fieldname
            ).distinct()

        # If the user is not root, get only the records of the current user
        if not self.request.user.is_root():
            result = result.filter(
                user__exact=self.request.user.id
            )

        # Sort by fieldname
        result = result.order_by(fieldname)
        # if the field is a DateTimeField, sort descending
        if (StormDrain._meta.get_field(fieldname).get_internal_type() ==
                'DateTimeField'):
            result = result.order_by('-'+fieldname)

        return result

    def _get_my_versions(self):
        """Return the versions of the current user."""
        result = {}
        versions = self.my_versions.order_by('-version')
        for v in versions:
            result.update({v['version']: {
                'title': (v['title'] is not None and v['title']) or '',
                'date': v['date'],
                'style_json': (v['style_json'] != ''
                               and json.loads(v['style_json'])) or '',
                'visible': v['visible']
            }})

        return result

    def _get_user_data_versions(self):
        """Return the user_versions."""
        # initialize result

        versions = {}
        # store versions from other users
        self.other_versions = self.versions.filter(
            user__in=StormDrain.objects.values(
                        'user_id'
                    ).distinct()
        ).exclude(
            user_id__exact=self.request.user.id
        ).order_by('-version', 'user')

        # get visibility of other user's data
        visibleVer = self._get_versions_visibility()
        # Get available versions for the user to choose
        for raw in self.other_versions:
            iduser = str(raw['user'])
            title = (raw['title'] is not None and raw['title']) or ''
            # if this user has no data yet, create it with an empty 'versions'
            if iduser not in versions:
                versions.update({iduser: {}})
                versions[iduser].update({
                    'username': raw['user__username'],
                    'visible': visibleVer[iduser],
                    'versions': []
                })

            # add the version to the user
            versions[iduser]['versions'].append({
                'version': raw['version'],
                'date': raw['date'],
                'visible': raw['visible'],
                'title': title
            })

        return versions

    def _get_version_fields(self):
        """Get the fields (and their values) for all versions."""
        result = {}
        # loop through every thematic field
        for fieldname in tematic_fields:
            # Get the distinct values of this field
            fieldValues = self._get_field_distinct_values(fieldname)
            # If there are values ...
            if len(fieldValues):
                # Iterate through the values and create structure
                for row in fieldValues:
                    version = row['version']
                    value = row[fieldname]
                    value = 'null' if value is None else value
                    iduser = row['user_id']

                    if iduser not in result:
                        result.update({iduser: {}})

                    if version not in result[iduser]:
                        result[iduser].update({version: {}})

                    if value != '':
                        if fieldname not in result[iduser][version]:
                            result[iduser][version].update({fieldname: []})
                        result[iduser][version][fieldname].append(value)

                # If user is not root and there is only NULL values
                # remove the field
                if (not self.request.user.is_root() and
                        len(result[iduser][version][fieldname]) == 1 and
                        result[iduser][version][fieldname][0] is 'null'):
                    del result[iduser][version][fieldname]

        return result

    def _get_version_operators(self):
        """Return a list of valid operators."""
        result = {}
        # Loop through every field in the model
        for field in StormDrain._meta.fields:
            # Common operators
            operators = ['=', '<>']
            # if it is not a thematic field, ignore it
            if field.name in tematic_fields:
                # If it is a field of type DateTimeField add '<=' and '>='
                # operators
                if field.get_internal_type() == 'DateTimeField':
                    operators = operators + ['<=', '>=']
                # Add the field to the result
                result.update({field.name: operators})

        return result

    def _get_versions_visibility(self):
        """Return a list of versions with their visibility."""
        visibleVer = {}
        # Get visible versions from super user versions
        if len(self.my_versions) > 0:
            jstyle = json.loads(self.my_versions[0]['style_json'])
            if 'users_version' in jstyle:
                for oneStyle in jstyle['users_version']:
                    iduser = str(oneStyle['user_id'])
                    if iduser not in visibleVer:
                        visibleVer[iduser] = oneStyle['version']

        # If we have no data, get visible versions from other user's versions
        if (not len(visibleVer.keys())):
            for oneVer in self.other_versions:
                iduser = str(oneVer['user'])
                if iduser not in visibleVer:
                    visibleVer[iduser] = oneVer['version']

        return visibleVer

    def get(self):
        """Return the list of storm drain user setups."""
        # Return an Unauthorized 401 message if the user is not authenticated
        if not self.request.user.is_authenticated:
            return self._end_unauthorized()

        # If super-mosquito, get list of all users and versions available
        if self.request.user.is_root():
            # get versions from other user's data
            self.response['users_version'] = self._get_user_data_versions()

        # Get my versions
        self.response['versions'] = self._get_my_versions()
        # Get the fields used for every version
        self.response['fields'] = self._get_version_fields()
        # Get the operators available for every field of every version
        self.response['operators'] = self._get_version_operators()
        # Return the user id
        self.response['user'] = self.request.user.id

        # Finish up
        return self._end()

    def _hide_all_versions(self):
        """Set all current versions to visible=False.

        If there are no versions and user is root, create a new version.
        Returns False if there is no data.
        Returns True if there is data.
        """
        # If user has no version ...
        if (len(self.my_versions) == 0):
            # If user is not root, return False
            if not self.request.user.is_root():
                return False
                # self._add_version(self.request)
            else:
                # if user is root, add a new version
                self._add_version(self.request, 1)
        else:
            # Set the visibility of all the versions to False
            user_version = StormDrainUserVersions.objects.filter(
                user=self.request.user.id
            )
            user_version.update(visible=False)

        return True

    def put(self):
        """Store a style configuration on the server."""
        # Return an Unauthorized 401 message if the user is not authenticated
        if not self.request.user.is_authenticated:
            return self._end_unauthorized()

        deactivated = self._hide_all_versions()

        # If deactivated is False, there is no data, bail out
        if not deactivated:
            self.response['err'] = 'No data available'
            return self._end()

        style_str = self.request.body.decode(encoding='UTF-8')
        style = json.loads(style_str)

        # Save the style json structure and make current version visible
        user_version = StormDrainUserVersions.objects.filter(
            user=self.request.user.id,
            version=style['version_data']
        )
        user_version.update(visible=True, style_json=style_str)

        self.response = {'success': True}

        return self._end()


class StormDrainUploader(StormDrainVersioningMixin, BaseManager):
    """Manage the storm drains data uploading."""

    response = {'success': False, 'desc': ''}

    def get_template(self):
        """Return the template used to import storm drain data."""
        if self.request.user.is_authorized:
            in_memory = BytesIO()
            zip = ZipFile(in_memory, "a")
            # Add files to zip
            for dirname, subdirs, files in os.walk(stormdrain_templates_path):
                for filename in files:
                    zip.write(os.path.join(dirname, filename), filename)
            # close zip
            zip.close()
            # prepare response object
            response = HttpResponse(content_type="application/zip")
            response["Content-Disposition"] = ("attachment;filename="
                                               "mosquito_alert_template.zip")
            # write files into the response
            in_memory.seek(0)
            response.write(in_memory.read())

            return response
        else:
            return self._end_unauthorized()

    def _match_column_to_field(self, fields, file_headers, key):
        """Match each column name with the model fields."""
        for field in fields:
            header_position = 0
            for header in file_headers:
                if header == field:
                    self.dataset.headers[header_position] = key
                else:
                    header_position = header_position + 1

    def _get_missing_fields(self, file_headers):
        """Return all missing headers."""
        # has_missing = False
        missing_headers = []
        for key, fieldVariants in (
                compulsatory_stormdrain_fields.items()
                ):
            if not bool(set(fieldVariants) & set(file_headers)):
                missing_headers.append(key)
            else:
                # find out the match between column name and model field
                self._match_column_to_field(
                    fieldVariants,
                    file_headers,
                    key
                )
        return missing_headers

    def _get_optional_fields(self, file_headers):
        for key, fieldVariants in optional_stormdrain_fields.items():
            # find out the match between column name and model field
            self._match_column_to_field(
                fieldVariants,
                file_headers,
                key
            )

    def _prepare_dataset_to_import(self):
        # Add column 'user_id'
        self.dataset.insert_col(
            0,
            col=([self.request.user.id, ]
                 * self.dataset.height),
            header="user_id"
        )
        # Add column 'version'
        self.last_ver = self._get_last_version_id(self.request)
        self.dataset.insert_col(
            0,
            col=[self.last_ver+1, ]*self.dataset.height,
            header="version"
        )
        # Define index position of headers
        headers = {k: v for v, k in
                   enumerate(self.dataset.headers)}

        # Add original lat, lon columns
        self.dataset.append_col(
            self.dataset.get_col(headers['lon']),
            header="original_lon"
        )
        self.dataset.append_col(
            self.dataset.get_col(headers['lat']),
            header="original_lat"
        )

        booleans = []
        numerics = []

        for field in StormDrain._meta.fields:
            if field.get_internal_type() == 'NullBooleanField':
                booleans.append(field.name)
            elif field.get_internal_type() in [
                        'FloatField',
                        'DecimalField',
                        'IntegerField'
                    ]:
                numerics.append(field.name)

        return {'booleans': booleans, 'numerics': numerics}

    def _check_fieldtypes(self, row, fieldtypes):
        # Check numeric fields. No value raises an error
        for field in fieldtypes['numerics']:
            if field in row:
                row[field] = row[field] if (
                    row[field] not in ['', None]
                ) else 0

        # Check boolean fields
        for field in fieldtypes['booleans']:
            if field in row:
                row[field] = 'null' if row[field] is None else (
                    1 if str(row[field]).lower() in (
                        true_values
                    ) else (
                        0 if str(row[field]).lower() in (
                            false_values
                        ) else None
                    )
                )
        return row

    def _import(self):
        """Execute the import."""
        import_dataset = Dataset()
        fieldtypes = self._prepare_dataset_to_import()
        import_dataset.headers = self.dataset.headers
        inProj = Proj(init='epsg:25831')
        outProj = Proj(init='epsg:4326')
        for row in self.dataset.dict:
            # Ignore rows with emtpy lat or lon
            if row['lon'] is not None and row['lat'] is not None:
                row['lon'], row['lat'] = transform(
                    inProj,
                    outProj,
                    row['lon'],
                    row['lat']
                )
                row = self._check_fieldtypes(row, fieldtypes)
                new = []
                for key in row:
                    new.append(row[key])
                try:
                    import_dataset.append(new)
                except Exception as e:
                    self.response = {'success': False, 'err': e}

        db = connection.cursor()
        import_dataset.headers = None

        with tempfile.NamedTemporaryFile(mode="r+",
                                         delete=False,
                                         newline='') as f:
            try:
                f.write(import_dataset.csv)
            except Exception as e:
                self.response = {'success': False, 'err': e}

            f.seek(0)

            try:
                db.copy_from(f, 'storm_drain',
                             columns=(self.dataset.headers),
                             sep=",",
                             null='null')

                self._add_version(
                    self.request,
                    self.dataset.dict[0]['version']
                )

                self.response = {
                    'success': True,
                    'headers': self.dataset.headers
                }
            except Exception as e:
                self.response = {'success': False, 'err': e}

    def put(self, *args, **kwargs):
        """Import a file."""
        if self.request.user.is_manager():
            if self.request.method == 'POST':
                # Prepare the input Dataset
                self.dataset = Dataset()
                # Get file name and extension
                file = self.request.FILES['stormdrain-file']
                name, extension = os.path.splitext(
                    self.request.FILES['stormdrain-file'].name
                )
                # Load data into the input Dataset
                self.dataset.load(file.read(), extension[1:])
                # headers to lowercase

                file_headers = [str(x).lower() for x in
                                self.dataset.headers]

                # Detect missing headers
                missing_headers = self._get_missing_fields(file_headers)
                # Get optional headers
                self._get_optional_fields(file_headers)
                # If there is no missing header
                if len(missing_headers) == 0:
                    try:
                        self._import()
                    except Exception as e:
                        # error = str(e).replace('\n', ' ').replace('\r', '')
                        self.response = {'success': False, 'err': str(e)}
                else:
                    txtMissing = ', '.join(missing_headers)
                    self.response['err'] = (
                        'Missing one or more required fields'
                        '('+txtMissing+')'
                    )
            else:
                self.response['err'] = 'No file uploaded'
        else:
            self.response['err'] = 'Unauthorized'

        return self._end()
