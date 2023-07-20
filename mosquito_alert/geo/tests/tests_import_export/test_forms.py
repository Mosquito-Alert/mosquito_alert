import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from import_export.formats.base_formats import DEFAULT_FORMATS

from ...import_export.forms import ShapefileConfirmImportForm, ShapefileImportForm


class TestShapefileImportForm:
    @pytest.fixture
    def tmpdir_csv_file(self):
        return SimpleUploadedFile(
            "file.csv",
            b"file_content",
            content_type="text/csv",
        )

    @pytest.fixture
    def common_data(self, tmpdir_csv_file):
        return {"input_format": "0", "import_file": tmpdir_csv_file}

    @pytest.fixture
    def common_files(self, tmpdir_csv_file):
        return {"import_file": tmpdir_csv_file}

    def test_valid_form(self, common_data, common_files, country_bl):
        data = {
            "code_field_name": "TEST_CODE",
            "name_field_name": "TEST_NAME",
            "boundary_layer": country_bl.pk,
        } | common_data

        form = ShapefileImportForm(
            data=data,
            files=common_files,
            import_formats=DEFAULT_FORMATS,
        )

        assert form.is_valid()

    def test_boundary_layer_is_required(self, common_data, common_files):
        data = {
            "code_field_name": "TEST_CODE",
            "name_field_name": "TEST_NAME",
        } | common_data

        form = ShapefileImportForm(data=data, files=common_files, import_formats=DEFAULT_FORMATS)

        assert not form.is_valid()
        assert "boundary_layer" in form.errors


class TestShapefileConfirmImportForm:
    @pytest.fixture
    def common_data(tmpdir_csv_file):
        return {
            "import_file_name": "/path/to/filename.test",
            "original_file_name": "original_filename.test",
            "input_format": "0",
        }

    def test_valid_form(self, common_data, country_bl):
        data = {
            "code_field_name": "TEST_CODE",
            "name_field_name": "TEST_NAME",
            "boundary_layer": country_bl.pk,
        } | common_data

        form = ShapefileConfirmImportForm(
            data=data,
        )

        print(form.errors)
        assert form.is_valid()

    def test_boundary_layer_is_required(self, common_data):
        data = {
            "code_field_name": "TEST_CODE",
            "name_field_name": "TEST_NAME",
        } | common_data

        form = ShapefileConfirmImportForm(data=data)

        assert not form.is_valid()
        assert "boundary_layer" in form.errors
