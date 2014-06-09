from django.shortcuts import render
from django.db.models import Q
from django.http import HttpResponse
from tigaserver_app.models import Fix, Report
from django.views.decorators.clickjacking import xframe_options_exempt


def show_webmap_app(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/app.html', context)


@xframe_options_exempt
def show_embedded_webmap(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/embedded.html', context)


def show_coverage_map(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/coverage_map.html', context)


def show_grid_05(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/grid_map.05.html', context)


def show_report_map(request):
    report_list = Report.objects.all()
    context = {'report_list': report_list}
    return render(request, 'tigamap/report_map.html', context)


def show_report_map_adults(request):
    report_list = Report.objects.filter(type='adult')
    context = {'report_list': report_list, 'type': 'adult'}
    return render(request, 'tigamap/report_map.html', context)


def show_report_map_sites(request, type):
    if type == 'embornals_fonts':
        report_list = [report for report in Report.objects.all() if report.embornals or report.fonts]
    elif type == 'basins':
        report_list = [report for report in Report.objects.all() if report.basins]
    elif type == 'buckets_wells':
        report_list = [report for report in Report.objects.all() if report.buckets or report.wells]
    elif type == 'other':
        report_list = [report for report in Report.objects.all() if report.other]
    else:
        report_list = Report.objects.all()
    context = {'report_list': report_list, 'type': 'site'}
    return render(request, 'tigamap/report_map.html', context)


def show_report_map_simple_cluster(request):
    report_list = Report.objects.all()
    context = {'report_list': report_list}
    return render(request, 'tigamap/report_map_simple_cluster.html', context)


def show_report_map_basic(request):
    report_list = Report.objects.all()
    context = {'report_list': report_list}
    return render(request, 'tigamap/report_map_no_clusters.html', context)
