import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import OrganizationPin, EuropeCountry
from django.contrib.gis.geos import GEOSGeometry


def run():

    OrganizationPin.objects.all().delete()

    countries = ['Austria', 'Cyprus', 'Portugal', 'Greece', 'Hungary', 'Serbia', 'Luxembourg', 'Netherlands', 'Spain', 'Bulgaria']

    for c in countries:
        if c == 'spain':
            url = 'http://www.mosquitoalert.com/en/espana/'
        else:
            url = 'http://www.mosquitoalert.com/en/{0}/'.format(c.lower())
        op = OrganizationPin(point=EuropeCountry.objects.get(name_engl=c).geom.centroid,textual_description=c,page_url=url)
        op.save()

run()