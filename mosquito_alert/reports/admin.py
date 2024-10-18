from django.contrib import admin
from nested_admin.forms import SortableHiddenMixin
from nested_admin.nested import NestedTabularInline
from nested_admin.polymorphic import NestedPolymorphicModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicChildModelFilter, PolymorphicParentModelAdmin
from reversion.admin import VersionAdmin

from mosquito_alert.images.admin import m2mPhotoAdminInlineMixin
from mosquito_alert.moderation.admin import FlaggedContentNestedInlineAdmin

from .forms import BiteReportForm, BreedingSiteReportForm, IndividualReportForm, ReportForm
from .models import BiteReport, BreedingSiteReport, IndividualReport, Report


class ReadOnlyPhotoAdminInline(SortableHiddenMixin, m2mPhotoAdminInlineMixin, NestedTabularInline):
    # WARNING: Using many2many as AdminInline does not trigger m2m_changed signals.
    # See:  https://code.djangoproject.com/ticket/17688
    #       https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#working-with-many-to-many-models
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
    inlines = [ReadOnlyPhotoAdminInline, FlaggedContentNestedInlineAdmin]
    list_filter = ["observed_at", "created_at"]
    list_display = ["id", "short_id", "user", "observed_at", "created_at", "updated_at"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.request = request
        return form


@admin.register(BiteReport)
class BiteReportChildAdmin(VersionAdmin, ReportChildAdmin):
    class BitesInlineAdmin(NestedTabularInline):
        model = BiteReport.bites.through
        extra = 0
        show_change_link = True

    base_model = BiteReport
    base_form = BiteReportForm

    inlines = ReportChildAdmin.inlines + [BitesInlineAdmin]


@admin.register(BreedingSiteReport)
class BreedingSiteReportChildAdmin(VersionAdmin, ReportChildAdmin):
    base_model = BreedingSiteReport
    base_form = BreedingSiteReportForm
    list_filter = ReportChildAdmin.list_filter + ["has_water"]
    list_display = ReportChildAdmin.list_display + ["has_water"]


@admin.register(IndividualReport)
class IndividualReportAdmin(VersionAdmin, ReportChildAdmin):
    base_model = IndividualReport
    base_form = IndividualReportForm

    class Individualm2mAdminInline(NestedTabularInline):
        def has_add_permission(self, request, obj=None) -> bool:
            return False

        def has_change_permission(self, request, obj=None) -> bool:
            return False

        is_sortable = False
        can_delete = False
        extra = 0

        show_change_link = True
        model = IndividualReport.individuals.through

    inlines = ReportChildAdmin.inlines + [Individualm2mAdminInline]


@admin.register(Report)
class ReportParentAdmin(VersionAdmin, PolymorphicParentModelAdmin):
    base_model = Report
    child_models = (BiteReport, BreedingSiteReport, IndividualReport)
    list_filter = (PolymorphicChildModelFilter, "observed_at", "created_at")
    list_display = ["id", "user", "observed_at", "created_at", "updated_at"]
