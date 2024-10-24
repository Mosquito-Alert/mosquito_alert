# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
from django.db import transaction
from django.db.models import Window, F, Min, Max
from django.db.models.functions import DenseRank
from django.utils import timezone

application = get_wsgi_application()

from tigascoring.xp_scoring import get_user_class
from tigaserver_app.models import RankingData, TigaUser

@transaction.atomic
def init_ranking_data():
    # Step 1: Clear existing ranking data
    RankingData.objects.all().delete()

    # Step 2: Get ranked users from TigaUser
    users_qs = TigaUser.objects.exclude(score_v2=0)
    ranked_users = users_qs.annotate(
        rank=Window(expression=DenseRank(), order_by=F('score_v2').desc())
    ).order_by('-score_v2')

    scores = users_qs.aggregate(
        min_score=Min('score_v2'),
        max_score=Max('score_v2')
    )
    min_score = scores['min_score']
    max_score = scores['max_score']

    # Step 3: Populate RankingData
    last_update = timezone.now()
    ranking_data_instances = []
    for user in ranked_users.iterator():
        ranking_data_instances.append(
            RankingData(
                user_uuid=user.pk,
                class_value=get_user_class(min=min_score, max=max_score, user_score=user.score_v2)['value'],
                rank=user.rank,
                score_v2=user.score_v2,
                last_update=last_update
            )
        )

    # Bulk create for efficiency
    RankingData.objects.bulk_create(ranking_data_instances)

init_ranking_data()
