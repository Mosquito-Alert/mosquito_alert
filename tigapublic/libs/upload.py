# -*- coding: utf-8 -*-
"""Storm Drain Libraries."""
import os
import tempfile
from io import BytesIO
from zipfile import ZipFile

from django.db import connection
from django.http import HttpResponse
from tablib import Dataset
from .base import BaseManager
from tigapublic.utils import extendUser
from tigapublic.constants import (true_values, false_values)
from tigapublic.models import Epidemiology


class ExcelUploader(BaseManager):
    """Manage general uploading."""

    response = {'success': False, 'desc': ''}

    def __init__(self, request, **kwargs):
        """Instantiate class ."""
        self.request = request
        self.request.user = extendUser(request.user)
        self.model = kwargs['model']

        self.compulsatory_fields = kwargs['compulsatory_fields']
        self.optional_fields = kwargs['optional_fields']
        self.template_location = kwargs['template_location']
        self.template_zipped_name = kwargs['template_zipped_name']
        self.form_input_name = kwargs['form_input_name']

    def get_template(self):
        """Return the template used to import storm drain data."""
        if self.request.user.is_epidemiologist_editor():
            in_memory = BytesIO()
            zip = ZipFile(in_memory, "a")
            # Add files to zip
            for dirname, subdirs, files in os.walk(self.template_location):
                for filename in files:
                    zip.write(os.path.join(dirname, filename), filename)
            # close zip
            zip.close()
            # prepare response object
            response = HttpResponse(content_type="application/zip")
            response["Content-Disposition"] = ("attachment;filename=" +
                                               self.template_zipped_name)
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
                self.compulsatory_fields.items()
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
        for key, fieldVariants in self.optional_fields.items():
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

        booleans = []
        numerics = []

        for field in Epidemiology._meta.fields:
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

        for row in self.dataset.dict:
            row = self._check_fieldtypes(row, fieldtypes)
            new = []
            for key in row:
                new.append(row[key])

            import_dataset.append(new)

        db = connection.cursor()
        import_dataset.headers = None

        with tempfile.NamedTemporaryFile(mode="r+",
                                         delete=False,
                                         newline='') as f:
                f.write(import_dataset.get_csv(delimiter='\t'))
                f.seek(0)

                try:
                    # Delete all elements before new import
                    self.model.objects.all().delete()
                    db.copy_from(f, self.model._meta.db_table,
                                 columns=(self.dataset.headers),
                                 sep="\t",
                                 null='')
                    self.response = {
                        'success': True,
                        'headers': self.dataset.headers
                    }
                except Exception as e:
                    # error = str(e).replace('\n', ' ').replace('\r', '')
                    self.response = {'success': False, 'err': e}

    def put(self, *args, **kwargs):
        """Import a file."""
        # print self.model
        if self.request.user.is_epidemiologist_editor():
            if self.request.method == 'POST':
                # Prepare the input Dataset
                self.dataset = Dataset()
                # Get file name and extension
                file = self.request.FILES[self.form_input_name]
                name, extension = os.path.splitext(
                    self.request.FILES[self.form_input_name].name
                )
                # Load data into the input Dataset
                self.dataset.load(file.read(), extension[1:])

                # headers to lowercase, and utf-8 encode (adreça...)
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
                        self.response = {'success': False, 'err': e}
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
