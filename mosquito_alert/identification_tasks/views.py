from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
)
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from mosquito_alert.geo.models import Country
from mosquito_alert.workspaces.models import Workspace
from .models import IdentificationTask, ExpertReportAnnotation


@login_required
def report_expiration(request, country_id=None):
    this_user = request.user

    has_global_review_perm = this_user.has_perm(
        "%(app_label)s.add_review"
        % {
            "app_label": IdentificationTask._meta.app_label,
        }
    )
    reviewer_countries = Country.objects.filter(
        workspace__collaboration_groups__reviewers=this_user
    )

    if not (has_global_review_perm or reviewer_countries.exists()):
        return HttpResponse(
            "You need to be logged in as reviewer to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab."
        )

    qs = ExpertReportAnnotation.objects.blocking()

    if reviewer_countries.exists() and not has_global_review_perm:
        qs = qs.filter(identification_task__report__country__in=reviewer_countries)

    country = None
    if country_id is not None:
        country = get_object_or_404(reviewer_countries, pk=country_id)
        qs = qs.filter(identification_task__report__country=country)

    data_dict = {}
    for annotation in qs.select_related("user"):
        if annotation.user.username not in data_dict:
            data_dict[annotation.user.username] = []

        data_dict[annotation.user.username].append(
            {
                "report_uuid": annotation.identification_task.report_id,
                "days": (timezone.now() - annotation.created).days,
            }
        )

    sorted_data = sorted(data_dict.items(), key=lambda x: x[1][0]["days"], reverse=True)

    return render(
        request,
        "identification_tasks/report_expiration.html",
        {
            "data": sorted_data,
            "lock_period": settings.ENTOLAB_LOCK_PERIOD,
            "country": country,
        },
    )


@transaction.atomic
@login_required
def expert_report_annotation(request):
    this_user = request.user

    if settings.SHOW_USER_AGREEMENT_ENTOLAB:
        if not this_user.userstat:
            return HttpResponse(
                "There is a problem with your current user. Please contact the EntoLab admin at "
                + settings.ENTOLAB_ADMIN
            )

    has_global_review_perm = this_user.has_perm(
        "%(app_label)s.add_review"
        % {
            "app_label": IdentificationTask._meta.app_label,
        }
    )

    if not has_global_review_perm:
        return HttpResponsePermanentRedirect("https://app.mosquitoalert.com")
    # NOTE: from now on, only reviewers are allowed to visit this view

    if request.method == "GET":
        return render(
            request, "identification_tasks/superexpert_report_annotation.html"
        )


@login_required
def expert_status(request):
    this_user = request.user

    has_global_review_perm = this_user.has_perm(
        "%(app_label)s.add_review"
        % {
            "app_label": IdentificationTask._meta.app_label,
        }
    )

    reviewer_workspaces_qs = Workspace.objects.filter(
        collaboration_groups__reviewers=this_user
    )

    if not (has_global_review_perm or reviewer_workspaces_qs.exists()):
        return HttpResponse("You need to be logged in as reviewer to view this page.")

    workspaces_qs = Workspace.objects.none()
    if has_global_review_perm:
        workspaces_qs = Workspace.objects.filter(members__isnull=False)
    elif reviewer_workspaces_qs.exists():
        workspaces_qs = reviewer_workspaces_qs.filter(members__isnull=False)

    return render(
        request,
        "identification_tasks/expert_status.html",
        {"workspaces": workspaces_qs.distinct().order_by("country__name_engl")},
    )


# var is an ExpertReportAnnotation
def reportannotation_formatter(var: ExpertReportAnnotation):
    return {
        "report_id": var.identification_task.report.version_UUID,
        "report_type": var.identification_task.report.type,
        "givenToExpert": var.created.strftime("%d/%m/%Y - %H:%M:%S"),
        "lastModified": var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
        "draftStatus": ExpertReportAnnotation.Status(var.status).label,
        "getCategory": var.taxon.name if var.taxon else None,
    }


@api_view(["GET"])
def expert_report_pending(request):
    user = request.query_params.get("u", None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=False)

    reports = []
    for var in x.select_related("identification_task", "identification_task__report"):
        reports.append(reportannotation_formatter(var))

    context = {"pendingReports": reports}

    return Response(context)


@api_view(["GET"])
def expert_report_complete(request):
    user = request.query_params.get("u", None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=True)

    reports = []
    for var in x.select_related("identification_task", "identification_task__report"):
        reports.append(reportannotation_formatter(var))

    context = {"completeReports": reports}

    return Response(context)


@login_required
def coarse_filter(request):
    this_user = request.user
    if this_user.groups.filter(name="coarse_filter").exists():
        range_list = [n for n in range(10, 101, 10)]
        context = {
            "tasks_per_page_choices": range_list + [200, 300],
            "countries": Country.objects.all().order_by("name_engl"),
        }
        return render(request, "identification_tasks/coarse_filter.html", context)
    else:
        return HttpResponse(
            "You need to belong to the coarse filter group to access this page, please contact MoveLab."
        )
