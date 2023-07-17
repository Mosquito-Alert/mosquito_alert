from import_export import admin

from .formats import ZippedShapefileFormat
from .forms import ShapefileConfirmImportForm, ShapefileImportForm
from .tmp_storage import TempFolderZippedGDALFileSystemStorage


class ShapefileImportMixin(admin.ImportMixin):
    import_form_class = ShapefileImportForm
    confirm_form_class = ShapefileConfirmImportForm

    formats = [
        ZippedShapefileFormat,
    ]

    tmp_storage_class = TempFolderZippedGDALFileSystemStorage

    def get_confirm_form_initial(self, request, import_form):
        initial = super().get_confirm_form_initial(request, import_form)
        # Pass on the custom fields value from the import form to
        # the confirm form (if provided)
        if import_form:
            initial["code_field_name"] = import_form.cleaned_data["code_field_name"]
            initial["name_field_name"] = import_form.cleaned_data["name_field_name"]
            initial["boundary_layer"] = import_form.cleaned_data["boundary_layer"]
        return initial

    def get_import_data_kwargs(self, request, *args, **kwargs):
        """
        Prepare kwargs for import_data.
        """
        form = kwargs.get("form")
        if form:
            kwargs.pop("form")
            kwargs["boundary_layer"] = form.cleaned_data["boundary_layer"]
            kwargs["code_fieldname"] = form.cleaned_data["code_field_name"]
            kwargs["name_fieldname"] = form.cleaned_data["name_field_name"]
            return kwargs
        return {}
