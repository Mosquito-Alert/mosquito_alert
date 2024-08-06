import django
from django.conf import settings
from django.db.models import F

import csv
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

django.setup()

from tigaserver_app.models import GlobalAssignmentStat, EuropeCountry
from tigacrafting.models import UserStat, ExpertReportAnnotation
from tigacrafting.report_queues import get_unassigned_available_reports, get_progress_available_reports, get_ns_locked_reports
from stats.views import get_blocked_count
from tigacrafting.views import get_blocked_reports_by_country
import datetime
import pytz

def do_update():
    countries_with_at_least_one_expert = UserStat.objects.exclude(native_of__isnull=True).exclude(native_of__gid=17).values('native_of').distinct()
    countries = EuropeCountry.objects.filter(gid__in=countries_with_at_least_one_expert)
    for current_country in countries:
        unassigned_filtered = get_unassigned_available_reports(current_country)
        progress_filtered = get_progress_available_reports(current_country)
        blocked_ns = get_ns_locked_reports(current_country)
        if current_country.gid == 17:
            user_id_filter = settings.USERS_IN_STATS
        else:
            user_id_filter = UserStat.objects.filter(native_of=current_country).values('user__id')
        pending = ExpertReportAnnotation.objects.filter(user__id__in=user_id_filter).filter(validation_complete=False).filter(report__type='adult').values('report')
        n_unassigned = unassigned_filtered.count()
        n_progress = progress_filtered.count()
        n_pending = pending.count()
        n_blocked_ns = 0 if blocked_ns is None else blocked_ns.count()
        try:
            g = GlobalAssignmentStat.objects.get(country=current_country)
            g.unassigned_reports = n_unassigned
            g.in_progress_reports = n_progress
            g.pending_reports = n_pending,
            g.nsqueue_reports = n_blocked_ns,
            g.last_update = datetime.datetime.now(pytz.utc)
        except GlobalAssignmentStat.DoesNotExist:
            g = GlobalAssignmentStat(
                country=current_country,
                unassigned_reports=n_unassigned,
                in_progress_reports=n_progress,
                pending_reports=n_pending,
                nsqueue_reports=n_blocked_ns,
                last_update=datetime.datetime.now(pytz.utc)
            )
        g.save()

if __name__ == "__main__":
    do_update()