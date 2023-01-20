from django import forms
from django.contrib.gis import forms as gisforms

from mosquito_alert.geo.models import Location
from mosquito_alert.individuals.models import Individual

from .models import BiteReport, BreedingSiteReport, IndividualReport, Report


class ReportForm(forms.ModelForm):

    location_point = gisforms.PointField(
        srid=Location._meta.get_field("point").srid,
        required=True,
        widget=gisforms.OSMWidget(),
        label="Location",
    )

    def __init__(self, *args, **kwargs) -> None:
        if instance := kwargs.get("instance", None):
            if hasattr(instance, "location"):
                self.declared_fields["location_point"].initial = instance.location.point
                self.declared_fields["location_point"].disabled = True
        super().__init__(*args, **kwargs)

    def save(self, commit=True):

        if self.instance._state.adding:
            self.instance.user = self.request.user

            self.instance.location = Location.objects.create(
                point=self.cleaned_data["location_point"]
            )
            # self.cleaned_data['location'] = location_obj

        return super().save(commit)

    class Meta:
        model = Report
        fields = ["observed_at", "note"]


class BiteReportForm(ReportForm):
    class Meta:
        model = BiteReport
        fields = ReportForm.Meta.fields + [
            "bites",
        ]


class BreedingSiteReportForm(ReportForm):
    class Meta:
        model = BreedingSiteReport
        fields = ReportForm.Meta.fields + ["has_water", "breeding_site"]


class IndividualReportForm(ReportForm):
    def save(self, commit=True):

        if self.instance._state.adding:
            self.instance.individual = Individual.objects.create()
            self.instance.individual.identification_set.taxon = self.cleaned_data[
                "taxon"
            ]
            self.instance.individual.identification_set.save()

        return super().save(commit)

    class Meta:
        model = IndividualReport
        fields = ReportForm.Meta.fields + [
            "taxon",
        ]
