from django.shortcuts import render
from django.db.models import Q
from datetime import date
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from tigaserver_app.models import Fix, Report
from django.views.decorators.clickjacking import xframe_options_exempt
from tigaserver_project.settings import LANGUAGES
from operator import itemgetter, attrgetter


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


def get_latest_reports(reports):
    unique_report_ids = set([r.report_id for r in reports])
    result = list()
    for this_id in unique_report_ids:
        these_reports = sorted([report for report in reports if report.report_id == this_id],
                               key=attrgetter('version_number'))
        if these_reports[0].version_number > -1:
            result.append(these_reports[-1])
    return result


def show_map(request, report_type='adults', category='all', data='live'):
    if data == 'beta':
        these_reports = get_latest_reports(Report.objects.all())
        coverage_areas = get_coverage(Fix.objects.all(), these_reports)
        href_url_name = 'webmap.show_map_beta'
    else:
        these_reports = get_latest_reports(Report.objects.filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) |
                                                                 Q(package_name='ceab.movelab.tigatrapp',
                                                                   package_version__gt=3)))
        coverage_areas = get_coverage(Fix.objects.filter(fix_time__gt='2014-06-13'), these_reports)
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
    if report_type == 'coverage':
        this_title = _('Coverage Map')
        context = {'coverage_list': coverage_areas, 'title': this_title, 'redirect_to': redirect_path, 'hrefs': hrefs}
        return render(request, 'tigamap/coverage_map.html', context)
    elif report_type == 'beta_coverage':
        this_title = _('Beta Coverage Map')
        context = {'coverage_list': coverage_areas, 'title': this_title, 'redirect_to': redirect_path, 'hrefs': hrefs}
        return render(request, 'tigamap/coverage_map_beta.html', context)
    elif report_type == 'adults':
        these_reports = [report for report in these_reports if report.type == 'adult']
        if category == 'medium':
            this_title = _('Adult tiger mosquitoes: Medium and high probability reports')
            report_list = [report for report in these_reports if report.tigaprob > 0]
        elif category == 'high':
            this_title = _('Adult tiger mosquitoes: High probability reports')
            report_list = [report for report in these_reports if report.tigaprob == 1]
        else:
            this_title = _('Adult tiger mosquitoes: All reports')
            report_list = these_reports
    elif report_type == 'sites':
        these_reports = [report for report in these_reports if report.type == 'site']
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
        report_list = [report for report in these_reports if report.type == 'adult']
    context = {'title': this_title, 'report_list': report_list, 'report_type': report_type,
               'redirect_to': redirect_path, 'hrefs': hrefs}
    return render(request, 'tigamap/report_map.html', context)

@xframe_options_exempt
def show_embedded_webmap(request):
    these_reports = get_latest_reports(Report.objects.filter(Q(package_name='Tigatrapp',  creation_time__gte=date(2014, 6, 24)) |
                                                                 Q(package_name='ceab.movelab.tigatrapp',
                                                                   package_version__gt=3)))
    report_list = [report for report in these_reports if report.type == 'adult']
    context = {'report_list': report_list}
    return render(request, 'tigamap/embedded.html', context)
