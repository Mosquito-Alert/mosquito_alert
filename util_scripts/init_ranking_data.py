# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigascoring.xp_scoring import get_ranking_data
from tigaserver_app.models import RankingData
import datetime

def init_ranking_data():
    data = get_ranking_data()
    RankingData.objects.all().delete()
    hydrated = []
    for d in data['data']:
        #hydrate models
        r = RankingData(
            user_uuid=d['user_uuid'],
            class_value=d['class']['value'],
            rank=d['rank'],
            score_v2=d['score_v2']
        )
        hydrated.append(r)
    RankingData.objects.bulk_create(hydrated)
    RankingData.objects.all().update(last_update=datetime.datetime.now())

init_ranking_data()
