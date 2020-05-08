# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import TigaUser
from tigascoring.xp_scoring import compute_user_score_in_xp_v2_fast


def compute_all_scores():
    all_users = TigaUser.objects.all()
    print("Starting...")
    goal = len(all_users)
    start = 1
    for user in all_users:
        score = compute_user_score_in_xp_v2_fast(user.user_UUID)
        user.score_v2 = score['total_score']
        user.score_v2_adult = score['score_detail']['adult']['score']
        user.score_v2_site = score['score_detail']['site']['score']
        user.score_v2_bite = score['score_detail']['bite']['score']
        user.save()
        print("Done {0} of {1}".format( start, goal ))
        start += 1


compute_all_scores()
