import csv
import pydenticon

import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import TigaUser
from tigaserver_project import settings as conf

foreground = ["rgb(45,79,255)",
              "rgb(254,180,44)",
              "rgb(226,121,234)",
              "rgb(30,179,253)",
              "rgb(232,77,65)",
              "rgb(49,203,115)",
              "rgb(141,69,170)"]


generator = pydenticon.Generator(5, 5, foreground=foreground)
for user in TigaUser.objects.exclude(score_v2=0):
    identicon_png = generator.generate(user.user_UUID, 200, 200, output_format="png")
    f = open(conf.MEDIA_ROOT + '/identicons/' + user.user_UUID + ".png", "wb")
    f.write(identicon_png)
