"""
WSGI config for tigaserver_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os,sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/opt/python/current/app')

sys.path.append('/opt/python/run/venv/lib/python2.7/site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")

application = get_wsgi_application()
