import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from tigaserver_app.models import Report
from progress.bar import Bar

reports = Report.objects.all()
bar = Bar('updating all reports', max=reports.count())
for r in reports:
    r.save()
    bar.next()
bar.finish()