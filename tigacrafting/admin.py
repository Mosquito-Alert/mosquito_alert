from django.contrib import admin
from tigacrafting.models import MoveLabAnnotation, ExpertReportAnnotation, UserStat, Taxon
from tigaserver_app.models import NutsEurope
import csv
from django.utils.encoding import smart_str
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from modeltranslation.admin import TranslationAdmin


def export_full_csv(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    this_meta = queryset[0]._meta
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_export_ ' + smart_str(this_meta.db_table) + '.csv'
    writer = csv.writer(response, csv.excel, quoting=csv.QUOTE_NONNUMERIC)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    colnames = []
    for field in this_meta.fields:
        colnames.append(smart_str(field.name))
    writer.writerow(colnames)
    for obj in queryset:
        this_row = []
        for field in this_meta.fields:
            this_row.append(smart_str(getattr(obj, field.name)))
        writer.writerow(this_row)
    return response
export_full_csv.short_description = u"Export Full CSV"


def export_full_csv_sc(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    this_meta = queryset[0]._meta
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_export_ ' + smart_str(this_meta.db_table) + '.csv'
    writer = csv.writer(response, csv.excel, delimiter=";",  quoting=csv.QUOTE_NONNUMERIC)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    colnames = []
    for field in this_meta.fields:
        colnames.append(smart_str(field.name))
    writer.writerow(colnames)
    for obj in queryset:
        this_row = []
        for field in this_meta.fields:
            this_row.append(smart_str(getattr(obj, field.name)))
        writer.writerow(this_row)
    return response
export_full_csv_sc.short_description = u"Export Full Semi-Colon Separated Values"


class MoveLabAnnotationAdmin(admin.ModelAdmin):
    list_display = ('task', 'tiger_certainty_category', 'created', 'last_modified')
    ordering = ('last_modified',)
    readonly_fields = ('task', 'tiger_certainty_category', 'created', 'last_modified', 'certainty_notes', 'hide', 'edited_user_notes')
    fields = ('task', 'tiger_certainty_category', 'created', 'last_modified', 'certainty_notes', 'hide', 'edited_user_notes')
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ExpertReportAnnotationAdmin(admin.ModelAdmin):
    list_display = ('user', 'report', 'tiger_certainty_category', 'created', 'last_modified')
    ordering = ('last_modified',)
    readonly_fields = ('user', 'report', 'tiger_certainty_category', 'tiger_certainty_notes', 'site_certainty_category', 'site_certainty_notes', 'edited_user_notes', 'message_for_user', 'status', 'last_modified', 'validation_complete', 'revise', 'best_photo', 'linked_id', 'created')
    fields = ('user', 'report', 'tiger_certainty_category', 'tiger_certainty_notes', 'site_certainty_category', 'site_certainty_notes', 'edited_user_notes', 'message_for_user', 'status', 'last_modified', 'validation_complete', 'revise', 'best_photo', 'linked_id', 'created')
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UserStatAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    ordering = ('user__username',)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "nuts2_assignation":
            kwargs["queryset"] = NutsEurope.objects.all().order_by('europecountry__name_engl','name_latn')
        return super(UserStatAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Taxon)
class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name", 'content_object', 'is_relevant')
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon)

    fieldsets = [
        (_("Node position"), {"fields": ("_position", "_ref_node_id")}),
        (_("Basic information"), {"fields": ("rank", ("name", "is_relevant"), "common_name")}),
        (_("Old tables relationship"), {"fields": ("content_type", "object_id")})
    ]

admin.site.register(MoveLabAnnotation, MoveLabAnnotationAdmin)
admin.site.register(ExpertReportAnnotation, ExpertReportAnnotationAdmin)
admin.site.register(UserStat, UserStatAdmin)
