# coding=utf-8
# !/usr/bin/env python
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.conf import settings
from rest_framework.renderers import JSONRenderer
import json
from mosquito_alert.tigaserver_app.views import coverage_month_internal

print('Starting coverage month request')
d = coverage_month_internal()
json_string = JSONRenderer().render(d)
data = json.loads(json_string)
accumulated_results = json.dumps(data)
text_file = open(settings.STATIC_ROOT + "/coverage_month_data.json", "w")
text_file.write(accumulated_results)
text_file.close()