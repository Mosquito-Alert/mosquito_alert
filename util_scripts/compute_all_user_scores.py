# This script fills the newly created point geofield
# coding=utf-8
import django
from django.db.models import Count, Q
from django.utils import timezone

from datetime import timedelta
import os, sys
from tqdm import tqdm

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

django.setup()

from tigaserver_app.models import TigaUser

one_week_ago = timezone.now() - timedelta(days=7)

if __name__ == "__main__":
    qs = TigaUser.objects.annotate(
        report_count=Count(
            'user_reports',
            filter=Q(
                Q(user_reports__updated_at__gte=one_week_ago)
                | Q(user_reports__identification_task__updated_at__gte=one_week_ago)
            )
        )
    ).filter(report_count__gt=0)
    for user in tqdm(qs.iterator(), total=qs.count()):
        user.update_score(commit=True)