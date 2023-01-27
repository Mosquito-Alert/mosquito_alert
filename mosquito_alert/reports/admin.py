from django.contrib import admin
from nested_admin.forms import SortableHiddenMixin
from nested_admin.nested import NestedTabularInline
from nested_admin.polymorphic import NestedPolymorphicModelAdmin
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)
from reversion.admin import VersionAdmin

from mosquito_alert.images.admin import m2mPhotoAdminInlineMixin
from mosquito_alert.utils.admin import FlaggedContentInlineAdmin

from .forms import (
    BiteReportForm,
    BreedingSiteReportForm,
    IndividualReportForm,
    ReportForm,
)
from .models import BiteReport, BreedingSiteReport, IndividualReport, Report


class ReadOnlyPhotoAdminInline(
    SortableHiddenMixin, m2mPhotoAdminInlineMixin, NestedTabularInline
):
    model = Report.photos.through
    fields = m2mPhotoAdminInlineMixin.fields + [
        "sort_value",
    ]
    sortable_field_name = "sort_value"


class ReportChildAdmin(NestedPolymorphicModelAdmin, PolymorphicChildModelAdmin):
    """Base admin class for all child models"""

    base_model = Report
    base_form = ReportForm
    show_in_index = True
    inlines = [ReadOnlyPhotoAdminInline, FlaggedContentInlineAdmin]
    list_filter = ["observed_at", "created_at"]
    list_display = ["uuid", "user", "observed_at", "created_at", "updated_at"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.request = request
        return form


@admin.register(BiteReport)
class BiteReportChildAdmin(ReportChildAdmin, VersionAdmin):
    class BitesInlineAdmin(NestedTabularInline):
        model = BiteReport.bites.through
        extra = 0
        show_change_link = True

    base_model = BiteReport
    base_form = BiteReportForm

    inlines = ReportChildAdmin.inlines + [BitesInlineAdmin]


@admin.register(BreedingSiteReport)
class BreedingSiteReportChildAdmin(ReportChildAdmin, VersionAdmin):
    base_model = BreedingSiteReport
    base_form = BreedingSiteReportForm
    list_filter = ReportChildAdmin.list_filter + ["has_water"]
    list_display = ReportChildAdmin.list_display + ["has_water"]


@admin.register(IndividualReport)
class IndividualReportAdmin(ReportChildAdmin, VersionAdmin):
    base_model = IndividualReport
    base_form = IndividualReportForm
    readonly_fields = ["individual"]


class ReportParentAdmin(VersionAdmin, PolymorphicParentModelAdmin):
    base_model = Report
    child_models = (BiteReport, BreedingSiteReport, IndividualReport)
    list_filter = (PolymorphicChildModelFilter, "observed_at", "created_at")
    list_display = ["uuid", "user", "observed_at", "created_at", "updated_at"]


admin.site.register(Report, ReportParentAdmin)
