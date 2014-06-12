from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from tigaserver_app.models import Fix, Report
from django.views.decorators.clickjacking import xframe_options_exempt
from tigaserver_project.settings import LANGUAGES

def show_webmap_app(request):
    context = {'title': _("title")}
    return render(request, 'tigamap/app.html', context)


@xframe_options_exempt
def show_embedded_webmap(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/embedded.html', context)


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


def show_map(request, report_type='adults', category='all'):
    redirect_path = strip_lang(reverse('webmap.show_map', kwargs={'report_type': report_type, 'category': category}))
    this_title = ''
    if report_type == 'coverage':
        this_title = _('Coverage Map')
        context = {'title': this_title, 'redirect_to': redirect_path}
        return render(request, 'tigamap/coverage_map.html', context)
    elif report_type == 'adults':
        if category == 'medium':
            this_title = _('Adult tiger mosquitoes: Medium and high probability reports')
            report_list = [report for report in Report.objects.filter(type='adult') if report.tigaprob > 0]
        elif category == 'high':
            this_title = _('Adult tiger mosquitoes: High probability reports')
            report_list = [report for report in Report.objects.filter(type='adult') if report.tigaprob == 1]
        else:
            this_title = _('Adult tiger mosquitoes: All reports')
            report_list = Report.objects.filter(type='adult')
    elif report_type == 'sites':
        if category == 'drains_fountains':
            this_title = _('Breeding sites: Storm drains and fountains')
            report_list = [report for report in Report.objects.filter(type='site') if report.embornals or report.fonts]
        elif category == 'basins':
            this_title = _('Breeding sites: Basins')
            report_list = [report for report in Report.objects.filter(type='site') if report.basins]
        elif category == 'buckets_wells':
            this_title = _('Breeding sites: Buckets and wells')
            report_list = [report for report in Report.objects.filter(type='site') if report.buckets or report.wells]
        elif category == 'other':
            this_title = _('Breeding sites: Other')
            report_list = [report for report in Report.objects.filter(type='site') if report.other]
        else:
            this_title = _('Breeding sites: All reports')
            report_list = Report.objects.filter(type='site')
    context = {'title': this_title, 'report_list': report_list, 'report_type': report_type, 'redirect_to':
        redirect_path}
    return render(request, 'tigamap/report_map.html', context)

