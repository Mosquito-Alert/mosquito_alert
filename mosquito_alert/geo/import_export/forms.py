from django import forms
from django.utils.translation import gettext_lazy as _
from import_export.forms import ConfirmImportForm, ImportForm

from ..models import BoundaryLayer


class ShapefileImportForm(ImportForm):
    code_field_name = forms.CharField(label=_("Code field name"))

    name_field_name = forms.CharField(label=_("Name field name"))

    boundary_layer = forms.ModelChoiceField(
        queryset=BoundaryLayer.objects.all(), required=True
    )


class ShapefileConfirmImportForm(ConfirmImportForm):
    code_field_name = forms.CharField(label=_("Code field name"))

    name_field_name = forms.CharField(label=_("Name field name"))

    boundary_layer = forms.ModelChoiceField(
        queryset=BoundaryLayer.objects.all(), required=True
    )
