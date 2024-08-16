# This script fills the newly created point geofield
# coding=utf-8
import os, sys
from tqdm import tqdm

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import TigaUser

if __name__ == "__main__":
    qs = TigaUser.objects.all()
    for user in tqdm(qs.iterator(), total=qs.count()):
        user.update_score(commit=True)
