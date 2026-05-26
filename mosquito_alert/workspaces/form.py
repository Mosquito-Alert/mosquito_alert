from django import forms
from django.contrib.gis.forms import GeometryField, OSMWidget

from .models import Workspace


class WorkspaceAdminForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = "__all__"

    geom = GeometryField(
        widget=OSMWidget(attrs={"disabled": True}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        if instance:
            geom = instance.geom or (
                instance.country.geom if instance.country else None
            )

            if geom:
                self.initial["geom"] = geom
