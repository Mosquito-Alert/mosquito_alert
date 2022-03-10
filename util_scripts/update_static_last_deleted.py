import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report
from progress.bar import Bar


def check():
    reports = Report.objects.all()
    bar = Bar('checking report values', max=reports.count())
    for r in reports:
        if r.deleted != r.removed and r.latest_version != r.last_version:
            print("report {0} WRONG dynamic_deleted - {1} vs static_deleted {2} dynamic_latest {3} vs static_latest {4}".format(r.version_UUID, r.deleted, r.removed, r.latest_version, r.last_version))
        bar.next()
    bar.finish()

def main():
    reports = Report.objects.all()
    bar = Bar('updating all reports', max=reports.count())
    for r in reports:
        r.removed = r.deleted
        r.last_version = r.latest_version
        r.save()
        bar.next()
    bar.finish()


if __name__ == '__main__':
    main()