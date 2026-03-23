from decimal import *

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework.decorators import api_view
from rest_framework.response import Response

from mosquito_alert.geo.models import EuropeCountry
from .models import ExpertReportAnnotation


@login_required
def report_expiration(request, country_id=None):
    this_user = request.user

    if not this_user.userstat.is_superexpert():
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    qs = ExpertReportAnnotation.objects.blocking()

    country = None
    if country_id is not None:
        country = get_object_or_404(EuropeCountry, pk=country_id)
        qs = qs.filter(identification_task__report__country=country)

    data_dict = {}
    for annotation in qs.select_related('user'):
        if annotation.user.username not in data_dict:
            data_dict[annotation.user.username] = []

        data_dict[annotation.user.username].append(
            {
                'report_uuid': annotation.identification_task.report_id,
                'days': (timezone.now() - annotation.created).days
            }
        )

    sorted_data = sorted(data_dict.items(), key=lambda x: x[1][0]['days'], reverse=True)

    return render(request, 'identification_tasks/report_expiration.html', { 'data':sorted_data, 'lock_period': settings.ENTOLAB_LOCK_PERIOD , 'country': country})


@transaction.atomic
@login_required
def expert_report_annotation(request):
    this_user = request.user

    if settings.SHOW_USER_AGREEMENT_ENTOLAB:
        if not this_user.userstat:
            return HttpResponse("There is a problem with your current user. Please contact the EntoLab admin at " + settings.ENTOLAB_ADMIN)

    this_user_is_expert = this_user.userstat.is_expert()
    this_user_is_superexpert = this_user.userstat.is_superexpert()

    if not (this_user_is_expert or this_user_is_superexpert):
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    if not this_user_is_superexpert:
        return HttpResponsePermanentRedirect('https://app.mosquitoalert.com')
    # NOTE: from now on, only superexpert is allowed to visit this view

    if request.method == 'GET':
        return render(request, 'identification_tasks/superexpert_report_annotation.html')


@login_required
def expert_status(request):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        groups = Group.objects.filter(name__in=['expert', 'superexpert'])
        return render(request, 'identification_tasks/expert_status.html', {'groups': groups})
    else:
        return HttpResponseRedirect(reverse('login'))

# var is an ExpertReportAnnotation
def reportannotation_formatter(var: ExpertReportAnnotation):
    return {
        'report_id': var.identification_task.report.version_UUID,
        'report_type': var.identification_task.report.type,
        'givenToExpert': var.created.strftime("%d/%m/%Y - %H:%M:%S"),
        'lastModified': var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
        'draftStatus': ExpertReportAnnotation.Status(var.status).label,
        'getCategory': var.taxon.name if var.taxon else None,
    }


@api_view(['GET'])
def expert_report_pending(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=False)

    reports = []
    for var in x.select_related('identification_task', 'identification_task__report'):
        reports.append(reportannotation_formatter(var))

    context = {'pendingReports': reports}

    return Response(context)


@api_view(['GET'])
def expert_report_complete(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=True)

    reports = []
    for var in x.select_related('identification_task', 'identification_task__report'):
        reports.append(reportannotation_formatter(var))

    context = {'completeReports': reports}

    return Response(context)


@login_required
def coarse_filter(request):
    this_user = request.user
    if this_user.groups.filter(name='coarse_filter').exists():
        range_list = [n for n in range(10, 101, 10)]
        context = {
            'tasks_per_page_choices': range_list + [200, 300],
            'countries': EuropeCountry.objects.all().order_by('name_engl')
        }
        return render(request, 'identification_tasks/coarse_filter.html', context)
    else:
        return HttpResponse("You need to belong to the coarse filter group to access this page, please contact MoveLab.")