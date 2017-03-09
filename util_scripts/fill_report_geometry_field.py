# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE","tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from tigaserver_app.models import Report

reports = Report.objects.all()

i = len(reports)
j = 0
for report in reports:
	if report.point is None:
		if report.get_point() is not None:
			report.point = report.get_point()
			report.save()
	j = j + 1
	print 'Fixed report ' + str(j) + ' of ' + str(i)
