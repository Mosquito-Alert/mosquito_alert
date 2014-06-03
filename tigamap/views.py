from django.shortcuts import render
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


def show_report_map_basic(request):
    report_list = Report.objects.all()
    context = {'report_list': report_list}
    return render(request, 'tigamap/report_map_no_clusters.html', context)
