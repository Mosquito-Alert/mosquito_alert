import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import IdentificationTask
from django.contrib.auth.models import User

user_pk = 115

this_user = User.objects.get(pk=115)
queue = IdentificationTask.objects.backlog(user=this_user)
print(len(queue))