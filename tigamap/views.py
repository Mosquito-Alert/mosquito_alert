from django.shortcuts import render, redirect
from django.db.models import Q
from datetime import date
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from tigaserver_app.models import Fix, Report
from django.views.decorators.clickjacking import xframe_options_exempt
from tigaserver_project.settings import LANGUAGES
from operator import itemgetter, attrgetter
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Count
import math

def show_grid_05(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/grid_map.05.html', context)


def strip_lang(path):
    l_path = path.split('/')
    no_lang_path = l_path
    codes = []
    for code, name in LANGUAGES:
        codes.append(code)
        if l_path[1] in codes:
            del l_path[1]
            no_lang_path = '/'.join(l_path)
    return no_lang_path


class CoverageArea():
    lat = float
    lon = float
    n_fixes = int

    def __init__(self, lat, lon, n_fixes):
        self.lat = lat
        self.lon = lon
        self.n_fixes = n_fixes

    def increment(self):
        self.n_fixes += 1


class OEArea():
    lat = float
    lon = float
    background_fixes = int
    report_fixes = int
    adult_reports = int
    occurrence = int
    exposure = int
    oe_rate = float

    def __init__(self, lat, lon, background_fixes, report_fixes, adult_reports):
        self.lat = lat
        self.lon = lon
        self.background_fixes = background_fixes
        self.report_fixes = report_fixes
        self.adult_reports = adult_reports
        self.exposure = background_fixes + report_fixes
        self.occurrence = adult_reports
        if self.background_fixes > 0:
            self.oe_rate = float(self.occurrence)/self.exposure


def get_coverage(fix_list, report_list):
    result = list()
    full_lat_list = [f.masked_lat for f in fix_list] + [r.masked_lat for r in report_list if r.masked_lat is not None]
    unique_lats = set(full_lat_list)
    for this_lat in unique_lats:
        these_lons = [f.masked_lon for f in fix_list if f.masked_lat == this_lat] + [r.masked_lon for r in
                                                                                     report_list if r.masked_lat is
                                                                                                    not None and r
                                                                                                        .masked_lat ==
                                                                                                    this_lat]
        unique_lons = set(these_lons)
        for this_lon in unique_lons:
            n_fixes = len([l for l in these_lons if l == this_lon])
            result.append(CoverageArea(this_lat, this_lon, n_fixes))
    return result


def get_oe_rates(fix_list, report_list):
    result = list()
    full_lat_list = [f.masked_lat for f in fix_list] + [r.masked_lat for r in report_list if r.masked_lat is not None]
    unique_lats = set(full_lat_list)
    for this_lat in unique_lats:
        these_lons = [f.masked_lon for f in fix_list if f.masked_lat == this_lat] + [r.masked_lon for r in
                                                                                     report_list if r.masked_lat is
                                                                                                    not None and r
                                                                                                        .masked_lat ==
                                                                                                    this_lat]
        these_background_fix_lons = [f.masked_lon for f in fix_list if f.masked_lat == this_lat]
        these_report_fix_lons = [r.masked_lon for r in report_list if r.masked_lat is not None and r.masked_lat == this_lat]
        these_adult_report_lons = [r.masked_lon for r in report_list if r.type == 'adult' and r.masked_lat is not None and r.masked_lat == this_lat]
        unique_lons = set(these_lons)
        for this_lon in unique_lons:
            these_background_fixes = len([l for l in these_background_fix_lons if l == this_lon])
            these_report_fixes = len([l for l in these_report_fix_lons if l == this_lon])
            these_adult_reports = len([l for l in these_adult_report_lons if l == this_lon])
            result.append(OEArea(lat=this_lat, lon=this_lon, background_fixes=these_background_fixes, report_fixes=these_report_fixes, adult_reports=these_adult_reports))
    return result


def get_latest_reports(reports):
    unique_report_ids = set([r.report_id for r in reports])
    result = list()
    for this_id in unique_report_ids:
        these_reports = sorted([report for report in reports if report.report_id == this_id],
                               key=attrgetter('version_number'))
        if these_reports[0].version_number > -1:
            result.append(these_reports[-1])
    return result


def show_map(request, report_type='adults', category='all', data='live', detail='none', validation=''):
    # set up hrefs and redirects
    if detail == 'detailed':
        href_url_name = 'webmap.show_map_detailed'
    else:
        href_url_name = 'webmap.show_map'
    hrefs = {'coverage': reverse(href_url_name, kwargs={'report_type': 'coverage', 'category': 'all'}),
                 'adults_all': reverse(href_url_name, kwargs={'report_type': 'adults', 'category': 'all'}),
                 'adults_medium': reverse(href_url_name, kwargs={'report_type': 'adults', 'category': 'medium'}),
                 'adults_high': reverse(href_url_name, kwargs={'report_type': 'adults', 'category': 'high'}),
                 'sites_all': reverse(href_url_name, kwargs={'report_type': 'sites', 'category': 'all'}),
                 'sites_drains_fountains': reverse(href_url_name, kwargs={'report_type': 'sites', 'category': 'drains_fountains'}),
                 'sites_basins': reverse(href_url_name, kwargs={'report_type': 'sites', 'category': 'basins'}),
                 'sites_buckets_wells': reverse(href_url_name, kwargs={'report_type': 'sites', 'category': 'buckets_wells'}),
                 'sites_other': reverse(href_url_name, kwargs={'report_type': 'sites', 'category': 'other'}),
                 }
    redirect_path = strip_lang(reverse(href_url_name, kwargs={'report_type': report_type, 'category': category}))

    # set up reports for coverage
    if report_type == 'coverage':
        these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)))
        coverage_areas = get_coverage(Fix.objects.filter(fix_time__gt='2014-06-13'), these_reports)
        this_title = _('Coverage Map')
        context = {'coverage_list': coverage_areas, 'title': this_title, 'redirect_to': redirect_path, 'hrefs': hrefs}
        return render(request, 'tigamap/coverage_map.html', context)

    # set up reports for oe-rates
    if report_type == 'oe':
        these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)))
        oe_areas = get_oe_rates(Fix.objects.filter(fix_time__gt='2014-06-13'), these_reports)
        this_title = _('Pseudo Occurrence-Exposure Map')
        context = {'area_list': oe_areas, 'title': this_title, 'redirect_to': redirect_path, 'hrefs': hrefs}
        return render(request, 'tigamap/oe_map.html', context)

    # now for adults
    elif report_type == 'adults':
        if category == 'crowd_validated':
            this_title = _('Adult tiger mosquitoes: Validated reports')
            these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(type='adult').filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)).annotate(n_responses=Count('photos__crowdcraftingtask__responses')).filter(n_responses__gte=30))
            if these_reports:
                    report_list = filter(lambda x: x.get_crowdcrafting_score() is not None, these_reports)
            else:
                report_list = None
        else:
            these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(type='adult').filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)))
            if category == 'medium':
                this_title = _('Adult tiger mosquitoes: Medium and high probability reports')
                if these_reports:
                    report_list = filter(lambda x: x.tigaprob > 0, these_reports)
                else:
                    report_list = None
            elif category == 'high':
                this_title = _('Adult tiger mosquitoes: High probability reports')
                if these_reports:
                    report_list = filter(lambda x: x.tigaprob == 1, these_reports)
                else:
                    report_list = None
            else:
                this_title = _('Adult tiger mosquitoes: All reports')
                report_list = these_reports

    #  now sites
    elif report_type == 'sites':
        if category == 'crowd_validated':
            this_title = _('Breeding Sites: Validated reports')
            these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(type='site').filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)).annotate(n_responses=Count('photos__crowdcraftingtask__responses')).filter(n_responses__gte=30))
            if these_reports:
                report_list = filter(lambda x: x.get_crowdcrafting_score() is not None, these_reports)
            else:
                report_list = None
        else:
            these_reports = get_latest_reports(Report.objects.exclude(hide=True).filter(type='site').filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)))
            # TODO change these list comprehensions to filters if it gains speed (not sure it would)
            if category == 'drains_fountains':
                this_title = _('Breeding sites: Storm drains and fountains')
                report_list = [report for report in these_reports if report.embornals or report.fonts]
            elif category == 'basins':
                this_title = _('Breeding sites: Basins')
                report_list = [report for report in these_reports if report.basins]
            elif category == 'buckets_wells':
                this_title = _('Breeding sites: Buckets and wells')
                report_list = [report for report in these_reports if report.buckets or report.wells]
            elif category == 'other':
                this_title = _('Breeding sites: Other')
                report_list = [report for report in these_reports if report.other]
            else:
                this_title = _('Breeding sites: All reports')
                report_list = these_reports
    else:
        this_title = _('Adult tiger mosquitoes: All reports')
        report_list = get_latest_reports(Report.objects.exclude(hide=True).filter(type='adult').filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)))
    context = {'title': this_title, 'report_list': report_list, 'report_type': report_type,
               'redirect_to': redirect_path, 'hrefs': hrefs, 'detailed': detail, 'validation': validation}
    return render(request, 'tigamap/report_map.html', context)

@login_required
def show_detailed_map(request, report_type='adults', category='all', data='live', detail='detailed', validation=''):
    if request.user.groups.filter(name='movelabmap').exists():
        return show_map(request, report_type, category, data, detail, validation)
    else:
        return render(request, 'registration/no_permission.html')

@xframe_options_exempt
def show_embedded_webmap(request, detail='none'):
    these_reports = get_latest_reports(Report.objects.filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) |
                                                                 Q(package_name='ceab.movelab.tigatrapp',
                                                                   package_version__gt=3)).filter(type='adult').exclude(hide=True))
    context = {'report_list': these_reports, 'detailed': detail}
    return render(request, 'tigamap/embedded.html', context)


def show_single_report_map(request, version_uuid, detail='detailed'):
    this_report = Report.objects.filter(version_UUID=version_uuid)
    context = {'report_list': this_report, 'detailed': detail}
    return render(request, 'tigamap/embedded.html', context)

