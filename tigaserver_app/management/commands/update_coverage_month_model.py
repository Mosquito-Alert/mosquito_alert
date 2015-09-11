from django.core.management.base import BaseCommand, CommandError
from tigaserver_app.models import CoverageAreaMonth, Fix, Report
from tigaserver_app.views import get_latest_reports_qs, lat_function, lat_function_m0, lat_function_y0
import pytz
from datetime import datetime
from django.conf import settings
from django.db.models import Q


class Command(BaseCommand):
    args = ''
    help = 'Updates coverage month model data based on background location and report location data'

    def handle(self, *args, **options):
        updated = False
        if CoverageAreaMonth.objects.all().count() > 0:
            latest_report_server_upload_time = CoverageAreaMonth.objects.order_by('latest_report_server_upload_time').last().latest_report_server_upload_time
            latest_fix_id = CoverageAreaMonth.objects.order_by('latest_fix_id').last().latest_fix_id
        else:
            latest_report_server_upload_time = pytz.utc.localize(datetime(1970, 1, 1))
            latest_fix_id = 0
        if CoverageAreaMonth.objects.all().count() == 0 or latest_report_server_upload_time < Report.objects.order_by('server_upload_time').last().server_upload_time or latest_fix_id < Fix.objects.order_by('id').last().id:
            report_list = get_latest_reports_qs(Report.objects.exclude(hide=True).filter(Q(package_name='Tigatrapp',  creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)).filter(server_upload_time__gt=latest_report_server_upload_time))
            fix_list = Fix.objects.filter(fix_time__gt=settings.START_TIME, id__gt=latest_fix_id)
            full_lat_list = [(f.masked_lat, f.fix_time.year, f.fix_time.month) for f in fix_list] + [(r.masked_lat, r.creation_time.year, r.creation_time.month) for r in report_list if r.masked_lat is not None]
            full_lat_list_m0 = [(f.masked_lat, f.fix_time.year) for f in fix_list] + [(r.masked_lat, r.creation_time.year) for r in report_list if r.masked_lat is not None]
            full_lat_list_y0 = [(f.masked_lat, f.fix_time.month) for f in fix_list] + [(r.masked_lat, r.creation_time.month) for r in report_list if r.masked_lat is not None]
            unique_lats = set(full_lat_list)
            unique_lats_m0 = set(full_lat_list_m0)
            unique_lats_y0 = set(full_lat_list_y0)
            [lat_function(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats]
            [lat_function_m0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats_m0]
            [lat_function_y0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats_y0]
            updated = True
        self.stdout.write('Successfully updated coverage area month model' if updated else 'No updates needed.')