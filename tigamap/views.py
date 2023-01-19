from django.shortcuts import render
from django.utils.translation import ugettext as _
from tigaserver_app.models import Report
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings
from django.http import HttpResponseRedirect


def single_report_map_simplified(request, version_uuid):
    this_report = Report.objects.get(version_UUID=version_uuid)
    context = {'report': this_report }
    return render(request, 'tigamap/single_simple.html', context)


def show_single_report_map(request, version_uuid, detail='detailed'):
    this_report = Report.objects.filter(version_UUID=version_uuid)
    context = {'report_list': this_report, 'detailed': detail}
    return render(request, 'tigamap/embedded.html', context)

@xframe_options_exempt
def show_filterable_report_map(request):
    #302 Redirect to new map
    languages = [l[0] for l in settings.LANGUAGES]
    current_lang = request.LANGUAGE_CODE
    if current_lang in languages:
        return HttpResponseRedirect('/static/tigapublic/spain.html#/' + current_lang + '/')
    return HttpResponseRedirect('/static/tigapublic/spain.html#/es/')
