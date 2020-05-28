from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import Report, EuropeCountry
from django.core.management import call_command

class ReportTestCase(TestCase):
    fixtures = ['europe_countries.json','tigausers.json','awardcategory.json','granter_user.json','reports.json']

    def test_fixtures_being_loaded(self):
        r = EuropeCountry.objects.get(pk=1)
        self.assertEqual(r.gid,1)