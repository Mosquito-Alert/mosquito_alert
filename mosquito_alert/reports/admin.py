from django.contrib import admin
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)
from reversion.admin import VersionAdmin

from .forms import (
    BiteReportForm,
    BreedingSiteReportForm,
    IndividualReportForm,
    ReportForm,
)
from .models import (
    BiteReport,
    BreedingSiteReport,
    IndividualReport,
    Report,
    ReportPhoto,
)


class ReportPhotoInline(admin.TabularInline):
    model = ReportPhoto


#################################################


class ReportChildAdmin(PolymorphicChildModelAdmin):
    """Base admin class for all child models"""

    base_model = Report
    base_form = ReportForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.request = request
        return form


@admin.register(BiteReport)
class BiteReportChildAdmin(ReportChildAdmin, VersionAdmin):
    base_model = BiteReport
    base_form = BiteReportForm

    filter_horizontal = ("bites",)


@admin.register(BreedingSiteReport)
class BreedingSiteReportChildAdmin(ReportChildAdmin, VersionAdmin):
    base_model = BreedingSiteReport
    base_form = BreedingSiteReportForm


@admin.register(IndividualReport)
class IndividualReportAdmin(VersionAdmin, ReportChildAdmin):
    base_model = IndividualReport
    base_form = IndividualReportForm


class ReportParentAdmin(VersionAdmin, PolymorphicParentModelAdmin):
    base_model = Report
    child_models = (BiteReport, BreedingSiteReport, IndividualReport)
    list_filter = (PolymorphicChildModelFilter, "observed_at", "created_at")
    list_display = ["uuid", "user", "observed_at", "created_at", "updated_at"]

    inlines = [
        ReportPhotoInline,
    ]


admin.site.register(Report, ReportParentAdmin)
