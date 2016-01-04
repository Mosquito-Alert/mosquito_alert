from django.contrib import admin
from models import Annotation, MoveLabAnnotation, ExpertReportAnnotation, UserStat, CrowdcraftingUser, CrowdcraftingResponse, CrowdcraftingTask
import csv
from django.utils.encoding import smart_str
from django.http.response import HttpResponse


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


admin.site.disable_action('delete_selected')


class MoveLabAnnotationAdmin(admin.ModelAdmin):
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ExpertReportAnnotationAdmin(admin.ModelAdmin):
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(MoveLabAnnotation, MoveLabAnnotationAdmin)
admin.site.register(ExpertReportAnnotation, ExpertReportAnnotationAdmin)
