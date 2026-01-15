from django.core.management.base import BaseCommand
from tigaserver_app.models import CoverageAreaMonth, Fix, Report
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from zoneinfo import ZoneInfo


def lon_function(this_lon, these_lons, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2]).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2])
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2], n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lon_function_m0(this_lon, these_lons_m0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons_m0 if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0)
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0, n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lon_function_y0(this_lon, these_lons_y0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons_y0 if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0)
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0, n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lat_function(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons = [(f.masked_lon, f.fix_time.year, f.fix_time.month) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.year == this_lat[1] and f.fix_time.month == this_lat[2])] + [(r.masked_lon, r.creation_time.year, r.creation_time.month) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.year == this_lat[1] and r.creation_time.month == this_lat[2])]
    unique_lons = set(these_lons)
    [lon_function(this_lon, these_lons, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons]


def lat_function_m0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons_m0 = [(f.masked_lon, f.fix_time.year) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.year == this_lat[1])] + [(r.masked_lon, r.creation_time.year) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.year == this_lat[1])]
    unique_lons_m0 = set(these_lons_m0)
    [lon_function_m0(this_lon, these_lons_m0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons_m0]


def lat_function_y0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons_y0 = [(f.masked_lon, f.fix_time.month) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.month == this_lat[1])] + [(r.masked_lon, r.creation_time.month) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.month == this_lat[1])]
    unique_lons_y0 = set(these_lons_y0)
    [lon_function_y0(this_lon, these_lons_y0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons_y0]


class Command(BaseCommand):
    args = ''
    help = 'Updates coverage month model data based on background location and report location data'

    def handle(self, *args, **options):
        updated = False

        last_coverage = CoverageAreaMonth.objects.all().order_by('latest_report_server_upload_time').last()
        if last_coverage:
            latest_report_server_upload_time = last_coverage.latest_report_server_upload_time
            latest_fix_id = CoverageAreaMonth.objects.order_by('latest_fix_id').last().latest_fix_id
        else:
            latest_report_server_upload_time = datetime(1970, 1, 1, tzinfo=ZoneInfo("UTC"))
            latest_fix_id = 0

        last_report = Report.objects.order_by('server_upload_time').last()
        last_fix = Fix.objects.order_by('id').last()
        if not last_coverage or latest_report_server_upload_time < last_report.server_upload_time or latest_fix_id < last_fix.id:
            report_list = Report.objects.exclude(hide=True).filter(
                Q(package_name='Tigatrapp',  creation_time__gte=settings.IOS_START_TIME)
                | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)
            ).filter(server_upload_time__gt=latest_report_server_upload_time)
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
        self.stdout.write('Successfully updated coverage area month model' if updated == True else 'No updates needed.')